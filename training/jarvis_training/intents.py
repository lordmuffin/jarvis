"""Canonical intent schema for Jarvis Phase 1.

The ordinal order in INTENT_ORDER is load-bearing: the LiteRT model's softmax head
indexes by position, the Android app's IntentDecoder reads the same ordinals.
Reordering this tuple silently breaks every prediction in the field. Any change
here is a model rebuild — bump INTENT_SCHEMA_VERSION.
"""

from __future__ import annotations

from enum import Enum


INTENT_SCHEMA_VERSION = "1.0.0"
TARGET_RECORDS_PER_INTENT = 10_000


class Intent(str, Enum):
    DEVICE_ACTION = "device.action"
    DRAFT_EMAIL = "draft.email"
    DRAFT_REPLY = "draft.reply"
    SCHEDULE_EVENT = "schedule.event"
    ESCALATE_BURST = "escalate.burst"
    NOTE_CAPTURE = "note.capture"
    DISMISS = "dismiss"


INTENT_ORDER: tuple[Intent, ...] = (
    Intent.DEVICE_ACTION,
    Intent.DRAFT_EMAIL,
    Intent.DRAFT_REPLY,
    Intent.SCHEDULE_EVENT,
    Intent.ESCALATE_BURST,
    Intent.NOTE_CAPTURE,
    Intent.DISMISS,
)

INTENT_VALUES: frozenset[str] = frozenset(i.value for i in INTENT_ORDER)


# Short, vault-grounded definitions used in the synthetic-data system prompt.
# Keep these terse — the architecture doc is the canonical longer form.
INTENT_DEFINITIONS: dict[Intent, str] = {
    Intent.DEVICE_ACTION: (
        "Phone-local state change: DND, alarms, focus modes, brightness, ringer. "
        "The Approve action toggles a device setting; no remote system is touched."
    ),
    Intent.DRAFT_EMAIL: (
        "A new outbound email derived from a recent event, note, or prompt. "
        "Distinct from draft.reply: there is no existing thread to attach to."
    ),
    Intent.DRAFT_REPLY: (
        "A reply to an existing email or message thread. The payload carries a "
        "thread_id; the Approve action attaches to that thread."
    ),
    Intent.SCHEDULE_EVENT: (
        "Create or modify a calendar entry. Title, start_at, duration_minutes, "
        "optional attendees and location."
    ),
    Intent.ESCALATE_BURST: (
        "Beyond the small intent router's horizon. Approve POSTs the prompt + "
        "vault context to the on-device llama.cpp mid-tier server."
    ),
    Intent.NOTE_CAPTURE: (
        "A passing observation, fact, or follow-up the user wants in the vault. "
        "Approve appends ONLY to outbox/jarvis-notes/ — never edits user-authored markdown."
    ),
    Intent.DISMISS: (
        "Not worth a toast. The classifier's verdict that the event is noise. "
        "No notification is posted; the decision row is still logged."
    ),
}


assert set(INTENT_DEFINITIONS) == set(INTENT_ORDER), (
    "INTENT_DEFINITIONS missing entries for some Intent members"
)
