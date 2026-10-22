package com.routedesk.model

import kotlinx.datetime.Instant
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class EscalationLevel(val code: String, val label: String) {
    @SerialName("E1")
    E1("E1", "Direct Member"),

    @SerialName("E2")
    E2("E2", "Team Lead"),

    @SerialName("E3")
    E3("E3", "SD Manager"),

    @SerialName("E4")
    E4("E4", "Director / Incident");

    val nextLevel: EscalationLevel?
        get() = when (this) {
            E1 -> E2
            E2 -> E3
            E3 -> E4
            E4 -> null
        }
}

@Serializable
enum class EscalationReason(val code: String, val label: String) {
    @SerialName("no_response")
    NO_RESPONSE("no_response", "No response received"),

    @SerialName("wrong_team")
    WRONG_TEAM("wrong_team", "Assigned to wrong team"),

    @SerialName("business_critical")
    BUSINESS_CRITICAL("business_critical", "Business-critical issue"),

    @SerialName("deadline_at_risk")
    DEADLINE_AT_RISK("deadline_at_risk", "Project deadline at risk"),

    @SerialName("other")
    OTHER("other", "Other reason");

    companion object {
        fun fromCode(code: String): EscalationReason =
            entries.firstOrNull { it.code.equals(code, ignoreCase = true) } ?: OTHER
    }
}

@Serializable
data class EscalationEligibility(
    val allowed: Boolean,
    @SerialName("used_last_24h")
    val usedLast24h: Int = 0,
    @SerialName("max_per_24h")
    val maxPer24h: Int = 3,
    @SerialName("next_allowed_at")
    val nextAllowedAt: Instant? = null,
    @SerialName("blocked_reason")
    val blockedReason: String? = null
)

@Serializable
enum class EscalationStatus {
    @SerialName("awaiting_response")
    AWAITING_RESPONSE,

    @SerialName("accepted")
    ACCEPTED,

    @SerialName("reassigned")
    REASSIGNED,

    @SerialName("declined")
    DECLINED,

    @SerialName("timed_out")
    TIMED_OUT
}

@Serializable
data class Escalation(
    val id: String,
    @SerialName("ticket_id")
    val ticketId: String,
    val level: EscalationLevel = EscalationLevel.E1,
    @SerialName("designated_member")
    val designatedMember: MemberRef,
    @SerialName("reason_code")
    val reasonCode: EscalationReason,
    val note: String,
    val status: EscalationStatus = EscalationStatus.AWAITING_RESPONSE,
    @SerialName("response_deadline")
    val responseDeadline: Instant,
    val responder: MemberRef? = null,
    @SerialName("response_note")
    val responseNote: String? = null,
    @SerialName("new_eta")
    val newEta: Instant? = null,
    @SerialName("created_at")
    val createdAt: Instant
)
