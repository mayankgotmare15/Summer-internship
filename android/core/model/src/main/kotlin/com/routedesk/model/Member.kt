package com.routedesk.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class TeamRef(
    val code: String,
    val name: String
)

@Serializable
data class MemberRef(
    val id: String,
    val name: String,
    val email: String,
    val role: String,
    @SerialName("avatar_url")
    val avatarUrl: String? = null
)

@Serializable
enum class ShiftStatus {
    @SerialName("on_shift")
    ON_SHIFT,

    @SerialName("off_shift")
    OFF_SHIFT,

    @SerialName("on_leave")
    ON_LEAVE
}

@Serializable
data class DirectoryMember(
    val id: String,
    val name: String,
    val email: String,
    val role: Role,
    val team: TeamRef,
    val skills: List<String> = emptyList(),
    @SerialName("shift_status")
    val shiftStatus: ShiftStatus = ShiftStatus.ON_SHIFT,
    @SerialName("on_leave")
    val onLeave: Boolean = false,
    @SerialName("leave_note")
    val leaveNote: String? = null,
    val delegate: MemberRef? = null,
    @SerialName("active_tickets_count")
    val activeTicketsCount: Int = 0,
    @SerialName("capacity_limit")
    val capacityLimit: Int = 10
)
