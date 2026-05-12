"""CLI: stream synthetic intent records from Gemini into data/raw/intents.jsonl.

  python -m jarvis_training.synth.cli_generate --vault $JARVIS_VAULT_PATH \
      --raw training/data/raw/intents.jsonl

Idempotent: re-runs only fill intents that are below TARGET_RECORDS_PER_INTENT.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from jarvis_training.intents import TARGET_RECORDS_PER_INTENT
from jarvis_training.synth.gemini_client import GeminiClient, GeminiConfigError
from jarvis_training.synth.generate import generate
from jarvis_training.synth.prompt_builder import MAX_CHUNKS_PER_BATCH
from jarvis_training.synth.vault_loader import iter_chunks


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Stream Gemini-synthesized intent records to JSONL")
    p.add_argument("--vault", required=True, type=Path)
    p.add_argument("--raw", required=True, type=Path)
    p.add_argument("--batch-size", type=int, default=50)
    p.add_argument("--target-per-intent", type=int, default=TARGET_RECORDS_PER_INTENT)
    p.add_argument(
        "--max-chunks", type=int, default=MAX_CHUNKS_PER_BATCH,
        help="Window of vault chunks per call (caps prompt size).",
    )
    p.add_argument("--seed", type=int, default=42, help="Shuffle seed for chunk sampling")
    args = p.parse_args(argv)

    chunks = list(iter_chunks(args.vault))
    if not chunks:
        print(f"ERROR: no chunks in vault {args.vault}", file=sys.stderr)
        return 2
    random.Random(args.seed).shuffle(chunks)

    try:
        client = GeminiClient()
    except GeminiConfigError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    counts = generate(
        client,
        chunks[: args.max_chunks],
        args.raw,
        batch_size=args.batch_size,
        target_per_intent=args.target_per_intent,
    )
    print(json.dumps({k.value: v for k, v in counts.items()}, indent=2))
    return 0 if all(v >= args.target_per_intent for v in counts.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
