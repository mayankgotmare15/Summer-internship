package com.routedesk.designsystem.component

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
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
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import com.routedesk.designsystem.theme.Brand
import com.routedesk.designsystem.theme.Neutral
import com.routedesk.designsystem.theme.Semantic

@Composable
fun RdTextField(
    value: String,
    onValueChange: (String) -> Unit,
    modifier: Modifier = Modifier,
    label: String? = null,
    placeholder: String? = null,
    helperText: String? = null,
    errorMessage: String? = null,
    maxCharacters: Int? = null,
    isDarkFace: Boolean = false,
    singleLine: Boolean = true,
    visualTransformation: VisualTransformation = VisualTransformation.None,
    keyboardOptions: KeyboardOptions = KeyboardOptions.Default,
    keyboardActions: KeyboardActions = KeyboardActions.Default,
    leadingIcon: (@Composable () -> Unit)? = null,
    trailingIcon: (@Composable () -> Unit)? = null
) {
    var isFocused by remember { mutableStateOf(false) }

    val backgroundColor = if (isDarkFace) Neutral.Nero800 else Brand.San
    val textColor = if (isDarkFace) Brand.San else Brand.Nero
    val placeholderColor = if (isDarkFace) Neutral.MutedDark else Neutral.MutedLight

    val isError = !errorMessage.isNullOrBlank()

    val borderColor = when {
        isError -> Semantic.Danger.fg
        isFocused -> Brand.Orange
        else -> Color.Transparent
    }

    Column(modifier = modifier.fillMaxWidth()) {
        label?.let {
            Text(
                text = it,
                style = MaterialTheme.typography.labelLarge.copy(fontWeight = FontWeight.Medium),
                color = if (isDarkFace) Brand.San else Brand.Nero,
                modifier = Modifier.padding(bottom = 6.dp)
            )
        }

        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(10.dp))
                .background(backgroundColor)
                .border(
                    width = if (isFocused || isError) 2.dp else 0.dp,
                    color = borderColor,
                    shape = RoundedCornerShape(10.dp)
                )
                .onFocusChanged { isFocused = it.isFocused }
                .padding(horizontal = 14.dp, vertical = if (singleLine) 14.dp else 12.dp)
        ) {
            Row(
                verticalAlignment = if (singleLine) Alignment.CenterVertically else Alignment.Top,
                modifier = Modifier.fillMaxWidth()
            ) {
                leadingIcon?.let {
                    it()
                    Spacer(modifier = Modifier.size(10.dp))
                }

                Box(modifier = Modifier.weight(1f)) {
                    if (value.isEmpty() && placeholder != null) {
                        Text(
                            text = placeholder,
                            style = MaterialTheme.typography.bodyLarge,
                            color = placeholderColor
                        )
                    }
                    BasicTextField(
                        value = value,
                        onValueChange = onValueChange,
                        modifier = Modifier.fillMaxWidth(),
                        textStyle = MaterialTheme.typography.bodyLarge.copy(color = textColor),
                        singleLine = singleLine,
                        visualTransformation = visualTransformation,
                        keyboardOptions = keyboardOptions,
                        keyboardActions = keyboardActions,
                        cursorBrush = SolidColor(Brand.Orange)
                    )
                }

                trailingIcon?.let {
                    Spacer(modifier = Modifier.size(8.dp))
                    it()
                }
            }
        }

        // Helper / Error / Counter row
        if (helperText != null || errorMessage != null || maxCharacters != null) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 4.dp, start = 4.dp, end = 4.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                if (errorMessage != null) {
                    Text(
                        text = errorMessage,
                        style = MaterialTheme.typography.bodySmall,
                        color = Semantic.Danger.fg,
                        modifier = Modifier.weight(1f)
                    )
                } else if (helperText != null) {
                    Text(
                        text = helperText,
                        style = MaterialTheme.typography.bodySmall,
                        color = if (isDarkFace) Neutral.MutedDark else Neutral.MutedLight,
                        modifier = Modifier.weight(1f)
                    )
                } else {
                    Spacer(modifier = Modifier.weight(1f))
                }

                maxCharacters?.let { max ->
                    Text(
                        text = "${value.length}/$max",
                        style = MaterialTheme.typography.labelSmall,
                        color = if (value.length > max) Semantic.Danger.fg else Neutral.MutedLight
                    )
                }
            }
        }
    }
}
