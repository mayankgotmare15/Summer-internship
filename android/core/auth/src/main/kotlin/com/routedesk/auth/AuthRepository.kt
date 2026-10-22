package com.routedesk.auth

import com.routedesk.model.Role
import com.routedesk.network.api.RouteDeskApiService
import com.routedesk.network.dto.DemoTokenRequest
import com.routedesk.network.dto.RefreshTokenRequest
import com.routedesk.network.dto.TokenRequest
import com.routedesk.network.dto.UserMeDto
import com.routedesk.network.unwrapOrThrow
import kotlinx.coroutines.flow.StateFlow

interface AuthRepository {
    val sessionState: StateFlow<SessionState>
    suspend fun login(email: String, password: String): UserMeDto
    suspend fun loginDemo(role: Role): UserMeDto
    suspend fun restoreSession(): Boolean
    suspend fun logout()
    suspend fun deleteAccount()
}

class DefaultAuthRepository(
    private val apiService: RouteDeskApiService,
    private val tokenStore: TokenStore,
    private val sessionManager: SessionManager
) : AuthRepository {

    override val sessionState: StateFlow<SessionState> = sessionManager.sessionState

    override suspend fun login(email: String, password: String): UserMeDto {
        val response = apiService.login(TokenRequest(email = email, password = password)).unwrapOrThrow()
        tokenStore.setTokens(
            accessToken = response.accessToken,
            expiresInSeconds = response.expiresIn,
            refreshToken = response.refreshToken
        )
        sessionManager.setAuthenticated(response.me)
        return response.me
    }

    override suspend fun loginDemo(role: Role): UserMeDto {
        val response = apiService.loginDemo(DemoTokenRequest(role = role.name.lowercase())).unwrapOrThrow()
        tokenStore.setTokens(
            accessToken = response.accessToken,
            expiresInSeconds = response.expiresIn,
            refreshToken = response.refreshToken
        )
        sessionManager.setAuthenticated(response.me)
        return response.me
    }

    override suspend fun restoreSession(): Boolean {
        val refreshToken = tokenStore.getRefreshToken()
        if (refreshToken.isNullOrBlank()) {
            sessionManager.setUnauthenticated(null)
            return false
        }

        return try {
            val me = apiService.getCurrentUser().unwrapOrThrow()
            sessionManager.setAuthenticated(me)
            true
        } catch (e: Exception) {
            sessionManager.setUnauthenticated("Session expired.")
            false
        }
    }

    override suspend fun logout() {
        val refreshToken = tokenStore.getRefreshToken()
        if (!refreshToken.isNullOrBlank()) {
            try {
                apiService.logout(RefreshTokenRequest(refreshToken = refreshToken))
            } catch (_: Exception) {
                // Ignore network errors on logout
            }
        }
        tokenStore.clearTokens()
        sessionManager.setUnauthenticated(null)
    }

    override suspend fun deleteAccount() {
        apiService.deleteAccount().unwrapOrThrow()
        tokenStore.clearTokens()
        sessionManager.setUnauthenticated("Account deleted.")
    }
}
