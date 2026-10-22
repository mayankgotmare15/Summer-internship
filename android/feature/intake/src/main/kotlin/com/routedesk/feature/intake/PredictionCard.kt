package com.routedesk.feature.intake

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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.LinearProgressIndicator
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
import com.routedesk.designsystem.component.RdButton
import com.routedesk.designsystem.component.RdButtonSize
import com.routedesk.designsystem.component.RdButtonVariant
import com.routedesk.designsystem.component.RdCard
import com.routedesk.designsystem.component.RdChip
import com.routedesk.designsystem.component.RdChipVariant
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Neutral
import com.routedesk.model.Category
import com.routedesk.model.Priority
import com.routedesk.network.dto.PredictResponse

@Composable
fun PredictionCard(
    prediction: PredictResponse,
    onLooksRightClick: () -> Unit,
    onNotQuiteClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val confidencePct = (prediction.confidence * 100).toInt()
    val confidenceColor = when {
        confidencePct >= 80 -> Color(0xFF2E7D32)
        confidencePct >= 60 -> Color(0xFF8A5A00)
        else -> Brand.Orange
    }

    RdCard(
        modifier = modifier.fillMaxWidth(),
        backgroundColor = Neutral.Paper
    ) {
        // Tag Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(8.dp)
                        .clip(RoundedCornerShape(2.dp))
                        .background(Color(0xFF7D5A9B))
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = "AI CLASSIFICATION",
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF7D5A9B),
                    letterSpacing = 1.sp
                )
            }

            Text(
                text = "$confidencePct% Match",
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.Bold,
                color = confidenceColor
            )
        }

        Spacer(modifier = Modifier.height(10.dp))

        // Category and Suggested Priority
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = prediction.category.uppercase(),
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                color = Brand.Nero
            )

            RdChip(
                text = "Priority: ${prediction.suggestedPriority.uppercase()}",
                variant = when (prediction.suggestedPriority.lowercase()) {
                    "critical" -> RdChipVariant.Danger
                    "high" -> RdChipVariant.Attention
                    "medium" -> RdChipVariant.Warning
                    else -> RdChipVariant.Neutral
                }
            )
        }

        Spacer(modifier = Modifier.height(10.dp))

        // Confidence Bar
        LinearProgressIndicator(
            progress = { prediction.confidence.toFloat() },
            modifier = Modifier
                .fillMaxWidth()
                .height(6.dp)
                .clip(RoundedCornerShape(3.dp)),
            color = confidenceColor,
            trackColor = Neutral.LineLight
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Action Buttons
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            RdButton(
                text = "Looks right ✓",
                onClick = onLooksRightClick,
                variant = RdButtonVariant.Primary,
                size = RdButtonSize.Small,
                modifier = Modifier.weight(1f)
            )

            RdButton(
                text = "Not quite ✕",
                onClick = onNotQuiteClick,
                variant = RdButtonVariant.Secondary,
                size = RdButtonSize.Small,
                modifier = Modifier.weight(1f)
            )
        }
    }
}
