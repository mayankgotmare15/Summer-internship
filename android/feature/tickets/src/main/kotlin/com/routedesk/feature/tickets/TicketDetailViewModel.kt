package com.routedesk.feature.tickets

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.routedesk.data.clock.ClockOffsetManager
import com.routedesk.data.repository.TicketRepository
import com.routedesk.model.Message
import com.routedesk.model.Ticket
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

data class TicketDetailUiState(
    val ticket: Ticket? = null,
    val messages: List<Message> = emptyList(),
    val isRefreshing: Boolean = false,
    val isActionLoading: Boolean = false,
    val errorMessage: String? = null
)

@HiltViewModel
class TicketDetailViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle,
    private val ticketRepository: TicketRepository,
    val clockOffsetManager: ClockOffsetManager
) : ViewModel() {

    val ticketId: String = checkNotNull(savedStateHandle["ticketId"])

    private val isRefreshing = MutableStateFlow(false)
    private val isActionLoading = MutableStateFlow(false)
    private val errorMessage = MutableStateFlow<String?>(null)

    val uiState: StateFlow<TicketDetailUiState> = combine(
        ticketRepository.observeTicketDetail(ticketId),
        ticketRepository.observeMessages(ticketId),
        isRefreshing,
        isActionLoading,
        errorMessage
    ) { ticket, messages, refreshing, actionLoading, error ->
        TicketDetailUiState(
            ticket = ticket,
            messages = messages,
            isRefreshing = refreshing,
            isActionLoading = actionLoading,
            errorMessage = error
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = TicketDetailUiState(isRefreshing = true)
    )

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            isRefreshing.value = true
            try {
                ticketRepository.refreshTicketDetail(ticketId)
                errorMessage.value = null
            } catch (e: Exception) {
                errorMessage.value = e.message
            } finally {
                isRefreshing.value = false
            }
        }
    }

    fun postMessage(body: String) {
        viewModelScope.launch {
            try {
                ticketRepository.postMessage(ticketId = ticketId, body = body)
            } catch (e: Exception) {
                errorMessage.value = e.message
            }
        }
    }

    fun confirmResolution() {
        viewModelScope.launch {
            isActionLoading.value = true
            try {
                ticketRepository.confirmResolution(ticketId)
            } catch (e: Exception) {
                errorMessage.value = e.message
            } finally {
                isActionLoading.value = false
            }
        }
    }

    fun reopenTicket(reason: String, notes: String) {
        viewModelScope.launch {
            isActionLoading.value = true
            try {
                ticketRepository.reopenTicket(ticketId, reason, notes)
            } catch (e: Exception) {
                errorMessage.value = e.message
            } finally {
                isActionLoading.value = false
            }
        }
    }
}
