package com.routedesk.feature.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.routedesk.auth.SessionManager
import com.routedesk.auth.SessionState
import com.routedesk.data.repository.TicketRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val sessionManager: SessionManager,
    private val ticketRepository: TicketRepository
) : ViewModel() {

    private val isRefreshing = MutableStateFlow(false)
    private val errorMessage = MutableStateFlow<String?>(null)

    val uiState: StateFlow<HomeUiState> = combine(
        sessionManager.sessionState,
        ticketRepository.observeOpenTickets(),
        ticketRepository.observeWaitingOnRequesterTickets(),
        isRefreshing,
        errorMessage
    ) { session, openTickets, waitingTickets, refreshing, error ->
        val userMe = (session as? SessionState.Authenticated)?.user
        HomeUiState(
            userName = userMe?.name ?: "Colleague",
            userRole = sessionManager.currentRole,
            isServerHealthy = true,
            unreadNotificationsCount = 2,
            openTickets = openTickets,
            waitingTickets = waitingTickets,
            isLoading = refreshing,
            errorMessage = error
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = HomeUiState(isLoading = true)
    )

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            isRefreshing.value = true
            try {
                ticketRepository.refreshTickets()
                errorMessage.value = null
            } catch (e: Exception) {
                errorMessage.value = e.message
            } finally {
                isRefreshing.value = false
            }
        }
    }
}
