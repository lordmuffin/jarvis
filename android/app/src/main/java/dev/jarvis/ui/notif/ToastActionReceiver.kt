package dev.jarvis.ui.notif

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

/** Stub for 1.5a — replaced by the real Approve/Edit/Dismiss handler in 1.6. */
class ToastActionReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        Log.i("ToastActionReceiver", "received ${intent.action} for event ${intent.getStringExtra(EXTRA_EVENT_ID)}")
    }

    companion object {
        const val ACTION_APPROVE = "dev.jarvis.action.APPROVE"
        const val ACTION_EDIT = "dev.jarvis.action.EDIT"
        const val ACTION_DISMISS = "dev.jarvis.action.DISMISS"
        const val EXTRA_EVENT_ID = "dev.jarvis.extra.EVENT_ID"
    }
}
