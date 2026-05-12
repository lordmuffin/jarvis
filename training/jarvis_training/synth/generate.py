"""Stream JSONL records from a Gemini-compatible client into data/raw/intents.jsonl.

Idempotent: re-runs read the existing raw file, count records per intent, and skip
any intent already at or above TARGET_RECORDS_PER_INTENT. Crashes mid-run leave a
valid partial file (we append + flush per record).

The actual Gemini SDK adapter is NOT in this module — it lives in
`jarvis_training.synth.gemini_client` (added after the 1.2 prompt-review gate
clears). Tests and the CI lint pass run against the Protocol below with a mock.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Protocol

from jarvis_training.intents import INTENT_ORDER, TARGET_RECORDS_PER_INTENT, Intent
from jarvis_training.synth.prompt_builder import build_batch
from jarvis_training.synth.vault_loader import VaultChunk


class JsonlClient(Protocol):
    """Narrow protocol for the upstream LLM call.

    Implementations stream parsed JSON objects, one per record. Any malformed
    line should be silently dropped by the implementation — this generator
    cannot recover from "half a JSON object".
    """

    def generate_jsonl(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Iterable[dict]: ...


def count_existing_per_intent(raw_path: Path) -> dict[Intent, int]:
    """Read raw_path and count records per known intent. Unknown intents ignored."""
    counts: dict[Intent, int] = dict.fromkeys(INTENT_ORDER, 0)
    if not raw_path.exists():
        return counts
    value_to_intent = {i.value: i for i in INTENT_ORDER}
    with raw_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            v = obj.get("intent")
            if isinstance(v, str) and v in value_to_intent:
                counts[value_to_intent[v]] += 1
    return counts


def generate(
    client: JsonlClient,
    vault_chunks: list[VaultChunk],
    raw_path: Path,
    *,
    batch_size: int = 50,
    target_per_intent: int = TARGET_RECORDS_PER_INTENT,
) -> dict[Intent, int]:
    """Generate up to `target_per_intent` records per intent, appending to raw_path.

    Returns final per-intent counts (which may exceed target if a batch came back
    with extras — we don't truncate, we just stop asking for more).
    """
    if not vault_chunks:
        raise ValueError("vault_chunks must be non-empty — synthesis is grounding-only")

    raw_path.parent.mkdir(parents=True, exist_ok=True)
    counts = count_existing_per_intent(raw_path)

    with raw_path.open("a", encoding="utf-8") as f:
        for intent in INTENT_ORDER:
            while counts[intent] < target_per_intent:
                remaining = target_per_intent - counts[intent]
                this_batch = min(batch_size, remaining)
                batch = build_batch(intent, this_batch, vault_chunks)

                produced_this_call = 0
                for rec in client.generate_jsonl(batch.system_prompt, batch.user_prompt):
                    if not isinstance(rec, dict):
                        continue
                    if rec.get("intent") != intent.value:
                        # Wrong intent — the client may have wandered. Drop.
                        continue
                    if not isinstance(rec.get("text"), str) or not rec["text"].strip():
                        continue
                    if rec.get("vault_source_chunk_id") not in {c.chunk_id for c in vault_chunks}:
                        # The validator would drop this anyway. Drop now to save disk.
                        continue
                    f.write(json.dumps(rec, separators=(",", ":"), ensure_ascii=False) + "\n")
                    f.flush()
                    counts[intent] += 1
                    produced_this_call += 1
                    if counts[intent] >= target_per_intent:
                        break

                if produced_this_call == 0:
                    # The client produced nothing usable for this intent on this batch.
                    # Break the inner while to avoid an infinite loop; the next run can
                    # try again (idempotent).
                    break

    return counts
