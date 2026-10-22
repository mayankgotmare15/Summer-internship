package com.routedesk.network

import com.routedesk.network.api.RouteDeskApiService
import com.routedesk.network.interceptor.BearerAuthInterceptor
import com.routedesk.network.interceptor.RequestIdAndUserAgentInterceptor
import com.routedesk.network.model.ApiError
import com.routedesk.network.model.ApiException
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.ResponseBody
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.util.concurrent.TimeUnit

object ApiErrorParser {
    val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        coerceInputValues = true
    }

    fun parse(responseBody: ResponseBody?, httpCode: Int): ApiError {
        val bodyString = responseBody?.string()
        return if (!bodyString.isNullOrBlank()) {
            try {
                json.decodeFromString<ApiError>(bodyString)
            } catch (e: Exception) {
                ApiError(
                    code = "HTTP_$httpCode",
                    message = "Server returned error: $bodyString"
                )
            }
        } else {
            ApiError(
                code = "HTTP_$httpCode",
                message = "HTTP request failed with status code $httpCode"
            )
        }
    }
}

fun <T> Response<T>.unwrapOrThrow(): T {
    if (isSuccessful) {
        val body = body()
        if (body != null) {
            return body
        }
        if (code() == 204) {
            @Suppress("UNCHECKED_CAST")
            return Unit as T
        }
        throw IllegalStateException("Successful response body was null")
    } else {
        val error = ApiErrorParser.parse(errorBody(), code())
        throw ApiException(error, code())
    }
}

class NetworkClientFactory(
    private val baseUrl: String,
    private val tokenProvider: () -> String?,
    private val isDebug: Boolean = false
) {
    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = true
    }

    fun createOkHttpClient(): OkHttpClient {
        val builder = OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .addInterceptor(RequestIdAndUserAgentInterceptor())
            .addInterceptor(BearerAuthInterceptor(tokenProvider))

        if (isDebug) {
            val loggingInterceptor = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
                redactHeader("Authorization")
            }
            builder.addInterceptor(loggingInterceptor)
        }

        return builder.build()
    }

    fun createApiService(okHttpClient: OkHttpClient = createOkHttpClient()): RouteDeskApiService {
        val contentType = "application/json".toMediaType()
        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(okHttpClient)
            .addConverterFactory(json.asConverterFactory(contentType))
            .build()
            .create(RouteDeskApiService::class.java)
    }
}
