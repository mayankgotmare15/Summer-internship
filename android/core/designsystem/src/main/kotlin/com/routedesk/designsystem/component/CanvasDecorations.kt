package com.routedesk.designsystem.component

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Neutral

@Composable
fun HatchedDivider(
    modifier: Modifier = Modifier,
    height: Dp = 12.dp,
    strokeColor: Color = Neutral.Nero700,
    spacing: Dp = 8.dp
) {
    Canvas(
        modifier = modifier
            .fillMaxWidth()
            .height(height)
    ) {
        val strokeWidthPx = 1.5.dp.toPx()
        val spacingPx = spacing.toPx()
        val canvasHeight = size.height

        var x = 0f
        while (x < size.width + canvasHeight) {
            drawLine(
                color = strokeColor,
                start = Offset(x, 0f),
                end = Offset(x - canvasHeight, canvasHeight),
                strokeWidth = strokeWidthPx,
                cap = StrokeCap.Square
            )
            x += spacingPx
        }
    }
}

@Composable
fun CropFrame(
    modifier: Modifier = Modifier,
    tickLength: Dp = 12.dp,
    strokeWidth: Dp = 2.dp,
    color: Color = Brand.Orange
) {
    Canvas(modifier = modifier) {
        val tickPx = tickLength.toPx()
        val strokePx = strokeWidth.toPx()
        val w = size.width
        val h = size.height

        // Top-left corner
        drawLine(color, Offset(0f, 0f), Offset(tickPx, 0f), strokePx)
        drawLine(color, Offset(0f, 0f), Offset(0f, tickPx), strokePx)

        // Top-right corner
        drawLine(color, Offset(w, 0f), Offset(w - tickPx, 0f), strokePx)
        drawLine(color, Offset(w, 0f), Offset(w, tickPx), strokePx)

        // Bottom-left corner
        drawLine(color, Offset(0f, h), Offset(tickPx, h), strokePx)
        drawLine(color, Offset(0f, h), Offset(0f, h - tickPx), strokePx)

        // Bottom-right corner
        drawLine(color, Offset(w, h), Offset(w - tickPx, h), strokePx)
        drawLine(color, Offset(w, h), Offset(w, h - tickPx), strokePx)
    }
}

@Composable
fun RdSkeleton(
    modifier: Modifier = Modifier,
    shape: androidx.compose.ui.graphics.Shape = RoundedCornerShape(8.dp)
) {
    val transition = rememberInfiniteTransition(label = "shimmer")
    val translateAnim by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1000f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 1200, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "shimmer_offset"
    )

    val shimmerColors = listOf(
        Neutral.LineLight.copy(alpha = 0.6f),
        Neutral.Paper,
        Neutral.LineLight.copy(alpha = 0.6f)
    )

    val brush = Brush.linearGradient(
        colors = shimmerColors,
        start = Offset(translateAnim - 500f, 0f),
        end = Offset(translateAnim, 0f)
    )

    Box(
        modifier = modifier
            .clip(shape)
            .background(brush)
    )
}
