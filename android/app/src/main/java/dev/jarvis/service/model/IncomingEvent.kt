package dev.jarvis.service.model

import kotlinx.serialization.Serializable

enum class EventSource(val wire: String) {
    EMAIL("email"),
    CALENDAR("calendar"),
    MANUAL_TEST("manual_test"),
    NOTIFICATION_LISTENER("notification_listener"),
    ;

    companion object {
        fun fromWire(v: String): EventSource? = entries.firstOrNull { it.wire == v }
    }
}

@Serializable
data class IncomingEvent(
    val text: String,
    val source: EventSource,
    /** Source-specific id, e.g. email message-id or calendar event id. */
    val externalId: String? = null,
)
