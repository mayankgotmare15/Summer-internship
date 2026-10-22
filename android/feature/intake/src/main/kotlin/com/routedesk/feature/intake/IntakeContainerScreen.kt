package com.routedesk.feature.intake

import androidx.compose.animation.AnimatedContent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.routedesk.designsystem.component.RdIconButton
import com.routedesk.designsystem.component.RdIconButtonStyle
import com.routedesk.designsystem.component.RdTopBar
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Face
import com.routedesk.designsystem.theme.Neutral
import com.routedesk.designsystem.theme.PillShape
import com.routedesk.designsystem.theme.RouteDeskTheme
import com.routedesk.model.Category

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun IntakeContainerScreen(
    viewModel: IntakeViewModel,
    onBackClick: () -> Unit,
    onNavigateToTicketDetail: (ticketId: String) -> Unit,
    modifier: Modifier = Modifier
) {
    val uiState by viewModel.uiState.collectAsState()
    var showCategoryOverrideSheet by remember { mutableStateOf(false) }

    // If ticket created, show confirmation
    uiState.createdTicket?.let { created ->
        TicketConfirmationScreen(
            ticket = created,
            onViewTicketClick = onNavigateToTicketDetail,
            onBackHomeClick = onBackClick
        )
        return
    }

    RouteDeskTheme(face = Face.San) {
        Scaffold(
            topBar = {
                RdTopBar(
                    title = "New Ticket",
                    onBackClick = onBackClick
                )
            }
        ) { paddingValues ->
            Column(
                modifier = modifier
                    .fillMaxSize()
                    .background(Brand.San)
                    .padding(paddingValues)
            ) {
                // Segmented Control (Chat Intake vs Form Intake)
                IntakeSegmentedControl(
                    selectedMode = uiState.mode,
                    onModeSelected = { viewModel.setMode(it) }
                )

                // Error message if any
                uiState.errorMessage?.let { error ->
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 20.dp, vertical = 6.dp)
                            .clip(RoundedCornerShape(8.dp))
                            .background(Color(0xFFF9E1DC))
                            .padding(horizontal = 12.dp, vertical = 8.dp)
                    ) {
                        Text(
                            text = error,
                            style = MaterialTheme.typography.labelSmall,
                            color = Color(0xFFB42318)
                        )
                    }
                }

                AnimatedContent(
                    targetState = uiState.mode,
                    label = "IntakeModeTransition"
                ) { mode ->
                    when (mode) {
                        IntakeMode.CHAT -> {
                            ChatIntakeView(
                                uiState = uiState,
                                onSendMessage = { viewModel.sendChatMessage(it) },
                                onLooksRight = { viewModel.submitTicket {} },
                                onNotQuite = { showCategoryOverrideSheet = true },
                                onSubmitTicket = { viewModel.submitTicket {} },
                                onDeflected = onBackClick
                            )
                        }

                        IntakeMode.FORM -> {
                            FormIntakeView(
                                uiState = uiState,
                                onSubjectChange = { viewModel.onSubjectChanged(it) },
                                onDescriptionChange = { viewModel.onDescriptionChanged(it) },
                                onCategoryClick = { showCategoryOverrideSheet = true },
                                onPriorityChange = { viewModel.onPrioritySelected(it) },
                                onBlockingTeamToggle = { viewModel.onBlockingTeamToggled(it) },
                                onSubmitClick = { viewModel.submitTicket {} }
                            )
                        }
                    }
                }
            }

            if (showCategoryOverrideSheet) {
                CategoryOverrideSheet(
                    currentCategory = uiState.category,
                    onCategoryChosen = { chosen ->
                        viewModel.overrideCategory(chosen)
                        showCategoryOverrideSheet = false
                    },
                    onDismiss = { showCategoryOverrideSheet = false }
                )
            }
        }
    }
}

@Composable
private fun IntakeSegmentedControl(
    selectedMode: IntakeMode,
    onModeSelected: (IntakeMode) -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 20.dp, vertical = 8.dp),
        contentAlignment = Alignment.Center
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .height(44.dp)
                .clip(PillShape)
                .background(Neutral.Paper)
                .padding(4.dp),
            horizontalArrangement = Arrangement.Center
        ) {
            IntakeSegmentOption(
                title = "AI Chat Intake",
                isSelected = selectedMode == IntakeMode.CHAT,
                onClick = { onModeSelected(IntakeMode.CHAT) },
                modifier = Modifier.weight(1f)
            )

            IntakeSegmentOption(
                title = "Standard Form",
                isSelected = selectedMode == IntakeMode.FORM,
                onClick = { onModeSelected(IntakeMode.FORM) },
                modifier = Modifier.weight(1f)
            )
        }
    }
}

@Composable
private fun IntakeSegmentOption(
    title: String,
    isSelected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .fillMaxSize()
            .clip(PillShape)
            .background(if (isSelected) Brand.Nero else Color.Transparent)
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.labelSmall,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.SemiBold,
            color = if (isSelected) Brand.San else Neutral.MutedLight
        )
    }
}
