package com.routedesk.database.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

enum class OutboxActionType {
    CREATE_TICKET,
    ADD_MESSAGE,
    SUBMIT_FEEDBACK
}

enum class OutboxStatus {
    PENDING,
    SYNCING,
    FAILED
}

@Entity(
    tableName = "outbox",
    indices = [
        Index(value = ["status"]),
        Index(value = ["createdAtEpochMs"]),
        Index(value = ["idempotencyKey"], unique = true)
    ]
)
data class OutboxEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val idempotencyKey: String,
    val actionType: OutboxActionType,
    val payloadJson: String,
    val targetTicketId: String? = null,
    val createdAtEpochMs: Long,
    val retryCount: Int = 0,
    val lastError: String? = null,
    val status: OutboxStatus = OutboxStatus.PENDING
)
