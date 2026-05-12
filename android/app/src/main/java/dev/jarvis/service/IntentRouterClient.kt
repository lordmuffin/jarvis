package dev.jarvis.service

import android.content.Context
import android.content.Intent as AndroidIntent
import androidx.core.content.ContextCompat
import dev.jarvis.service.inference.ClassifierHolder
import dev.jarvis.service.inference.StubClassifier
import dev.jarvis.service.model.IncomingEvent
import dev.jarvis.service.model.IntentDecision

/**
 * Façade for callers (Compose UIs, broadcast receivers) that want to run an event
 * through the classifier. Ensures the service is running before issuing the call.
 *
 * If the service hasn't finished its cold-start model load yet, a one-shot
 * [StubClassifier] is used so the smoke test and manual-trigger UI return
 * something rather than crashing. The decision is tagged with
 * `accelerator=AUTO_UNKNOWN` so post-hoc the user can see which events got the
 * stub fallback.
 */
class IntentRouterClient(private val context: Context) {

    private val coldStartFallback by lazy { StubClassifier() }

    fun classify(event: IncomingEvent): IntentDecision {
        ensureServiceStarted()
        val classifier = ClassifierHolder.get() ?: coldStartFallback
        return classifier.classify(event)
    }

    private fun ensureServiceStarted() {
        val intent = AndroidIntent(context, IntentRouterService::class.java)
        ContextCompat.startForegroundService(context, intent)
    }
}
