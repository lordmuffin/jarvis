package dev.jarvis.service

import android.content.Context
import android.content.Intent
import android.util.Log
import androidx.core.content.ContextCompat
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import dev.jarvis.data.Heartbeat
import dev.jarvis.data.JarvisDatabase
import dev.jarvis.service.inference.ClassifierHolder
import java.util.concurrent.TimeUnit

/**
 * WorkManager liveness backstop — fires every 15 minutes.
 *
 * Responsibilities:
 *   1. Sample whether [ClassifierHolder] has a live classifier.
 *   2. Write a [Heartbeat] row to Room.
 *   3. If the classifier is gone, restart [IntentRouterService].
 *
 * Deliberately does NOT run inference — only checks liveness. The
 * heartbeat rows are consumed by [StatsScreen] for DOZE_KILLED detection.
 */
class HeartbeatWorker(appContext: Context, params: WorkerParameters) :
    CoroutineWorker(appContext, params) {

    override suspend fun doWork(): Result {
        val db = JarvisDatabase.get(applicationContext)
        val isAlive = ClassifierHolder.get() != null

        db.heartbeatDao().insert(
            Heartbeat(
                recordedAt = System.currentTimeMillis(),
                serviceAlive = isAlive,
            ),
        )

        if (!isAlive) {
            Log.w(TAG, "classifier not found — restarting IntentRouterService")
            try {
                ContextCompat.startForegroundService(
                    applicationContext,
                    Intent(applicationContext, IntentRouterService::class.java),
                )
            } catch (e: Exception) {
                Log.w(TAG, "could not restart IntentRouterService", e)
            }
        }

        return Result.success()
    }

    companion object {
        private const val TAG = "HeartbeatWorker"
        const val WORK_NAME = "jarvis.heartbeat"

        fun schedule(context: Context) {
            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                WORK_NAME,
                ExistingPeriodicWorkPolicy.KEEP,
                PeriodicWorkRequestBuilder<HeartbeatWorker>(15, TimeUnit.MINUTES).build(),
            )
        }
    }
}
