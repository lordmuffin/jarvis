"""Tests for synth.generate. The Gemini client is mocked — no live API calls."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import pytest

from jarvis_training.intents import INTENT_ORDER, Intent
from jarvis_training.synth.generate import (
    count_existing_per_intent,
    generate,
)
from jarvis_training.synth.vault_loader import iter_chunks


class FakeClient:
    """Yields the predetermined dicts; ignores prompt content."""

    def __init__(self, batches: list[list[dict]]) -> None:
        # batches is a queue: each generate_jsonl call consumes the head.
        self._batches = list(batches)
        self.call_count = 0

    def generate_jsonl(self, system_prompt: str, user_prompt: str) -> Iterable[dict]:
        self.call_count += 1
        if not self._batches:
            return iter([])
        return iter(self._batches.pop(0))


def _make_rec(intent: Intent, chunk_id: str, suffix: str = "") -> dict:
    return {
        "text": f"sample event text for {intent.value}{suffix}",
        "intent": intent.value,
        "rationale": "matches observable pattern",
        "vault_source_chunk_id": chunk_id,
    }


def test_count_existing_per_intent_on_missing_file(tmp_path: Path):
    counts = count_existing_per_intent(tmp_path / "nope.jsonl")
    assert all(v == 0 for v in counts.values())
    assert set(counts) == set(INTENT_ORDER)


def test_count_existing_per_intent_ignores_garbage(tmp_path: Path):
    p = tmp_path / "raw.jsonl"
    p.write_text(
        '{"intent":"draft.email","text":"x"}\n'
        "not json\n"
        "\n"
        '{"intent":"bogus","text":"x"}\n'
        '{"intent":"draft.email","text":"y"}\n',
        encoding="utf-8",
    )
    counts = count_existing_per_intent(p)
    assert counts[Intent.DRAFT_EMAIL] == 2
    assert counts[Intent.DISMISS] == 0


def test_generate_writes_records_until_target(tmp_path: Path, sample_vault: Path):
    chunks = list(iter_chunks(sample_vault))
    chunk_id = chunks[0].chunk_id

    # Per-intent batches: enough records so target_per_intent=2 is met quickly.
    per_intent_batch = [
        [_make_rec(i, chunk_id, f"-{n}") for n in range(2)]
        for i in INTENT_ORDER
    ]
    client = FakeClient(per_intent_batch)

    raw = tmp_path / "raw" / "intents.jsonl"
    counts = generate(client, chunks, raw, batch_size=2, target_per_intent=2)

    assert all(counts[i] >= 2 for i in INTENT_ORDER)
    lines = raw.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2 * len(INTENT_ORDER)
    for line in lines:
        rec = json.loads(line)
        assert rec["intent"] in {i.value for i in INTENT_ORDER}


def test_generate_is_idempotent(tmp_path: Path, sample_vault: Path):
    chunks = list(iter_chunks(sample_vault))
    chunk_id = chunks[0].chunk_id
    raw = tmp_path / "raw" / "intents.jsonl"

    # First run: fills draft.email to 2.
    first_client = FakeClient(
        # one batch per intent in canonical order
        [[_make_rec(i, chunk_id, f"-r1-{n}") for n in range(2)] for i in INTENT_ORDER]
    )
    generate(first_client, chunks, raw, batch_size=2, target_per_intent=2)
    counts_after_first = count_existing_per_intent(raw)
    assert all(counts_after_first[i] == 2 for i in INTENT_ORDER)

    # Second run: target unchanged → no new records, no client calls.
    second_client = FakeClient([])
    generate(second_client, chunks, raw, batch_size=2, target_per_intent=2)
    counts_after_second = count_existing_per_intent(raw)
    assert counts_after_second == counts_after_first
    assert second_client.call_count == 0


def test_generate_drops_records_with_wrong_intent(tmp_path: Path, sample_vault: Path):
    chunks = list(iter_chunks(sample_vault))
    chunk_id = chunks[0].chunk_id
    raw = tmp_path / "raw.jsonl"

    # Client returns mostly noise for the device.action call, then good records
    # for everything else. The mismatched records must be dropped.
    bad_batch_for_first = [
        {"text": "wrong", "intent": "draft.email", "vault_source_chunk_id": chunk_id},
        _make_rec(Intent.DEVICE_ACTION, chunk_id),
    ]
    other_batches = [
        [_make_rec(i, chunk_id)] for i in INTENT_ORDER if i is not Intent.DEVICE_ACTION
    ]
    client = FakeClient([bad_batch_for_first] + other_batches)

    counts = generate(client, chunks, raw, batch_size=1, target_per_intent=1)
    assert counts[Intent.DEVICE_ACTION] == 1


def test_generate_drops_dangling_chunk_id(tmp_path: Path, sample_vault: Path):
    chunks = list(iter_chunks(sample_vault))
    real_chunk_id = chunks[0].chunk_id
    raw = tmp_path / "raw.jsonl"

    # First record has a fake chunk_id, second has a real one. Only the second
    # should land. Each intent gets its own batch in canonical order.
    batches = []
    for i, intent in enumerate(INTENT_ORDER):
        if i == 0:
            batches.append(
                [
                    {
                        "text": "fabricated",
                        "intent": intent.value,
                        "vault_source_chunk_id": "ffffffffffffffff",  # not in vault
                    },
                    _make_rec(intent, real_chunk_id),
                ]
            )
        else:
            batches.append([_make_rec(intent, real_chunk_id)])
    client = FakeClient(batches)

    generate(client, chunks, raw, batch_size=2, target_per_intent=1)
    lines = raw.read_text(encoding="utf-8").strip().splitlines()
    for line in lines:
        rec = json.loads(line)
        assert rec["vault_source_chunk_id"] == real_chunk_id


def test_generate_breaks_when_client_produces_nothing(tmp_path: Path, sample_vault: Path):
    """If the client produces zero usable records, we don't infinite-loop."""
    chunks = list(iter_chunks(sample_vault))
    raw = tmp_path / "raw.jsonl"
    # An empty batch for every intent.
    client = FakeClient([[] for _ in INTENT_ORDER])
    counts = generate(client, chunks, raw, batch_size=1, target_per_intent=5)
    assert all(counts[i] == 0 for i in INTENT_ORDER)
    # We made exactly one call per intent before giving up on each.
    assert client.call_count == len(INTENT_ORDER)


def test_generate_rejects_empty_vault_chunks(tmp_path: Path):
    raw = tmp_path / "raw.jsonl"
    with pytest.raises(ValueError, match="grounding"):
        generate(FakeClient([]), [], raw, target_per_intent=1)
