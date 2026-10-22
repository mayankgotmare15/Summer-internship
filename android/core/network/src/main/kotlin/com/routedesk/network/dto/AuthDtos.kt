package com.routedesk.network.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class TokenRequest(
    val email: String,
    val password: String,
    @SerialName("device_name")
    val deviceName: String = "Android Device"
)

@Serializable
data class DemoTokenRequest(
    val role: String,
    @SerialName("device_name")
    val deviceName: String = "Android Device"
)

@Serializable
data class RefreshTokenRequest(
    @SerialName("refresh_token")
    val refreshToken: String
)

@Serializable
data class UserMeDto(
    val id: String,
    val email: String,
    val name: String,
    val role: String,
    val department: String? = null,
    @SerialName("is_demo")
    val isDemo: Boolean = false,
    @SerialName("team_id")
    val teamId: String? = null
)

@Serializable
data class TokenResponse(
    @SerialName("access_token")
    val accessToken: String,
    @SerialName("expires_in")
    val expiresIn: Long,
    @SerialName("refresh_token")
    val refreshToken: String,
    val me: UserMeDto
)
