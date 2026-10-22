package com.routedesk.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Upsert
import com.routedesk.database.entity.TicketEntity
import com.routedesk.model.TicketStatus
import kotlinx.coroutines.flow.Flow

@Dao
interface TicketDao {

    @Upsert
    suspend fun upsertTickets(tickets: List<TicketEntity>)

    @Upsert
    suspend fun upsertTicket(ticket: TicketEntity)

    @Query("SELECT * FROM tickets WHERE id = :id")
    suspend fun getTicketById(id: String): TicketEntity?

    @Query("SELECT * FROM tickets WHERE id = :id")
    fun observeTicketById(id: String): Flow<TicketEntity?>

    @Query("SELECT * FROM tickets ORDER BY createdAt DESC")
    fun observeAllTickets(): Flow<List<TicketEntity>>

    @Query("SELECT * FROM tickets WHERE status = :status ORDER BY createdAt DESC")
    fun observeTicketsByStatus(status: TicketStatus): Flow<List<TicketEntity>>

    @Query("SELECT * FROM tickets WHERE status = 'WAITING_ON_REQUESTER' ORDER BY createdAt DESC")
    fun observeTicketsWaitingOnRequester(): Flow<List<TicketEntity>>

    @Query("SELECT * FROM tickets WHERE status NOT IN ('RESOLVED', 'CLOSED') ORDER BY createdAt DESC")
    fun observeOpenTickets(): Flow<List<TicketEntity>>

    @Query("DELETE FROM tickets WHERE id = :id")
    suspend fun deleteTicketById(id: String)

    @Query("DELETE FROM tickets")
    suspend fun deleteAll()
}
