package com.routedesk.network.api

import com.routedesk.network.dto.AppConfigResponse
import com.routedesk.network.dto.ChangeEtaRequest
import com.routedesk.network.dto.DemoTokenRequest
import com.routedesk.network.dto.EscalateRequest
import com.routedesk.network.dto.EscalationResponse
import com.routedesk.network.dto.FeedbackRequest
import com.routedesk.network.dto.MessageDto
import com.routedesk.network.dto.PostMessageRequest
import com.routedesk.network.dto.PredictRequest
import com.routedesk.network.dto.PredictResponse
import com.routedesk.network.dto.ReassignRequest
import com.routedesk.network.dto.RefreshTokenRequest
import com.routedesk.network.dto.RegisterDeviceRequest
import com.routedesk.network.dto.ReopenRequest
import com.routedesk.network.dto.RequestInfoRequest
import com.routedesk.network.dto.RespondEscalationRequest
import com.routedesk.network.dto.TicketCreateRequest
import com.routedesk.network.dto.TicketCreatedResponse
import com.routedesk.network.dto.TicketDetailResponse
import com.routedesk.network.dto.TokenRequest
import com.routedesk.network.dto.TokenResponse
import com.routedesk.network.dto.UpdateStatusRequest
import com.routedesk.network.dto.UserMeDto
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface RouteDeskApiService {

    // --- Authentication ---
    @POST("auth/token")
    suspend fun login(
        @Body request: TokenRequest
    ): Response<TokenResponse>

    @POST("auth/demo-token")
    suspend fun loginDemo(
        @Body request: DemoTokenRequest
    ): Response<TokenResponse>

    @POST("auth/refresh")
    suspend fun refreshToken(
        @Body request: RefreshTokenRequest
    ): Response<TokenResponse>

    @GET("auth/me")
    suspend fun getCurrentUser(): Response<UserMeDto>

    @POST("auth/logout")
    suspend fun logout(
        @Body request: RefreshTokenRequest
    ): Response<Unit>

    @DELETE("auth/me")
    suspend fun deleteAccount(): Response<Unit>

    // --- Inference & ML ---
    @POST("predict")
    suspend fun predict(
        @Body request: PredictRequest
    ): Response<PredictResponse>

    @POST("feedback")
    suspend fun submitFeedback(
        @Body request: FeedbackRequest
    ): Response<Unit>

    // --- Tickets ---
    @POST("tickets")
    suspend fun createTicket(
        @Header("Idempotency-Key") idempotencyKey: String,
        @Body request: TicketCreateRequest
    ): Response<TicketCreatedResponse>

    @GET("tickets")
    suspend fun getTickets(
        @Query("view") view: String? = null,
        @Query("status") status: String? = null,
        @Query("cursor") cursor: String? = null,
        @Query("limit") limit: Int = 20
    ): Response<List<TicketDetailResponse>>

    @GET("tickets/{id}")
    suspend fun getTicketDetail(
        @Path("id") ticketId: String
    ): Response<TicketDetailResponse>

    @POST("tickets/{id}/messages")
    suspend fun postMessage(
        @Path("id") ticketId: String,
        @Header("Idempotency-Key") idempotencyKey: String,
        @Body request: PostMessageRequest
    ): Response<MessageDto>

    @POST("tickets/{id}/status")
    suspend fun updateStatus(
        @Path("id") ticketId: String,
        @Body request: UpdateStatusRequest
    ): Response<TicketDetailResponse>

    @POST("tickets/{id}/eta")
    suspend fun changeEta(
        @Path("id") ticketId: String,
        @Body request: ChangeEtaRequest
    ): Response<TicketDetailResponse>

    @POST("tickets/{id}/request-info")
    suspend fun requestInfo(
        @Path("id") ticketId: String,
        @Body request: RequestInfoRequest
    ): Response<TicketDetailResponse>

    @POST("tickets/{id}/reassign")
    suspend fun reassign(
        @Path("id") ticketId: String,
        @Body request: ReassignRequest
    ): Response<TicketDetailResponse>

    @POST("tickets/{id}/confirm")
    suspend fun confirmResolution(
        @Path("id") ticketId: String
    ): Response<TicketDetailResponse>

    @POST("tickets/{id}/reopen")
    suspend fun reopenTicket(
        @Path("id") ticketId: String,
        @Body request: ReopenRequest
    ): Response<TicketDetailResponse>

    // --- Escalations ---
    @POST("tickets/{id}/escalate")
    suspend fun escalateTicket(
        @Path("id") ticketId: String,
        @Body request: EscalateRequest
    ): Response<EscalationResponse>

    @POST("escalations/{id}/respond")
    suspend fun respondToEscalation(
        @Path("id") escalationId: String,
        @Body request: RespondEscalationRequest
    ): Response<EscalationResponse>

    // --- Notifications & Config ---
    @POST("devices")
    suspend fun registerDevice(
        @Body request: RegisterDeviceRequest
    ): Response<Unit>

    @DELETE("devices/{id}")
    suspend fun unregisterDevice(
        @Path("id") deviceId: String
    ): Response<Unit>

    @POST("notifications/read-all")
    suspend fun markAllNotificationsRead(): Response<Unit>

    @GET("app-config")
    suspend fun getAppConfig(): Response<AppConfigResponse>
}
