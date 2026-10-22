package com.routedesk.database.di

import android.content.Context
import androidx.room.Room
import com.routedesk.database.AppDatabase
import com.routedesk.database.dao.MessageDao
import com.routedesk.database.dao.NotificationDao
import com.routedesk.database.dao.OutboxDao
import com.routedesk.database.dao.TicketDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideAppDatabase(
        @ApplicationContext context: Context
    ): AppDatabase {
        return Room.databaseBuilder(
            context,
            AppDatabase::class.java,
            "routedesk.db"
        )
        .fallbackToDestructiveMigration()
        .build()
    }

    @Provides
    fun provideTicketDao(database: AppDatabase): TicketDao = database.ticketDao()

    @Provides
    fun provideMessageDao(database: AppDatabase): MessageDao = database.messageDao()

    @Provides
    fun provideNotificationDao(database: AppDatabase): NotificationDao = database.notificationDao()

    @Provides
    fun provideOutboxDao(database: AppDatabase): OutboxDao = database.outboxDao()
}
