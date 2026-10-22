package com.routedesk.database

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import com.routedesk.database.converter.Converters
import com.routedesk.database.dao.MessageDao
import com.routedesk.database.dao.NotificationDao
import com.routedesk.database.dao.OutboxDao
import com.routedesk.database.dao.TicketDao
import com.routedesk.database.entity.MessageEntity
import com.routedesk.database.entity.NotificationEntity
import com.routedesk.database.entity.OutboxEntity
import com.routedesk.database.entity.TicketEntity

@Database(
    entities = [
        TicketEntity::class,
        MessageEntity::class,
        NotificationEntity::class,
        OutboxEntity::class
    ],
    version = 1,
    exportSchema = false
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun ticketDao(): TicketDao
    abstract fun messageDao(): MessageDao
    abstract fun notificationDao(): NotificationDao
    abstract fun outboxDao(): OutboxDao
}
