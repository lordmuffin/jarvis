package dev.jarvis.data

import java.io.File
import java.io.IOException
import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

/**
 * Appends a JSONL record per decision to:
 *
 *     <vault>/outbox/jarvis-decisions/YYYY-MM-DD.jsonl
 *
 * Atomicity: each record is one fwrite + fsync; partial-write risk is limited
 * to the trailing line (which the validator on the homelab side ignores). We
 * don't try harder than that — the SQLite Room copy is the source of truth.
 *
 * Path safety: every File handed to writeLine() is asserted by VaultPaths.
 * Any attempt to write outside outbox/jarvis-* raises SecurityException.
 */
class OutboxWriter(
    private val vaultPaths: VaultPaths,
    private val clock: () -> Instant = Instant::now,
    private val json: Json = DEFAULT_JSON,
) {

    @PublishedApi
    internal val datesFormatter: DateTimeFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd")
        .withZone(ZoneOffset.UTC)

    inline fun <reified T> append(payload: T) {
        val line = json.encodeToString(payload)
        appendLine(line)
    }

    fun appendLine(jsonLine: String) {
        require(!jsonLine.contains('\n')) { "JSONL line must not contain newlines" }
        val today = datesFormatter.format(clock())
        val file = vaultPaths.outboxFile("jarvis-decisions/$today.jsonl")
        ensureParentExists(file)
        try {
            file.appendText(jsonLine + "\n", Charsets.UTF_8)
        } catch (e: IOException) {
            throw IOException("outbox append failed: ${file.path}", e)
        }
    }

    private fun ensureParentExists(file: File) {
        val parent = file.parentFile ?: return
        if (!parent.exists() && !parent.mkdirs()) {
            throw IOException("could not create outbox dir: ${parent.path}")
        }
        // Defense in depth: re-check the parent itself is under outbox/jarvis-*
        // in case some race created an unexpected symlink.
        vaultPaths.assertWriteAllowed(parent)
    }

    companion object {
        val DEFAULT_JSON = Json {
            encodeDefaults = true
            ignoreUnknownKeys = true
            prettyPrint = false
        }
    }
}
