package com.routedesk.feature.home

import com.routedesk.model.Role
import com.routedesk.model.Ticket

data class HomeUiState(
    val userName: String = "Colleague",
    val userRole: Role = Role.REQUESTER,
    val isServerHealthy: Boolean = true,
    val unreadNotificationsCount: Int = 0,
    val openTickets: List<Ticket> = emptyList(),
    val waitingTickets: List<Ticket> = emptyList(),
    val isLoading: Boolean = false,
    val errorMessage: String? = null
)
