package dev.jarvis.testing

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import dev.jarvis.service.IntentRouterClient
import dev.jarvis.service.model.EventSource
import dev.jarvis.service.model.IncomingEvent

/**
 * Debug-only receiver fed by scripts/phase-1-smoke-test.sh:
 *
 *   adb shell am broadcast -a dev.jarvis.testing.SMOKE_EVENT \
 *     --es text "subject: ..." --es source manual_test
 *
 * Not declared in the release manifest — production cannot be poked.
 */
class SmokeTestReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != ACTION) return
        val text = intent.getStringExtra(EXTRA_TEXT) ?: run {
            Log.w(TAG, "missing --es text=...; dropping")
            return
        }
        val sourceName = intent.getStringExtra(EXTRA_SOURCE) ?: "manual_test"
        val source = EventSource.fromWire(sourceName) ?: EventSource.MANUAL_TEST
        val decision = IntentRouterClient(context).classify(
            IncomingEvent(text = text, source = source),
        )
        Log.i(
            TAG,
            "decision: intent=${decision.intent.wire} " +
                "confidence=${decision.confidence} " +
                "accelerator=${decision.acceleratorUsed} " +
                "latency_ms=${decision.latencyMs}",
        )
    }

    companion object {
        const val ACTION = "dev.jarvis.testing.SMOKE_EVENT"
        const val EXTRA_TEXT = "text"
        const val EXTRA_SOURCE = "source"
        private const val TAG = "SmokeTestReceiver"
    }
}
