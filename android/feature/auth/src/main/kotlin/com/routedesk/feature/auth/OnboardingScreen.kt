package com.routedesk.feature.auth

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.routedesk.designsystem.component.CropFrame
import com.routedesk.designsystem.component.HatchedDivider
import com.routedesk.designsystem.component.RdButton
import com.routedesk.designsystem.component.RdButtonSize
import com.routedesk.designsystem.component.RdButtonVariant
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Face
import com.routedesk.designsystem.theme.Neutral
import com.routedesk.designsystem.theme.RouteDeskTheme
import kotlinx.coroutines.launch

data class OnboardingPageData(
    val title: String,
    val subtitle: String,
    val tag: String,
    val statValue: String? = null,
    val statLabel: String? = null
)

val OnboardingPages = listOf(
    OnboardingPageData(
        title = "Describe it once",
        subtitle = "Say what's broken in your own words. Our AI model classifies urgency, extracts key context, and predicts routing in milliseconds.",
        tag = "Smart Intake",
        statValue = "< 5s",
        statLabel = "Average ticket submission"
    ),
    OnboardingPageData(
        title = "Routed to the right person in seconds",
        subtitle = "Zero manual sorting queues. Direct escalation paths ensure critical blockers reach designated owners with strict 30-minute response windows.",
        tag = "Zero Latency",
        statValue = "68%",
        statLabel = "Tickets auto-routed"
    ),
    OnboardingPageData(
        title = "Track SLAs and escalate anywhere",
        subtitle = "Locked out of your workstation? Stay in total command from your phone with live SLA countdowns, push alerts, and one-tap approvals.",
        tag = "Mobile Command",
        statValue = "94%",
        statLabel = "SLA compliance target"
    )
)

@Composable
fun OnboardingScreen(
    onGetStartedClick: () -> Unit,
    onSignInClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val pagerState = rememberPagerState(pageCount = { OnboardingPages.size })
    val coroutineScope = rememberCoroutineScope()

    RouteDeskTheme(face = Face.Nero) {
        Column(
            modifier = modifier
                .fillMaxSize()
                .background(Brand.Nero)
                .statusBarsPadding()
                .navigationBarsPadding()
                .padding(horizontal = 24.dp, vertical = 16.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            // Header: Logo Mark and Skip
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(28.dp)
                            .clip(CircleShape)
                            .background(Brand.Orange)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "RouteDesk",
                        style = MaterialTheme.typography.titleLarge,
                        color = Brand.San
                    )
                }

                if (pagerState.currentPage < OnboardingPages.size - 1) {
                    RdButton(
                        text = "Skip",
                        onClick = onSignInClick,
                        variant = RdButtonVariant.Ghost,
                        size = RdButtonSize.Small
                    )
                }
            }

            // Carousel Content
            HorizontalPager(
                state = pagerState,
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .padding(vertical = 24.dp)
            ) { pageIndex ->
                val page = OnboardingPages[pageIndex]
                OnboardingPageContent(page = page)
            }

            // Bottom Section: Indicators and Action Buttons
            Column(
                modifier = Modifier.fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Page Indicator Dots
                Row(
                    modifier = Modifier.padding(bottom = 24.dp),
                    horizontalArrangement = Arrangement.Center
                ) {
                    repeat(OnboardingPages.size) { index ->
                        val isSelected = pagerState.currentPage == index
                        Box(
                            modifier = Modifier
                                .padding(horizontal = 4.dp)
                                .size(if (isSelected) 24.dp else 8.dp, 8.dp)
                                .clip(CircleShape)
                                .background(if (isSelected) Brand.Orange else Neutral.Nero700)
                        )
                    }
                }

                HatchedDivider(
                    modifier = Modifier.padding(bottom = 20.dp),
                    strokeColor = Neutral.Nero700
                )

                // Buttons
                if (pagerState.currentPage < OnboardingPages.size - 1) {
                    RdButton(
                        text = "Continue",
                        onClick = {
                            coroutineScope.launch {
                                pagerState.animateScrollToPage(pagerState.currentPage + 1)
                            }
                        },
                        variant = RdButtonVariant.Accent,
                        size = RdButtonSize.Large,
                        modifier = Modifier.fillMaxWidth()
                    )
                } else {
                    RdButton(
                        text = "Get Started",
                        onClick = onGetStartedClick,
                        variant = RdButtonVariant.Accent,
                        size = RdButtonSize.Large,
                        modifier = Modifier.fillMaxWidth()
                    )
                }

                Spacer(modifier = Modifier.height(10.dp))

                RdButton(
                    text = "I already have an account",
                    onClick = onSignInClick,
                    variant = RdButtonVariant.Link,
                    size = RdButtonSize.Small
                )
            }
        }
    }
}

@Composable
private fun OnboardingPageContent(page: OnboardingPageData) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(vertical = 12.dp)
    ) {
        CropFrame(
            modifier = Modifier.fillMaxSize(),
            tickLength = 16.dp,
            strokeWidth = 2.dp,
            color = Neutral.Nero700
        )

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(20.dp),
            verticalArrangement = Arrangement.Center
        ) {
            // Tag
            Box(
                modifier = Modifier
                    .clip(CircleShape)
                    .background(Brand.Orange.copy(alpha = 0.15f))
                    .padding(horizontal = 12.dp, vertical = 6.dp)
            ) {
                Text(
                    text = page.tag.uppercase(),
                    color = Brand.Orange,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
            }

            Spacer(modifier = Modifier.height(20.dp))

            // Headline
            Text(
                text = page.title,
                style = MaterialTheme.typography.displayMedium,
                color = Brand.San,
                lineHeight = 44.sp
            )

            Spacer(modifier = Modifier.height(16.dp))

            // Body
            Text(
                text = page.subtitle,
                style = MaterialTheme.typography.bodyLarge,
                color = Neutral.MutedDark,
                lineHeight = 24.sp
            )

            // Stat card if present
            if (page.statValue != null && page.statLabel != null) {
                Spacer(modifier = Modifier.height(32.dp))
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(12.dp))
                        .background(Neutral.Nero800)
                        .padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = page.statValue,
                        fontSize = 32.sp,
                        fontWeight = FontWeight.Bold,
                        color = Brand.Orange
                    )
                    Spacer(modifier = Modifier.width(14.dp))
                    Text(
                        text = page.statLabel,
                        style = MaterialTheme.typography.bodyMedium,
                        color = Brand.San
                    )
                }
            }
        }
    }
}
