package com.routedesk.feature.tickets

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Neutral
import com.routedesk.model.TicketStatus

@Composable
fun StatusStepper(
    currentStatus: TicketStatus,
    modifier: Modifier = Modifier
) {
    val steps = listOf("New", "In Progress", "Waiting", "Resolved")
    val currentStepIndex = when (currentStatus) {
        TicketStatus.OPEN -> 0
        TicketStatus.IN_PROGRESS -> 1
        TicketStatus.WAITING_ON_REQUESTER, TicketStatus.PENDING_APPROVAL -> 2
        TicketStatus.RESOLVED, TicketStatus.CLOSED -> 3
    }

    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(vertical = 12.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        steps.forEachIndexed { index, stepName ->
            val isCompleted = index < currentStepIndex
            val isCurrent = index == currentStepIndex

            val dotColor = when {
                isCurrent -> Brand.Orange
                isCompleted -> Color(0xFF2E7D32)
                else -> Neutral.LineLight
            }

            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                modifier = Modifier.weight(1f)
            ) {
                Box(
                    modifier = Modifier
                        .size(24.dp)
                        .clip(CircleShape)
                        .background(dotColor),
                    contentAlignment = Alignment.Center
                ) {
                    if (isCompleted) {
                        Icon(
                            imageVector = Icons.Default.Check,
                            contentDescription = null,
                            tint = Brand.San,
                            modifier = Modifier.size(14.dp)
                        )
                    } else if (isCurrent) {
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .clip(CircleShape)
                                .background(Brand.Nero)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = stepName,
                    style = MaterialTheme.typography.labelSmall,
                    fontSize = 11.sp,
                    fontWeight = if (isCurrent) FontWeight.Bold else FontWeight.Normal,
                    color = if (isCurrent) Brand.Nero else Neutral.MutedLight,
                    maxLines = 1
                )
            }

            if (index < steps.size - 1) {
                val lineColor = if (index < currentStepIndex) Color(0xFF2E7D32) else Neutral.LineLight
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .height(2.dp)
                        .background(lineColor)
                )
            }
        }
    }
}
