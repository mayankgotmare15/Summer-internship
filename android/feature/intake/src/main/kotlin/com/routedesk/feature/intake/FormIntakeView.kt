package com.routedesk.feature.intake

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
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.routedesk.designsystem.component.RdButton
import com.routedesk.designsystem.component.RdButtonSize
import com.routedesk.designsystem.component.RdButtonVariant
import com.routedesk.designsystem.component.RdCard
import com.routedesk.designsystem.component.RdChip
import com.routedesk.designsystem.component.RdChipVariant
import com.routedesk.designsystem.component.RdTextField
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Neutral
import com.routedesk.model.Category
import com.routedesk.model.Priority

@Composable
fun FormIntakeView(
    uiState: IntakeUiState,
    onSubjectChange: (String) -> Unit,
    onDescriptionChange: (String) -> Unit,
    onCategoryClick: () -> Unit,
    onPriorityChange: (Priority) -> Unit,
    onBlockingTeamToggle: (Boolean) -> Unit,
    onSubmitClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .imePadding()
            .padding(horizontal = 20.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Subject Field
        RdTextField(
            value = uiState.subject,
            onValueChange = onSubjectChange,
            label = "SUBJECT",
            placeholder = "Brief summary of the blocker...",
            singleLine = true
        )

        // Description Field with 5000-character counter
        RdTextField(
            value = uiState.description,
            onValueChange = onDescriptionChange,
            label = "DETAILED DESCRIPTION",
            placeholder = "Steps to reproduce, error messages, and context...",
            maxChars = 5000,
            singleLine = false,
            modifier = Modifier.height(180.dp)
        )

        // Category Selection Row
        RdCard(
            modifier = Modifier.fillMaxWidth(),
            onClick = onCategoryClick
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "CATEGORY",
                        style = MaterialTheme.typography.labelSmall,
                        fontWeight = FontWeight.Bold,
                        color = Neutral.MutedLight,
                        letterSpacing = 1.sp
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = uiState.category.name.lowercase().replaceFirstChar { it.uppercase() },
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                        color = Brand.Nero
                    )
                }

                Text(
                    text = "Change ›",
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = Brand.Orange
                )
            }
        }

        // Priority Selector Chips
        Column {
            Text(
                text = "PRIORITY URGENCY",
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.Bold,
                color = Neutral.MutedLight,
                letterSpacing = 1.sp,
                modifier = Modifier.padding(bottom = 8.dp)
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Priority.entries.forEach { p ->
                    val isSelected = p == uiState.priority
                    RdChip(
                        text = p.name,
                        variant = if (isSelected) {
                            when (p) {
                                Priority.CRITICAL -> RdChipVariant.Danger
                                Priority.HIGH -> RdChipVariant.Attention
                                Priority.MEDIUM -> RdChipVariant.Warning
                                Priority.LOW -> RdChipVariant.Neutral
                            }
                        } else {
                            RdChipVariant.Neutral
                        },
                        onClick = { onPriorityChange(p) },
                        modifier = Modifier.weight(1f)
                    )
                }
            }
        }

        // Blocking Team Toggle
        RdCard(modifier = Modifier.fillMaxWidth()) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = "Blocking Entire Team?",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                        color = Brand.Nero
                    )
                    Text(
                        text = "Prioritizes immediate routing to on-call lead",
                        style = MaterialTheme.typography.labelSmall,
                        color = Neutral.MutedLight
                    )
                }

                Switch(
                    checked = uiState.isBlockingTeam,
                    onCheckedChange = onBlockingTeamToggle,
                    colors = SwitchDefaults.colors(
                        checkedThumbColor = Brand.Nero,
                        checkedTrackColor = Brand.Orange,
                        uncheckedThumbColor = Brand.Concrete,
                        uncheckedTrackColor = Neutral.LineLight
                    )
                )
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        // Submit Button
        RdButton(
            text = "Create Ticket →",
            onClick = onSubmitClick,
            variant = RdButtonVariant.Primary,
            size = RdButtonSize.Large,
            isLoading = uiState.isSubmitting,
            modifier = Modifier.fillMaxWidth()
        )
    }
}
