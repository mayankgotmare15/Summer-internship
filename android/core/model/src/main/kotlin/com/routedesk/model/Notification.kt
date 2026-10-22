package com.routedesk.model

import kotlinx.datetime.Instant
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class NotificationType {
    @SerialName("escalation_assigned")
    ESCALATION_ASSIGNED,

    @SerialName("escalation_deadline_warning")
    ESCALATION_DEADLINE_WARNING,

    @SerialName("escalation_outcome")
    ESCALATION_OUTCOME,

    @SerialName("approval_pending")
    APPROVAL_PENDING,

    @SerialName("approval_outcome")
    APPROVAL_OUTCOME,

    @SerialName("sla_risk")
    SLA_RISK,

    @SerialName("sla_breached")
    SLA_BREACHED,

    @SerialName("ticket_assigned")
    TICKET_ASSIGNED,

    @SerialName("eta_changed")
    ETA_CHANGED,

    @SerialName("status_changed")
    STATUS_CHANGED,

    @SerialName("message_received")
    MESSAGE_RECEIVED,

    @SerialName("info_requested")
    INFO_REQUESTED,

    @SerialName("system_status")
    SYSTEM_STATUS
}

@Serializable
data class NotificationItem(
    val id: String,
    val type: NotificationType,
    val title: String,
    val body: String,
    @SerialName("ticket_id")
    val ticketId: String? = null,
    @SerialName("escalation_id")
    val escalationId: String? = null,
    @SerialName("deep_link_url")
    val deepLinkUrl: String? = null,
    @SerialName("is_read")
    val isRead: Boolean = false,
    @SerialName("created_at")
    val createdAt: Instant
)
