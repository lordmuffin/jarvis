package dev.jarvis.service.model

import com.google.common.truth.Truth.assertThat
import org.junit.Test

/** The ordinal order of [Intent] is load-bearing — must match training/intents.py. */
class IntentTest {

    @Test
    fun ordinalOrderIsFrozen() {
        assertThat(Intent.ORDER).containsExactly(
            Intent.DEVICE_ACTION,
            Intent.DRAFT_EMAIL,
            Intent.DRAFT_REPLY,
            Intent.SCHEDULE_EVENT,
            Intent.ESCALATE_BURST,
            Intent.NOTE_CAPTURE,
            Intent.DISMISS,
        ).inOrder()
    }

    @Test
    fun wireValuesMatchSchemaDoc() {
        assertThat(Intent.values().map { it.wire }).containsExactly(
            "device.action",
            "draft.email",
            "draft.reply",
            "schedule.event",
            "escalate.burst",
            "note.capture",
            "dismiss",
        ).inOrder()
    }

    @Test
    fun fromWireRoundTrips() {
        Intent.values().forEach {
            assertThat(Intent.fromWire(it.wire)).isEqualTo(it)
        }
    }

    @Test
    fun fromWireReturnsNullForUnknown() {
        assertThat(Intent.fromWire("device.dnd")).isNull()
    }

    @Test
    fun fromOrdinalMatchesOrder() {
        Intent.ORDER.forEachIndexed { i, expected ->
            assertThat(Intent.fromOrdinal(i)).isEqualTo(expected)
        }
    }

    @Test
    fun schemaVersionMatchesTrainingPackage() {
        // Bumping this requires a model rebuild — see training/jarvis_training/intents.py
        assertThat(Intent.SCHEMA_VERSION).isEqualTo("1.0.0")
    }
}
