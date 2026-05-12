package dev.jarvis.ui

import dev.jarvis.service.model.Intent
import dev.jarvis.service.model.IntentDecision

/**
 * Sealed type representing the surface shape of an interactive toast HUN.
 *
 * Phase 1 dispatches [ApproveDismissAtom] and [EditableTextAtom] only.
 * [ChoiceAtom] is stubbed here to prove the dispatch shape for Phase 3 MCP atoms.
 *
 * Intent → atom mapping (Phase 1):
 *   draft.email, draft.reply, note.capture  → EditableTextAtom
 *   everything else (except dismiss)        → ApproveDismissAtom
 *   dismiss                                 → auto-dismissed before a HUN is posted
 */
sealed class UiAtom {
    abstract val eventId: String
    abstract val title: String
    abstract val body: String

    data class ApproveDismissAtom(
        override val eventId: String,
        override val title: String,
        override val body: String,
    ) : UiAtom()

    data class EditableTextAtom(
        override val eventId: String,
        override val title: String,
        override val body: String,
        val draftPayload: String,
    ) : UiAtom()

    /** Phase 3 placeholder — choice atoms are NOT dispatched in Phase 1. */
    data class ChoiceAtom(
        override val eventId: String,
        override val title: String,
        override val body: String,
        val choices: List<String> = emptyList(),
    ) : UiAtom()

    companion object {
        fun from(decision: IntentDecision, eventText: String): UiAtom {
            val title = when (decision.intent) {
                Intent.DEVICE_ACTION -> "Device action"
                Intent.DRAFT_EMAIL -> "Draft email"
                Intent.DRAFT_REPLY -> "Draft reply"
                Intent.SCHEDULE_EVENT -> "Schedule event"
                Intent.ESCALATE_BURST -> "Escalation"
                Intent.NOTE_CAPTURE -> "Capture note"
                Intent.DISMISS -> "Dismiss"
            }
            val body = eventText.take(200)
            return when (decision.intent) {
                Intent.DRAFT_EMAIL, Intent.DRAFT_REPLY, Intent.NOTE_CAPTURE ->
                    EditableTextAtom(
                        eventId = decision.eventId,
                        title = title,
                        body = body,
                        draftPayload = eventText,
                    )
                else ->
                    ApproveDismissAtom(
                        eventId = decision.eventId,
                        title = title,
                        body = body,
                    )
            }
        }
    }
}
