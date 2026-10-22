package com.routedesk.feature.intake

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
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.routedesk.designsystem.component.RdBottomSheet
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Neutral
import com.routedesk.model.Category

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CategoryOverrideSheet(
    currentCategory: Category,
    onCategoryChosen: (Category) -> Unit,
    onDismiss: () -> Unit
) {
    val categories = Category.entries

    RdBottomSheet(
        onDismissRequest = onDismiss,
        title = "Choose Correct Category"
    ) {
        Text(
            text = "Tell us what this request is actually about. We'll update the ticket and tune the model.",
            style = MaterialTheme.typography.bodyMedium,
            color = Neutral.MutedLight,
            modifier = Modifier.padding(bottom = 16.dp)
        )

        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            categories.forEach { cat ->
                val isSelected = cat == currentCategory

                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(14.dp))
                        .background(if (isSelected) Brand.San else Color.Transparent)
                        .clickable(role = Role.RadioButton) {
                            onCategoryChosen(cat)
                            onDismiss()
                        }
                        .padding(horizontal = 16.dp, vertical = 12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = cat.name.lowercase().replaceFirstChar { it.uppercase() },
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.SemiBold,
                            color = Brand.Nero
                        )
                        Text(
                            text = getCategoryDescription(cat),
                            style = MaterialTheme.typography.labelSmall,
                            color = Neutral.MutedLight
                        )
                    }

                    if (isSelected) {
                        Box(
                            modifier = Modifier
                                .size(24.dp)
                                .clip(CircleShape)
                                .background(Brand.Orange),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                imageVector = Icons.Default.Check,
                                contentDescription = "Selected",
                                tint = Brand.Nero,
                                modifier = Modifier.size(16.dp)
                            )
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(24.dp))
    }
}

private fun getCategoryDescription(category: Category): String = when (category) {
    Category.ACCESS -> "Passwords, logins, permissions, Okta & MFA"
    Category.HARDWARE -> "Laptops, monitors, chargers, keyboards & peripherals"
    Category.SOFTWARE -> "Applications, licenses, IDEs & developer tools"
    Category.NETWORK -> "VPN, Wi-Fi connectivity, DNS & office networks"
    Category.HR -> "Payroll, benefits, leave policies & onboarding"
    Category.FINANCE -> "Expenses, reimbursements, billing & credit cards"
    Category.SECURITY -> "Phishing reports, malware, incident alerts & compliance"
    Category.OTHER -> "General workplace assistance and uncategorized issues"
}
