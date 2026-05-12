"""Tests for synth.validate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from jarvis_training.intents import Intent
from jarvis_training.synth.validate import validate


def _write_raw(path: Path, records: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(records) + "\n", encoding="utf-8")


def test_validate_happy_path(tmp_path: Path):
    raw = tmp_path / "raw.jsonl"
    clean = tmp_path / "clean.jsonl"
    valid_ids = {"abc"}
    records = [
        json.dumps({"text": "hello", "intent": "draft.email", "vault_source_chunk_id": "abc"}),
        json.dumps({"text": "world", "intent": "dismiss", "vault_source_chunk_id": "abc"}),
    ]
    _write_raw(raw, records)
    stats = validate(raw, clean, valid_ids)
    assert stats.accepted == 2
    assert stats.total_in == 2
    assert stats.accepted_per_intent[Intent.DRAFT_EMAIL.value] == 1
    assert stats.accepted_per_intent[Intent.DISMISS.value] == 1
    assert clean.read_text(encoding="utf-8").count("\n") == 2


def test_validate_rejects_malformed_json(tmp_path: Path):
    raw = tmp_path / "raw.jsonl"
    clean = tmp_path / "clean.jsonl"
    _write_raw(raw, ["not json", '{"text":"x","intent":"draft.email","vault_source_chunk_id":"abc"}'])
    stats = validate(raw, clean, {"abc"})
    assert stats.rejected_malformed == 1
    assert stats.accepted == 1


def test_validate_rejects_missing_or_empty_text(tmp_path: Path):
    raw = tmp_path / "raw.jsonl"
    clean = tmp_path / "clean.jsonl"
    _write_raw(
        raw,
        [
            json.dumps({"intent": "draft.email", "vault_source_chunk_id": "abc"}),
            json.dumps({"text": "", "intent": "draft.email", "vault_source_chunk_id": "abc"}),
            json.dumps({"text": "   ", "intent": "draft.email", "vault_source_chunk_id": "abc"}),
        ],
    )
    stats = validate(raw, clean, {"abc"})
    assert stats.accepted == 0
    assert stats.rejected_malformed == 3


def test_validate_rejects_unknown_intent(tmp_path: Path):
    raw = tmp_path / "raw.jsonl"
    clean = tmp_path / "clean.jsonl"
    _write_raw(
        raw,
        [
            json.dumps({"text": "x", "intent": "device.dnd", "vault_source_chunk_id": "abc"}),
            json.dumps({"text": "y", "intent": "draft.email", "vault_source_chunk_id": "abc"}),
        ],
    )
    stats = validate(raw, clean, {"abc"})
    assert stats.rejected_invalid_intent == 1
    assert stats.accepted == 1


def test_validate_rejects_dangling_chunk(tmp_path: Path):
    raw = tmp_path / "raw.jsonl"
    clean = tmp_path / "clean.jsonl"
    _write_raw(
        raw,
        [
            json.dumps({"text": "a", "intent": "draft.email", "vault_source_chunk_id": "unknown"}),
            json.dumps({"text": "b", "intent": "draft.email", "vault_source_chunk_id": "abc"}),
        ],
    )
    stats = validate(raw, clean, {"abc"})
    assert stats.rejected_dangling_chunk == 1
    assert stats.accepted == 1


def test_validate_caps_duplicates_at_max(tmp_path: Path):
    raw = tmp_path / "raw.jsonl"
    clean = tmp_path / "clean.jsonl"
    dup = json.dumps({"text": "same", "intent": "draft.email", "vault_source_chunk_id": "abc"})
    _write_raw(raw, [dup, dup, dup, dup, dup])  # 5 instances; max_duplicates=3
    stats = validate(raw, clean, {"abc"}, max_duplicates=3)
    assert stats.accepted == 3
    assert stats.rejected_duplicate == 2


def test_validate_treats_text_whitespace_as_equivalent(tmp_path: Path):
    raw = tmp_path / "raw.jsonl"
    clean = tmp_path / "clean.jsonl"
    _write_raw(
        raw,
        [
            json.dumps({"text": "same", "intent": "draft.email", "vault_source_chunk_id": "abc"}),
            json.dumps({"text": " same ", "intent": "draft.email", "vault_source_chunk_id": "abc"}),
        ],
    )
    stats = validate(raw, clean, {"abc"}, max_duplicates=1)
    # Both normalize to "same"; second is a duplicate.
    assert stats.accepted == 1
    assert stats.rejected_duplicate == 1


def test_validate_raises_on_missing_input(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        validate(tmp_path / "nope.jsonl", tmp_path / "clean.jsonl", set())


def test_validate_overwrites_clean_file(tmp_path: Path):
    raw = tmp_path / "raw.jsonl"
    clean = tmp_path / "clean.jsonl"
    clean.write_text("pre-existing garbage\n", encoding="utf-8")
    _write_raw(raw, [json.dumps({"text": "x", "intent": "dismiss", "vault_source_chunk_id": "abc"})])
    validate(raw, clean, {"abc"})
    content = clean.read_text(encoding="utf-8")
    assert "pre-existing" not in content
    assert "dismiss" in content
