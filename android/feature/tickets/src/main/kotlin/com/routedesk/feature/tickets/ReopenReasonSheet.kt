package com.routedesk.feature.tickets

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.routedesk.designsystem.component.RdBottomSheet
import com.routedesk.designsystem.component.RdButton
import com.routedesk.designsystem.component.RdButtonSize
import com.routedesk.designsystem.component.RdButtonVariant
import com.routedesk.designsystem.component.RdChip
import com.routedesk.designsystem.component.RdChipVariant
import com.routedesk.designsystem.component.RdTextField
import com.routedesk.designsystem.theme.Neutral

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ReopenReasonSheet(
    onConfirmReopen: (reason: String, notes: String) -> Unit,
    onDismiss: () -> Unit
) {
    val reasons = listOf(
        "Issue not resolved",
        "Problem recurred",
        "New side effect",
        "Other"
    )
    var selectedReason by remember { mutableStateOf(reasons[0]) }
    var notesText by remember { mutableStateOf("") }

    RdBottomSheet(
        onDismissRequest = onDismiss,
        title = "Reopen Ticket"
    ) {
        Text(
            text = "Please specify why this ticket needs further investigation:",
            style = MaterialTheme.typography.bodyMedium,
            color = Neutral.MutedLight,
            modifier = Modifier.padding(bottom = 12.dp)
        )

        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            reasons.forEach { r ->
                val isSelected = r == selectedReason
                RdChip(
                    text = r,
                    variant = if (isSelected) RdChipVariant.Attention else RdChipVariant.Neutral,
                    onClick = { selectedReason = r },
                    modifier = Modifier.fillMaxWidth()
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        RdTextField(
            value = notesText,
            onValueChange = { notesText = it },
            label = "EXPLANATION",
            placeholder = "Describe what is still not working...",
            singleLine = false,
            modifier = Modifier.height(110.dp)
        )

        Spacer(modifier = Modifier.height(20.dp))

        RdButton(
            text = "Reopen Ticket",
            onClick = {
                onConfirmReopen(selectedReason, notesText)
                onDismiss()
            },
            variant = RdButtonVariant.Primary,
            size = RdButtonSize.Large,
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(16.dp))
    }
}
