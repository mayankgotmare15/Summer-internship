package com.routedesk.data.repository

import android.content.Context
import com.routedesk.data.clock.ClockOffsetManager
import com.routedesk.data.sync.OutboxSyncWorker
import com.routedesk.database.dao.MessageDao
import com.routedesk.database.dao.OutboxDao
import com.routedesk.database.dao.TicketDao
import com.routedesk.database.entity.OutboxActionType
import com.routedesk.database.entity.OutboxEntity
import com.routedesk.database.entity.toDomain
import com.routedesk.database.entity.toEntity
import com.routedesk.model.Category
import com.routedesk.model.Message
import com.routedesk.model.Priority
import com.routedesk.model.Ticket
import com.routedesk.network.api.RouteDeskApiService
import com.routedesk.network.dto.FeedbackRequest
import com.routedesk.network.dto.PostMessageRequest
import com.routedesk.network.dto.PredictRequest
import com.routedesk.network.dto.PredictResponse
import com.routedesk.network.dto.ReopenRequest
import com.routedesk.network.dto.TicketCreateRequest
import com.routedesk.network.dto.TicketCreatedResponse
import com.routedesk.network.unwrapOrThrow
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.datetime.Clock
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.IOException
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

interface TicketRepository {
    fun observeAllTickets(): Flow<List<Ticket>>
    fun observeOpenTickets(): Flow<List<Ticket>>
    fun observeWaitingOnRequesterTickets(): Flow<List<Ticket>>
    fun observeTicketDetail(ticketId: String): Flow<Ticket?>
    fun observeMessages(ticketId: String): Flow<List<Message>>
    
    suspend fun refreshTickets(status: String? = null)
    suspend fun refreshTicketDetail(ticketId: String)
    suspend fun createTicket(
        subject: String,
        description: String,
        category: Category,
        priority: Priority,
        blockingTeam: Boolean = false
    ): Result<TicketCreatedResponse>
    suspend fun postMessage(
        ticketId: String,
        body: String,
        isInternal: Boolean = false
    ): Result<Unit>
    suspend fun predict(text: String): Result<PredictResponse>
    suspend fun submitFeedback(
        ticketId: String,
        originalPrediction: String,
        correctedCategory: String,
        confidence: Double
    )
    suspend fun confirmResolution(ticketId: String): Result<Unit>
    suspend fun reopenTicket(ticketId: String, reason: String, notes: String): Result<Unit>
}

@Singleton
class DefaultTicketRepository @Inject constructor(
    @ApplicationContext private val context: Context,
    private val apiService: RouteDeskApiService,
    private val ticketDao: TicketDao,
    private val messageDao: MessageDao,
    private val outboxDao: OutboxDao,
    private val clockOffsetManager: ClockOffsetManager
) : TicketRepository {

    private val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }

    override fun observeAllTickets(): Flow<List<Ticket>> =
        ticketDao.observeAllTickets().map { list -> list.map { it.toDomain() } }

    override fun observeOpenTickets(): Flow<List<Ticket>> =
        ticketDao.observeOpenTickets().map { list -> list.map { it.toDomain() } }

    override fun observeWaitingOnRequesterTickets(): Flow<List<Ticket>> =
        ticketDao.observeTicketsWaitingOnRequester().map { list -> list.map { it.toDomain() } }

    override fun observeTicketDetail(ticketId: String): Flow<Ticket?> =
        ticketDao.observeTicketById(ticketId).map { it?.toDomain() }

    override fun observeMessages(ticketId: String): Flow<List<Message>> =
        messageDao.observeMessagesForTicket(ticketId).map { list -> list.map { it.toDomain() } }

    override suspend fun refreshTickets(status: String?) {
        try {
            val response = apiService.getTickets(status = status)
            clockOffsetManager.updateOffsetFromDateHeader(response.headers()["Date"])
            if (response.isSuccessful && response.body() != null) {
                val tickets = response.body()!!.map { it.toDomain().toEntity() }
                ticketDao.upsertTickets(tickets)
            }
        } catch (_: Exception) {
            // Keep Room cached data on network failure
        }
    }

    override suspend fun refreshTicketDetail(ticketId: String) {
        try {
            val response = apiService.getTicketDetail(ticketId)
            clockOffsetManager.updateOffsetFromDateHeader(response.headers()["Date"])
            if (response.isSuccessful && response.body() != null) {
                val detail = response.body()!!.toDomain()
                ticketDao.upsertTicket(detail.toEntity())
                val messages = detail.messages.map { it.toEntity(ticketId) }
                messageDao.upsertMessages(messages)
            }
        } catch (_: Exception) {
            // Keep Room cached data on network failure
        }
    }

    override suspend fun createTicket(
        subject: String,
        description: String,
        category: Category,
        priority: Priority,
        blockingTeam: Boolean
    ): Result<TicketCreatedResponse> {
        val idempotencyKey = UUID.randomUUID().toString()
        val request = TicketCreateRequest(
            subject = subject,
            description = description,
            category = category.name.lowercase(),
            priority = priority.name.lowercase(),
            blockingTeam = blockingTeam
        )

        return try {
            val response = apiService.createTicket(
                idempotencyKey = idempotencyKey,
                request = request
            )
            clockOffsetManager.updateOffsetFromDateHeader(response.headers()["Date"])
            if (response.isSuccessful && response.body() != null) {
                val created = response.body()!!
                // Trigger background refresh of ticket list
                refreshTickets()
                Result.success(created)
            } else {
                Result.failure(Exception("Failed to create ticket: ${response.code()}"))
            }
        } catch (e: IOException) {
            // Offline: Queue to Room outbox with Idempotency Key!
            outboxDao.enqueue(
                OutboxEntity(
                    idempotencyKey = idempotencyKey,
                    actionType = OutboxActionType.CREATE_TICKET,
                    payloadJson = json.encodeToString(request),
                    createdAtEpochMs = System.currentTimeMillis()
                )
            )
            OutboxSyncWorker.schedule(context)

            // Synthetic response for offline UI feedback
            val syntheticResponse = TicketCreatedResponse(
                ticketId = "T-PENDING",
                ticketUuid = idempotencyKey,
                subject = subject,
                assignedTo = null,
                slaMinutes = 240,
                status = "queued"
            )
            Result.success(syntheticResponse)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun postMessage(
        ticketId: String,
        body: String,
        isInternal: Boolean
    ): Result<Unit> {
        val idempotencyKey = UUID.randomUUID().toString()
        val request = PostMessageRequest(body = body, isInternal = isInternal)

        return try {
            val response = apiService.postMessage(
                ticketId = ticketId,
                idempotencyKey = idempotencyKey,
                request = request
            )
            if (response.isSuccessful && response.body() != null) {
                val msg = response.body()!!.toDomain()
                messageDao.upsertMessage(msg.toEntity(ticketId))
                Result.success(Unit)
            } else {
                Result.failure(Exception("Failed to post message: ${response.code()}"))
            }
        } catch (e: IOException) {
            // Queue to outbox
            outboxDao.enqueue(
                OutboxEntity(
                    idempotencyKey = idempotencyKey,
                    actionType = OutboxActionType.ADD_MESSAGE,
                    targetTicketId = ticketId,
                    payloadJson = json.encodeToString(request),
                    createdAtEpochMs = System.currentTimeMillis()
                )
            )
            // Add optimistic local queued message
            messageDao.upsertMessage(
                com.routedesk.database.entity.MessageEntity(
                    id = "msg_opt_${System.currentTimeMillis()}",
                    ticketId = ticketId,
                    authorId = null,
                    authorName = "You",
                    kind = if (isInternal) "INTERNAL_NOTE" else "PUBLIC",
                    body = body,
                    createdAt = Clock.System.now(),
                    isQueued = true
                )
            )
            OutboxSyncWorker.schedule(context)
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun predict(text: String): Result<PredictResponse> {
        return try {
            val response = apiService.predict(PredictRequest(text = text)).unwrapOrThrow()
            Result.success(response)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun submitFeedback(
        ticketId: String,
        originalPrediction: String,
        correctedCategory: String,
        confidence: Double
    ) {
        val request = FeedbackRequest(
            ticketId = ticketId,
            predictedCategory = originalPrediction,
            correctedCategory = correctedCategory,
            confidence = confidence
        )
        try {
            apiService.submitFeedback(request)
        } catch (_: Exception) {
            outboxDao.enqueue(
                OutboxEntity(
                    idempotencyKey = UUID.randomUUID().toString(),
                    actionType = OutboxActionType.SUBMIT_FEEDBACK,
                    targetTicketId = ticketId,
                    payloadJson = json.encodeToString(request),
                    createdAtEpochMs = System.currentTimeMillis()
                )
            )
            OutboxSyncWorker.schedule(context)
        }
    }

    override suspend fun confirmResolution(ticketId: String): Result<Unit> {
        return try {
            apiService.confirmResolution(ticketId).unwrapOrThrow()
            refreshTicketDetail(ticketId)
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun reopenTicket(ticketId: String, reason: String, notes: String): Result<Unit> {
        return try {
            apiService.reopenTicket(ticketId, ReopenRequest(reason = reason, notes = notes)).unwrapOrThrow()
            refreshTicketDetail(ticketId)
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
