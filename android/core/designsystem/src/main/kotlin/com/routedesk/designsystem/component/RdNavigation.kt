package com.routedesk.designsystem.component

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
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
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Neutral
import com.routedesk.designsystem.theme.PillShape
import com.routedesk.designsystem.theme.softShadow

@Composable
fun RdTopBar(
    title: String,
    modifier: Modifier = Modifier,
    onBackClick: (() -> Unit)? = null,
    trailingAction: (@Composable () -> Unit)? = null
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .statusBarsPadding()
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        if (onBackClick != null) {
            RdIconButton(
                icon = Icons.AutoMirrored.Filled.ArrowBack,
                contentDescription = "Navigate back",
                onClick = onBackClick,
                style = RdIconButtonStyle.Paper
            )
            Spacer(modifier = Modifier.size(12.dp))
        }

        Text(
            text = title,
            style = MaterialTheme.typography.titleLarge,
            color = Brand.Nero,
            modifier = Modifier.weight(1f)
        )

        trailingAction?.let {
            it()
        }
    }
}

data class BottomBarItem(
    val icon: ImageVector,
    val label: String,
    val isSelected: Boolean,
    val badgeCount: Int = 0,
    val onClick: () -> Unit
)

@Composable
fun RdBottomBar(
    items: List<BottomBarItem>,
    onCenterActionClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    // Floating pill bar with 5 slots, center is FAB
    Box(
        modifier = modifier
            .fillMaxWidth()
            .navigationBarsPadding()
            .padding(horizontal = 20.dp, vertical = 12.dp),
        contentAlignment = Alignment.Center
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .height(64.dp)
                .softShadow(elevation = 6.dp, shape = PillShape)
                .clip(PillShape)
                .background(Brand.Nero)
                .padding(horizontal = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceAround
        ) {
            // Slot 1 & Slot 2
            items.take(2).forEach { item ->
                BottomBarSlot(item = item)
            }

            // Center slot reserved for RdFab
            Spacer(modifier = Modifier.size(56.dp))

            // Slot 4 & Slot 5
            items.drop(2).take(2).forEach { item ->
                BottomBarSlot(item = item)
            }
        }

        // Center floating action button
        RdFab(
            onClick = onCenterActionClick,
            modifier = Modifier.align(Alignment.Center)
        )
    }
}

@Composable
private fun BottomBarSlot(item: BottomBarItem) {
    val tint = if (item.isSelected) Brand.Orange else Neutral.MutedDark

    Column(
        modifier = Modifier
            .size(48.dp)
            .clip(CircleShape)
            .clickable(role = Role.Tab, onClick = item.onClick),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            imageVector = item.icon,
            contentDescription = item.label,
            tint = tint,
            modifier = Modifier.size(22.dp)
        )
        Text(
            text = item.label,
            fontSize = 10.sp,
            fontWeight = if (item.isSelected) FontWeight.SemiBold else FontWeight.Normal,
            color = tint,
            maxLines = 1
        )
    }
}
