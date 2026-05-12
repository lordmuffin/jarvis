"""JSONL loader + 80/10/10 stratified split + label-id mapping for 1.3 training.

Input: `data/clean/intents.jsonl` (output of `synth/validate.py`). Each record:
    {text, intent, rationale, vault_source_chunk_id}

This module is pure data wrangling — no TF dependency — so the splitting logic
is testable without the heavy training stack installed.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from jarvis_training.intents import INTENT_ORDER, Intent


def load_jsonl(path: Path) -> list[dict]:
    """Stream-read a JSONL file into a list of dicts.

    Input is assumed to be post-validation (`synth/validate.py` is the single
    source of schema enforcement). This loader does not re-validate.
    """
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def stratified_split(
    records: Sequence[dict],
    *,
    seed: int = 42,
    val_size: float = 0.10,
    test_size: float = 0.10,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Split records 80/10/10 stratified by the `intent` field.

    Implemented in two passes via sklearn: first split off (val + test), then
    halve that into val and test. Both passes stratify on the string intent.
    """
    from sklearn.model_selection import train_test_split

    labels = [r["intent"] for r in records]
    holdout_frac = val_size + test_size
    train_records, holdout_records, _, holdout_labels = train_test_split(
        list(records),
        labels,
        test_size=holdout_frac,
        random_state=seed,
        stratify=labels,
    )
    # Second split: halve holdout into val + test, again stratified.
    relative_test = test_size / holdout_frac
    val_records, test_records = train_test_split(
        holdout_records,
        test_size=relative_test,
        random_state=seed,
        stratify=holdout_labels,
    )
    return train_records, val_records, test_records


def to_label_ids(records: Sequence[dict]) -> np.ndarray:
    """Map each record's `intent` string to its ordinal in `INTENT_ORDER`.

    This is the ONLY place where label ordering is resolved. The rest of the
    training pipeline operates on int ids that line up with the LiteRT softmax
    head and the Android `Intent.fromOrdinal()`.
    """
    return np.asarray(
        [INTENT_ORDER.index(Intent(r["intent"])) for r in records],
        dtype=np.int32,
    )


def extract_texts(records: Sequence[dict]) -> list[str]:
    return [r["text"] for r in records]
