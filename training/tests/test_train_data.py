"""Tests for jarvis_training.train.data (split + label-id correctness).

Heavy training paths (TF, transformers) are covered by the make-target smoke
run, not unit tests. These tests focus on the pure-Python parts so they run
under `pip install -e ".[dev]"` augmented with numpy/sklearn.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

pytest.importorskip("numpy")
pytest.importorskip("sklearn")

from jarvis_training.intents import INTENT_ORDER, Intent
from jarvis_training.train.data import (
    extract_texts,
    load_jsonl,
    stratified_split,
    to_label_ids,
)


def _balanced_records(per_class: int = 100) -> list[dict]:
    return [
        {
            "text": f"text-{intent.value}-{i}",
            "intent": intent.value,
            "rationale": "test",
            "vault_source_chunk_id": "0" * 16,
        }
        for intent in INTENT_ORDER
        for i in range(per_class)
    ]


def test_load_jsonl_roundtrips(tmp_path: Path):
    records = _balanced_records(per_class=2)
    p = tmp_path / "intents.jsonl"
    with p.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
        f.write("\n")  # blank line tolerated
    assert load_jsonl(p) == records


def test_stratified_split_has_all_seven_intents_in_every_split():
    records = _balanced_records(per_class=100)
    train, val, test = stratified_split(records, seed=42)
    for split, name in [(train, "train"), (val, "val"), (test, "test")]:
        intents = {r["intent"] for r in split}
        assert intents == {i.value for i in INTENT_ORDER}, (
            f"split {name!r} is missing intents"
        )


def test_stratified_split_proportions_are_80_10_10_within_one():
    per_class = 100
    records = _balanced_records(per_class=per_class)
    train, val, test = stratified_split(records, seed=42)
    train_c = Counter(r["intent"] for r in train)
    val_c = Counter(r["intent"] for r in val)
    test_c = Counter(r["intent"] for r in test)
    for intent in INTENT_ORDER:
        # 80/10/10 of 100 = 80/10/10 exactly, but sklearn may shift by 1
        # under rounding. Allow ±1 per class.
        assert abs(train_c[intent.value] - 80) <= 1
        assert abs(val_c[intent.value] - 10) <= 1
        assert abs(test_c[intent.value] - 10) <= 1


def test_stratified_split_is_deterministic_given_seed():
    records = _balanced_records(per_class=50)
    a = stratified_split(records, seed=7)
    b = stratified_split(records, seed=7)
    assert [r["text"] for r in a[0]] == [r["text"] for r in b[0]]
    assert [r["text"] for r in a[1]] == [r["text"] for r in b[1]]
    assert [r["text"] for r in a[2]] == [r["text"] for r in b[2]]


def test_to_label_ids_matches_canonical_intent_order():
    records = [{"intent": i.value} for i in INTENT_ORDER]
    ids = to_label_ids(records)
    assert list(ids) == list(range(len(INTENT_ORDER)))
    # Explicit sanity check on the load-bearing ordinals:
    by_value = {INTENT_ORDER[ordinal].value: ordinal for ordinal in range(len(INTENT_ORDER))}
    assert by_value["device.action"] == 0
    assert by_value["draft.email"] == 1
    assert by_value["draft.reply"] == 2
    assert by_value["schedule.event"] == 3
    assert by_value["escalate.burst"] == 4
    assert by_value["note.capture"] == 5
    assert by_value["dismiss"] == 6


def test_to_label_ids_rejects_unknown_intent():
    with pytest.raises(ValueError):
        to_label_ids([{"intent": "not.a.real.intent"}])


def test_extract_texts_preserves_order():
    records = [{"text": "a"}, {"text": "b"}, {"text": "c"}]
    assert extract_texts(records) == ["a", "b", "c"]


def test_max_seq_length_matches_android_constant():
    """MAX_SEQ_LENGTH must equal Android's WordPieceTokenizer.DEFAULT_MAX_LENGTH (=128).

    If either side moves, training-time tokenization and on-device tokenization
    truncate differently, silently degrading accuracy. The Android constant is
    documented in android/app/src/main/java/dev/jarvis/service/inference/WordPieceTokenizer.kt.
    """
    from jarvis_training.train.model import MAX_SEQ_LENGTH

    assert MAX_SEQ_LENGTH == 128


def test_intent_string_to_enum_round_trip():
    for intent in INTENT_ORDER:
        assert Intent(intent.value) is intent
