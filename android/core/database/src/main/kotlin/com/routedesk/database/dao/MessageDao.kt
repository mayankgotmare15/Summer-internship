package com.routedesk.database.dao

import androidx.room.Dao
import androidx.room.Query
import androidx.room.Upsert
import com.routedesk.database.entity.MessageEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface MessageDao {

    @Upsert
    suspend fun upsertMessages(messages: List<MessageEntity>)

    @Upsert
    suspend fun upsertMessage(message: MessageEntity)

    @Query("SELECT * FROM messages WHERE ticketId = :ticketId ORDER BY createdAt ASC")
    fun observeMessagesForTicket(ticketId: String): Flow<List<MessageEntity>>

    @Query("SELECT * FROM messages WHERE ticketId = :ticketId ORDER BY createdAt ASC")
    suspend fun getMessagesForTicket(ticketId: String): List<MessageEntity>

    @Query("DELETE FROM messages WHERE ticketId = :ticketId")
    suspend fun deleteForTicket(ticketId: String)
}
