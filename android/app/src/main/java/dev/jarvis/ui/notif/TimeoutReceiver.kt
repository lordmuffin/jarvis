package dev.jarvis.ui.notif

import android.app.NotificationManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import dev.jarvis.data.JarvisDatabase
import dev.jarvis.data.UserAction
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/**
 * Fires ~30 minutes after a HUN is posted if the user never acted on it.
 *
 * Checks whether the notification is still visible. If the user already
 * acted (APPROVE/EDIT/DISMISS), the notification is gone and user_action is
 * already set — we do nothing. If the notification is still up (or was
 * auto-cancelled by [setTimeoutAfter]), we record user_action = timeout.
 */
class TimeoutReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        val eventId = intent.getStringExtra(ToastActionReceiver.EXTRA_EVENT_ID) ?: run {
            Log.w(TAG, "missing ${ToastActionReceiver.EXTRA_EVENT_ID}")
            return
        }
        val notifId = intent.getIntExtra(HunDispatcher.EXTRA_NOTIFICATION_ID, -1)

        val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        if (notifId != -1 && nm.activeNotifications.any { it.id == notifId }) {
            nm.cancel(notifId)
        }

        CoroutineScope(Dispatchers.IO).launch {
            val db = JarvisDatabase.get(context)
            val row = db.decisionDao().byEventId(eventId) ?: return@launch
            if (row.userAction == null) {
                db.decisionDao().setUserAction(
                    eventId,
                    UserAction.TIMEOUT.wire,
                    System.currentTimeMillis(),
                )
                Log.i(TAG, "timeout recorded: event=$eventId")
            }
        }
    }

    companion object {
        private const val TAG = "TimeoutReceiver"
    }
}
