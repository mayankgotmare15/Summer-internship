package com.routedesk.auth

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.datetime.Clock
import kotlinx.datetime.Instant
import java.util.concurrent.atomic.AtomicReference

interface TokenStore {
    fun getAccessToken(): String?
    fun setTokens(accessToken: String, expiresInSeconds: Long, refreshToken: String)
    fun getRefreshToken(): String?
    fun clearTokens()
    fun isAccessTokenExpired(): Boolean
}

class InMemoryTokenStore : TokenStore {
    private val accessTokenRef = AtomicReference<String?>(null)
    private val refreshTokenRef = AtomicReference<String?>(null)
    private val expiresAtRef = AtomicReference<Instant?>(null)

    override fun getAccessToken(): String? = accessTokenRef.get()

    override fun setTokens(accessToken: String, expiresInSeconds: Long, refreshToken: String) {
        accessTokenRef.set(accessToken)
        refreshTokenRef.set(refreshToken)
        val expiresAt = Clock.System.now().plus(kotlin.time.Duration.parse("${expiresInSeconds}s"))
        expiresAtRef.set(expiresAt)
    }

    override fun getRefreshToken(): String? = refreshTokenRef.get()

    override fun clearTokens() {
        accessTokenRef.set(null)
        refreshTokenRef.set(null)
        expiresAtRef.set(null)
    }

    override fun isAccessTokenExpired(): Boolean {
        val expiresAt = expiresAtRef.get() ?: return true
        // Buffer by 30 seconds to refresh proactively
        return Clock.System.now() >= expiresAt.minus(kotlin.time.Duration.parse("30s"))
    }
}
