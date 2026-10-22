package com.routedesk.model

import kotlinx.datetime.Instant
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class MessageKind {
    @SerialName("public")
    PUBLIC,

    @SerialName("internal_note")
    INTERNAL_NOTE,

    @SerialName("system")
    SYSTEM
}

@Serializable
data class Message(
    val id: String,
    @SerialName("author_id")
    val authorId: String? = null,
    @SerialName("author_name")
    val authorName: String? = null,
    val kind: MessageKind = MessageKind.PUBLIC,
    val body: String,
    @SerialName("created_at")
    val createdAt: Instant,
    @SerialName("is_queued")
    val isQueued: Boolean = false
)

@Serializable
data class Attachment(
    val id: String,
    val filename: String,
    @SerialName("content_type")
    val contentType: String,
    val size: Long,
    @SerialName("download_url")
    val downloadUrl: String,
    @SerialName("created_at")
    val createdAt: Instant
)

@Serializable
data class EtaChange(
    @SerialName("changed_by")
    val changedBy: MemberRef,
    @SerialName("previous_eta")
    val previousEta: Instant,
    @SerialName("new_eta")
    val newEta: Instant,
    val reason: String,
    @SerialName("changed_at")
    val changedAt: Instant
)

@Serializable
enum class SlaState {
    @SerialName("on_track")
    ON_TRACK,

    @SerialName("at_risk")
    AT_RISK,

    @SerialName("breached")
    BREACHED,

    @SerialName("paused")
    PAUSED,

    @SerialName("completed")
    COMPLETED
}

@Serializable
data class Ticket(
    val id: String,
    @SerialName("ticket_uuid")
    val ticketUuid: String,
    val subject: String,
    val description: String,
    val category: Category,
    val priority: Priority,
    @SerialName("priority_source")
    val prioritySource: PrioritySource = PrioritySource.MODEL,
    val status: TicketStatus,
    val decision: Decision = Decision.AUTO_ROUTE,
    @SerialName("review_reason")
    val reviewReason: ReviewReason? = null,
    val team: TeamRef,
    val assignee: MemberRef? = null,
    @SerialName("is_escalated")
    val isEscalated: Boolean = false,
    @SerialName("escalation_level")
    val escalationLevel: EscalationLevel = EscalationLevel.E1,
    @SerialName("can_escalate")
    val canEscalate: Boolean = false,
    @SerialName("escalation_eligibility")
    val escalationEligibility: EscalationEligibility? = null,
    @SerialName("allowed_actions")
    val allowedActions: List<AllowedAction> = emptyList(),
    @SerialName("first_response_due")
    val firstResponseDue: Instant? = null,
    @SerialName("resolution_due")
    val resolutionDue: Instant? = null,
    @SerialName("first_responded_at")
    val firstRespondedAt: Instant? = null,
    @SerialName("sla_state")
    val slaState: SlaState = SlaState.ON_TRACK,
    @SerialName("used_pct")
    val usedPct: Double = 0.0,
    val messages: List<Message> = emptyList(),
    val attachments: List<Attachment> = emptyList(),
    @SerialName("eta_history")
    val etaHistory: List<EtaChange> = emptyList(),
    val version: Long = 1,
    @SerialName("is_sending")
    val isSending: Boolean = false,
    @SerialName("created_at")
    val createdAt: Instant,
    @SerialName("updated_at")
    val updatedAt: Instant? = null
)
