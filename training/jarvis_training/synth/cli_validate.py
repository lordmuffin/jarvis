"""CLI for the validate step: `python -m jarvis_training.synth.cli_validate ...`"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jarvis_training.synth.validate import validate
from jarvis_training.synth.vault_loader import collect_chunk_ids


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Validate raw synthetic data → clean JSONL")
    p.add_argument("--vault", required=True, type=Path, help="vault root (for chunk_id set)")
    p.add_argument("--raw", required=True, type=Path, help="input raw JSONL")
    p.add_argument("--clean", required=True, type=Path, help="output clean JSONL")
    p.add_argument("--max-duplicates", type=int, default=3)
    args = p.parse_args(argv)

    valid_ids = collect_chunk_ids(args.vault)
    if not valid_ids:
        print(f"ERROR: no chunks found in vault {args.vault}", file=sys.stderr)
        return 2

    stats = validate(args.raw, args.clean, valid_ids, max_duplicates=args.max_duplicates)
    print(json.dumps(stats.as_dict(), indent=2))
    if stats.accepted == 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
