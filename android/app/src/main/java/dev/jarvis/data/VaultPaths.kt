package dev.jarvis.data

import java.io.File
import java.io.IOException

/**
 * Authority on which vault paths Jarvis is allowed to write to.
 *
 * The phone is READ-ONLY with respect to user-authored markdown. Every write
 * MUST land under `<vault>/outbox/jarvis-*`. This class is the single chokepoint
 * that asserts the rule, and OutboxWriter is the only caller. The runtime
 * assertion is paired with a unit test in `OutboxWriterTest` to prevent
 * regressions.
 *
 * Why three layers of defense?
 *   1. Syncthing folder type: ReceiveOnly (set in docs/phase-0-bringup.md).
 *   2. App: SAF scope (vault tree is opened read-only; outbox/ subtree opened
 *      via a separate write-scope grant).
 *   3. THIS class: every File path crossing the OutboxWriter API is checked.
 *
 * One layer failing should never silently break the rule.
 */
class VaultPaths(private val vaultRoot: File) {

    private val outboxRoot: File = File(vaultRoot, "outbox").canonicalFile

    /** Resolve a relative path under outbox/, asserting it stays inside. */
    fun outboxFile(relativeBeneathOutbox: String): File {
        require(relativeBeneathOutbox.isNotBlank()) {
            "relativeBeneathOutbox must not be blank"
        }
        require(!relativeBeneathOutbox.startsWith("/")) {
            "outbox path must be relative, got: $relativeBeneathOutbox"
        }
        val resolved = File(outboxRoot, relativeBeneathOutbox).canonicalFile
        assertWriteAllowed(resolved)
        return resolved
    }

    /** Public guard reused by tests. Throws if [target] would escape outbox/. */
    fun assertWriteAllowed(target: File) {
        val canonical = try {
            target.canonicalFile
        } catch (e: IOException) {
            throw SecurityException("cannot canonicalize $target", e)
        }
        if (!isStrictlyUnder(canonical, outboxRoot)) {
            throw SecurityException(
                "Vault write rejected: ${canonical.path} is not under ${outboxRoot.path}. " +
                    "Phase 1 invariant: phone writes ONLY under <vault>/outbox/jarvis-*",
            )
        }
        // Defense in depth: outbox writes must live under outbox/jarvis-*
        // subdirectories. We allow only paths whose first path segment under
        // outbox/ starts with "jarvis-".
        val rel = canonical.path.removePrefix(outboxRoot.path).trimStart(File.separatorChar)
        val firstSegment = rel.substringBefore(File.separatorChar)
        require(firstSegment.startsWith("jarvis-")) {
            "outbox write must live under outbox/jarvis-* (got: $rel)"
        }
    }

    private fun isStrictlyUnder(candidate: File, root: File): Boolean {
        var cur: File? = candidate
        while (cur != null) {
            if (cur == root) return true
            cur = cur.parentFile?.canonicalFile
        }
        return false
    }
}
