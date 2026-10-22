package com.routedesk.network.interceptor

import okhttp3.Interceptor
import okhttp3.Response
import java.util.UUID

class RequestIdAndUserAgentInterceptor(
    private val appVersion: String = "1.0.0",
    private val osVersion: String = "Android",
    private val deviceModel: String = "Generic"
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()
        val requestId = originalRequest.header("X-Request-ID") ?: UUID.randomUUID().toString()

        val newRequest = originalRequest.newBuilder()
            .header("X-Request-ID", requestId)
            .header("User-Agent", "RouteDesk-Android/$appVersion ($osVersion; $deviceModel)")
            .build()

        return chain.proceed(newRequest)
    }
}

class BearerAuthInterceptor(
    private val tokenProvider: () -> String?
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()
        val token = tokenProvider()

        val request = if (!token.isNullOrBlank() && originalRequest.header("Authorization") == null) {
            originalRequest.newBuilder()
                .header("Authorization", "Bearer $token")
                .build()
        } else {
            originalRequest
        }

        return chain.proceed(request)
    }
}
