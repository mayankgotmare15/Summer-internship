package com.routedesk.feature.auth

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.MailOutline
import androidx.compose.material3.Divider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.routedesk.designsystem.component.HatchedDivider
import com.routedesk.designsystem.component.RdButton
import com.routedesk.designsystem.component.RdButtonSize
import com.routedesk.designsystem.component.RdButtonVariant
import com.routedesk.designsystem.component.RdTextField
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Face
import com.routedesk.designsystem.theme.Neutral
import com.routedesk.designsystem.theme.RouteDeskTheme
import com.routedesk.designsystem.theme.Semantic
import com.routedesk.model.Role

@Composable
fun SignInScreen(
    onSignInSuccess: () -> Unit,
    onNavigateToSignUp: () -> Unit,
    onNavigateToForgotPassword: () -> Unit,
    modifier: Modifier = Modifier
) {
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var isPasswordVisible by remember { mutableStateOf(false) }
    var isDemoSheetOpen by remember { mutableStateOf(false) }
    var isLoading by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    var isColdStarting by remember { mutableStateOf(false) }

    val isFormValid = email.isNotBlank() && password.length >= 6
    val scrollState = rememberScrollState()

    RouteDeskTheme(face = Face.Nero) {
        Box(
            modifier = modifier
                .fillMaxSize()
                .background(Brand.Nero)
                .statusBarsPadding()
                .navigationBarsPadding()
                .imePadding()
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(scrollState)
                    .padding(horizontal = 24.dp, vertical = 16.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Cold-Start Alert Banner if server is warming up
                ColdStartBanner(
                    isVisible = isColdStarting,
                    modifier = Modifier.padding(bottom = 12.dp)
                )

                // Hero Card with Brand Gradient
                HeroCard()

                Spacer(modifier = Modifier.height(24.dp))

                // Welcome Header
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.Start
                ) {
                    Text(
                        text = "Welcome back!",
                        style = MaterialTheme.typography.headlineMedium,
                        color = Brand.San
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "Sign in to resolve or track IT tickets",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Neutral.MutedDark
                    )
                }

                Spacer(modifier = Modifier.height(24.dp))

                // Email input
                RdTextField(
                    value = email,
                    onValueChange = { email = it; errorMessage = null },
                    label = "Work Email",
                    placeholder = "you@company.com",
                    isDarkFace = true,
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                    leadingIcon = {
                        Icon(
                            imageVector = Icons.Default.MailOutline,
                            contentDescription = null,
                            tint = Neutral.MutedDark,
                            modifier = Modifier.size(20.dp)
                        )
                    }
                )

                Spacer(modifier = Modifier.height(16.dp))

                // Password input
                RdTextField(
                    value = password,
                    onValueChange = { password = it; errorMessage = null },
                    label = "Password",
                    placeholder = "Enter your password",
                    isDarkFace = true,
                    singleLine = true,
                    visualTransformation = if (isPasswordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                    leadingIcon = {
                        Icon(
                            imageVector = Icons.Default.Lock,
                            contentDescription = null,
                            tint = Neutral.MutedDark,
                            modifier = Modifier.size(20.dp)
                        )
                    },
                    trailingIcon = {
                        Text(
                            text = if (isPasswordVisible) "HIDE" else "SHOW",
                            style = MaterialTheme.typography.labelSmall,
                            fontWeight = FontWeight.Bold,
                            color = Brand.Orange,
                            modifier = Modifier.clickable { isPasswordVisible = !isPasswordVisible }
                        )
                    }
                )

                // Error Message if any
                errorMessage?.let {
                    Text(
                        text = it,
                        style = MaterialTheme.typography.bodySmall,
                        color = Semantic.Danger.fg,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 8.dp)
                    )
                }

                // Forgot Password link
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 10.dp),
                    horizontalArrangement = Arrangement.End
                ) {
                    Text(
                        text = "Forgot password?",
                        style = MaterialTheme.typography.bodySmall,
                        color = Brand.Orange,
                        modifier = Modifier.clickable(onClick = onNavigateToForgotPassword)
                    )
                }

                Spacer(modifier = Modifier.height(24.dp))

                // Sign In Button
                RdButton(
                    text = "Sign In",
                    onClick = {
                        isLoading = true
                        // Simulated login success
                        onSignInSuccess()
                    },
                    variant = if (isFormValid) RdButtonVariant.Accent else RdButtonVariant.Primary,
                    size = RdButtonSize.Large,
                    enabled = isFormValid,
                    isLoading = isLoading,
                    modifier = Modifier.fillMaxWidth()
                )

                Spacer(modifier = Modifier.height(20.dp))

                // "or" divider with label
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .height(1.dp)
                            .background(Neutral.Nero700)
                    )
                    Text(
                        text = "OR",
                        style = MaterialTheme.typography.labelSmall,
                        color = Neutral.MutedDark,
                        modifier = Modifier.padding(horizontal = 12.dp)
                    )
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .height(1.dp)
                            .background(Neutral.Nero700)
                    )
                }

                Spacer(modifier = Modifier.height(20.dp))

                // Demo Quick Login Button
                RdButton(
                    text = "Demo Role Quick Login",
                    onClick = { isDemoSheetOpen = true },
                    variant = RdButtonVariant.Secondary,
                    size = RdButtonSize.Large,
                    modifier = Modifier.fillMaxWidth()
                )

                Spacer(modifier = Modifier.height(28.dp))

                // Footer: Sign Up Link
                Row(
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "New here? ",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Neutral.MutedDark
                    )
                    Text(
                        text = "Sign Up",
                        style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.Bold),
                        color = Brand.Orange,
                        modifier = Modifier.clickable(onClick = onNavigateToSignUp)
                    )
                }
            }

            // Demo Role Sheet
            if (isDemoSheetOpen) {
                DemoRolePickerSheet(
                    onRoleSelected = { role ->
                        isDemoSheetOpen = false
                        onSignInSuccess()
                    },
                    onDismiss = { isDemoSheetOpen = false }
                )
            }
        }
    }
}

@Composable
private fun HeroCard() {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(160.dp)
            .clip(RoundedCornerShape(20.dp))
            .background(
                Brush.linearGradient(
                    colors = listOf(Brand.Orange, Brand.Concrete, Brand.Nero)
                )
            )
            .padding(16.dp)
    ) {
        Column(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Box(
                    modifier = Modifier
                        .clip(CircleShape)
                        .background(Brand.Nero.copy(alpha = 0.4f))
                        .padding(horizontal = 10.dp, vertical = 4.dp)
                ) {
                    Text(
                        text = "Auto-routed",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = Brand.San
                    )
                }

                Box(
                    modifier = Modifier
                        .clip(CircleShape)
                        .background(Brand.Nero.copy(alpha = 0.4f))
                        .padding(horizontal = 10.dp, vertical = 4.dp)
                ) {
                    Text(
                        text = "SLA on track",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = Brand.San
                    )
                }
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.Bottom,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column {
                    Text(
                        text = "RouteDesk AI",
                        fontSize = 22.sp,
                        fontWeight = FontWeight.Bold,
                        color = Brand.San
                    )
                    Text(
                        text = "IT Ticket Auto-Routing & Priority Engine",
                        fontSize = 12.sp,
                        color = Brand.San.copy(alpha = 0.8f)
                    )
                }

                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(10.dp))
                        .background(Neutral.Paper.copy(alpha = 0.2f))
                        .padding(horizontal = 12.dp, vertical = 8.dp)
                ) {
                    Text(
                        text = "94% SLA",
                        fontWeight = FontWeight.Bold,
                        fontSize = 14.sp,
                        color = Brand.San
                    )
                }
            }
        }
    }
}
