package com.routedesk.feature.intake

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
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
import com.routedesk.designsystem.component.HatchedDivider
import com.routedesk.designsystem.component.RdButton
import com.routedesk.designsystem.component.RdButtonSize
import com.routedesk.designsystem.component.RdButtonVariant
import com.routedesk.designsystem.component.RdCard
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Face
import com.routedesk.designsystem.theme.Neutral
import com.routedesk.designsystem.theme.RouteDeskTheme
import com.routedesk.designsystem.theme.softShadow
import com.routedesk.network.dto.TicketCreatedResponse

@Composable
fun TicketConfirmationScreen(
    ticket: TicketCreatedResponse,
    onViewTicketClick: (String) -> Unit,
    onBackHomeClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    RouteDeskTheme(face = Face.Nero) {
        Column(
            modifier = modifier
                .fillMaxSize()
                .background(Brand.Nero)
                .statusBarsPadding()
                .navigationBarsPadding()
                .padding(24.dp),
            verticalArrangement = Arrangement.SpaceBetween,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.height(20.dp))

            // Main Slide-up Card
            RdCard(
                modifier = Modifier.fillMaxWidth(),
                backgroundColor = Neutral.Paper
            ) {
                // Checkmark Monogram
                Box(
                    modifier = Modifier
                        .size(64.dp)
                        .clip(CircleShape)
                        .background(Brand.Orange)
                        .align(Alignment.CenterHorizontally),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.Check,
                        contentDescription = "Success",
                        tint = Brand.Nero,
                        modifier = Modifier.size(36.dp)
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))

                Text(
                    text = "Ticket Submitted!",
                    style = MaterialTheme.typography.headlineMedium,
                    fontWeight = FontWeight.Bold,
                    color = Brand.Nero,
                    modifier = Modifier.align(Alignment.CenterHorizontally)
                )

                Text(
                    text = "Auto-routed to on-call engineer in < 5 seconds.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Neutral.MutedLight,
                    modifier = Modifier.align(Alignment.CenterHorizontally)
                )

                Spacer(modifier = Modifier.height(20.dp))
                HatchedDivider()
                Spacer(modifier = Modifier.height(20.dp))

                // Detail Rows
                ConfirmationDetailRow(
                    label = "TICKET ID",
                    value = "#${ticket.ticketId}",
                    isMono = true
                )

                ConfirmationDetailRow(
                    label = "ASSIGNED TO",
                    value = ticket.assignedTo ?: "Tier 2 Auto-Queue",
                    isMono = false
                )

                ConfirmationDetailRow(
                    label = "FIRST RESPONSE SLA",
                    value = "${ticket.slaMinutes} minutes",
                    isMono = false
                )

                ConfirmationDetailRow(
                    label = "STATUS",
                    value = ticket.status.uppercase(),
                    isMono = false,
                    valueColor = Color(0xFF2E7D32)
                )
            }

            // Action Buttons
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                RdButton(
                    text = "View Ticket Details →",
                    onClick = { onViewTicketClick(ticket.ticketId) },
                    variant = RdButtonVariant.Accent,
                    size = RdButtonSize.Large,
                    modifier = Modifier.fillMaxWidth()
                )

                RdButton(
                    text = "Back to Home",
                    onClick = onBackHomeClick,
                    variant = RdButtonVariant.LightPill,
                    size = RdButtonSize.Medium,
                    modifier = Modifier.fillMaxWidth()
                )
            }
        }
    }
}

@Composable
private fun ConfirmationDetailRow(
    label: String,
    value: String,
    isMono: Boolean = false,
    valueColor: Color = Brand.Nero
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 6.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.Bold,
            color = Neutral.MutedLight,
            letterSpacing = 1.sp
        )

        Text(
            text = value,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            color = valueColor
        )
    }
}
