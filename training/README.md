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
│   ├── train/                     # 1.3 (not yet implemented)
│   ├── convert/                   # 1.4 (not yet implemented)
│   └── eval/                      # 1.4 acceptance gates (not yet implemented)
└── tests/
    ├── fixtures/                  # tiny sample vault for vault_loader tests
    └── ...
```
