package com.routedesk.designsystem.component

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.LocalRouteDeskColors
import com.routedesk.designsystem.theme.Neutral
import com.routedesk.designsystem.theme.PillShape

enum class RdButtonVariant {
    Primary,    // Nero fill, San text
    Accent,     // Orange fill, Nero text
    Secondary,  // Paper fill, LineLight border
    Ghost,      // Transparent
    Link,       // OrangeText clickable
    LightPill   // San fill on dark background
}

enum class RdButtonSize(val height: Dp, val horizontalPadding: Dp) {
    Small(40.dp, 16.dp),
    Medium(48.dp, 24.dp),
    Large(56.dp, 32.dp)
}

@Composable
fun RdButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    variant: RdButtonVariant = RdButtonVariant.Primary,
    size: RdButtonSize = RdButtonSize.Medium,
    enabled: Boolean = true,
    isLoading: Boolean = false,
    leadingIcon: (@Composable () -> Unit)? = null
) {
    val colors = LocalRouteDeskColors.current

    val (containerColor, contentColor, border) = when (variant) {
        RdButtonVariant.Primary -> Triple(Brand.Nero, Brand.San, null)
        RdButtonVariant.Accent -> Triple(Brand.Orange, Brand.Nero, null)
        RdButtonVariant.Secondary -> Triple(Neutral.Paper, Brand.Nero, BorderStroke(1.dp, Neutral.LineLight))
        RdButtonVariant.Ghost -> Triple(Color.Transparent, Brand.Nero, null)
        RdButtonVariant.Link -> Triple(Color.Transparent, colors.orangeText, null)
        RdButtonVariant.LightPill -> Triple(Brand.San, Brand.Nero, null)
    }

    if (variant == RdButtonVariant.Link) {
        TextButton(
            onClick = onClick,
            enabled = enabled && !isLoading,
            modifier = modifier.height(size.height),
            shape = PillShape
        ) {
            Text(
                text = text,
                style = MaterialTheme.typography.bodyLarge.copy(fontWeight = FontWeight.SemiBold),
                color = if (enabled) contentColor else Neutral.MutedLight
            )
        }
    } else {
        Button(
            onClick = onClick,
            enabled = enabled && !isLoading,
            modifier = modifier.height(size.height),
            shape = PillShape,
            border = border,
            colors = ButtonDefaults.buttonColors(
                containerColor = containerColor,
                contentColor = contentColor,
                disabledContainerColor = containerColor.copy(alpha = 0.4f),
                disabledContentColor = contentColor.copy(alpha = 0.5f)
            ),
            contentPadding = PaddingValues(horizontal = size.horizontalPadding)
        ) {
            Box(contentAlignment = Alignment.Center) {
                if (isLoading) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        strokeWidth = 2.dp,
                        color = contentColor
                    )
                } else {
                    androidx.compose.foundation.layout.Row(
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        leadingIcon?.let {
                            it()
                            androidx.compose.foundation.layout.Spacer(modifier = Modifier.size(8.dp))
                        }
                        Text(
                            text = text,
                            style = MaterialTheme.typography.bodyLarge.copy(fontWeight = FontWeight.SemiBold)
                        )
                    }
                }
            }
        }
    }
}
