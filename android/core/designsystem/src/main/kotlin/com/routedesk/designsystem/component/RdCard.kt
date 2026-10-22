package com.routedesk.designsystem.component

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Neutral
import com.routedesk.designsystem.theme.RouteDeskShapes
import com.routedesk.designsystem.theme.softShadow

@Composable
fun RdCard(
    modifier: Modifier = Modifier,
    backgroundColor: Color = Neutral.Paper,
    onClick: (() -> Unit)? = null,
    content: @Composable ColumnScope.() -> Unit
) {
    val baseModifier = modifier
        .softShadow(elevation = 3.dp, shape = RouteDeskShapes.medium)
        .clip(RouteDeskShapes.medium)
        .background(backgroundColor)

    val finalModifier = if (onClick != null) {
        baseModifier.clickable(role = Role.Button, onClick = onClick)
    } else {
        baseModifier
    }

    Column(
        modifier = finalModifier.padding(16.dp),
        content = content
    )
}

@Composable
fun RdTile(
    label: String,
    icon: ImageVector,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    iconBgColor: Color = Brand.San,
    iconTint: Color = Brand.Concrete
) {
    RdCard(
        modifier = modifier.size(width = 110.dp, height = 110.dp),
        onClick = onClick
    ) {
        Box(
            modifier = Modifier
                .size(40.dp)
                .clip(CircleShape)
                .background(iconBgColor),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = iconTint,
                modifier = Modifier.size(20.dp)
            )
        }
        Spacer(modifier = Modifier.weight(1f))
        Text(
            text = label.uppercase(),
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.SemiBold,
            color = Brand.Nero,
            maxLines = 2
        )
    }
}

@Composable
fun RdListRow(
    title: String,
    meta: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    leadingIcon: (@Composable () -> Unit)? = null,
    trailingContent: (@Composable () -> Unit)? = null
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .softShadow(elevation = 2.dp, shape = RouteDeskShapes.medium)
            .clip(RouteDeskShapes.medium)
            .background(Neutral.Paper)
            .clickable(role = Role.Button, onClick = onClick)
            .padding(16.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        leadingIcon?.let {
            it()
            Spacer(modifier = Modifier.width(12.dp))
        }

        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium,
                color = Brand.Nero,
                maxLines = 1
            )
            Text(
                text = meta,
                style = MaterialTheme.typography.bodyMedium,
                color = Neutral.MutedLight,
                maxLines = 1
            )
        }

        trailingContent?.let {
            Spacer(modifier = Modifier.width(8.dp))
            it()
        }
    }
}
