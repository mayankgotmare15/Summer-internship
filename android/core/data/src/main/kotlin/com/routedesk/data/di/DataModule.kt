package com.routedesk.data.di

import com.routedesk.data.repository.DefaultTicketRepository
import com.routedesk.data.repository.TicketRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class DataModule {

    @Binds
    @Singleton
    abstract fun bindTicketRepository(
        impl: DefaultTicketRepository
    ): TicketRepository
}
