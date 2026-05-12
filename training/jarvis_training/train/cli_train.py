"""CLI: fine-tune MobileBERT on data/clean/intents.jsonl.

  python -m jarvis_training.train.cli_train \
      --data training/data/clean/intents.jsonl \
      --artifacts training/artifacts

Exit codes:
  0 — success; artifacts written
  1 — TrainingGateError (per-class accuracy below threshold) or unhandled error
  2 — usage / I/O precondition failure
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Fine-tune MobileBERT on cleaned intents JSONL")
    p.add_argument("--data", required=True, type=Path, help="Path to data/clean/intents.jsonl")
    p.add_argument(
        "--artifacts", required=True, type=Path, help="Directory to write checkpoint + tokenizer"
    )
    p.add_argument("--epochs", type=int, default=4)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument(
        "--min-class-acc",
        type=float,
        default=0.85,
        help="Per-class val accuracy gate. Training fails closed if any class is below.",
    )
    args = p.parse_args(argv)

    if not args.data.exists():
        print(f"ERROR: data file not found: {args.data}", file=sys.stderr)
        return 2

    # Heavy imports deferred until argparse succeeds, so --help works without TF.
    from jarvis_training.train.train import TrainingGateError, train

    try:
        stats = train(
            args.data,
            args.artifacts,
            epochs=args.epochs,
            batch_size=args.batch_size,
            seed=args.seed,
            min_per_class_val_acc=args.min_class_acc,
        )
    except TrainingGateError as e:
        print(json.dumps({"error": "gate_failed", "per_class_val_accuracy": e.per_class_acc, "threshold": e.threshold}, indent=2), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    print(json.dumps(stats.as_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
