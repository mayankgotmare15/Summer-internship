package com.routedesk.designsystem.component

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Badge
import androidx.compose.material3.BadgedBox
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Neutral

enum class RdIconButtonStyle {
    Paper,
    Dark
}

@Composable
fun RdIconButton(
    icon: ImageVector,
    contentDescription: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    style: RdIconButtonStyle = RdIconButtonStyle.Paper,
    badgeCount: Int = 0,
    hasUnreadBadge: Boolean = false
) {
    val (backgroundColor, iconColor) = when (style) {
        RdIconButtonStyle.Paper -> Pair(Neutral.Paper, Brand.Nero)
        RdIconButtonStyle.Dark -> Pair(Brand.Nero, Brand.San)
    }

    Box(
        modifier = modifier
            .size(48.dp)
            .clip(RoundedCornerShape(14.dp))
            .background(backgroundColor)
            .clickable(role = Role.Button, onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        BadgedBox(
            badge = {
                if (badgeCount > 0) {
                    Badge(
                        containerColor = Brand.Orange,
                        contentColor = Brand.Nero,
                        modifier = Modifier.offset(x = 4.dp, y = (-4).dp)
                    ) {
                        Text(
                            text = if (badgeCount > 99) "99+" else badgeCount.toString(),
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                } else if (hasUnreadBadge) {
                    Box(
                        modifier = Modifier
                            .size(8.dp)
                            .offset(x = 2.dp, y = (-2).dp)
                            .clip(CircleShape)
                            .background(Brand.Orange)
                    )
                }
            }
        ) {
            Icon(
                imageVector = icon,
                contentDescription = contentDescription,
                tint = iconColor,
                modifier = Modifier.size(24.dp)
            )
        }
    }
}

@Composable
fun RdFab(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    contentDescription: String = "Create new action"
) {
    Box(
        modifier = modifier
            .size(56.dp)
            .clip(CircleShape)
            .background(Brand.Orange)
            .clickable(role = Role.Button, onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        androidx.compose.material3.Text(
            text = "+",
            color = Color.White,
            fontSize = 32.sp,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.offset(y = (-2).dp)
        )
    }
}
