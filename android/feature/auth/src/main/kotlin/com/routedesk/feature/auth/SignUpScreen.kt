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
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.routedesk.designsystem.component.RdButton
import com.routedesk.designsystem.component.RdButtonSize
import com.routedesk.designsystem.component.RdButtonVariant
import com.routedesk.designsystem.component.RdTextField
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Face
import com.routedesk.designsystem.theme.Neutral
import com.routedesk.designsystem.theme.RouteDeskTheme
import com.routedesk.designsystem.theme.Semantic

@Composable
fun SignUpScreen(
    onSignUpSuccess: () -> Unit,
    onNavigateToSignIn: () -> Unit,
    modifier: Modifier = Modifier
) {
    var name by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var department by remember { mutableStateOf("Engineering") }
    var password by remember { mutableStateOf("") }
    var confirmPassword by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }

    val isFormValid = name.isNotBlank() &&
            email.contains("@") &&
            password.length >= 6 &&
            password == confirmPassword

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
                    .padding(horizontal = 24.dp, vertical = 20.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Header
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.Start
                ) {
                    Text(
                        text = "Create your account",
                        style = MaterialTheme.typography.headlineMedium,
                        color = Brand.San
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "Sign up as an employee requester to raise and track tickets",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Neutral.MutedDark
                    )
                }

                Spacer(modifier = Modifier.height(24.dp))

                // Full Name
                RdTextField(
                    value = name,
                    onValueChange = { name = it; errorMessage = null },
                    label = "Full Name",
                    placeholder = "Alex Chen",
                    isDarkFace = true,
                    singleLine = true
                )

                Spacer(modifier = Modifier.height(16.dp))

                // Work Email
                RdTextField(
                    value = email,
                    onValueChange = { email = it; errorMessage = null },
                    label = "Work Email",
                    placeholder = "alex@company.com",
                    isDarkFace = true,
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email)
                )

                Spacer(modifier = Modifier.height(16.dp))

                // Department
                RdTextField(
                    value = department,
                    onValueChange = { department = it },
                    label = "Department",
                    placeholder = "e.g. Engineering, Sales, HR",
                    isDarkFace = true,
                    singleLine = true
                )

                Spacer(modifier = Modifier.height(16.dp))

                // Password
                RdTextField(
                    value = password,
                    onValueChange = { password = it; errorMessage = null },
                    label = "Password",
                    placeholder = "At least 6 characters",
                    isDarkFace = true,
                    singleLine = true,
                    visualTransformation = PasswordVisualTransformation(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password)
                )

                Spacer(modifier = Modifier.height(16.dp))

                // Confirm Password
                RdTextField(
                    value = confirmPassword,
                    onValueChange = { confirmPassword = it; errorMessage = null },
                    label = "Confirm Password",
                    placeholder = "Re-enter your password",
                    isDarkFace = true,
                    singleLine = true,
                    visualTransformation = PasswordVisualTransformation(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                    errorMessage = if (confirmPassword.isNotEmpty() && password != confirmPassword) {
                        "Passwords do not match"
                    } else null
                )

                errorMessage?.let {
                    Text(
                        text = it,
                        style = MaterialTheme.typography.bodySmall,
                        color = Semantic.Danger.fg,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 10.dp)
                    )
                }

                Spacer(modifier = Modifier.height(28.dp))

                // Sign Up Button
                RdButton(
                    text = "Create Account",
                    onClick = {
                        isLoading = true
                        onSignUpSuccess()
                    },
                    variant = if (isFormValid) RdButtonVariant.Accent else RdButtonVariant.Primary,
                    size = RdButtonSize.Large,
                    enabled = isFormValid,
                    isLoading = isLoading,
                    modifier = Modifier.fillMaxWidth()
                )

                Spacer(modifier = Modifier.height(20.dp))

                // Footer: Sign In Link
                Row(
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Already have an account? ",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Neutral.MutedDark
                    )
                    Text(
                        text = "Sign In",
                        style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.Bold),
                        color = Brand.Orange,
                        modifier = Modifier.clickable(onClick = onNavigateToSignIn)
                    )
                }
            }
        }
    }
}
