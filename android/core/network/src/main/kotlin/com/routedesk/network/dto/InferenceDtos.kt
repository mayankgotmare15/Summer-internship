package com.routedesk.network.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class PredictRequest(
    val text: String
)

@Serializable
data class ScoredCategoryDto(
    val category: String,
    val score: Double
)

@Serializable
data class TeamRefDto(
    val code: String,
    val name: String
)

@Serializable
data class PredictResponse(
    val category: String,
    @SerialName("category_confidence")
    val categoryConfidence: Double,
    @SerialName("top_categories")
    val topCategories: List<ScoredCategoryDto>,
    val priority: String,
    @SerialName("priority_confidence")
    val priorityConfidence: Double,
    @SerialName("priority_source")
    val prioritySource: String,
    val decision: String,
    @SerialName("review_reason")
    val reviewReason: String? = null,
    @SerialName("routed_team")
    val routedTeam: TeamRefDto,
    val threshold: Double = 0.70,
    @SerialName("model_version")
    val modelVersion: String = "v1",
    @SerialName("prediction_id")
    val predictionId: String,
    @SerialName("latency_ms")
    val latencyMs: Long = 0,
    @SerialName("top_keywords")
    val topKeywords: List<String> = emptyList()
)

@Serializable
data class FeedbackRequest(
    @SerialName("prediction_id")
    val predictionId: String? = null,
    @SerialName("ticket_id")
    val ticketId: String? = null,
    val kind: String,
    @SerialName("predicted_category")
    val predictedCategory: String? = null,
    @SerialName("corrected_category")
    val correctedCategory: String? = null,
    @SerialName("predicted_priority")
    val predictedPriority: String? = null,
    @SerialName("corrected_priority")
    val correctedPriority: String? = null,
    val notes: String? = null
)
