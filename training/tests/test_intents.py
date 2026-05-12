"""Tests for the canonical intents module."""

from __future__ import annotations

from jarvis_training.intents import (
    INTENT_DEFINITIONS,
    INTENT_ORDER,
    INTENT_SCHEMA_VERSION,
    INTENT_VALUES,
    TARGET_RECORDS_PER_INTENT,
    Intent,
)


def test_seven_canonical_intents_exist():
    assert len(Intent) == 7


def test_intent_order_lists_every_intent_exactly_once():
    assert set(INTENT_ORDER) == set(Intent)
    assert len(INTENT_ORDER) == 7
    assert len(set(INTENT_ORDER)) == 7


def test_canonical_order_is_load_bearing():
    """If you must reorder, bump INTENT_SCHEMA_VERSION and rebuild the model."""
    assert INTENT_ORDER == (
        Intent.DEVICE_ACTION,
        Intent.DRAFT_EMAIL,
        Intent.DRAFT_REPLY,
        Intent.SCHEDULE_EVENT,
        Intent.ESCALATE_BURST,
        Intent.NOTE_CAPTURE,
        Intent.DISMISS,
    )


def test_intent_values_set_matches_enum():
    assert INTENT_VALUES == {i.value for i in Intent}


def test_every_intent_has_a_definition():
    for intent in Intent:
        assert intent in INTENT_DEFINITIONS
        assert len(INTENT_DEFINITIONS[intent]) > 30, (
            f"{intent.value} definition is suspiciously short"
        )


def test_schema_version_is_semver_like():
    parts = INTENT_SCHEMA_VERSION.split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


def test_target_records_per_intent_matches_brief():
    assert TARGET_RECORDS_PER_INTENT == 10_000
