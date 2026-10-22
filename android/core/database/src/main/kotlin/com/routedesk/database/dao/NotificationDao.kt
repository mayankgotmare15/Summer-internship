package com.routedesk.database.dao

import androidx.room.Dao
import androidx.room.Query
import androidx.room.Upsert
import com.routedesk.database.entity.NotificationEntity
import kotlinx.coroutines.flow.Flow
import kotlinx.datetime.Instant

@Dao
interface NotificationDao {

    @Upsert
    suspend fun upsertNotifications(notifications: List<NotificationEntity>)

    @Upsert
    suspend fun upsertNotification(notification: NotificationEntity)

    @Query("SELECT * FROM notifications ORDER BY createdAt DESC")
    fun observeNotifications(): Flow<List<NotificationEntity>>

    @Query("SELECT COUNT(*) FROM notifications WHERE readAt IS NULL")
    fun observeUnreadCount(): Flow<Int>

    @Query("UPDATE notifications SET readAt = :readAt WHERE id = :id")
    suspend fun markAsRead(id: String, readAt: Instant)

    @Query("UPDATE notifications SET readAt = :readAt WHERE readAt IS NULL")
    suspend fun markAllAsRead(readAt: Instant)
}
