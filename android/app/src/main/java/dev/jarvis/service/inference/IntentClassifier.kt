package dev.jarvis.service.inference

import dev.jarvis.service.model.IncomingEvent
import dev.jarvis.service.model.IntentDecision

/** Abstraction over the on-device classifier. Implemented by [LiteRtClassifier]
 *  in 1.5b; substituted with a fake in tests and during initial scaffolding. */
interface IntentClassifier {
    fun classify(event: IncomingEvent): IntentDecision
    fun close()
}
