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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
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
import com.routedesk.data.clock.ClockOffsetManager
import com.routedesk.data.clock.SlaTicker
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Neutral
import kotlinx.datetime.Instant

@Composable
fun SlaTimer(
    dueInstant: Instant?,
    clockOffsetManager: ClockOffsetManager,
    modifier: Modifier = Modifier,
    label: String = "FIRST RESPONSE SLA"
) {
    val currentServerEpochMs by clockOffsetManager.tickerFlow.collectAsState(
        initial = clockOffsetManager.currentServerTimeMillis()
    )

    val countdown = SlaTicker.computeCountdown(
        dueInstant = dueInstant,
        currentServerEpochMs = currentServerEpochMs
    )

    val timerColor = when {
        countdown.isBreached -> Color(0xFFB42318)
        countdown.isAtRisk -> Brand.Orange
        else -> Color(0xFF2E7D32)
    }

    val timerBgColor = when {
        countdown.isBreached -> Color(0xFFF9E1DC)
        countdown.isAtRisk -> Color(0xFFFDE3D8)
        else -> Color(0xFFDDEBDD)
    }

    Box(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(timerBgColor)
            .padding(horizontal = 16.dp, vertical = 12.dp)
    ) {
        Column {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(8.dp)
                            .clip(CircleShape)
                            .background(timerColor)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = label,
                        style = MaterialTheme.typography.labelSmall,
                        fontWeight = FontWeight.Bold,
                        color = timerColor,
                        letterSpacing = 1.sp
                    )
                }

                Text(
                    text = countdown.formatted,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = timerColor
                )
            }

            Spacer(modifier = Modifier.height(8.dp))

            LinearProgressIndicator(
                progress = { countdown.progressPct },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(4.dp)
                    .clip(RoundedCornerShape(2.dp)),
                color = timerColor,
                trackColor = timerColor.copy(alpha = 0.2f)
            )
        }
    }
}
