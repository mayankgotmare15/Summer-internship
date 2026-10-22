package com.routedesk.feature.auth

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.Role as ComposeRole
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Neutral
import com.routedesk.model.Role

data class DemoRoleOption(
    val role: Role,
    val title: String,
    val subtitle: String,
    val tag: String,
    val color: Color
)

val DemoRoleOptions = listOf(
    DemoRoleOption(
        role = Role.REQUESTER,
        title = "Requester",
        subtitle = "Raise tickets via chat/form, track live SLA & escalate",
        tag = "Employee",
        color = Brand.Orange
    ),
    DemoRoleOption(
        role = Role.ENGINEER,
        title = "Resolver Engineer",
        subtitle = "Manage queue by SLA urgency, change ETA & request info",
        tag = "Tier 2",
        color = Color(0xFF2E7D32)
    ),
    DemoRoleOption(
        role = Role.TEAM_LEAD,
        title = "Team Lead",
        subtitle = "SLA warnings, reassign tickets & check team availability",
        tag = "Lead",
        color = Color(0xFF8A5A00)
    ),
    DemoRoleOption(
        role = Role.APPROVER,
        title = "Approver",
        subtitle = "One-tap approvals for hardware & admin rights",
        tag = "Manager",
        color = Color(0xFF7D5A9B)
    ),
    DemoRoleOption(
        role = Role.AGENT,
        title = "Service Desk Agent",
        subtitle = "Human review queue cards, triage & correct predictions",
        tag = "Desk",
        color = Brand.Concrete
    ),
    DemoRoleOption(
        role = Role.MANAGER,
        title = "IT Delivery Manager",
        subtitle = "8 KPI tiles, trend charts & SLA breach analysis",
        tag = "Exec",
        color = Neutral.Ink
    )
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DemoRolePickerSheet(
    onRoleSelected: (Role) -> Unit,
    onDismiss: () -> Unit
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = sheetState,
        containerColor = Neutral.Paper,
        shape = RoundedCornerShape(topStart = 24.dp, topEnd = 24.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp, vertical = 8.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "Demo Quick Login",
                        style = MaterialTheme.typography.titleLarge,
                        color = Brand.Nero
                    )
                    Text(
                        text = "Select a persona to explore the app instantly",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Neutral.MutedLight
                    )
                }
                IconButton(onClick = onDismiss) {
                    Icon(
                        imageVector = Icons.Default.Close,
                        contentDescription = "Close sheet",
                        tint = Brand.Nero
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            DemoRoleOptions.forEach { option ->
                DemoRoleRow(
                    option = option,
                    onClick = {
                        onRoleSelected(option.role)
                        onDismiss()
                    }
                )
                Spacer(modifier = Modifier.height(10.dp))
            }

            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}

@Composable
private fun DemoRoleRow(
    option: DemoRoleOption,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(Brand.San)
            .clickable(role = ComposeRole.Button, onClick = onClick)
            .padding(14.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(42.dp)
                .clip(CircleShape)
                .background(option.color.copy(alpha = 0.15f)),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = option.title.take(1),
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp,
                color = option.color
            )
        }

        Spacer(modifier = Modifier.width(12.dp))

        Column(modifier = Modifier.weight(1f)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = option.title,
                    style = MaterialTheme.typography.titleMedium,
                    color = Brand.Nero
                )
                Spacer(modifier = Modifier.width(6.dp))
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(4.dp))
                        .background(Brand.Nero)
                        .padding(horizontal = 6.dp, vertical = 2.dp)
                ) {
                    Text(
                        text = option.tag.uppercase(),
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        color = Brand.San
                    )
                }
            }
            Text(
                text = option.subtitle,
                style = MaterialTheme.typography.bodySmall,
                color = Neutral.MutedLight,
                maxLines = 2
            )
        }
    }
}
