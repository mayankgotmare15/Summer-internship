package com.routedesk.auth

import com.routedesk.model.Role
import com.routedesk.network.dto.UserMeDto
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

sealed interface SessionState {
    data object Loading : SessionState
    data class Unauthenticated(val reason: String? = null) : SessionState
    data class Authenticated(
        val user: UserMeDto,
        val role: Role
    ) : SessionState
}

class SessionManager(
    private val tokenStore: TokenStore
) {
    private val _sessionState = MutableStateFlow<SessionState>(SessionState.Loading)
    val sessionState: StateFlow<SessionState> = _sessionState.asStateFlow()

    fun setAuthenticated(user: UserMeDto) {
        val role = Role.fromString(user.role)
        _sessionState.value = SessionState.Authenticated(user = user, role = role)
    }

    fun setUnauthenticated(reason: String? = null) {
        tokenStore.clearTokens()
        _sessionState.value = SessionState.Unauthenticated(reason = reason)
    }

    val currentRole: Role?
        get() = (_sessionState.value as? SessionState.Authenticated)?.role

    val currentUser: UserMeDto?
        get() = (_sessionState.value as? SessionState.Authenticated)?.user
}
