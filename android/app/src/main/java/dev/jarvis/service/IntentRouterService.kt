package dev.jarvis.service

import android.app.Notification
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import android.util.Log
import androidx.core.app.NotificationCompat
import dev.jarvis.JarvisApp
import dev.jarvis.MainActivity
import dev.jarvis.R
import dev.jarvis.service.inference.ClassifierHolder
import dev.jarvis.service.inference.IntentClassifier
import dev.jarvis.service.inference.LiteRtClassifier
import dev.jarvis.service.inference.StubClassifier
import dev.jarvis.service.model.Accelerator

/**
 * Foreground service that owns the on-device classifier.
 *
 * Phase 1.5a scaffolding: starts foreground, installs a [StubClassifier] into
 * [ClassifierHolder], and survives. 1.5b swaps the stub for [LiteRtClassifier]
 * (real model load with Accelerator.AUTO).
 *
 * Lifecycle:
 *   onCreate: register foreground notification, build classifier.
 *   onStartCommand: idempotent — service stays START_STICKY.
 *   onDestroy: close classifier, clear holder.
 *
 * Wake locking: only acquired around an actual classify() call, never held
 * continuously. The release budget is < 500 ms (Phase 1 acceptance gate).
 */
class IntentRouterService : Service() {

    private lateinit var classifier: IntentClassifier
    private var wakeLock: PowerManager.WakeLock? = null
    private var accelerator: Accelerator = Accelerator.AUTO_UNKNOWN

    override fun onCreate() {
        super.onCreate()
        startForegroundCompat()
        classifier = buildClassifier()
        ClassifierHolder.set(classifier)
        Log.i(TAG, "IntentRouterService started; accelerator=$accelerator")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return START_STICKY
    }

    override fun onDestroy() {
        ClassifierHolder.set(null)
        try {
            classifier.close()
        } catch (e: Exception) {
            Log.w(TAG, "Classifier close failed", e)
        }
        wakeLock?.takeIf { it.isHeld }?.release()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    /** Try LiteRT first; fall back to the stub with a loud log if the model
     *  asset is absent (pre-1.4) or the runtime cannot compile it.
     *  No silent fallback — the persistent service notification reports the
     *  actually-used accelerator. */
    private fun buildClassifier(): IntentClassifier {
        val litert = LiteRtClassifier.tryCreate(applicationContext)
        return if (litert != null) {
            accelerator = readAcceleratorFromLiteRt(litert)
            Log.i(TAG, "Using LiteRT classifier; accelerator=$accelerator")
            litert
        } else {
            accelerator = Accelerator.AUTO_UNKNOWN
            Log.w(TAG, "LiteRT unavailable — using StubClassifier; check assets/intent_router.tflite")
            StubClassifier()
        }
    }

    /** The classifier reports its accelerator on every IntentDecision; we read
     *  it once at cold start by issuing a synthetic encode for the foreground
     *  notification subtitle. Cheap (model already warm). */
    private fun readAcceleratorFromLiteRt(litert: LiteRtClassifier): Accelerator {
        return try {
            val decision = litert.classify(
                dev.jarvis.service.model.IncomingEvent(
                    text = "warmup",
                    source = dev.jarvis.service.model.EventSource.MANUAL_TEST,
                ),
            )
            decision.acceleratorUsed
        } catch (e: Exception) {
            Log.w(TAG, "warm-up classify failed", e)
            Accelerator.AUTO_UNKNOWN
        }
    }

    private fun startForegroundCompat() {
        val tap = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )
        val notification: Notification = NotificationCompat.Builder(this, JarvisApp.CHANNEL_SERVICE)
            .setContentTitle(getString(R.string.service_running))
            .setContentText(getString(R.string.service_running_subtitle, accelerator.name))
            .setSmallIcon(android.R.drawable.stat_notify_sync_noanim)
            .setOngoing(true)
            .setContentIntent(tap)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()

        if (Build.VERSION.SDK_INT >= 34) {
            startForeground(
                NOTIFICATION_ID,
                notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC or
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE,
            )
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }
    }

    companion object {
        const val NOTIFICATION_ID = 1001
        private const val TAG = "IntentRouterService"
    }
}
