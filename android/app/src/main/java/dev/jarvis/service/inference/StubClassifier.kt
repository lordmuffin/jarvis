package dev.jarvis.service.inference

import dev.jarvis.service.model.Accelerator
import dev.jarvis.service.model.IncomingEvent
import dev.jarvis.service.model.Intent
import dev.jarvis.service.model.IntentDecision
import java.util.UUID

/**
 * Placeholder classifier used during 1.5 scaffolding and as a test double.
 *
 * Deterministic: hashes the event text into the seven-class space so unit tests
 * can assert specific outputs without depending on a real model. The real
 * [LiteRtClassifier] replaces this in 1.5b.
 */
class StubClassifier : IntentClassifier {
    override fun classify(event: IncomingEvent): IntentDecision {
        val started = System.currentTimeMillis()
        val ordinal = (Math.floorMod(event.text.hashCode(), Intent.ORDER.size))
        val intent = Intent.ORDER[ordinal]
        return IntentDecision(
            eventId = UUID.randomUUID().toString(),
            intent = intent,
            confidence = 0.99f,  // honest mock: stub is always sure, surface this if it leaks to prod
            acceleratorUsed = Accelerator.AUTO_UNKNOWN,
            latencyMs = System.currentTimeMillis() - started,
        )
    }

    override fun close() = Unit
}
