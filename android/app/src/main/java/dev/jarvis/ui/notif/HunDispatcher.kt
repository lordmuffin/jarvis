package dev.jarvis.ui.notif

import android.app.AlarmManager
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.SystemClock
import androidx.core.app.NotificationCompat
import dev.jarvis.JarvisApp
import dev.jarvis.R
import dev.jarvis.ui.UiAtom
import dev.jarvis.ui.edit.EditActivity
import kotlin.math.abs

/**
 * Posts a high-importance HUN notification for the given [UiAtom] and
 * registers an inexact AlarmManager callback to detect 30-minute timeouts.
 *
 * Phase 1 dispatches ApproveDismissAtom and EditableTextAtom only.
 * ChoiceAtom is a no-op here; it will be wired in Phase 3.
 */
object HunDispatcher {

    const val TIMEOUT_MILLIS = 30L * 60 * 1000
    const val EXTRA_NOTIFICATION_ID = "dev.jarvis.extra.NOTIF_ID"

    fun post(context: Context, atom: UiAtom) {
        val notifId = notifIdFor(atom.eventId)
        val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        val builder = NotificationCompat.Builder(context, JarvisApp.CHANNEL_TOASTS)
            .setContentTitle(atom.title)
            .setContentText(atom.body)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_REMINDER)
            .setAutoCancel(false)
            .setOngoing(false)
            .setTimeoutAfter(TIMEOUT_MILLIS)

        when (atom) {
            is UiAtom.ApproveDismissAtom -> {
                builder.addAction(
                    android.R.drawable.ic_menu_send,
                    context.getString(R.string.action_approve),
                    approveIntent(context, atom.eventId, notifId),
                )
                builder.addAction(
                    android.R.drawable.ic_delete,
                    context.getString(R.string.action_dismiss),
                    dismissIntent(context, atom.eventId, notifId),
                )
            }
            is UiAtom.EditableTextAtom -> {
                builder.addAction(
                    android.R.drawable.ic_menu_send,
                    context.getString(R.string.action_approve),
                    approveIntent(context, atom.eventId, notifId),
                )
                builder.addAction(
                    android.R.drawable.ic_menu_edit,
                    context.getString(R.string.action_edit),
                    editIntent(context, atom.eventId, notifId, atom.draftPayload),
                )
                builder.addAction(
                    android.R.drawable.ic_delete,
                    context.getString(R.string.action_dismiss),
                    dismissIntent(context, atom.eventId, notifId),
                )
            }
            is UiAtom.ChoiceAtom -> return  // Phase 3 — not dispatched in Phase 1
        }

        nm.notify(notifId, builder.build())
        scheduleTimeout(context, atom.eventId, notifId)
    }

    fun cancelHun(context: Context, eventId: String) {
        val notifId = notifIdFor(eventId)
        val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        nm.cancel(notifId)
        cancelTimeout(context, eventId, notifId)
    }

    fun cancelTimeout(context: Context, eventId: String, notifId: Int = notifIdFor(eventId)) {
        val am = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        am.cancel(timeoutPendingIntent(context, eventId, notifId))
    }

    fun timeoutPendingIntent(context: Context, eventId: String, notifId: Int): PendingIntent {
        val i = Intent(context, TimeoutReceiver::class.java).apply {
            putExtra(ToastActionReceiver.EXTRA_EVENT_ID, eventId)
            putExtra(EXTRA_NOTIFICATION_ID, notifId)
        }
        return PendingIntent.getBroadcast(
            context,
            reqCode(notifId, 3),
            i,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )
    }

    // ---------- private -------------------------------------------------------

    private fun notifIdFor(eventId: String): Int = abs(eventId.hashCode()).coerceAtLeast(1)

    private fun approveIntent(context: Context, eventId: String, notifId: Int): PendingIntent {
        val i = Intent(ToastActionReceiver.ACTION_APPROVE).apply {
            setClass(context, ToastActionReceiver::class.java)
            putExtra(ToastActionReceiver.EXTRA_EVENT_ID, eventId)
            putExtra(EXTRA_NOTIFICATION_ID, notifId)
        }
        return PendingIntent.getBroadcast(
            context, reqCode(notifId, 0), i,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )
    }

    private fun editIntent(
        context: Context,
        eventId: String,
        notifId: Int,
        draft: String,
    ): PendingIntent {
        val i = Intent(ToastActionReceiver.ACTION_EDIT).apply {
            setClass(context, ToastActionReceiver::class.java)
            putExtra(ToastActionReceiver.EXTRA_EVENT_ID, eventId)
            putExtra(EXTRA_NOTIFICATION_ID, notifId)
            putExtra(EditActivity.EXTRA_DRAFT_PAYLOAD, draft)
        }
        return PendingIntent.getBroadcast(
            context, reqCode(notifId, 1), i,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )
    }

    private fun dismissIntent(context: Context, eventId: String, notifId: Int): PendingIntent {
        val i = Intent(ToastActionReceiver.ACTION_DISMISS).apply {
            setClass(context, ToastActionReceiver::class.java)
            putExtra(ToastActionReceiver.EXTRA_EVENT_ID, eventId)
            putExtra(EXTRA_NOTIFICATION_ID, notifId)
        }
        return PendingIntent.getBroadcast(
            context, reqCode(notifId, 2), i,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )
    }

    private fun scheduleTimeout(context: Context, eventId: String, notifId: Int) {
        val am = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        // Inexact alarm — no SCHEDULE_EXACT_ALARM permission needed.
        am.set(
            AlarmManager.ELAPSED_REALTIME_WAKEUP,
            SystemClock.elapsedRealtime() + TIMEOUT_MILLIS,
            timeoutPendingIntent(context, eventId, notifId),
        )
    }

    /** Each (notifId, slot) pair needs a distinct request code for PendingIntent identity. */
    private fun reqCode(notifId: Int, slot: Int): Int = notifId * 10 + slot
}
