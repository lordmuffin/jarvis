"""Tests for synth.prompt_builder."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis_training.intents import (
    INTENT_DEFINITIONS,
    INTENT_ORDER,
    INTENT_SCHEMA_VERSION,
    Intent,
)
from jarvis_training.synth.prompt_builder import (
    MAX_CHARS_PER_CHUNK,
    MAX_CHUNKS_PER_BATCH,
    build_batch,
    build_system_prompt,
    render_for_review,
)
from jarvis_training.synth.vault_loader import iter_chunks


def test_system_prompt_contains_hard_constraints():
    p = build_system_prompt()
    # The constraints are the integrity boundary; they must be present verbatim.
    assert "HARD CONSTRAINTS" in p
    assert "You are NOT an author" in p
    assert "Do NOT invent personas" in p
    assert "Do NOT extrapolate" in p


def test_system_prompt_lists_all_seven_intents_in_canonical_order():
    p = build_system_prompt()
    positions = [p.find(f"`{i.value}`") for i in INTENT_ORDER]
    assert all(pos != -1 for pos in positions), "every intent must appear"
    assert positions == sorted(positions), "intents must appear in canonical order"


def test_system_prompt_pins_schema_version():
    p = build_system_prompt()
    assert INTENT_SCHEMA_VERSION in p


def test_system_prompt_includes_every_definition():
    p = build_system_prompt()
    for intent, defn in INTENT_DEFINITIONS.items():
        # The first short clause of each definition should appear verbatim.
        first_clause = defn.split(".")[0]
        assert first_clause in p, f"definition missing for {intent.value}"


def test_system_prompt_specifies_jsonl_output_format():
    p = build_system_prompt()
    assert "JSONL" in p
    assert '"text"' in p
    assert '"intent"' in p
    assert '"rationale"' in p
    assert '"vault_source_chunk_id"' in p
    # Explicit "no markdown fences" — Gemini loves to wrap in ```.
    assert "no markdown fences" in p.lower()


def test_build_batch_renders_target_intent_and_count(sample_vault: Path):
    chunks = list(iter_chunks(sample_vault))
    batch = build_batch(Intent.DRAFT_REPLY, target_count=7, vault_chunks=chunks)
    assert batch.target_intent is Intent.DRAFT_REPLY
    assert batch.target_count == 7
    assert "TARGET_INTENT: draft.reply" in batch.user_prompt
    assert "TARGET_COUNT: 7" in batch.user_prompt
    # Every supplied chunk's id appears verbatim so the model can cite it.
    for c in chunks[:MAX_CHUNKS_PER_BATCH]:
        assert c.chunk_id in batch.user_prompt


def test_build_batch_truncates_chunks_over_cap(sample_vault: Path):
    # The fixture vault is small; synthesize a large list by repeating.
    chunks = list(iter_chunks(sample_vault))
    blown_up = (chunks * 100)[: MAX_CHUNKS_PER_BATCH + 10]
    batch = build_batch(Intent.NOTE_CAPTURE, target_count=1, vault_chunks=blown_up)
    # We can't directly inspect the trimmed list, but we can count chunk_id mentions
    # and assert it's at most the cap (one mention per chunk in the rendered block).
    assert len(batch.chunk_ids) == MAX_CHUNKS_PER_BATCH


def test_build_batch_rejects_empty_chunks():
    with pytest.raises(ValueError, match="grounding"):
        build_batch(Intent.DISMISS, target_count=1, vault_chunks=[])


def test_build_batch_rejects_nonpositive_count(sample_vault: Path):
    chunks = list(iter_chunks(sample_vault))
    with pytest.raises(ValueError, match="target_count"):
        build_batch(Intent.DISMISS, target_count=0, vault_chunks=chunks)


def test_build_batch_truncates_very_long_chunk_body(tmp_path: Path):
    """Chunks longer than MAX_CHARS_PER_CHUNK get an ellipsis suffix."""
    from jarvis_training.synth.vault_loader import VaultChunk

    long_body = "x" * (MAX_CHARS_PER_CHUNK + 500)
    chunk = VaultChunk(
        chunk_id="abc123",
        source_path="t.md",
        heading="huge",
        text=long_body,
        link_targets=(),
    )
    batch = build_batch(Intent.NOTE_CAPTURE, target_count=1, vault_chunks=[chunk])
    # The rendered chunk in the user prompt should contain an ellipsis indicator
    # and should not contain the full untruncated body.
    assert "…" in batch.user_prompt
    assert "x" * (MAX_CHARS_PER_CHUNK + 100) not in batch.user_prompt


def test_render_for_review_includes_both_prompts():
    review = render_for_review()
    assert "SYSTEM PROMPT" in review
    assert "USER PROMPT TEMPLATE" in review
    assert "HARD CONSTRAINTS" in review
