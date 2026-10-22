package com.routedesk.auth

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class TokenStoreTest {

    @Test
    fun `test in-memory token store lifecycle`() {
        val store = InMemoryTokenStore()

        assertNull(store.getAccessToken())
        assertNull(store.getRefreshToken())
        assertTrue(store.isAccessTokenExpired())

        store.setTokens(
            accessToken = "access_token_abc",
            expiresInSeconds = 900,
            refreshToken = "refresh_token_xyz"
        )

        assertEquals("access_token_abc", store.getAccessToken())
        assertEquals("refresh_token_xyz", store.getRefreshToken())
        assertFalse(store.isAccessTokenExpired())

        store.clearTokens()

        assertNull(store.getAccessToken())
        assertNull(store.getRefreshToken())
        assertTrue(store.isAccessTokenExpired())
    }
}
