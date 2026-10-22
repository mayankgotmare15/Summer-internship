package com.routedesk.designsystem.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider

enum class Face { Nero, San }

private val LightScheme = lightColorScheme(
    primary = Brand.Nero,
    onPrimary = Brand.San,
    secondary = Brand.Concrete,
    onSecondary = Neutral.Paper,
    tertiary = Brand.Orange,
    onTertiary = Brand.Nero,
    background = Brand.San,
    onBackground = Brand.Nero,
    surface = Neutral.Paper,
    onSurface = Brand.Nero,
    surfaceVariant = Brand.San,
    onSurfaceVariant = Brand.Concrete,
    outline = Neutral.LineLight,
    error = Semantic.Danger.fg,
    onError = Brand.San
)

private val NeroScheme = darkColorScheme(
    primary = Brand.San,
    onPrimary = Brand.Nero,
    secondary = Neutral.MutedDark,
    onSecondary = Neutral.Nero800,
    tertiary = Brand.Orange,
    onTertiary = Brand.Nero,
    background = Brand.Nero,
    onBackground = Brand.San,
    surface = Neutral.Nero800,
    onSurface = Brand.San,
    surfaceVariant = Neutral.Nero700,
    onSurfaceVariant = Neutral.MutedDark,
    outline = Neutral.Nero700,
    error = Semantic.Danger.fg,
    onError = Brand.San
)

@Composable
fun RouteDeskTheme(
    face: Face = Face.San,
    content: @Composable () -> Unit
) {
    val colorScheme = if (face == Face.Nero) NeroScheme else LightScheme

    CompositionLocalProvider(
        LocalRouteDeskColors provides RouteDeskColors(),
        LocalRouteDeskExtendedTypography provides RouteDeskExtendedTypography()
    ) {
        MaterialTheme(
            colorScheme = colorScheme,
            typography = RouteDeskTypography,
            shapes = RouteDeskShapes,
            content = content
        )
    }
}
