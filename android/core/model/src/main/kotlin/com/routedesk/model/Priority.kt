package com.routedesk.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class Priority(val label: String, val level: Int) {
    @SerialName("critical")
    CRITICAL("Critical", 1),

    @SerialName("high")
    HIGH("High", 2),

    @SerialName("medium")
    MEDIUM("Medium", 3),

    @SerialName("low")
    LOW("Low", 4);

    companion object {
        fun fromString(value: String): Priority =
            entries.firstOrNull { it.name.equals(value, ignoreCase = true) } ?: MEDIUM
    }
}

@Serializable
enum class PrioritySource {
    @SerialName("model")
    MODEL,

    @SerialName("rule")
    RULE,

    @SerialName("agent")
    AGENT
}
