package com.routedesk.network.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonObject

@Serializable
data class ApiError(
    val code: String,
    val message: String,
    val field: String? = null,
    val details: JsonObject? = null,
    @SerialName("request_id")
    val requestId: String? = null
)

class ApiException(
    val error: ApiError,
    val httpStatusCode: Int
) : Exception("${error.code}: ${error.message} (HTTP $httpStatusCode, RequestId: ${error.requestId})")
