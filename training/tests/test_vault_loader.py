"""Tests for synth.vault_loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis_training.synth.vault_loader import (
    VaultChunk,
    _chunk_id_for,
    _strip_wikilinks,
    collect_chunk_ids,
    iter_chunks,
)


def test_strip_wikilinks_target_only():
    clean, targets = _strip_wikilinks("see [[Bob]] tomorrow")
    assert clean == "see Bob tomorrow"
    assert targets == ("Bob",)


def test_strip_wikilinks_target_with_display():
    clean, targets = _strip_wikilinks("ping [[Bob|@bob]] for review")
    assert clean == "ping @bob for review"
    assert targets == ("Bob",)


def test_strip_wikilinks_preserves_order_with_duplicates():
    clean, targets = _strip_wikilinks("[[A]] then [[B|b]] then [[A|alpha]]")
    assert clean == "A then b then alpha"
    assert targets == ("A", "B", "A")


def test_strip_wikilinks_passthrough_for_no_links():
    clean, targets = _strip_wikilinks("no links here")
    assert clean == "no links here"
    assert targets == ()


def test_chunk_id_is_deterministic_and_stable():
    a = _chunk_id_for("path.md", "hello world")
    b = _chunk_id_for("path.md", "hello world")
    c = _chunk_id_for("other.md", "hello world")
    d = _chunk_id_for("path.md", "hello world!")
    assert a == b
    assert a != c
    assert a != d
    assert len(a) == 16


def test_iter_chunks_yields_per_heading(sample_vault: Path):
    chunks = list(iter_chunks(sample_vault))
    # standup.md → 3 chunks (Standup notes, Today, Blockers).
    # Family.md  → 3 chunks (preamble, Recurring chores, Random).
    # The "Random" heading has no body besides the heading line; we keep the
    # heading-only chunk so downstream stages can choose whether to ground on it.
    headings = [(c.source_path, c.heading) for c in chunks]
    assert ("Areas/Personal/Family.md", None) in headings  # preamble
    assert ("Areas/Personal/Family.md", "Recurring chores") in headings
    assert ("Areas/Work/standup.md", "Standup notes") in headings
    assert ("Areas/Work/standup.md", "Today") in headings
    assert ("Areas/Work/standup.md", "Blockers") in headings


def test_iter_chunks_strips_wikilinks_in_body(sample_vault: Path):
    chunks = {(c.source_path, c.heading): c for c in iter_chunks(sample_vault)}
    today = chunks[("Areas/Work/standup.md", "Today")]
    assert "[[" not in today.text
    assert "draft PR" in today.text
    assert "@bob" in today.text
    assert "Bob" in today.link_targets


def test_iter_chunks_is_sorted_for_determinism(sample_vault: Path):
    runs = [
        [c.chunk_id for c in iter_chunks(sample_vault)]
        for _ in range(3)
    ]
    assert runs[0] == runs[1] == runs[2]


def test_chunk_text_is_post_wikilink_strip(sample_vault: Path):
    """The chunk_id must be derived from the post-strip text, not the raw text.

    Otherwise the validator's vault_source_chunk_id checks would be sensitive to
    whether Gemini saw the stripped or raw form.
    """
    chunks = list(iter_chunks(sample_vault))
    for c in chunks:
        assert "[[" not in c.text, f"chunk {c.chunk_id} still contains wikilink syntax"
        # And the id is reproducible from the same fields.
        assert c.chunk_id == _chunk_id_for(c.source_path, c.text)


def test_collect_chunk_ids_matches_iter_chunks(sample_vault: Path):
    ids = collect_chunk_ids(sample_vault)
    direct = {c.chunk_id for c in iter_chunks(sample_vault)}
    assert ids == direct
    assert len(ids) >= 5


def test_iter_chunks_raises_on_missing_dir(tmp_path: Path):
    with pytest.raises(NotADirectoryError):
        list(iter_chunks(tmp_path / "does-not-exist"))


def test_chunk_is_frozen():
    c = VaultChunk(
        chunk_id="x", source_path="p.md", heading="h", text="t", link_targets=()
    )
    with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
        c.text = "mutated"  # type: ignore[misc]
