package com.routedesk.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class TicketStatus(val displayName: String) {
    @SerialName("new")
    NEW("New"),

    @SerialName("assigned")
    ASSIGNED("Assigned"),

    @SerialName("in_progress")
    IN_PROGRESS("In Progress"),

    @SerialName("waiting_on_requester")
    WAITING_ON_REQUESTER("Waiting on Requester"),

    @SerialName("resolved")
    RESOLVED("Resolved"),

    @SerialName("closed")
    CLOSED("Closed");

    val isTerminal: Boolean
        get() = this == RESOLVED || this == CLOSED

    companion object {
        fun fromString(value: String): TicketStatus =
            entries.firstOrNull { it.name.equals(value, ignoreCase = true) } ?: NEW
    }
}

@Serializable
enum class Role(val displayName: String) {
    @SerialName("requester")
    REQUESTER("Requester"),

    @SerialName("agent")
    AGENT("Service Desk Agent"),

    @SerialName("engineer")
    ENGINEER("Resolver Engineer"),

    @SerialName("team_lead")
    TEAM_LEAD("Team Lead"),

    @SerialName("manager")
    MANAGER("SD Manager"),

    @SerialName("approver")
    APPROVER("Approver"),

    @SerialName("admin")
    ADMIN("Platform Admin");

    val isStaff: Boolean
        get() = this != REQUESTER

    companion object {
        fun fromString(value: String): Role =
            entries.firstOrNull { it.name.equals(value, ignoreCase = true) } ?: REQUESTER
    }
}
