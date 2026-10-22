package com.routedesk.database.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey
import com.routedesk.model.Notification
import com.routedesk.model.NotificationKind
import kotlinx.datetime.Instant

@Entity(
    tableName = "notifications",
    indices = [
        Index(value = ["ticketId"]),
        Index(value = ["createdAt"]),
        Index(value = ["readAt"])
    ]
)
data class NotificationEntity(
    @PrimaryKey
    val id: String,
    val kind: String,
    val title: String,
    val body: String,
    val ticketId: String?,
    val deepLink: String?,
    val readAt: Instant?,
    val createdAt: Instant
)

fun NotificationEntity.toDomain(): Notification = Notification(
    id = id,
    kind = runCatching { NotificationKind.valueOf(kind) }.getOrDefault(NotificationKind.TICKET_ASSIGNED),
    title = title,
    body = body,
    ticketId = ticketId,
    deepLink = deepLink,
    readAt = readAt,
    createdAt = createdAt
)

fun Notification.toEntity(): NotificationEntity = NotificationEntity(
    id = id,
    kind = kind.name,
    title = title,
    body = body,
    ticketId = ticketId,
    deepLink = deepLink,
    readAt = readAt,
    createdAt = createdAt
)
