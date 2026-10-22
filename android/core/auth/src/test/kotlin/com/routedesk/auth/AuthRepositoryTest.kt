package com.routedesk.auth

import com.routedesk.model.Role
import com.routedesk.network.api.RouteDeskApiService
import com.routedesk.network.dto.DemoTokenRequest
import com.routedesk.network.dto.RefreshTokenRequest
import com.routedesk.network.dto.TokenRequest
import com.routedesk.network.dto.TokenResponse
import com.routedesk.network.dto.UserMeDto
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.runBlocking
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import retrofit2.Response

class AuthRepositoryTest {

    private lateinit var mockApiService: RouteDeskApiService
    private lateinit var tokenStore: TokenStore
    private lateinit var sessionManager: SessionManager
    private lateinit var repository: DefaultAuthRepository

    @BeforeEach
    fun setup() {
        mockApiService = mockk()
        tokenStore = InMemoryTokenStore()
        sessionManager = SessionManager(tokenStore)
        repository = DefaultAuthRepository(
            apiService = mockApiService,
            tokenStore = tokenStore,
            sessionManager = sessionManager
        )
    }

    @Test
    fun `login sets tokens and marks session authenticated`() = runBlocking {
        val testUser = UserMeDto(
            id = "usr_100",
            email = "engineer@example.com",
            name = "Test Engineer",
            role = "engineer"
        )
        val tokenResponse = TokenResponse(
            accessToken = "access_123",
            expiresIn = 900,
            refreshToken = "refresh_456",
            me = testUser
        )

        coEvery {
            mockApiService.login(TokenRequest("engineer@example.com", "Password123!"))
        } returns Response.success(tokenResponse)

        val result = repository.login("engineer@example.com", "Password123!")

        assertEquals(testUser, result)
        assertEquals("access_123", tokenStore.getAccessToken())
        assertEquals("refresh_456", tokenStore.getRefreshToken())
        assertTrue(sessionManager.sessionState.value is SessionState.Authenticated)
        assertEquals(Role.ENGINEER, sessionManager.currentRole)
    }

    @Test
    fun `loginDemo sets tokens and updates current role`() = runBlocking {
        val testUser = UserMeDto(
            id = "usr_demo",
            email = "approver@example.com",
            name = "Demo Approver",
            role = "approver"
        )
        val tokenResponse = TokenResponse(
            accessToken = "demo_access",
            expiresIn = 900,
            refreshToken = "demo_refresh",
            me = testUser
        )

        coEvery {
            mockApiService.loginDemo(DemoTokenRequest("approver"))
        } returns Response.success(tokenResponse)

        val result = repository.loginDemo(Role.APPROVER)

        assertEquals(testUser, result)
        assertEquals(Role.APPROVER, sessionManager.currentRole)
        assertEquals("demo_access", tokenStore.getAccessToken())
    }

    @Test
    fun `logout clears tokens and sets session unauthenticated`() = runBlocking {
        tokenStore.setTokens("acc", 900, "ref")
        sessionManager.setAuthenticated(UserMeDto("id", "email", "name", "requester"))

        coEvery {
            mockApiService.logout(RefreshTokenRequest("ref"))
        } returns Response.success(Unit)

        repository.logout()

        coVerify { mockApiService.logout(RefreshTokenRequest("ref")) }
        assertNull(tokenStore.getAccessToken())
        assertNull(tokenStore.getRefreshToken())
        assertTrue(sessionManager.sessionState.value is SessionState.Unauthenticated)
    }

    @Test
    fun `restoreSession returns false when no refresh token exists`() = runBlocking {
        val success = repository.restoreSession()
        assertFalse(success)
        assertTrue(sessionManager.sessionState.value is SessionState.Unauthenticated)
    }
}
