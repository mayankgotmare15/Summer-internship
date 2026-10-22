package com.routedesk.auth

import com.routedesk.model.Role
import com.routedesk.network.api.RouteDeskApiService
import com.routedesk.network.dto.RefreshTokenRequest
import com.routedesk.network.dto.TokenResponse
import com.routedesk.network.dto.UserMeDto
import io.mockk.coEvery
import io.mockk.mockk
import okhttp3.Protocol
import okhttp3.Request
import okhttp3.Response
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import retrofit2.Response as RetrofitResponse

class TokenAuthenticatorTest {

    private lateinit var tokenStore: TokenStore
    private lateinit var sessionManager: SessionManager
    private lateinit var mockApiService: RouteDeskApiService
    private lateinit var authenticator: TokenAuthenticator

    @BeforeEach
    fun setup() {
        tokenStore = InMemoryTokenStore()
        sessionManager = SessionManager(tokenStore)
        mockApiService = mockk()
        authenticator = TokenAuthenticator(
            tokenStore = tokenStore,
            sessionManager = sessionManager,
            apiServiceProvider = { mockApiService }
        )
    }

    @Test
    fun `test authenticate rotates refresh token on 401 and returns new request`() {
        tokenStore.setTokens("old_access_token", 900, "old_refresh_token")

        val newAccessToken = "new_access_token_777"
        val newRefreshToken = "new_refresh_token_888"

        coEvery { mockApiService.refreshToken(RefreshTokenRequest("old_refresh_token")) } returns RetrofitResponse.success(
            TokenResponse(
                accessToken = newAccessToken,
                expiresIn = 900,
                refreshToken = newRefreshToken,
                me = UserMeDto(
                    id = "usr_01",
                    email = "test@example.com",
                    name = "Test User",
                    role = "requester"
                )
            )
        )

        val failedRequest = Request.Builder()
            .url("https://api.routedesk.com/tickets")
            .header("Authorization", "Bearer old_access_token")
            .build()

        val response = Response.Builder()
            .request(failedRequest)
            .protocol(Protocol.HTTP_1_1)
            .code(401)
            .message("Unauthorized")
            .build()

        val retriedRequest = authenticator.authenticate(null, response)

        assertNotNull(retriedRequest)
        assertEquals("Bearer $newAccessToken", retriedRequest?.header("Authorization"))
        assertEquals(newAccessToken, tokenStore.getAccessToken())
        assertEquals(newRefreshToken, tokenStore.getRefreshToken())
        assertEquals(Role.REQUESTER, sessionManager.currentRole)
    }

    @Test
    fun `test authenticate marks session unauthenticated when refresh token fails`() {
        tokenStore.setTokens("old_access_token", 900, "invalid_refresh_token")

        coEvery { mockApiService.refreshToken(RefreshTokenRequest("invalid_refresh_token")) } returns RetrofitResponse.error(
            401,
            okhttp3.ResponseBody.create(null, """{"code":"AUTH_INVALID","message":"Invalid token"}""")
        )

        val failedRequest = Request.Builder()
            .url("https://api.routedesk.com/tickets")
            .header("Authorization", "Bearer old_access_token")
            .build()

        val response = Response.Builder()
            .request(failedRequest)
            .protocol(Protocol.HTTP_1_1)
            .code(401)
            .message("Unauthorized")
            .build()

        val retriedRequest = authenticator.authenticate(null, response)

        assertNull(retriedRequest)
        assertTrue(sessionManager.sessionState.value is SessionState.Unauthenticated)
        assertNull(tokenStore.getAccessToken())
    }
}
