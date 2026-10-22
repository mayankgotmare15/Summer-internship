package com.routedesk.designsystem.theme

import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Shapes
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

val RouteDeskShapes = Shapes(
    small = RoundedCornerShape(10.dp),
    medium = RoundedCornerShape(16.dp),
    large = RoundedCornerShape(24.dp),
    extraLarge = RoundedCornerShape(32.dp)
)

val PillShape = CircleShape

fun Modifier.softShadow(
    elevation: Dp = 4.dp,
    shape: Shape = RouteDeskShapes.medium,
    ambientColor: Color = Neutral.Ink.copy(alpha = 0.06f),
    spotColor: Color = Neutral.Ink.copy(alpha = 0.08f)
): Modifier = this.shadow(
    elevation = elevation,
    shape = shape,
    ambientColor = ambientColor,
    spotColor = spotColor
)
