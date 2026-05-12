package dev.jarvis

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log
import androidx.core.content.ContextCompat
import dev.jarvis.service.HeartbeatWorker
import dev.jarvis.service.IntentRouterService

class JarvisApp : Application() {
    override fun onCreate() {
        super.onCreate()
        registerNotificationChannels()
        startClassifierService()
        HeartbeatWorker.schedule(this)
    }

    private fun registerNotificationChannels() {
        val nm = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        // High importance — these are the user-facing Approve/Edit/Dismiss HUNs.
        nm.createNotificationChannel(
            NotificationChannel(
                CHANNEL_TOASTS,
                getString(R.string.channel_toasts),
                NotificationManager.IMPORTANCE_HIGH,
            ).apply {
                description = getString(R.string.channel_toasts_description)
                enableVibration(true)
            },
        )

        // Low importance — the persistent foreground-service status.
        nm.createNotificationChannel(
            NotificationChannel(
                CHANNEL_SERVICE,
                getString(R.string.channel_service),
                NotificationManager.IMPORTANCE_LOW,
            ).apply {
                description = getString(R.string.channel_service_description)
                setShowBadge(false)
            },
        )
    }

    private fun startClassifierService() {
        try {
            ContextCompat.startForegroundService(
                this,
                Intent(this, IntentRouterService::class.java),
            )
        } catch (e: Exception) {
            // Foreground-service start can throw on cold-boot before the user has
            // unlocked the device on Android 14. Surface, don't swallow.
            Log.w(TAG, "Failed to start IntentRouterService on app onCreate", e)
        }
    }

    companion object {
        const val CHANNEL_TOASTS = "jarvis.toasts"
        const val CHANNEL_SERVICE = "jarvis.service"
        private const val TAG = "JarvisApp"
        const val SDK_AT_LEAST_34 = Build.VERSION.SDK_INT >= 34
    }
}
