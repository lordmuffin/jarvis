package dev.jarvis.service

import android.content.Context
import android.util.Log
import dev.jarvis.data.Decision
import dev.jarvis.data.JarvisDatabase
import dev.jarvis.data.UserAction
import dev.jarvis.service.model.IncomingEvent
import dev.jarvis.service.model.Intent
import dev.jarvis.service.model.IntentDecision
import dev.jarvis.ui.UiAtom
import dev.jarvis.ui.notif.HunDispatcher
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/**
 * Orchestrates the full event → classify → Room write → HUN pipeline.
 *
 * Usage pattern:
 *   - Call [process] from any thread; classification is synchronous (in-process).
 *   - Room writes and notification dispatch are fire-and-forget on Dispatchers.IO.
 *   - The 2-second sleep in `scripts/phase-1-smoke-test.sh` is ample for the
 *     async writes to land before the DB is pulled.
 *
 * Auto-disposition rules (no HUN posted):
 *   1. predicted_intent == DISMISS  → user_action = auto_dismiss_intent
 *   2. confidence < CONFIDENCE_THRESHOLD → user_action = auto_low_confidence
 */
class ToastPipeline(private val context: Context) {

    private val db by lazy { JarvisDatabase.get(context) }
    private val client by lazy { IntentRouterClient(context) }

    fun process(event: IncomingEvent): IntentDecision {
        val decision = client.classify(event)
        CoroutineScope(Dispatchers.IO).launch {
            persist(event, decision)
        }
        return decision
    }

    private suspend fun persist(event: IncomingEvent, decision: IntentDecision) {
        val now = System.currentTimeMillis()
        val row = Decision(
            eventId = decision.eventId,
            eventSource = event.source.wire,
            eventText = event.text,
            predictedIntent = decision.intent.wire,
            confidence = decision.confidence,
            acceleratorUsed = decision.acceleratorUsed.name,
            inferenceLatencyMs = decision.latencyMs,
            createdAt = now,
        )
        db.decisionDao().insert(row)

        when {
            decision.intent == Intent.DISMISS -> {
                db.decisionDao().setUserAction(
                    decision.eventId,
                    UserAction.AUTO_DISMISS_INTENT.wire,
                    System.currentTimeMillis(),
                )
                Log.d(TAG, "auto-dismiss: event=${decision.eventId}")
            }
            decision.confidence < CONFIDENCE_THRESHOLD -> {
                db.decisionDao().setUserAction(
                    decision.eventId,
                    UserAction.AUTO_LOW_CONFIDENCE.wire,
                    System.currentTimeMillis(),
                )
                Log.d(TAG, "low-confidence (${decision.confidence}): event=${decision.eventId}")
            }
            else -> {
                val atom = UiAtom.from(decision, event.text)
                HunDispatcher.post(context, atom)
            }
        }
    }

    companion object {
        private const val TAG = "ToastPipeline"
        const val CONFIDENCE_THRESHOLD = 0.40f
    }
}
