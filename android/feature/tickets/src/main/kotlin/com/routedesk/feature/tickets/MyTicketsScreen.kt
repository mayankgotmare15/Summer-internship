package com.routedesk.feature.tickets

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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ExperimentalMaterial3Api
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.routedesk.designsystem.component.RdCard
import com.routedesk.designsystem.component.RdChip
import com.routedesk.designsystem.component.RdChipVariant
import com.routedesk.designsystem.component.RdListRow
import com.routedesk.designsystem.component.RdTextField
import com.routedesk.designsystem.component.RdTopBar
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Face
import com.routedesk.designsystem.theme.Neutral
import com.routedesk.designsystem.theme.PillShape
import com.routedesk.designsystem.theme.RouteDeskTheme
import com.routedesk.model.Category
import com.routedesk.model.Priority
import com.routedesk.model.Ticket

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MyTicketsScreen(
    viewModel: MyTicketsViewModel,
    onBackClick: () -> Unit,
    onTicketClick: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val state by viewModel.uiState.collectAsState()

    RouteDeskTheme(face = Face.San) {
        Scaffold(
            topBar = {
                RdTopBar(
                    title = "My Tickets",
                    onBackClick = onBackClick
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
                Column(modifier = Modifier.fillMaxSize()) {
                    // Search Bar
                    Box(modifier = Modifier.padding(horizontal = 20.dp, vertical = 8.dp)) {
                        RdTextField(
                            value = state.searchQuery,
                            onValueChange = { viewModel.onSearchQueryChanged(it) },
                            placeholder = "Search tickets by title, ID, or description...",
                            singleLine = true
                        )
                    }

                    // Tab Selector
                    TicketTabsHeader(
                        selectedTab = state.selectedTab,
                        onTabSelected = { viewModel.selectTab(it) }
                    )

                    // Category Filter Chips
                    CategoryFilterRow(
                        selectedCategory = state.selectedCategory,
                        onCategorySelected = { viewModel.onCategoryFilterSelected(it) }
                    )

                    // Tickets List
                    if (state.tickets.isEmpty()) {
                        Box(
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(32.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "No tickets match your filters",
                                style = MaterialTheme.typography.titleMedium,
                                color = Neutral.MutedLight
                            )
                        }
                    } else {
                        LazyColumn(
                            contentPadding = PaddingValues(horizontal = 20.dp, vertical = 12.dp),
                            verticalArrangement = Arrangement.spacedBy(10.dp)
                        ) {
                            items(state.tickets, key = { it.id }) { ticket ->
                                TicketListItem(
                                    ticket = ticket,
                                    onClick = { onTicketClick(ticket.id) }
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun TicketTabsHeader(
    selectedTab: TicketTab,
    onTabSelected: (TicketTab) -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 20.dp, vertical = 6.dp)
            .height(40.dp)
            .clip(PillShape)
            .background(Neutral.Paper)
            .padding(4.dp),
        horizontalArrangement = Arrangement.SpaceAround
    ) {
        TicketTabOption(
            title = "Open",
            isSelected = selectedTab == TicketTab.OPEN,
            onClick = { onTabSelected(TicketTab.OPEN) },
            modifier = Modifier.weight(1f)
        )
        TicketTabOption(
            title = "Waiting on me",
            isSelected = selectedTab == TicketTab.WAITING_ON_ME,
            onClick = { onTabSelected(TicketTab.WAITING_ON_ME) },
            modifier = Modifier.weight(1.3f)
        )
        TicketTabOption(
            title = "Resolved",
            isSelected = selectedTab == TicketTab.RESOLVED,
            onClick = { onTabSelected(TicketTab.RESOLVED) },
            modifier = Modifier.weight(1f)
        )
    }
}

@Composable
private fun TicketTabOption(
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

@Composable
private fun CategoryFilterRow(
    selectedCategory: Category?,
    onCategorySelected: (Category?) -> Unit
) {
    LazyRow(
        contentPadding = PaddingValues(horizontal = 20.dp, vertical = 8.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        item {
            RdChip(
                text = "All",
                variant = if (selectedCategory == null) RdChipVariant.Attention else RdChipVariant.Neutral,
                onClick = { onCategorySelected(null) }
            )
        }
        items(Category.entries.toTypedArray()) { cat ->
            val isSelected = cat == selectedCategory
            RdChip(
                text = cat.name.lowercase().replaceFirstChar { it.uppercase() },
                variant = if (isSelected) RdChipVariant.Attention else RdChipVariant.Neutral,
                onClick = { onCategorySelected(cat) }
            )
        }
    }
}

@Composable
private fun TicketListItem(
    ticket: Ticket,
    onClick: () -> Unit
) {
    RdCard(
        modifier = Modifier.fillMaxWidth(),
        backgroundColor = Neutral.Paper,
        onClick = onClick
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "#${ticket.id}",
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.Bold,
                    color = Brand.Concrete
                )
                Spacer(modifier = Modifier.width(8.dp))
                RdChip(
                    text = ticket.category.name.lowercase().replaceFirstChar { it.uppercase() },
                    variant = RdChipVariant.Neutral
                )
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

        Spacer(modifier = Modifier.height(6.dp))

        Text(
            text = ticket.subject,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            color = Brand.Nero,
            maxLines = 1
        )

        Spacer(modifier = Modifier.height(2.dp))

        Text(
            text = ticket.description,
            style = MaterialTheme.typography.bodyMedium,
            color = Neutral.MutedLight,
            maxLines = 2
        )

        Spacer(modifier = Modifier.height(10.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "Status: ${ticket.status.name.lowercase().replaceFirstChar { it.uppercase() }}",
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.SemiBold,
                color = Brand.Nero
            )

            Text(
                text = ticket.assignee?.name ?: "Auto-Routing...",
                style = MaterialTheme.typography.labelSmall,
                color = Neutral.MutedLight
            )
        }
    }
}
