package com.routedesk.database.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey
import com.routedesk.model.AllowedAction
import com.routedesk.model.Category
import com.routedesk.model.Decision
import com.routedesk.model.EscalationEligibility
import com.routedesk.model.EscalationLevel
import com.routedesk.model.MemberRef
import com.routedesk.model.Priority
import com.routedesk.model.PrioritySource
import com.routedesk.model.ReviewReason
import com.routedesk.model.SlaState
import com.routedesk.model.TeamRef
import com.routedesk.model.Ticket
import com.routedesk.model.TicketStatus
import kotlinx.datetime.Instant

@Entity(
    tableName = "tickets",
    indices = [
        Index(value = ["status"]),
        Index(value = ["priority"]),
        Index(value = ["category"]),
        Index(value = ["createdAt"])
    ]
)
data class TicketEntity(
    @PrimaryKey
    val id: String,
    val ticketUuid: String,
    val subject: String,
    val description: String,
    val category: Category,
    val priority: Priority,
    val prioritySource: String,
    val status: TicketStatus,
    val decision: Decision,
    val reviewReason: String?,
    val team: TeamRef,
    val assignee: MemberRef?,
    val isEscalated: Boolean,
    val escalationLevel: EscalationLevel,
    val canEscalate: Boolean,
    val escalationEligibility: EscalationEligibility?,
    val allowedActions: List<AllowedAction>,
    val firstResponseDue: Instant?,
    val resolutionDue: Instant?,
    val firstRespondedAt: Instant?,
    val slaState: SlaState,
    val usedPct: Double,
    val version: Long,
    val isSending: Boolean,
    val createdAt: Instant,
    val updatedAt: Instant?
)

fun TicketEntity.toDomain(): Ticket = Ticket(
    id = id,
    ticketUuid = ticketUuid,
    subject = subject,
    description = description,
    category = category,
    priority = priority,
    prioritySource = runCatching { PrioritySource.valueOf(prioritySource) }.getOrDefault(PrioritySource.MODEL),
    status = status,
    decision = decision,
    reviewReason = reviewReason?.let { runCatching { ReviewReason.valueOf(it) }.getOrNull() },
    team = team,
    assignee = assignee,
    isEscalated = isEscalated,
    escalationLevel = escalationLevel,
    canEscalate = canEscalate,
    escalationEligibility = escalationEligibility,
    allowedActions = allowedActions,
    firstResponseDue = firstResponseDue,
    resolutionDue = resolutionDue,
    firstRespondedAt = firstRespondedAt,
    slaState = slaState,
    usedPct = usedPct,
    messages = emptyList(),
    attachments = emptyList(),
    etaHistory = emptyList(),
    version = version,
    isSending = isSending,
    createdAt = createdAt,
    updatedAt = updatedAt
)

fun Ticket.toEntity(): TicketEntity = TicketEntity(
    id = id,
    ticketUuid = ticketUuid,
    subject = subject,
    description = description,
    category = category,
    priority = priority,
    prioritySource = prioritySource.name,
    status = status,
    decision = decision,
    reviewReason = reviewReason?.name,
    team = team,
    assignee = assignee,
    isEscalated = isEscalated,
    escalationLevel = escalationLevel,
    canEscalate = canEscalate,
    escalationEligibility = escalationEligibility,
    allowedActions = allowedActions,
    firstResponseDue = firstResponseDue,
    resolutionDue = resolutionDue,
    firstRespondedAt = firstRespondedAt,
    slaState = slaState,
    usedPct = usedPct,
    version = version,
    isSending = isSending,
    createdAt = createdAt,
    updatedAt = updatedAt
)
