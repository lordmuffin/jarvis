"""Validate raw synthetic data, emit clean/intents.jsonl.

Rejection rules (in order):
  1. Malformed JSON — count as `rejected_malformed`.
  2. Missing or non-string `text` → `rejected_malformed`.
  3. `intent` not in the canonical schema → `rejected_invalid_intent`.
  4. `vault_source_chunk_id` not in the supplied set of valid chunk ids →
     `rejected_dangling_chunk`.
  5. Same `text` (post-strip) appearing more than `max_duplicates` times across the
     whole dataset → `rejected_duplicate` (only the 4th+ instance is dropped).

The validator is deterministic and order-preserving for accepted rows.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


from jarvis_training.intents import INTENT_VALUES


@dataclass
class ValidationStats:
    total_in: int = 0
    accepted: int = 0
    rejected_malformed: int = 0
    rejected_invalid_intent: int = 0
    rejected_dangling_chunk: int = 0
    rejected_duplicate: int = 0
    accepted_per_intent: Counter[str] = field(default_factory=Counter)

    def as_dict(self) -> dict:
        return {
            "total_in": self.total_in,
            "accepted": self.accepted,
            "rejected_malformed": self.rejected_malformed,
            "rejected_invalid_intent": self.rejected_invalid_intent,
            "rejected_dangling_chunk": self.rejected_dangling_chunk,
            "rejected_duplicate": self.rejected_duplicate,
            "accepted_per_intent": dict(self.accepted_per_intent),
        }


def validate(
    raw_path: Path,
    clean_path: Path,
    valid_chunk_ids: set[str],
    *,
    max_duplicates: int = 3,
) -> ValidationStats:
    """Process raw_path → clean_path. Returns ValidationStats."""
    if not raw_path.exists():
        raise FileNotFoundError(f"raw_path does not exist: {raw_path}")

    stats = ValidationStats()
    text_counts: Counter[str] = Counter()
    clean_path.parent.mkdir(parents=True, exist_ok=True)

    with raw_path.open("r", encoding="utf-8") as fin, clean_path.open("w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            stats.total_in += 1

            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                stats.rejected_malformed += 1
                continue

            text = rec.get("text")
            if not isinstance(text, str) or not text.strip():
                stats.rejected_malformed += 1
                continue

            intent = rec.get("intent")
            if not isinstance(intent, str) or intent not in INTENT_VALUES:
                stats.rejected_invalid_intent += 1
                continue

            chunk_id = rec.get("vault_source_chunk_id")
            if not isinstance(chunk_id, str) or chunk_id not in valid_chunk_ids:
                stats.rejected_dangling_chunk += 1
                continue

            normalized = text.strip()
            text_counts[normalized] += 1
            if text_counts[normalized] > max_duplicates:
                stats.rejected_duplicate += 1
                continue

            fout.write(json.dumps(rec, separators=(",", ":"), ensure_ascii=False) + "\n")
            stats.accepted += 1
            stats.accepted_per_intent[intent] += 1

    return stats
