package com.routedesk.feature.tickets

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.routedesk.data.repository.TicketRepository
import com.routedesk.model.Category
import com.routedesk.model.Ticket
import com.routedesk.model.TicketStatus
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

enum class TicketTab {
    OPEN,
    WAITING_ON_ME,
    RESOLVED
}

data class MyTicketsUiState(
    val selectedTab: TicketTab = TicketTab.OPEN,
    val searchQuery: String = "",
    val selectedCategory: Category? = null,
    val tickets: List<Ticket> = emptyList(),
    val isRefreshing: Boolean = false,
    val errorMessage: String? = null
)

@HiltViewModel
class MyTicketsViewModel @Inject constructor(
    private val ticketRepository: TicketRepository
) : ViewModel() {

    private val selectedTab = MutableStateFlow(TicketTab.OPEN)
    private val searchQuery = MutableStateFlow("")
    private val selectedCategory = MutableStateFlow<Category?>(null)
    private val isRefreshing = MutableStateFlow(false)
    private val errorMessage = MutableStateFlow<String?>(null)

    val uiState: StateFlow<MyTicketsUiState> = combine(
        ticketRepository.observeAllTickets(),
        selectedTab,
        searchQuery,
        selectedCategory,
        isRefreshing,
        errorMessage
    ) { allTickets, tab, query, category, refreshing, error ->
        val filtered = allTickets.filter { ticket ->
            val matchesTab = when (tab) {
                TicketTab.OPEN -> ticket.status != TicketStatus.RESOLVED && ticket.status != TicketStatus.CLOSED
                TicketTab.WAITING_ON_ME -> ticket.status == TicketStatus.WAITING_ON_REQUESTER
                TicketTab.RESOLVED -> ticket.status == TicketStatus.RESOLVED || ticket.status == TicketStatus.CLOSED
            }

            val matchesQuery = if (query.isBlank()) {
                true
            } else {
                ticket.subject.contains(query, ignoreCase = true) ||
                    ticket.id.contains(query, ignoreCase = true) ||
                    ticket.description.contains(query, ignoreCase = true)
            }

            val matchesCategory = category == null || ticket.category == category

            matchesTab && matchesQuery && matchesCategory
        }

        MyTicketsUiState(
            selectedTab = tab,
            searchQuery = query,
            selectedCategory = category,
            tickets = filtered,
            isRefreshing = refreshing,
            errorMessage = error
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = MyTicketsUiState(isRefreshing = true)
    )

    init {
        refresh()
    }

    fun selectTab(tab: TicketTab) {
        selectedTab.value = tab
    }

    fun onSearchQueryChanged(query: String) {
        searchQuery.value = query
    }

    fun onCategoryFilterSelected(category: Category?) {
        selectedCategory.value = if (selectedCategory.value == category) null else category
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
