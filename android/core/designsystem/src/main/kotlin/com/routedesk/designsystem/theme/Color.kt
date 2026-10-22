package com.routedesk.designsystem.theme

import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color

object Brand {
    val Nero = Color(0xFF171717)
    val Concrete = Color(0xFF594542)
    val Orange = Color(0xFFFD5323)
    val San = Color(0xFFEEE2D8)
}

object Neutral {
    val Paper = Color(0xFFF8F2ED)      // Cards on San
    val Ink = Color(0xFF360A00)        // Display headings on light
    val Nero800 = Color(0xFF202020)    // Inputs and cards on dark
    val Nero700 = Color(0xFF2A2A2A)    // Borders, hatch strokes on dark
    val MutedLight = Color(0xFF6B5A55)
    val MutedDark = Color(0xFFA8958E)
    val LineLight = Color(0xFFE2D3C7)
    val OrangeText = Color(0xFFB83A12) // Orange text or links on light (5.2:1 contrast on Paper)
}

@Immutable
data class StatusColor(val fg: Color, val tint: Color)

object Semantic {
    val Danger = StatusColor(Color(0xFFB42318), Color(0xFFF9E1DC))   // Critical, breached, decline
    val Attention = StatusColor(Neutral.OrangeText, Color(0xFFFDE3D8)) // High, escalated
    val Warning = StatusColor(Color(0xFF8A5A00), Color(0xFFF6E7C8))  // At risk, awaiting approval
    val Success = StatusColor(Color(0xFF2E7D32), Color(0xFFDDEBDD))  // Resolved, on track, auto-routed
    val Model = StatusColor(Color(0xFF7D5A9B), Color(0xFFE9E0F0))    // Prediction chips
    val NeutralStatus = StatusColor(Brand.Concrete, Brand.San)       // Low, closed, off shift
}

@Immutable
data class RouteDeskColors(
    val brandNero: Color = Brand.Nero,
    val brandConcrete: Color = Brand.Concrete,
    val brandOrange: Color = Brand.Orange,
    val brandSan: Color = Brand.San,
    val paper: Color = Neutral.Paper,
    val ink: Color = Neutral.Ink,
    val nero800: Color = Neutral.Nero800,
    val nero700: Color = Neutral.Nero700,
    val mutedLight: Color = Neutral.MutedLight,
    val mutedDark: Color = Neutral.MutedDark,
    val lineLight: Color = Neutral.LineLight,
    val orangeText: Color = Neutral.OrangeText,
    val danger: StatusColor = Semantic.Danger,
    val attention: StatusColor = Semantic.Attention,
    val warning: StatusColor = Semantic.Warning,
    val success: StatusColor = Semantic.Success,
    val model: StatusColor = Semantic.Model,
    val neutralStatus: StatusColor = Semantic.NeutralStatus
)

val LocalRouteDeskColors = staticCompositionLocalOf { RouteDeskColors() }
