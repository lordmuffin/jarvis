package dev.jarvis.service.model

/**
 * Mirror of `jarvis_training.intents.Intent`. The ordinal order is load-bearing:
 * the LiteRT softmax head outputs in this exact order. If you must reorder,
 * also bump `INTENT_SCHEMA_VERSION` in training/jarvis_training/intents.py and
 * rebuild the model.
 */
enum class Intent(val wire: String) {
    DEVICE_ACTION("device.action"),
    DRAFT_EMAIL("draft.email"),
    DRAFT_REPLY("draft.reply"),
    SCHEDULE_EVENT("schedule.event"),
    ESCALATE_BURST("escalate.burst"),
    NOTE_CAPTURE("note.capture"),
    DISMISS("dismiss"),
    ;

    companion object {
        const val SCHEMA_VERSION = "1.0.0"

        /** Canonical ordinal order — matches model softmax output index. */
        val ORDER: List<Intent> = entries.toList()

        fun fromOrdinal(i: Int): Intent =
            ORDER.getOrNull(i)
                ?: error("Intent ordinal $i is out of range (0..${ORDER.lastIndex})")

        fun fromWire(value: String): Intent? = entries.firstOrNull { it.wire == value }
    }
}
