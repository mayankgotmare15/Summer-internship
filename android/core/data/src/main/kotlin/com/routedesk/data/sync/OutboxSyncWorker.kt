package com.routedesk.data.sync

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.routedesk.database.dao.MessageDao
import com.routedesk.database.dao.OutboxDao
import com.routedesk.database.dao.TicketDao
import com.routedesk.database.entity.OutboxActionType
import com.routedesk.database.entity.OutboxStatus
import com.routedesk.database.entity.toEntity
import com.routedesk.network.api.RouteDeskApiService
import com.routedesk.network.dto.FeedbackRequest
import com.routedesk.network.dto.PostMessageRequest
import com.routedesk.network.dto.TicketCreateRequest
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import kotlinx.serialization.json.Json
import java.io.IOException
import java.util.concurrent.TimeUnit

@HiltWorker
class OutboxSyncWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted params: WorkerParameters,
    private val outboxDao: OutboxDao,
    private val ticketDao: TicketDao,
    private val messageDao: MessageDao,
    private val apiService: RouteDeskApiService
) : CoroutineWorker(appContext, params) {

    private val json = Json { ignoreUnknownKeys = true }

    override suspend fun doWork(): Result {
        val pendingItems = outboxDao.getPendingItems()
        if (pendingItems.isEmpty()) {
            return Result.success()
        }

        var hasNetworkFailures = false

        for (item in pendingItems) {
            outboxDao.updateStatus(item.id, OutboxStatus.SYNCING, item.retryCount, null)

            try {
                when (item.actionType) {
                    OutboxActionType.CREATE_TICKET -> {
                        val request = json.decodeFromString<TicketCreateRequest>(item.payloadJson)
                        val response = apiService.createTicket(
                            idempotencyKey = item.idempotencyKey,
                            request = request
                        )
                        if (response.isSuccessful && response.body() != null) {
                            val created = response.body()!!
                            outboxDao.deleteById(item.id)
                            // Ticket will be refreshed via repository
                        } else {
                            val code = response.code()
                            if (code in 400..499 && code != 429) {
                                outboxDao.updateStatus(item.id, OutboxStatus.FAILED, item.retryCount + 1, "Client error: $code")
                            } else {
                                outboxDao.updateStatus(item.id, OutboxStatus.PENDING, item.retryCount + 1, "Server error: $code")
                                hasNetworkFailures = true
                            }
                        }
                    }

                    OutboxActionType.ADD_MESSAGE -> {
                        val ticketId = item.targetTicketId ?: continue
                        val request = json.decodeFromString<PostMessageRequest>(item.payloadJson)
                        val response = apiService.postMessage(
                            ticketId = ticketId,
                            idempotencyKey = item.idempotencyKey,
                            request = request
                        )
                        if (response.isSuccessful && response.body() != null) {
                            val msgDto = response.body()!!
                            messageDao.upsertMessage(msgDto.toDomain().toEntity(ticketId))
                            outboxDao.deleteById(item.id)
                        } else {
                            val code = response.code()
                            if (code in 400..499 && code != 429) {
                                outboxDao.updateStatus(item.id, OutboxStatus.FAILED, item.retryCount + 1, "Client error: $code")
                            } else {
                                outboxDao.updateStatus(item.id, OutboxStatus.PENDING, item.retryCount + 1, "Server error: $code")
                                hasNetworkFailures = true
                            }
                        }
                    }

                    OutboxActionType.SUBMIT_FEEDBACK -> {
                        val request = json.decodeFromString<FeedbackRequest>(item.payloadJson)
                        val response = apiService.submitFeedback(request)
                        if (response.isSuccessful) {
                            outboxDao.deleteById(item.id)
                        } else {
                            val code = response.code()
                            if (code in 400..499 && code != 429) {
                                outboxDao.updateStatus(item.id, OutboxStatus.FAILED, item.retryCount + 1, "Client error: $code")
                            } else {
                                outboxDao.updateStatus(item.id, OutboxStatus.PENDING, item.retryCount + 1, "Server error: $code")
                                hasNetworkFailures = true
                            }
                        }
                    }
                }
            } catch (e: IOException) {
                outboxDao.updateStatus(item.id, OutboxStatus.PENDING, item.retryCount + 1, e.message)
                hasNetworkFailures = true
            } catch (e: Exception) {
                outboxDao.updateStatus(item.id, OutboxStatus.FAILED, item.retryCount + 1, e.message)
            }
        }

        return if (hasNetworkFailures) {
            Result.retry()
        } else {
            Result.success()
        }
    }

    companion object {
        const val WORK_NAME = "RouteDeskOutboxSync"

        fun schedule(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()

            val request = OneTimeWorkRequestBuilder<OutboxSyncWorker>()
                .setConstraints(constraints)
                .setBackoffCriteria(
                    BackoffPolicy.EXPONENTIAL,
                    10,
                    TimeUnit.SECONDS
                )
                .build()

            WorkManager.getInstance(context).enqueueUniqueWork(
                WORK_NAME,
                ExistingWorkPolicy.REPLACE,
                request
            )
        }
    }
}
