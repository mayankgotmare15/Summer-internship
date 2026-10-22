package com.routedesk.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class Decision {
    @SerialName("auto_route")
    AUTO_ROUTE,

    @SerialName("human_review")
    HUMAN_REVIEW
}

@Serializable
enum class ReviewReason {
    @SerialName("low_confidence")
    LOW_CONFIDENCE,

    @SerialName("multi_issue")
    MULTI_ISSUE,

    @SerialName("miscellaneous")
    MISCELLANEOUS,

    @SerialName("model_unavailable")
    MODEL_UNAVAILABLE
}

@Serializable
data class ScoredCategory(
    val category: String,
    val score: Double
)

@Serializable
data class Prediction(
    val category: Category,
    @SerialName("category_confidence")
    val categoryConfidence: Double,
    @SerialName("top_categories")
    val topCategories: List<ScoredCategory>,
    val priority: Priority,
    @SerialName("priority_confidence")
    val priorityConfidence: Double,
    @SerialName("priority_source")
    val prioritySource: PrioritySource,
    val decision: Decision,
    @SerialName("review_reason")
    val reviewReason: ReviewReason? = null,
    @SerialName("routed_team")
    val routedTeam: TeamRef,
    val threshold: Double = 0.70,
    @SerialName("prediction_id")
    val predictionId: String,
    @SerialName("latency_ms")
    val latencyMs: Long = 0,
    @SerialName("top_keywords")
    val topKeywords: List<String> = emptyList()
)
