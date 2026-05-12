package dev.jarvis.data

import com.google.common.truth.Truth.assertThat
import java.io.File
import java.time.Instant
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class OutboxWriterTest {

    @get:Rule val tmp = TemporaryFolder()

    private fun makeWriter(at: Instant = Instant.parse("2026-05-12T10:00:00Z")): Pair<OutboxWriter, File> {
        val vault = tmp.newFolder("vault")
        val writer = OutboxWriter(VaultPaths(vault), clock = { at })
        return writer to vault
    }

    @Test
    fun writesOneRecordPerLineUnderJarvisDecisions() {
        val (writer, vault) = makeWriter()
        val rec = OutboxDecisionRecord(
            eventId = "abc",
            eventSource = "manual_test",
            eventText = "hello",
            predictedIntent = "draft.email",
            confidence = 0.91f,
            acceleratorUsed = "NPU",
            inferenceLatencyMs = 42,
            userAction = null,
            createdAtMs = 100,
            intentSchemaVersion = "1.0.0",
        )
        writer.append(rec)
        val f = File(vault, "outbox/jarvis-decisions/2026-05-12.jsonl")
        assertThat(f.exists()).isTrue()
        val lines = f.readText().trim().split("\n")
        assertThat(lines).hasSize(1)
        assertThat(lines[0]).contains("\"event_id\":\"abc\"")
        assertThat(lines[0]).contains("\"intent_schema_version\":\"1.0.0\"")
    }

    @Test
    fun appendsAcrossMultipleCalls() {
        val (writer, vault) = makeWriter()
        repeat(3) { i ->
            writer.append(
                OutboxDecisionRecord(
                    eventId = "id-$i",
                    eventSource = "manual_test",
                    eventText = "t-$i",
                    predictedIntent = "dismiss",
                    confidence = 0.5f,
                    acceleratorUsed = "CPU",
                    inferenceLatencyMs = 1,
                    createdAtMs = i.toLong(),
                    intentSchemaVersion = "1.0.0",
                ),
            )
        }
        val f = File(vault, "outbox/jarvis-decisions/2026-05-12.jsonl")
        assertThat(f.readText().trim().split("\n")).hasSize(3)
    }

    @Test
    fun rotatesPerDay() {
        val vault = tmp.newFolder("vault")
        val day1 = OutboxWriter(VaultPaths(vault), clock = { Instant.parse("2026-05-12T23:59:00Z") })
        val day2 = OutboxWriter(VaultPaths(vault), clock = { Instant.parse("2026-05-13T00:01:00Z") })
        day1.appendLine("""{"x":1}""")
        day2.appendLine("""{"x":2}""")
        assertThat(File(vault, "outbox/jarvis-decisions/2026-05-12.jsonl").exists()).isTrue()
        assertThat(File(vault, "outbox/jarvis-decisions/2026-05-13.jsonl").exists()).isTrue()
    }

    @Test
    fun rejectsNewlineInPayload() {
        val (writer, _) = makeWriter()
        try {
            writer.appendLine("a\nb")
            assert(false) { "expected IllegalArgumentException" }
        } catch (e: IllegalArgumentException) {
            assertThat(e.message).contains("newlines")
        }
    }

    @Test
    fun runtimeAssertBlocksWriteOutsideOutbox() {
        // Constructing a writer is fine; but if some refactor ever hands File
        // paths around the VaultPaths checks, the layered defense in
        // VaultPaths.assertWriteAllowed still rejects.
        val vault = tmp.newFolder("vault")
        val vp = VaultPaths(vault)
        val attacker = File(vault, "user-authored.md")  // not under outbox/
        try {
            vp.assertWriteAllowed(attacker)
            assert(false) { "expected SecurityException" }
        } catch (e: SecurityException) {
            assertThat(e.message).contains("not under")
        }
    }
}
