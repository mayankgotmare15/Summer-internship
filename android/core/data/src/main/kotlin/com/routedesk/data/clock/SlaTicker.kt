package com.routedesk.data.clock

import kotlinx.datetime.Instant
import kotlin.math.abs

data class SlaCountdown(
    val formatted: String,
    val isBreached: Boolean,
    val isAtRisk: Boolean,
    val remainingMillis: Long,
    val progressPct: Float
)

object SlaTicker {

    fun computeCountdown(
        dueInstant: Instant?,
        currentServerEpochMs: Long,
        totalWindowMillis: Long = 4 * 3600 * 1000L // default 4-hour SLA window
    ): SlaCountdown {
        if (dueInstant == null) {
            return SlaCountdown(
                formatted = "No SLA target",
                isBreached = false,
                isAtRisk = false,
                remainingMillis = 0L,
                progressPct = 1.0f
            )
        }

        val dueEpochMs = dueInstant.toEpochMilliseconds()
        val diff = dueEpochMs - currentServerEpochMs

        return if (diff < 0) {
            val overdueSeconds = abs(diff) / 1000
            val hours = overdueSeconds / 3600
            val minutes = (overdueSeconds % 3600) / 60
            val formatted = if (hours > 0) {
                "Breached by ${hours}h ${minutes}m"
            } else {
                "Breached by ${minutes}m"
            }
            SlaCountdown(
                formatted = formatted,
                isBreached = true,
                isAtRisk = true,
                remainingMillis = diff,
                progressPct = 1.0f
            )
        } else {
            val remainingSeconds = diff / 1000
            val hours = remainingSeconds / 3600
            val minutes = (remainingSeconds % 3600) / 60
            val seconds = remainingSeconds % 60
            val formatted = String.format("%02d:%02d:%02d", hours, minutes, seconds)
            val isAtRisk = diff < 3600 * 1000L // less than 1 hour remaining
            val elapsed = totalWindowMillis - diff
            val progress = (elapsed.toFloat() / totalWindowMillis.toFloat()).coerceIn(0f, 1f)

            SlaCountdown(
                formatted = formatted,
                isBreached = false,
                isAtRisk = isAtRisk,
                remainingMillis = diff,
                progressPct = progress
            )
        }
    }
}
