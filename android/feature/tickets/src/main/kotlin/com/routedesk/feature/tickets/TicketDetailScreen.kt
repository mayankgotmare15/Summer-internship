package com.routedesk.feature.tickets

import androidx.compose.foundation.background
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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
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
import com.routedesk.designsystem.component.HatchedDivider
import com.routedesk.designsystem.component.RdButton
import com.routedesk.designsystem.component.RdButtonSize
import com.routedesk.designsystem.component.RdButtonVariant
import com.routedesk.designsystem.component.RdCard
import com.routedesk.designsystem.component.RdChip
import com.routedesk.designsystem.component.RdChipVariant
import com.routedesk.designsystem.component.RdTopBar
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Face
import com.routedesk.designsystem.theme.Neutral
import com.routedesk.designsystem.theme.RouteDeskTheme
import com.routedesk.model.AllowedAction
import com.routedesk.model.Priority
import com.routedesk.model.TicketStatus

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TicketDetailScreen(
    viewModel: TicketDetailViewModel,
    onBackClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val state by viewModel.uiState.collectAsState()
    var showReopenSheet by remember { mutableStateOf(false) }

    val ticket = state.ticket

    RouteDeskTheme(face = Face.San) {
        Scaffold(
            topBar = {
                RdTopBar(
                    title = if (ticket != null) "#${ticket.id}" else "Ticket Details",
                    onBackClick = onBackClick,
                    trailingAction = {
                        ticket?.let {
                            RdChip(
                                text = it.status.name.lowercase().replaceFirstChar { c -> c.uppercase() },
                                variant = when (it.status) {
                                    TicketStatus.RESOLVED, TicketStatus.CLOSED -> RdChipVariant.Neutral
                                    TicketStatus.WAITING_ON_REQUESTER -> RdChipVariant.Attention
                                    else -> RdChipVariant.Neutral
                                }
                            )
                        }
                    }
                )
            }
        ) { paddingValues ->
            PullToRefreshBox(
                isRefreshing = state.isRefreshing,
                onRefresh = { viewModel.refresh() },
                modifier = modifier
                    .fillMaxSize()
                    .background(Brand.San)
                    .padding(paddingValues)
            ) {
                if (ticket == null) {
                    Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "Loading ticket details...",
                            style = MaterialTheme.typography.bodyMedium,
                            color = Neutral.MutedLight
                        )
                    }
                } else {
                    Column(modifier = Modifier.fillMaxSize()) {
                        // Header Summary Card
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(horizontal = 20.dp, vertical = 6.dp)
                        ) {
                            Text(
                                text = ticket.subject,
                                style = MaterialTheme.typography.titleLarge,
                                fontWeight = FontWeight.Bold,
                                color = Brand.Nero
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = ticket.description,
                                style = MaterialTheme.typography.bodyMedium,
                                color = Neutral.MutedLight,
                                maxLines = 3
                            )

                            // Status Stepper
                            StatusStepper(currentStatus = ticket.status)

                            // SLA Timer (Real-time synchronized)
                            SlaTimer(
                                dueInstant = ticket.firstResponseDue ?: ticket.resolutionDue,
                                clockOffsetManager = viewModel.clockOffsetManager
                            )

                            // Assignee Summary Row
                            Spacer(modifier = Modifier.height(8.dp))
                            RdCard(modifier = Modifier.fillMaxWidth()) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Box(
                                            modifier = Modifier
                                                .size(36.dp)
                                                .clip(CircleShape)
                                                .background(Brand.Concrete),
                                            contentAlignment = Alignment.Center
                                        ) {
                                            Text(
                                                text = (ticket.assignee?.name?.take(1) ?: "T").uppercase(),
                                                style = MaterialTheme.typography.labelSmall,
                                                fontWeight = FontWeight.Bold,
                                                color = Brand.San
                                            )
                                        }
                                        Spacer(modifier = Modifier.width(10.dp))
                                        Column {
                                            Text(
                                                text = ticket.assignee?.name ?: "Tier 2 Auto-Queue",
                                                style = MaterialTheme.typography.titleMedium,
                                                fontWeight = FontWeight.SemiBold,
                                                color = Brand.Nero
                                            )
                                            Text(
                                                text = ticket.team.name,
                                                style = MaterialTheme.typography.labelSmall,
                                                color = Neutral.MutedLight
                                            )
                                        }
                                    }

                                    RdChip(
                                        text = ticket.priority.name,
                                        variant = when (ticket.priority) {
                                            Priority.CRITICAL -> RdChipVariant.Danger
                                            Priority.HIGH -> RdChipVariant.Attention
                                            Priority.MEDIUM -> RdChipVariant.Warning
                                            Priority.LOW -> RdChipVariant.Neutral
                                        }
                                    )
                                }
                            }
                        }

                        // Resolution Action Banner (if allowed or waiting confirmation)
                        if (ticket.status == TicketStatus.RESOLVED || ticket.allowedActions.contains(AllowedAction.CONFIRM_RESOLUTION)) {
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(horizontal = 20.dp, vertical = 6.dp)
                                    .clip(androidx.compose.foundation.shape.RoundedCornerShape(12.dp))
                                    .background(Color(0xFFDDEBDD))
                                    .padding(14.dp)
                            ) {
                                Column {
                                    Text(
                                        text = "Is this issue resolved to your satisfaction?",
                                        style = MaterialTheme.typography.titleMedium,
                                        fontWeight = FontWeight.Bold,
                                        color = Color(0xFF2E7D32)
                                    )
                                    Spacer(modifier = Modifier.height(10.dp))
                                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                                        RdButton(
                                            text = "Confirm Resolution ✓",
                                            onClick = { viewModel.confirmResolution() },
                                            variant = RdButtonVariant.Primary,
                                            size = RdButtonSize.Small,
                                            isLoading = state.isActionLoading
                                        )
                                        RdButton(
                                            text = "Reopen",
                                            onClick = { showReopenSheet = true },
                                            variant = RdButtonVariant.Secondary,
                                            size = RdButtonSize.Small
                                        )
                                    }
                                }
                            }
                        }

                        // Conversation Message Thread
                        ConversationTab(
                            messages = state.messages,
                            onSendMessage = { viewModel.postMessage(it) },
                            modifier = Modifier.weight(1f)
                        )
                    }
                }
            }

            if (showReopenSheet) {
                ReopenReasonSheet(
                    onConfirmReopen = { reason, notes ->
                        viewModel.reopenTicket(reason, notes)
                        showReopenSheet = false
                    },
                    onDismiss = { showReopenSheet = false }
                )
            }
        }
    }
}
