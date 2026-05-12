package dev.jarvis.data

import com.google.common.truth.Truth.assertThat
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class VaultPathsTest {

    @get:Rule val tmp = TemporaryFolder()

    @Test
    fun acceptsPathUnderOutboxJarvisDecisions() {
        val vp = VaultPaths(tmp.newFolder("vault"))
        val f = vp.outboxFile("jarvis-decisions/2026-05-12.jsonl")
        assertThat(f.path).contains("outbox")
        assertThat(f.path).contains("jarvis-decisions")
    }

    @Test
    fun rejectsAbsolutePath() {
        val vp = VaultPaths(tmp.newFolder("vault"))
        try {
            vp.outboxFile("/etc/passwd")
            assert(false) { "expected IllegalArgumentException" }
        } catch (e: IllegalArgumentException) {
            assertThat(e.message).contains("relative")
        }
    }

    @Test
    fun rejectsPathOutsideOutboxJarvisPrefix() {
        val vp = VaultPaths(tmp.newFolder("vault"))
        try {
            vp.outboxFile("user-authored/notes.md")
            assert(false) { "expected IllegalArgumentException" }
        } catch (e: IllegalArgumentException) {
            assertThat(e.message).contains("jarvis-")
        }
    }

    @Test
    fun rejectsTraversalOutsideVault() {
        val root = tmp.newFolder("vault")
        val vp = VaultPaths(root)
        try {
            vp.outboxFile("jarvis-decisions/../../escape.jsonl")
            assert(false) { "expected SecurityException" }
        } catch (e: SecurityException) {
            assertThat(e.message).contains("not under")
        } catch (e: IllegalArgumentException) {
            // Acceptable: canonical-path rejection can land here if the trailing
            // segment outside outbox/ doesn't start with "jarvis-".
            assertThat(e.message).contains("jarvis-")
        }
    }

    @Test
    fun rejectsParentEscapeAtAssertLayer() {
        val root = tmp.newFolder("vault")
        val vp = VaultPaths(root)
        val outsideFile = tmp.newFile("escape.txt")
        try {
            vp.assertWriteAllowed(outsideFile)
            assert(false) { "expected SecurityException" }
        } catch (e: SecurityException) {
            assertThat(e.message).contains("not under")
        }
    }

    @Test
    fun acceptsNestedJarvisSubdirs() {
        val vp = VaultPaths(tmp.newFolder("vault"))
        val a = vp.outboxFile("jarvis-decisions/2026-05-12.jsonl")
        val b = vp.outboxFile("jarvis-notes/2026-05-12.md")
        val c = vp.outboxFile("jarvis-pending/event-12345.json")
        listOf(a, b, c).forEach {
            assertThat(it.path).contains("outbox")
        }
    }
}
