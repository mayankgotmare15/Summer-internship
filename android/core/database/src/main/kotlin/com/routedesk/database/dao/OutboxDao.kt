package com.routedesk.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.routedesk.database.entity.OutboxEntity
import com.routedesk.database.entity.OutboxStatus
import kotlinx.coroutines.flow.Flow

@Dao
interface OutboxDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun enqueue(item: OutboxEntity): Long

    @Query("SELECT * FROM outbox WHERE status = 'PENDING' ORDER BY createdAtEpochMs ASC")
    suspend fun getPendingItems(): List<OutboxEntity>

    @Query("SELECT * FROM outbox WHERE id = :id")
    suspend fun getItemById(id: Long): OutboxEntity?

    @Query("SELECT COUNT(*) FROM outbox WHERE status IN ('PENDING', 'SYNCING')")
    fun observePendingCount(): Flow<Int>

    @Query("UPDATE outbox SET status = :status, retryCount = :retryCount, lastError = :error WHERE id = :id")
    suspend fun updateStatus(id: Long, status: OutboxStatus, retryCount: Int, error: String?)

    @Query("DELETE FROM outbox WHERE id = :id")
    suspend fun deleteById(id: Long)

    @Query("DELETE FROM outbox WHERE idempotencyKey = :key")
    suspend fun deleteByIdempotencyKey(key: String)

    @Query("DELETE FROM outbox WHERE status = 'FAILED' AND retryCount >= 5")
    suspend fun clearDeadLetters()
}
