package dev.jarvis.ui.notif

import android.app.NotificationManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import dev.jarvis.data.JarvisDatabase
import dev.jarvis.data.UserAction
import dev.jarvis.ui.edit.EditActivity
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/**
 * Receives Approve / Edit / Dismiss taps from the HUN notification action buttons.
 *
 * For APPROVE and DISMISS: writes the user_action to Room, cancels the timeout
 * alarm, and dismisses the notification.
 *
 * For EDIT: cancels the HUN and timeout alarm, then launches [EditActivity]
 * (bottom sheet). The Room write happens inside EditActivity on Send.
 */
class ToastActionReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        val eventId = intent.getStringExtra(EXTRA_EVENT_ID) ?: run {
            Log.w(TAG, "missing $EXTRA_EVENT_ID; dropping ${intent.action}")
            return
        }
        val notifId = intent.getIntExtra(HunDispatcher.EXTRA_NOTIFICATION_ID, -1)

        when (intent.action) {
            ACTION_APPROVE -> handleApprove(context, eventId, notifId)
            ACTION_EDIT -> handleEdit(context, intent, eventId, notifId)
            ACTION_DISMISS -> handleDismiss(context, eventId, notifId)
            else -> Log.w(TAG, "unhandled action: ${intent.action}")
        }
    }

    private fun handleApprove(context: Context, eventId: String, notifId: Int) {
        Log.i(TAG, "APPROVE event=$eventId")
        dismissHunAndCancelAlarm(context, eventId, notifId)
        CoroutineScope(Dispatchers.IO).launch {
            recordAction(context, eventId, UserAction.APPROVE)
            dispatchStubAction(context, eventId)
        }
    }

    private fun handleEdit(context: Context, intent: Intent, eventId: String, notifId: Int) {
        val draft = intent.getStringExtra(EditActivity.EXTRA_DRAFT_PAYLOAD) ?: ""
        Log.i(TAG, "EDIT event=$eventId")
        dismissHunAndCancelAlarm(context, eventId, notifId)
        context.startActivity(
            Intent(context, EditActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
                putExtra(EditActivity.EXTRA_EVENT_ID, eventId)
                putExtra(EditActivity.EXTRA_DRAFT_PAYLOAD, draft)
            },
        )
        // Room write happens in EditActivity when the user taps Send.
    }

    private fun handleDismiss(context: Context, eventId: String, notifId: Int) {
        Log.i(TAG, "DISMISS event=$eventId")
        dismissHunAndCancelAlarm(context, eventId, notifId)
        CoroutineScope(Dispatchers.IO).launch {
            recordAction(context, eventId, UserAction.DISMISS)
        }
    }

    private fun dismissHunAndCancelAlarm(context: Context, eventId: String, notifId: Int) {
        val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        if (notifId != -1) nm.cancel(notifId)
        HunDispatcher.cancelTimeout(context, eventId)
    }

    private suspend fun recordAction(context: Context, eventId: String, action: UserAction) {
        JarvisDatabase.get(context)
            .decisionDao()
            .setUserAction(eventId, action.wire, System.currentTimeMillis())
    }

    private suspend fun dispatchStubAction(context: Context, eventId: String) {
        val intent = JarvisDatabase.get(context)
            .decisionDao()
            .byEventId(eventId)
            ?.predictedIntent
            ?: return
        // Phase 1 stub — actual dispatch (Appium / MCP) lands in Phase 2.
        Log.i(TAG, "stub action dispatched: intent=$intent event=$eventId")
    }

    companion object {
        const val ACTION_APPROVE = "dev.jarvis.action.APPROVE"
        const val ACTION_EDIT = "dev.jarvis.action.EDIT"
        const val ACTION_DISMISS = "dev.jarvis.action.DISMISS"
        const val EXTRA_EVENT_ID = "dev.jarvis.extra.EVENT_ID"
        private const val TAG = "ToastActionReceiver"
    }
}
