package com.routedesk.network.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class TicketCreateRequest(
    val subject: String,
    val description: String,
    @SerialName("blocking_team")
    val blockingTeam: Boolean = false,
    val channel: String = "android",
    @SerialName("category_hint")
    val categoryHint: String? = null
)

@Serializable
data class MemberRefDto(
    val id: String,
    val name: String,
    val email: String,
    val role: String,
    @SerialName("avatar_url")
    val avatarUrl: String? = null
)

@Serializable
data class TicketCreatedResponse(
    val id: String,
    @SerialName("ticket_uuid")
    val ticketUuid: String,
    val status: String,
    val category: String,
    val priority: String,
    val decision: String,
    val assignee: MemberRefDto? = null,
    val team: TeamRefDto,
    @SerialName("first_response_due")
    val firstResponseDue: String? = null,
    @SerialName("resolution_due")
    val resolutionDue: String? = null,
    @SerialName("awaiting_approval_from")
    val awaitingApprovalFrom: MemberRefDto? = null,
    @SerialName("review_promise_by")
    val reviewPromiseBy: String? = null,
    @SerialName("can_escalate")
    val canEscalate: Boolean = false
)

@Serializable
data class MessageDto(
    val id: String,
    @SerialName("author_id")
    val authorId: String? = null,
    @SerialName("author_name")
    val authorName: String? = null,
    val kind: String = "public",
    val body: String,
    @SerialName("created_at")
    val createdAt: String
)

@Serializable
data class PostMessageRequest(
    val body: String,
    val kind: String = "public"
)

@Serializable
data class EscalationEligibilityDto(
    val allowed: Boolean,
    @SerialName("used_last_24h")
    val usedLast24h: Int = 0,
    @SerialName("max_per_24h")
    val maxPer24h: Int = 3,
    @SerialName("next_allowed_at")
    val nextAllowedAt: String? = null,
    @SerialName("blocked_reason")
    val blockedReason: String? = null
)

@Serializable
data class EtaChangeDto(
    @SerialName("changed_by")
    val changedBy: MemberRefDto,
    @SerialName("previous_eta")
    val previousEta: String,
    @SerialName("new_eta")
    val newEta: String,
    val reason: String,
    @SerialName("changed_at")
    val changedAt: String
)

@Serializable
data class TicketDetailResponse(
    val id: String,
    @SerialName("ticket_uuid")
    val ticketUuid: String,
    val subject: String,
    val description: String,
    val category: String,
    val priority: String,
    @SerialName("priority_source")
    val prioritySource: String,
    val status: String,
    val decision: String,
    @SerialName("review_reason")
    val reviewReason: String? = null,
    val team: TeamRefDto,
    val assignee: MemberRefDto? = null,
    @SerialName("is_escalated")
    val isEscalated: Boolean = false,
    @SerialName("escalation_level")
    val escalationLevel: String = "E1",
    @SerialName("can_escalate")
    val canEscalate: Boolean = false,
    @SerialName("escalation_eligibility")
    val escalationEligibility: EscalationEligibilityDto? = null,
    @SerialName("allowed_actions")
    val allowedActions: List<String> = emptyList(),
    @SerialName("first_response_due")
    val firstResponseDue: String? = null,
    @SerialName("resolution_due")
    val resolutionDue: String? = null,
    @SerialName("first_responded_at")
    val firstRespondedAt: String? = null,
    @SerialName("sla_state")
    val slaState: String = "on_track",
    @SerialName("used_pct")
    val usedPct: Double = 0.0,
    val messages: List<MessageDto> = emptyList(),
    @SerialName("eta_history")
    val etaHistory: List<EtaChangeDto> = emptyList(),
    val version: Long = 1,
    @SerialName("created_at")
    val createdAt: String,
    @SerialName("updated_at")
    val updatedAt: String? = null
)

@Serializable
data class ChangeEtaRequest(
    @SerialName("new_eta")
    val newEta: String,
    val reason: String,
    val version: Long
)

@Serializable
data class UpdateStatusRequest(
    val status: String,
    val note: String? = null,
    val version: Long
)

@Serializable
data class RequestInfoRequest(
    val question: String,
    val version: Long
)

@Serializable
data class ReassignRequest(
    @SerialName("target_member_id")
    val targetMemberId: String,
    val reason: String,
    @SerialName("new_eta")
    val newEta: String? = null,
    val version: Long
)

@Serializable
data class ReopenRequest(
    val reason: String
)
