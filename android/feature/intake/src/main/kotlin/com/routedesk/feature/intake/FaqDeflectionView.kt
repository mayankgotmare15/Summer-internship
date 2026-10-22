package com.routedesk.feature.intake

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Info
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.routedesk.designsystem.component.RdButton
import com.routedesk.designsystem.component.RdButtonSize
import com.routedesk.designsystem.component.RdButtonVariant
import com.routedesk.designsystem.component.RdCard
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Neutral
import com.routedesk.model.Category

data class FaqArticle(
    val id: String,
    val title: String,
    val snippet: String
)

@Composable
fun FaqDeflectionView(
    category: Category,
    onDeflected: () -> Unit,
    modifier: Modifier = Modifier
) {
    val article = getSuggestedFaq(category) ?: return

    RdCard(
        modifier = modifier.fillMaxWidth(),
        backgroundColor = Brand.San
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(24.dp)
                    .clip(CircleShape)
                    .background(Brand.Orange.copy(alpha = 0.2f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.Info,
                    contentDescription = null,
                    tint = Brand.Orange,
                    modifier = Modifier.size(16.dp)
                )
            }
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = "SUGGESTED SELF-SERVICE FIX",
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.Bold,
                color = Brand.Concrete,
                letterSpacing = 1.sp
            )
        }

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = article.title,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            color = Brand.Nero
        )

        Spacer(modifier = Modifier.height(4.dp))

        Text(
            text = article.snippet,
            style = MaterialTheme.typography.bodyMedium,
            color = Neutral.MutedLight
        )

        Spacer(modifier = Modifier.height(12.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.End
        ) {
            RdButton(
                text = "This fixed it! ✓",
                onClick = onDeflected,
                variant = RdButtonVariant.Primary,
                size = RdButtonSize.Small
            )
        }
    }
}

private fun getSuggestedFaq(category: Category): FaqArticle? = when (category) {
    Category.ACCESS -> FaqArticle(
        id = "faq_01",
        title = "Self-Service Password Reset",
        snippet = "Visit sso.internal/reset on your registered mobile authenticator to unlock your account in 30 seconds."
    )
    Category.NETWORK -> FaqArticle(
        id = "faq_02",
        title = "GlobalProtect VPN Certificate Renewal",
        snippet = "If VPN disconnects with 'Certificate Invalid', open Terminal and run 'route-vpn cert-refresh'."
    )
    Category.SOFTWARE -> FaqArticle(
        id = "faq_03",
        title = "Developer License Activation Portal",
        snippet = "Request JetBrains & GitHub Copilot licenses automatically via self-serve at tools.internal/licenses."
    )
    else -> null
}
