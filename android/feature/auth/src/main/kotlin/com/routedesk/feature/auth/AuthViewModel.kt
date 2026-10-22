package com.routedesk.feature.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.routedesk.auth.AuthRepository
import com.routedesk.auth.SessionState
import com.routedesk.model.Role
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class AuthUiState(
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val isColdStarting: Boolean = false,
    val isLoginSuccess: Boolean = false
)

class AuthViewModel(
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(AuthUiState())
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()

    val sessionState: StateFlow<SessionState> = authRepository.sessionState

    fun login(email: String, password: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }
            val warmupJob = startColdStartTimer()

            try {
                authRepository.login(email = email, password = password)
                warmupJob.cancel()
                _uiState.update { it.copy(isLoading = false, isColdStarting = false, isLoginSuccess = true) }
            } catch (e: Exception) {
                warmupJob.cancel()
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        isColdStarting = false,
                        errorMessage = e.message ?: "Authentication failed. Please verify credentials."
                    )
                }
            }
        }
    }

    fun loginDemo(role: Role) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }
            val warmupJob = startColdStartTimer()

            try {
                authRepository.loginDemo(role = role)
                warmupJob.cancel()
                _uiState.update { it.copy(isLoading = false, isColdStarting = false, isLoginSuccess = true) }
            } catch (e: Exception) {
                warmupJob.cancel()
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        isColdStarting = false,
                        errorMessage = e.message ?: "Demo login failed."
                    )
                }
            }
        }
    }

    private fun startColdStartTimer(): Job {
        return viewModelScope.launch {
            delay(5000)
            _uiState.update { it.copy(isColdStarting = true) }
        }
    }

    fun clearError() {
        _uiState.update { it.copy(errorMessage = null) }
    }
}
