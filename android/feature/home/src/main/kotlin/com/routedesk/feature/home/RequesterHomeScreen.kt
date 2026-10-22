package com.routedesk.feature.home

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.routedesk.designsystem.component.HatchedDivider
import com.routedesk.designsystem.component.RdCard
import com.routedesk.designsystem.component.RdChip
import com.routedesk.designsystem.component.RdChipVariant
import com.routedesk.designsystem.component.RdIconButton
import com.routedesk.designsystem.component.RdIconButtonStyle
import com.routedesk.designsystem.component.RdTile
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Face
import com.routedesk.designsystem.theme.LocalRouteDeskColors
import com.routedesk.designsystem.theme.Neutral
import com.routedesk.designsystem.theme.PillShape
import com.routedesk.designsystem.theme.RouteDeskShapes
import com.routedesk.designsystem.theme.RouteDeskTheme
import com.routedesk.designsystem.theme.softShadow
import com.routedesk.model.Category
import com.routedesk.model.Ticket

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RequesterHomeScreen(
    viewModel: HomeViewModel,
    onNavigateToIntake: (prefilledCategory: Category?) -> Unit,
    onNavigateToTicketDetail: (ticketId: String) -> Unit,
    onNavigateToMyTickets: () -> Unit,
    onNavigateToNotifications: () -> Unit,
    modifier: Modifier = Modifier
) {
    val state by viewModel.uiState.collectAsState()

    RouteDeskTheme(face = Face.San) {
        Scaffold(
            floatingActionButton = {
                FloatingActionButton(
                    onClick = { onNavigateToIntake(null) },
                    containerColor = Brand.Orange,
                    contentColor = Brand.Nero,
                    shape = CircleShape,
                    modifier = Modifier
                        .size(56.dp)
                        .softShadow(elevation = 6.dp, shape = CircleShape)
                ) {
                    Icon(imageVector = Icons.Default.Add, contentDescription = "Create ticket")
                }
            }
        ) { paddingValues ->
            PullToRefreshBox(
                isRefreshing = state.isLoading,
                onRefresh = { viewModel.refresh() },
                modifier = modifier
                    .fillMaxSize()
                    .background(Brand.San)
                    .padding(paddingValues)
            ) {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(bottom = 80.dp)
                ) {
                    // 1. Header with greeting and bell
                    item {
                        HomeHeader(
                            userName = state.userName,
                            badgeCount = state.unreadNotificationsCount,
                            onBellClick = onNavigateToNotifications
                        )
                    }

                    // 2. Operational Health Banner
                    item {
                        HealthBanner(isHealthy = state.isServerHealthy)
                    }

                    // 3. Quick Help Actions
                    item {
                        QuickHelpSection(
                            onQuickHelpClick = { category -> onNavigateToIntake(category) }
                        )
                    }

                    // 4. "Waiting On You" Urgent Section (if any)
                    if (state.waitingTickets.isNotEmpty()) {
                        item {
                            WaitingOnYouSection(
                                tickets = state.waitingTickets,
                                onTicketClick = onNavigateToTicketDetail
                            )
                        }
                    }

                    // 5. Open Tickets Carousel
                    item {
                        OpenTicketsSection(
                            tickets = state.openTickets,
                            onTicketClick = onNavigateToTicketDetail,
                            onViewAllClick = onNavigateToMyTickets
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun HomeHeader(
    userName: String,
    badgeCount: Int,
    onBellClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .statusBarsPadding()
            .padding(horizontal = 20.dp, vertical = 16.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "Hi, $userName",
                    style = MaterialTheme.typography.headlineMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = Brand.Nero
                )
                Spacer(modifier = Modifier.width(8.dp))
                Box(
                    modifier = Modifier
                        .clip(PillShape)
                        .background(Brand.Concrete.copy(alpha = 0.15f))
                        .padding(horizontal = 8.dp, vertical = 2.dp)
                ) {
                    Text(
                        text = "REQUESTER",
                        style = MaterialTheme.typography.labelSmall,
                        fontWeight = FontWeight.Bold,
                        color = Brand.Concrete,
                        fontSize = 10.sp
                    )
                }
            }
            Text(
                text = "What can we help you resolve today?",
                style = MaterialTheme.typography.bodyMedium,
                color = Neutral.MutedLight
            )
        }

        RdIconButton(
            icon = Icons.Default.Notifications,
            contentDescription = "Notifications",
            onClick = onBellClick,
            style = RdIconButtonStyle.Paper,
            badgeCount = badgeCount
        )
    }
}

@Composable
private fun HealthBanner(isHealthy: Boolean) {
    val colors = LocalRouteDeskColors.current
    val (bgColor, fgColor, dotColor, text) = if (isHealthy) {
        listOf(
            colors.success.tint,
            colors.success.fg,
            Color(0xFF2E7D32),
            "All Systems Operational • Instant ML Routing Active"
        )
    } else {
        listOf(
            colors.warning.tint,
            colors.warning.fg,
            Color(0xFF8A5A00),
            "High Ticket Volume • AI Queues Experiencing Slight Latency"
        )
    }

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 20.dp, vertical = 4.dp)
            .clip(RoundedCornerShape(12.dp))
            .background(bgColor as Color)
            .padding(horizontal = 14.dp, vertical = 10.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(8.dp)
                    .clip(CircleShape)
                    .background(dotColor as Color)
            )
            Spacer(modifier = Modifier.width(10.dp))
            Text(
                text = text as String,
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.SemiBold,
                color = fgColor as Color
            )
        }
    }
}

@Composable
private fun QuickHelpSection(onQuickHelpClick: (Category) -> Unit) {
    Column(modifier = Modifier.padding(top = 20.dp)) {
        Text(
            text = "QUICK ACTIONS",
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.Bold,
            color = Neutral.MutedLight,
            letterSpacing = 1.sp,
            modifier = Modifier.padding(horizontal = 20.dp, vertical = 8.dp)
        )

        LazyRow(
            contentPadding = PaddingValues(horizontal = 20.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item {
                RdTile(
                    label = "Password\nReset",
                    icon = Icons.Default.Lock,
                    iconBgColor = Brand.San,
                    iconTint = Brand.Orange,
                    onClick = { onQuickHelpClick(Category.ACCESS) }
                )
            }
            item {
                RdTile(
                    label = "VPN &\nAccess",
                    icon = Icons.Default.Settings,
                    iconBgColor = Brand.San,
                    iconTint = Brand.Concrete,
                    onClick = { onQuickHelpClick(Category.NETWORK) }
                )
            }
            item {
                RdTile(
                    label = "Hardware\nRequest",
                    icon = Icons.Default.Build,
                    iconBgColor = Brand.San,
                    iconTint = Color(0xFF2E7D32),
                    onClick = { onQuickHelpClick(Category.HARDWARE) }
                )
            }
            item {
                RdTile(
                    label = "Software\nInstall",
                    icon = Icons.Default.PlayArrow,
                    iconBgColor = Brand.San,
                    iconTint = Color(0xFF7D5A9B),
                    onClick = { onQuickHelpClick(Category.SOFTWARE) }
                )
            }
        }
    }
}

@Composable
private fun WaitingOnYouSection(
    tickets: List<Ticket>,
    onTicketClick: (String) -> Unit
) {
    Column(modifier = Modifier.padding(top = 24.dp)) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp, vertical = 6.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "ACTION REQUIRED",
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.Bold,
                color = Brand.Orange,
                letterSpacing = 1.sp
            )
            Spacer(modifier = Modifier.width(6.dp))
            Box(
                modifier = Modifier
                    .size(6.dp)
                    .clip(CircleShape)
                    .background(Brand.Orange)
            )
        }

        tickets.take(2).forEach { ticket ->
            RdCard(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp, vertical = 4.dp),
                backgroundColor = Neutral.Paper,
                onClick = { onTicketClick(ticket.id) }
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "#${ticket.id}",
                        style = MaterialTheme.typography.labelSmall,
                        fontWeight = FontWeight.Bold,
                        color = Brand.Concrete
                    )
                    RdChip(
                        text = "Needs Info",
                        variant = RdChipVariant.Attention
                    )
                }
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = ticket.subject,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = Brand.Nero,
                    maxLines = 1
                )
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = "Engineer is waiting for clarification from you.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Neutral.MutedLight
                )
            }
        }
    }
}

@Composable
private fun OpenTicketsSection(
    tickets: List<Ticket>,
    onTicketClick: (String) -> Unit,
    onViewAllClick: () -> Unit
) {
    Column(modifier = Modifier.padding(top = 24.dp)) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "YOUR TICKETS (${tickets.size})",
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.Bold,
                color = Neutral.MutedLight,
                letterSpacing = 1.sp
            )

            Text(
                text = "View all",
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.SemiBold,
                color = Brand.Orange,
                modifier = Modifier.clickable(onClick = onViewAllClick)
            )
        }

        if (tickets.isEmpty()) {
            RdCard(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp),
                backgroundColor = Neutral.Paper
            ) {
                Text(
                    text = "No open tickets",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = Brand.Nero
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Everything is running smoothly! Tap '+' below if you need assistance.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Neutral.MutedLight
                )
            }
        } else {
            LazyRow(
                contentPadding = PaddingValues(horizontal = 20.dp),
                horizontalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                items(tickets, key = { it.id }) { ticket ->
                    OpenTicketCard(ticket = ticket, onClick = { onTicketClick(ticket.id) })
                }
            }
        }
    }
}

@Composable
private fun OpenTicketCard(
    ticket: Ticket,
    onClick: () -> Unit
) {
    RdCard(
        modifier = Modifier
            .size(width = 240.dp, height = 145.dp),
        backgroundColor = Neutral.Paper,
        onClick = onClick
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "#${ticket.id}",
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.Bold,
                color = Brand.Concrete
            )
            RdChip(
                text = ticket.category.name.lowercase().replaceFirstChar { it.uppercase() },
                variant = RdChipVariant.Neutral
            )
        }

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = ticket.subject,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold,
            color = Brand.Nero,
            maxLines = 2,
            modifier = Modifier.weight(1f)
        )

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = ticket.status.name.lowercase().replaceFirstChar { it.uppercase() },
                style = MaterialTheme.typography.labelSmall,
                color = Neutral.MutedLight
            )

            RdChip(
                text = ticket.priority.name,
                variant = when (ticket.priority) {
                    com.routedesk.model.Priority.CRITICAL -> RdChipVariant.Danger
                    com.routedesk.model.Priority.HIGH -> RdChipVariant.Attention
                    com.routedesk.model.Priority.MEDIUM -> RdChipVariant.Warning
                    com.routedesk.model.Priority.LOW -> RdChipVariant.Neutral
                }
            )
        }
    }
}
