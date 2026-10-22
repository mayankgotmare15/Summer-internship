package com.routedesk.feature.intake

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
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
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Neutral
import com.routedesk.designsystem.theme.PillShape
import com.routedesk.designsystem.theme.softShadow
import com.routedesk.model.Category

@Composable
fun ChatIntakeView(
    uiState: IntakeUiState,
    onSendMessage: (String) -> Unit,
    onLooksRight: () -> Unit,
    onNotQuite: () -> Unit,
    onSubmitTicket: () -> Unit,
    onDeflected: () -> Unit,
    modifier: Modifier = Modifier
) {
    var inputText by remember { mutableStateOf("") }
    val listState = rememberLazyListState()

    LaunchedEffect(uiState.chatMessages.size, uiState.prediction) {
        listState.animateScrollToItem(listState.layoutInfo.totalItemsCount.coerceAtLeast(1) - 1)
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .imePadding()
    ) {
        LazyColumn(
            state = listState,
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
            contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            items(uiState.chatMessages, key = { it.id }) { msg ->
                ChatBubble(message = msg)
            }

            if (uiState.isPredicting) {
                item {
                    TypingIndicator()
                }
            }

            uiState.prediction?.let { pred ->
                item {
                    PredictionCard(
                        prediction = pred,
                        onLooksRightClick = onLooksRight,
                        onNotQuiteClick = onNotQuite
                    )
                }

                item {
                    FaqDeflectionView(
                        category = uiState.category,
                        onDeflected = onDeflected
                    )
                }

                item {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 8.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        RdButton(
                            text = "Submit Ticket (${uiState.category.name.lowercase()}) →",
                            onClick = onSubmitTicket,
                            variant = RdButtonVariant.Accent,
                            size = RdButtonSize.Medium,
                            isLoading = uiState.isSubmitting
                        )
                    }
                }
            }
        }

        // Composer Bar
        ChatComposer(
            text = inputText,
            onTextChanged = { inputText = it },
            onSendClick = {
                if (inputText.isNotBlank()) {
                    onSendMessage(inputText.trim())
                    inputText = ""
                }
            },
            enabled = !uiState.isSubmitting
        )
    }
}

@Composable
private fun ChatBubble(message: ChatMessageItem) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (message.isAssistant) Arrangement.Start else Arrangement.End,
        verticalAlignment = Alignment.Top
    ) {
        if (message.isAssistant) {
            Box(
                modifier = Modifier
                    .size(32.dp)
                    .clip(CircleShape)
                    .background(Brand.Nero),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "AI",
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.Bold,
                    color = Brand.Orange,
                    fontSize = 11.sp
                )
            }
            Spacer(modifier = Modifier.width(8.dp))
        }

        val bubbleShape = if (message.isAssistant) {
            RoundedCornerShape(topStart = 4.dp, topEnd = 16.dp, bottomEnd = 16.dp, bottomStart = 16.dp)
        } else {
            RoundedCornerShape(topStart = 16.dp, topEnd = 4.dp, bottomEnd = 16.dp, bottomStart = 16.dp)
        }

        val bgColor = if (message.isAssistant) Neutral.Paper else Brand.Nero
        val textColor = if (message.isAssistant) Brand.Nero else Brand.San

        Box(
            modifier = Modifier
                .widthIn(max = 280.dp)
                .softShadow(elevation = 2.dp, shape = bubbleShape)
                .clip(bubbleShape)
                .background(bgColor)
                .padding(horizontal = 14.dp, vertical = 12.dp)
        ) {
            Text(
                text = message.text,
                style = MaterialTheme.typography.bodyLarge,
                color = textColor
            )
        }
    }
}

@Composable
private fun TypingIndicator() {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier.padding(start = 40.dp)
    ) {
        CircularProgressIndicator(
            modifier = Modifier.size(16.dp),
            strokeWidth = 2.dp,
            color = Brand.Orange
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = "Analyzing with RouteDesk ML...",
            style = MaterialTheme.typography.labelSmall,
            color = Neutral.MutedLight
        )
    }
}

@Composable
private fun ChatComposer(
    text: String,
    onTextChanged: (String) -> Unit,
    onSendClick: () -> Unit,
    enabled: Boolean
) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(Brand.San)
            .navigationBarsPadding()
            .padding(horizontal = 16.dp, vertical = 8.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clip(PillShape)
                .background(Neutral.Paper)
                .padding(horizontal = 12.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            TextField(
                value = text,
                onValueChange = onTextChanged,
                placeholder = {
                    Text(
                        text = "e.g. My GlobalProtect VPN won't connect...",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Neutral.MutedLight
                    )
                },
                modifier = Modifier.weight(1f),
                colors = TextFieldDefaults.colors(
                    focusedContainerColor = Color.Transparent,
                    unfocusedContainerColor = Color.Transparent,
                    focusedIndicatorColor = Color.Transparent,
                    unfocusedIndicatorColor = Color.Transparent
                ),
                singleLine = false,
                maxLines = 4,
                enabled = enabled
            )

            IconButton(
                onClick = onSendClick,
                enabled = enabled && text.isNotBlank(),
                modifier = Modifier
                    .size(40.dp)
                    .clip(CircleShape)
                    .background(if (text.isNotBlank()) Brand.Orange else Neutral.LineLight)
            ) {
                Icon(
                    imageVector = Icons.AutoMirrored.Filled.Send,
                    contentDescription = "Send",
                    tint = if (text.isNotBlank()) Brand.Nero else Neutral.MutedLight,
                    modifier = Modifier.size(20.dp)
                )
            }
        }
    }
}

private fun Modifier.widthIn(max: androidx.compose.ui.unit.Dp): Modifier =
    this.then(androidx.compose.foundation.layout.widthIn(max = max))
