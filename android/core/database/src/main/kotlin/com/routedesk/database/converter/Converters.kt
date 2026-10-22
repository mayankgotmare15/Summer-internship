package com.routedesk.database.converter

import androidx.room.TypeConverter
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
import com.routedesk.model.TicketStatus
import kotlinx.datetime.Instant
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

class Converters {
    private val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }

    @TypeConverter
    fun fromInstant(instant: Instant?): Long? = instant?.toEpochMilliseconds()

    @TypeConverter
    fun toInstant(epochMs: Long?): Instant? = epochMs?.let { Instant.fromEpochMilliseconds(it) }

    @TypeConverter
    fun fromCategory(category: Category?): String? = category?.name

    @TypeConverter
    fun toCategory(name: String?): Category? = name?.let {
        runCatching { Category.valueOf(it) }.getOrDefault(Category.OTHER)
    }

    @TypeConverter
    fun fromPriority(priority: Priority?): String? = priority?.name

    @TypeConverter
    fun toPriority(name: String?): Priority? = name?.let {
        runCatching { Priority.valueOf(it) }.getOrDefault(Priority.MEDIUM)
    }

    @TypeConverter
    fun fromStatus(status: TicketStatus?): String? = status?.name

    @TypeConverter
    fun toStatus(name: String?): TicketStatus? = name?.let {
        runCatching { TicketStatus.valueOf(it) }.getOrDefault(TicketStatus.OPEN)
    }

    @TypeConverter
    fun fromSlaState(state: SlaState?): String? = state?.name

    @TypeConverter
    fun toSlaState(name: String?): SlaState? = name?.let {
        runCatching { SlaState.valueOf(it) }.getOrDefault(SlaState.ON_TRACK)
    }

    @TypeConverter
    fun fromDecision(decision: Decision?): String? = decision?.name

    @TypeConverter
    fun toDecision(name: String?): Decision? = name?.let {
        runCatching { Decision.valueOf(it) }.getOrDefault(Decision.AUTO_ROUTE)
    }

    @TypeConverter
    fun fromEscalationLevel(level: EscalationLevel?): String? = level?.name

    @TypeConverter
    fun toEscalationLevel(name: String?): EscalationLevel? = name?.let {
        runCatching { EscalationLevel.valueOf(it) }.getOrDefault(EscalationLevel.E1)
    }

    @TypeConverter
    fun fromAllowedActions(actions: List<AllowedAction>?): String? =
        actions?.let { json.encodeToString(it) }

    @TypeConverter
    fun toAllowedActions(jsonString: String?): List<AllowedAction>? =
        jsonString?.let { runCatching { json.decodeFromString<List<AllowedAction>>(it) }.getOrDefault(emptyList()) }

    @TypeConverter
    fun fromTeamRef(team: TeamRef?): String? = team?.let { json.encodeToString(it) }

    @TypeConverter
    fun toTeamRef(jsonString: String?): TeamRef? =
        jsonString?.let { runCatching { json.decodeFromString<TeamRef>(it) }.getOrNull() }

    @TypeConverter
    fun fromMemberRef(member: MemberRef?): String? = member?.let { json.encodeToString(it) }

    @TypeConverter
    fun toMemberRef(jsonString: String?): MemberRef? =
        jsonString?.let { runCatching { json.decodeFromString<MemberRef>(it) }.getOrNull() }

    @TypeConverter
    fun fromEligibility(eligibility: EscalationEligibility?): String? =
        eligibility?.let { json.encodeToString(it) }

    @TypeConverter
    fun toEligibility(jsonString: String?): EscalationEligibility? =
        jsonString?.let { runCatching { json.decodeFromString<EscalationEligibility>(it) }.getOrNull() }

    @TypeConverter
    fun fromOutboxActionType(action: com.routedesk.database.entity.OutboxActionType?): String? = action?.name

    @TypeConverter
    fun toOutboxActionType(name: String?): com.routedesk.database.entity.OutboxActionType? = name?.let {
        runCatching { com.routedesk.database.entity.OutboxActionType.valueOf(it) }.getOrDefault(com.routedesk.database.entity.OutboxActionType.CREATE_TICKET)
    }

    @TypeConverter
    fun fromOutboxStatus(status: com.routedesk.database.entity.OutboxStatus?): String? = status?.name

    @TypeConverter
    fun toOutboxStatus(name: String?): com.routedesk.database.entity.OutboxStatus? = name?.let {
        runCatching { com.routedesk.database.entity.OutboxStatus.valueOf(it) }.getOrDefault(com.routedesk.database.entity.OutboxStatus.PENDING)
    }
}
