"""CLI: 8-bit PTQ convert Keras → LiteRT and stage assets to the Android app.

  python -m jarvis_training.convert.cli_convert_ptq \
      --keras training/artifacts/mobilebert_intent.keras \
      --tokenizer training/artifacts/tokenizer.json \
      --data training/data/clean/intents.jsonl \
      --artifacts training/artifacts \
      --assets android/app/src/main/assets

Exit codes:
  0 — success; .tflite + metadata written, assets copied
  1 — ConvertSizeError (model too large) or unhandled error
  2 — usage / I/O precondition failure
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="PTQ-quantize the Keras MobileBERT checkpoint to LiteRT INT8"
    )
    p.add_argument("--keras", required=True, type=Path)
    p.add_argument("--tokenizer", required=True, type=Path)
    p.add_argument("--data", required=True, type=Path, help="data/clean/intents.jsonl path")
    p.add_argument("--artifacts", required=True, type=Path)
    p.add_argument(
        "--assets", required=True, type=Path,
        help="Android assets directory (e.g. android/app/src/main/assets)",
    )
    p.add_argument(
        "--size-limit-mb", type=float, default=30.0,
        help="Hard ceiling on the resulting intent_router.tflite size (MB).",
    )
    args = p.parse_args(argv)

    for path, label in [
        (args.keras, "keras"),
        (args.tokenizer, "tokenizer"),
        (args.data, "data"),
    ]:
        if not path.exists():
            print(f"ERROR: {label} path not found: {path}", file=sys.stderr)
            return 2

    from jarvis_training.convert.to_litert_ptq import ConvertSizeError, convert

    try:
        stats = convert(
            keras_path=args.keras,
            tokenizer_path=args.tokenizer,
            data_path=args.data,
            artifacts_dir=args.artifacts,
            android_assets_dir=args.assets,
            size_limit_mb=args.size_limit_mb,
        )
    except ConvertSizeError as e:
        print(
            json.dumps(
                {"error": "size_limit_exceeded", "size_mb": e.size_mb, "limit_mb": e.limit_mb},
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    print(json.dumps(stats.as_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
