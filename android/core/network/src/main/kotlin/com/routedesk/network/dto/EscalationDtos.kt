package com.routedesk.network.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class EscalateRequest(
    @SerialName("target_user_id")
    val targetUserId: String,
    @SerialName("reason_code")
    val reasonCode: String,
    val note: String
)

@Serializable
data class RespondEscalationRequest(
    val action: String, // "accept", "reassign", "decline"
    @SerialName("new_eta")
    val newEta: String? = null,
    @SerialName("target_member_id")
    val targetMemberId: String? = null,
    val reason: String? = null
)

@Serializable
data class EscalationResponse(
    val id: String,
    @SerialName("ticket_id")
    val ticketId: String,
    val level: String,
    @SerialName("designated_member")
    val designatedMember: MemberRefDto,
    @SerialName("reason_code")
    val reasonCode: String,
    val note: String,
    val status: String,
    @SerialName("response_deadline")
    val responseDeadline: String,
    val responder: MemberRefDto? = null,
    @SerialName("response_note")
    val responseNote: String? = null,
    @SerialName("new_eta")
    val newEta: String? = null,
    @SerialName("created_at")
    val createdAt: String
)

@Serializable
data class AppConfigResponse(
    val android: AndroidConfigDto,
    val status: SystemStatusDto,
    val features: Map<String, Boolean> = emptyMap(),
    @SerialName("business_calendar")
    val businessCalendar: BusinessCalendarDto
)

@Serializable
data class AndroidConfigDto(
    @SerialName("min_supported_version_code")
    val minSupportedVersionCode: Int,
    @SerialName("latest_version_code")
    val latestVersionCode: Int
)

@Serializable
data class SystemStatusDto(
    val level: String, // "ok", "degraded", "incident"
    val message: String
)

@Serializable
data class BusinessCalendarDto(
    val timezone: String = "Asia/Kolkata",
    val hours: String = "Mon-Fri 09:00-18:00"
)

@Serializable
data class RegisterDeviceRequest(
    @SerialName("fcm_token")
    val fcmToken: String,
    val platform: String = "android",
    @SerialName("app_version")
    val appVersion: String,
    @SerialName("os_version")
    val osVersion: String,
    val locale: String = "en"
)
