package com.routedesk.data.clock

import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.datetime.Instant
import java.text.SimpleDateFormat
import java.util.Locale
import java.util.TimeZone
import java.util.concurrent.atomic.AtomicLong
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ClockOffsetManager @Inject constructor() {

    private val offsetMillis = AtomicLong(0L)

    private val httpDateFormat = SimpleDateFormat("EEE, dd MMM yyyy HH:mm:ss z", Locale.US).apply {
        timeZone = TimeZone.getTimeZone("GMT")
    }

    fun updateOffsetFromDateHeader(dateHeader: String?) {
        if (dateHeader.isNullOrBlank()) return
        try {
            val serverDate = httpDateFormat.parse(dateHeader)
            if (serverDate != null) {
                val serverEpoch = serverDate.time
                val localEpoch = System.currentTimeMillis()
                offsetMillis.set(serverEpoch - localEpoch)
            }
        } catch (_: Exception) {
            // Fallback to local clock on parse errors
        }
    }

    fun currentServerTimeMillis(): Long = System.currentTimeMillis() + offsetMillis.get()

    fun currentServerInstant(): Instant = Instant.fromEpochMilliseconds(currentServerTimeMillis())

    val tickerFlow: Flow<Long> = flow {
        while (true) {
            emit(currentServerTimeMillis())
            delay(1000L)
        }
    }
}
