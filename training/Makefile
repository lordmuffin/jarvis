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
	@echo "1.2 Gemini synth is gated. To unblock:"
	@echo "  1. Run 'make review-prompt > /tmp/jarvis-prompt-review.txt'"
	@echo "  2. Have the user approve it."
	@echo "  3. Add jarvis_training/synth/gemini_client.py (real SDK adapter)."
	@echo "  4. Re-run 'make synth'."
	@exit 3

validate:
	@if [ -z "$(VAULT)" ]; then echo "VAULT is required"; exit 2; fi
	$(PYTHON) -m jarvis_training.synth.cli_validate --vault "$(VAULT)" \
		--raw data/raw/intents.jsonl \
		--clean data/clean/intents.jsonl

train:
	@echo "1.3 not yet implemented"
	@exit 3

convert:
	@echo "1.4 not yet implemented"
	@exit 3

all: synth validate train convert

clean:
	rm -rf data/clean artifacts
	@echo "data/raw/ kept (regenerable but expensive). To wipe: rm -rf data/raw"
