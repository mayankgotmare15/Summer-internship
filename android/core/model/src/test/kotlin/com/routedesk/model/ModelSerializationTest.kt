package com.routedesk.model

import kotlinx.datetime.Clock
import kotlinx.datetime.Instant
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class ModelSerializationTest {

    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = true
    }

    @Test
    fun `test Ticket serialization roundtrip`() {
        val now = Clock.System.now()
        val ticket = Ticket(
            id = "T-1042",
            ticketUuid = "550e8400-e29b-41d4-a716-446655440000",
            subject = "VPN connection drops every 10 minutes",
            description = "Whenever I connect to the Pune office VPN, it drops constantly.",
            category = Category.NETWORK,
            priority = Priority.HIGH,
            status = TicketStatus.IN_PROGRESS,
            team = TeamRef(code = "net_ops", name = "Network Operations"),
            assignee = MemberRef(id = "user_42", name = "Priya Sharma", email = "priya@example.com", role = "engineer"),
            allowedActions = listOf(AllowedAction.UPDATE_STATUS, AllowedAction.CHANGE_ETA, AllowedAction.REQUEST_INFO),
            firstResponseDue = now,
            resolutionDue = now,
            createdAt = now
        )

        val encoded = json.encodeToString(ticket)
        assertNotNull(encoded)
        assertTrue(encoded.contains("T-1042"))

        val decoded = json.decodeFromString<Ticket>(encoded)
        assertEquals(ticket.id, decoded.id)
        assertEquals(Category.NETWORK, decoded.category)
        assertEquals(Priority.HIGH, decoded.priority)
        assertEquals(TicketStatus.IN_PROGRESS, decoded.status)
        assertEquals(3, decoded.allowedActions.size)
    }

    @Test
    fun `test Category fromCode returns fallback on unknown`() {
        assertEquals(Category.ACCESS, Category.fromCode("access"))
        assertEquals(Category.HARDWARE, Category.fromCode("hardware"))
        assertEquals(Category.SOFTWARE, Category.fromCode("unknown_foo"))
    }

    @Test
    fun `test EscalationLevel progression`() {
        assertEquals(EscalationLevel.E2, EscalationLevel.E1.nextLevel)
        assertEquals(EscalationLevel.E3, EscalationLevel.E2.nextLevel)
        assertEquals(EscalationLevel.E4, EscalationLevel.E3.nextLevel)
        assertEquals(null, EscalationLevel.E4.nextLevel)
    }
}
