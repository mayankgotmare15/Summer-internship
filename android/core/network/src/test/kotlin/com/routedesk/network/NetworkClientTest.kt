package com.routedesk.network

import com.routedesk.network.dto.PredictRequest
import com.routedesk.network.dto.TicketCreateRequest
import com.routedesk.network.dto.TokenRequest
import com.routedesk.testing.MockResponseDispatcher
import kotlinx.coroutines.test.runTest
import okhttp3.mockwebserver.MockWebServer
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

class NetworkClientTest {

    private lateinit var mockWebServer: MockWebServer
    private lateinit var networkFactory: NetworkClientFactory

    @BeforeEach
    fun setup() {
        mockWebServer = MockWebServer()
        mockWebServer.dispatcher = MockResponseDispatcher()
        mockWebServer.start()

        networkFactory = NetworkClientFactory(
            baseUrl = mockWebServer.url("/").toString(),
            tokenProvider = { "mock_test_token" },
            isDebug = true
        )
    }

    @AfterEach
    fun teardown() {
        mockWebServer.shutdown()
    }

    @Test
    fun `test login returns tokens and user info`() = runTest {
        val api = networkFactory.createApiService()
        val response = api.login(TokenRequest("alex@example.com", "password")).unwrapOrThrow()

        assertNotNull(response.accessToken)
        assertEquals("usr_req_01", response.me.id)
        assertEquals("requester", response.me.role)
    }

    @Test
    fun `test predict returns categories and confidence`() = runTest {
        val api = networkFactory.createApiService()
        val response = api.predict(PredictRequest("VPN dropping frequently")).unwrapOrThrow()

        assertEquals("access", response.category)
        assertTrue(response.categoryConfidence >= 0.70)
        assertEquals("high", response.priority)
        assertEquals("auto_route", response.decision)
    }

    @Test
    fun `test createTicket returns assigned owner and SLA target`() = runTest {
        val api = networkFactory.createApiService()
        val response = api.createTicket(
            idempotencyKey = "uuid_test_123",
            request = TicketCreateRequest(
                subject = "VPN dropping",
                description = "VPN dropping frequently in office",
                channel = "android"
            )
        ).unwrapOrThrow()

        assertEquals("T-1042", response.id)
        assertEquals("assigned", response.status)
        assertEquals("Priya Sharma", response.assignee?.name)
        assertTrue(response.canEscalate)
    }
}
