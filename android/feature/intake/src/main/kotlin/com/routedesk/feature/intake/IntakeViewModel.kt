package com.routedesk.feature.intake

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.routedesk.data.repository.TicketRepository
import com.routedesk.model.Category
import com.routedesk.model.Priority
import com.routedesk.network.dto.PredictResponse
import com.routedesk.network.dto.TicketCreatedResponse
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

enum class IntakeMode {
    CHAT,
    FORM
}

data class ChatMessageItem(
    val id: String,
    val isAssistant: Boolean,
    val text: String,
    val timestampMs: Long = System.currentTimeMillis()
)

data class IntakeUiState(
    val mode: IntakeMode = IntakeMode.CHAT,
    val subject: String = "",
    val description: String = "",
    val category: Category = Category.ACCESS,
    val priority: Priority = Priority.MEDIUM,
    val isBlockingTeam: Boolean = false,
    val chatMessages: List<ChatMessageItem> = listOf(
        ChatMessageItem(
            id = "intro",
            isAssistant = true,
            text = "Hi! Describe what's broken in your own words. Our AI model will classify urgency and route it to the right engineer in seconds."
        )
    ),
    val isPredicting: Boolean = false,
    val prediction: PredictResponse? = null,
    val isSubmitting: Boolean = false,
    val createdTicket: TicketCreatedResponse? = null,
    val errorMessage: String? = null
)

@HiltViewModel
class IntakeViewModel @Inject constructor(
    private val ticketRepository: TicketRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(IntakeUiState())
    val uiState: StateFlow<IntakeUiState> = _uiState.asStateFlow()

    fun setMode(mode: IntakeMode) {
        _uiState.value = _uiState.value.copy(mode = mode)
    }

    fun onSubjectChanged(subject: String) {
        _uiState.value = _uiState.value.copy(subject = subject)
    }

    fun onDescriptionChanged(description: String) {
        _uiState.value = _uiState.value.copy(description = description)
    }

    fun onCategorySelected(category: Category) {
        _uiState.value = _uiState.value.copy(category = category)
    }

    fun onPrioritySelected(priority: Priority) {
        _uiState.value = _uiState.value.copy(priority = priority)
    }

    fun onBlockingTeamToggled(isBlocking: Boolean) {
        _uiState.value = _uiState.value.copy(isBlockingTeam = isBlocking)
    }

    fun sendChatMessage(text: String) {
        if (text.isBlank()) return

        val userMsg = ChatMessageItem(
            id = "msg_${System.currentTimeMillis()}",
            isAssistant = false,
            text = text
        )

        val updatedMessages = _uiState.value.chatMessages + userMsg
        _uiState.value = _uiState.value.copy(
            chatMessages = updatedMessages,
            description = text,
            subject = text.take(60),
            isPredicting = true
        )

        // Trigger ML prediction call
        viewModelScope.launch {
            val result = ticketRepository.predict(text)
            result.onSuccess { pred ->
                val predictedCat = runCatching {
                    Category.valueOf(pred.category.uppercase())
                }.getOrDefault(Category.ACCESS)

                val predictedPriority = runCatching {
                    Priority.valueOf(pred.suggestedPriority.uppercase())
                }.getOrDefault(Priority.MEDIUM)

                val assistantAck = ChatMessageItem(
                    id = "pred_ack_${System.currentTimeMillis()}",
                    isAssistant = true,
                    text = "I've analyzed your issue as ${predictedCat.name.lowercase()} with ${(pred.confidence * 100).toInt()}% confidence. Does this look accurate?"
                )

                _uiState.value = _uiState.value.copy(
                    prediction = pred,
                    category = predictedCat,
                    priority = predictedPriority,
                    chatMessages = _uiState.value.chatMessages + assistantAck,
                    isPredicting = false
                )
            }.onFailure {
                _uiState.value = _uiState.value.copy(isPredicting = false)
            }
        }
    }

    fun submitTicket(onSuccess: (TicketCreatedResponse) -> Unit) {
        val state = _uiState.value
        if (state.subject.isBlank() || state.description.isBlank()) {
            _uiState.value = state.copy(errorMessage = "Subject and description cannot be empty")
            return
        }

        _uiState.value = state.copy(isSubmitting = true, errorMessage = null)

        viewModelScope.launch {
            val result = ticketRepository.createTicket(
                subject = state.subject,
                description = state.description,
                category = state.category,
                priority = state.priority,
                blockingTeam = state.isBlockingTeam
            )

            result.onSuccess { response ->
                _uiState.value = _uiState.value.copy(
                    isSubmitting = false,
                    createdTicket = response
                )
                onSuccess(response)
            }.onFailure { e ->
                _uiState.value = _uiState.value.copy(
                    isSubmitting = false,
                    errorMessage = e.message ?: "Failed to submit ticket"
                )
            }
        }
    }

    fun overrideCategory(newCategory: Category) {
        val state = _uiState.value
        val originalPred = state.prediction?.category ?: state.category.name

        _uiState.value = state.copy(category = newCategory)

        // Submit feedback asynchronously to improve model
        viewModelScope.launch {
            ticketRepository.submitFeedback(
                ticketId = "intake_feedback",
                originalPrediction = originalPred,
                correctedCategory = newCategory.name.lowercase(),
                confidence = state.prediction?.confidence ?: 0.5
            )
        }
    }
}
