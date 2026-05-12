# Jarvis training pipeline.
#
# Each target is idempotent and depends on its predecessor. Re-running with
# unchanged inputs is a no-op. Outputs land in:
#   data/raw/intents.jsonl       — 1.2 synth output
#   data/clean/intents.jsonl     — 1.2 validate output
#   artifacts/mobilebert_intent.keras  — 1.3
#   artifacts/intent_router.tflite     — 1.4
#   artifacts/tokenizer.json           — 1.3 (single source of truth)
#   artifacts/model_metadata.json      — 1.4 sidecar

PYTHON ?= python
VAULT  ?= $(JARVIS_VAULT_PATH)

.PHONY: help install lint test synth validate train convert all clean review-prompt

help:
	@echo "Targets:"
	@echo "  install         — pip install -e .[dev]"
	@echo "  lint            — ruff check"
	@echo "  test            — pytest"
	@echo "  review-prompt   — emit the 1.2 grounding prompts for human review"
	@echo "  synth           — 1.2 Gemini → data/raw (requires VAULT, gated; see docs)"
	@echo "  validate        — 1.2 raw → clean"
	@echo "  train           — 1.3 MobileBERT fine-tune"
	@echo "  convert         — 1.4 LiteRT conversion (PTQ default, QAT fallback)"
	@echo "  all             — synth + validate + train + convert"
	@echo "  clean           — wipe data/ and artifacts/ (raw kept; rerun synth)"

install:
	$(PYTHON) -m pip install -e ".[dev]"

lint:
	ruff check jarvis_training tests

test:
	$(PYTHON) -m pytest tests/ -q

review-prompt:
	$(PYTHON) -c "from jarvis_training.synth.prompt_builder import render_for_review; print(render_for_review())"

synth:
	@if [ -z "$(VAULT)" ]; then echo "VAULT (or \$$JARVIS_VAULT_PATH) is required"; exit 2; fi
	@if [ -z "$(JARVIS_CLOUD_LLM_API_KEY)" ]; then echo "JARVIS_CLOUD_LLM_API_KEY is required"; exit 2; fi
	$(PYTHON) -m jarvis_training.synth.cli_generate --vault "$(VAULT)" --raw data/raw/intents.jsonl

validate:
	@if [ -z "$(VAULT)" ]; then echo "VAULT is required"; exit 2; fi
	$(PYTHON) -m jarvis_training.synth.cli_validate --vault "$(VAULT)" \
		--raw data/raw/intents.jsonl \
		--clean data/clean/intents.jsonl

train:
	$(PYTHON) -m jarvis_training.train.cli_train \
		--data data/clean/intents.jsonl \
		--artifacts artifacts

convert:
	$(PYTHON) -m jarvis_training.convert.cli_convert_ptq \
		--keras artifacts/mobilebert_intent.keras \
		--tokenizer artifacts/tokenizer.json \
		--data data/clean/intents.jsonl \
		--artifacts artifacts \
		--assets ../android/app/src/main/assets

all: synth validate train convert

clean:
	rm -rf data/clean artifacts
	@echo "data/raw/ kept (regenerable but expensive). To wipe: rm -rf data/raw"
