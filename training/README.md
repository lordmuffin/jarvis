# jarvis-training

Phase 1 training pipeline. Four stages, each idempotent:

1. **synth** — walk the vault, build grounded prompts, stream JSONL records from Gemini
   2.5 Pro into `data/raw/`, then validate into `data/clean/`.
2. **train** — fine-tune MobileBERT on the cleaned JSONL, save the Keras checkpoint and
   the canonical `tokenizer.json`.
3. **convert** — PTQ (default) or QAT (fallback) to LiteRT, write `intent_router.tflite`
   plus `model_metadata.json`, copy both into `android/app/src/main/assets/`.
4. **eval** — sanity checks (size ≤ 30 MB, per-intent val accuracy ≥ 85%, tokenizer
   hash matches the committed value).

## Install

```sh
cd training
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
# Stage-specific extras as needed:
# pip install -e ".[train]"
# pip install -e ".[convert]"
# pip install -e ".[gemini]"  # only after the 1.2 prompt review gate is cleared
```

## Schema

The seven canonical intents live in [jarvis_training/intents.py](jarvis_training/intents.py).
**The ordinal order is frozen** — the LiteRT softmax head indexes by it. Bump
`INTENT_SCHEMA_VERSION` on every non-trivial change and re-run all four stages.

See [../docs/phase-1-architecture.md](../docs/phase-1-architecture.md) for the
schema definition and the gates that block synthetic data generation.

## Layout

```
training/
├── pyproject.toml
├── Makefile
├── jarvis_training/
│   ├── __init__.py
│   ├── intents.py                 # canonical schema (frozen ordinal)
│   ├── synth/
│   │   ├── vault_loader.py        # walk *.md, chunk by heading, strip wikilinks
│   │   ├── prompt_builder.py      # grounding system + user prompts (gated)
│   │   ├── generate.py            # idempotent JSONL streamer, client via Protocol
│   │   └── validate.py            # rejects invalid/dangling/duplicate records
│   ├── train/                     # 1.3 MobileBERT fine-tune
│   │   ├── data.py                # JSONL load + 80/10/10 stratified split
│   │   ├── model.py               # HF tokenizer + TFMobileBertForSequenceClassification
│   │   ├── train.py               # training loop + per-class gate + artifact save
│   │   └── cli_train.py           # CLI entry
│   ├── convert/                   # 1.4 LiteRT conversion (PTQ INT8)
│   │   ├── to_litert_ptq.py       # convert + metadata + asset copy
│   │   └── cli_convert_ptq.py     # CLI entry
│   └── eval/                      # 1.4 acceptance gates (not yet implemented)
└── tests/
    ├── fixtures/                  # tiny sample vault for vault_loader tests
    └── ...
```

## 1.3 — fine-tune

```sh
pip install -e ".[train,dev]"   # adds tensorflow, tf-keras, transformers, sklearn, ...
make train                       # = python -m jarvis_training.train.cli_train \
                                 #     --data data/clean/intents.jsonl --artifacts artifacts
```

Outputs (only on success — the script fails closed if any class's val accuracy
falls below 85%):

- `artifacts/mobilebert_intent.keras` — Keras-format checkpoint
- `artifacts/tokenizer.json` — HuggingFace tokenizer (the Android side parses this
  via `WordPieceTokenizer.fromTokenizerJson`)
- `artifacts/.tokenizer.sha256` — SHA-256 of `tokenizer.json` bytes
- `artifacts/train_stats.json` — per-class val accuracy, split sizes, seed, schema version

The 128-token max sequence length is mirrored by `WordPieceTokenizer.DEFAULT_MAX_LENGTH`
on Android. The `MAX_SEQ_LENGTH` constant in `train/model.py` must not drift from it
(there's a unit test that asserts the value).

## 1.4 — convert

```sh
pip install -e ".[train,convert,dev]"  # adds ai-edge-litert on top of the train extras
make convert                            # = python -m jarvis_training.convert.cli_convert_ptq ...
```

Applies 8-bit dynamic-range PTQ to `mobilebert_intent.keras`, then:

- Writes `artifacts/intent_router.tflite` and `artifacts/model_metadata.json`
- Copies `intent_router.tflite`, `tokenizer.json`, and `model_metadata.json` into
  `../android/app/src/main/assets/` (creates the directory if needed)

Fails closed if `intent_router.tflite` is ≥ 30 MB (override with `--size-limit-mb`,
but the on-device latency budget is the real reason for the limit). On size
failure, no metadata is written and no files are copied to the Android assets dir.

The `model_metadata.json::intent_order` array is generated from
`jarvis_training.intents.INTENT_ORDER`, so it cannot drift from the Python schema.
After `make convert`, rebuild the APK (`cd ../android && ./gradlew assembleDebug`)
to pick up the new assets.
