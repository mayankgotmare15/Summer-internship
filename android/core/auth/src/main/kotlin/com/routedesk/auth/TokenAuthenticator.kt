package com.routedesk.auth

import com.routedesk.network.api.RouteDeskApiService
import com.routedesk.network.dto.RefreshTokenRequest
import kotlinx.coroutines.runBlocking
import okhttp3.Authenticator
import okhttp3.Request
import okhttp3.Response
import okhttp3.Route

class TokenAuthenticator(
    private val tokenStore: TokenStore,
    private val sessionManager: SessionManager,
    private val apiServiceProvider: () -> RouteDeskApiService
) : Authenticator {

    @Synchronized
    override fun authenticate(route: Route?, response: Response): Request? {
        // Prevent infinite loops if retry also gets 401
        if (responseCount(response) >= 2) {
            sessionManager.setUnauthenticated("Authentication failed after retry.")
            return null
        }

        val currentRefreshToken = tokenStore.getRefreshToken()
        if (currentRefreshToken.isNullOrBlank()) {
            sessionManager.setUnauthenticated("No refresh token available.")
            return null
        }

        // Check if another thread already refreshed the token
        val currentAccessToken = tokenStore.getAccessToken()
        val requestToken = response.request.header("Authorization")?.removePrefix("Bearer ")
        if (currentAccessToken != null && currentAccessToken != requestToken) {
            // Already refreshed by concurrent thread; retry with the new token
            return response.request.newBuilder()
                .header("Authorization", "Bearer $currentAccessToken")
                .build()
        }

        return try {
            val refreshResponse = runBlocking {
                apiServiceProvider().refreshToken(RefreshTokenRequest(refreshToken = currentRefreshToken))
            }

            if (refreshResponse.isSuccessful && refreshResponse.body() != null) {
                val tokenData = refreshResponse.body()!!
                tokenStore.setTokens(
                    accessToken = tokenData.accessToken,
                    expiresInSeconds = tokenData.expiresIn,
                    refreshToken = tokenData.refreshToken
                )
                sessionManager.setAuthenticated(tokenData.me)

                response.request.newBuilder()
                    .header("Authorization", "Bearer ${tokenData.accessToken}")
                    .build()
            } else {
                sessionManager.setUnauthenticated("Session expired. Please sign in again.")
                null
            }
        } catch (e: Exception) {
            sessionManager.setUnauthenticated("Network error during session refresh: ${e.message}")
            null
        }
    }

    private fun responseCount(response: Response): Int {
        var result = 1
        var prior = response.priorResponse
        while (prior != null) {
            result++
            prior = prior.priorResponse
        }
        return result
    }
}
