package dev.jarvis.data

/** What the user did with the toast (or what the system did when the user did nothing). */
enum class UserAction(val wire: String) {
    APPROVE("approve"),
    EDIT("edit"),
    DISMISS("dismiss"),
    TIMEOUT("timeout"),
    AUTO_LOW_CONFIDENCE("auto_low_confidence"),
    AUTO_DISMISS_INTENT("auto_dismiss_intent"),
    ;

    companion object {
        fun fromWire(v: String?): UserAction? = entries.firstOrNull { it.wire == v }
    }
}
