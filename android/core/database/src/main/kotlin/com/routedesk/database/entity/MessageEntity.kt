package com.routedesk.database.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey
import com.routedesk.model.Message
import com.routedesk.model.MessageKind
import kotlinx.datetime.Instant

@Entity(
    tableName = "messages",
    indices = [
        Index(value = ["ticketId"]),
        Index(value = ["createdAt"])
    ]
)
data class MessageEntity(
    @PrimaryKey
    val id: String,
    val ticketId: String,
    val authorId: String?,
    val authorName: String?,
    val kind: String,
    val body: String,
    val createdAt: Instant,
    val isQueued: Boolean
)

fun MessageEntity.toDomain(): Message = Message(
    id = id,
    authorId = authorId,
    authorName = authorName,
    kind = runCatching { MessageKind.valueOf(kind) }.getOrDefault(MessageKind.PUBLIC),
    body = body,
    createdAt = createdAt,
    isQueued = isQueued
)

fun Message.toEntity(ticketId: String): MessageEntity = MessageEntity(
    id = id,
    ticketId = ticketId,
    authorId = authorId,
    authorName = authorName,
    kind = kind.name,
    body = body,
    createdAt = createdAt,
    isQueued = isQueued
)
