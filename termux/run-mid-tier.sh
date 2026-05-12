#!/usr/bin/env bash
# Start the llama.cpp HTTP server for the Jarvis mid-tier.
# Listens on 127.0.0.1:8080 — phone-local only, no LAN/WAN exposure.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Config ----------------------------------------------------------------
SERVER_BIN="${SERVER_BIN:-$HOME/.jarvis/llama.cpp/build/bin/llama-server}"
MODEL_PATH="${JARVIS_MID_TIER_MODEL_PATH:-}"
HOST="${JARVIS_MID_TIER_HOST:-127.0.0.1}"
PORT="${JARVIS_MID_TIER_PORT:-8080}"

# Sensible defaults for a 3B-class model on a Pixel 8.
CTX_SIZE="${JARVIS_MID_TIER_CTX:-4096}"
N_THREADS="${JARVIS_MID_TIER_THREADS:-4}"
GPU_LAYERS="${JARVIS_MID_TIER_NGL:-99}"   # offload everything we can to Vulkan

# Source ~/.jarvisrc for $JARVIS_MID_TIER_MODEL_PATH if it wasn't passed in env.
if [ -z "$MODEL_PATH" ] && [ -f "$HOME/.jarvisrc" ]; then
  # shellcheck disable=SC1091
  . "$HOME/.jarvisrc"
  MODEL_PATH="${JARVIS_MID_TIER_MODEL_PATH:-}"
fi

if [ ! -x "$SERVER_BIN" ]; then
  echo "ERROR: $SERVER_BIN is not executable. Run termux/build-llama.sh first." >&2
  exit 2
fi
if [ -z "$MODEL_PATH" ] || [ ! -r "$MODEL_PATH" ]; then
  echo "ERROR: JARVIS_MID_TIER_MODEL_PATH is not set or unreadable: $MODEL_PATH" >&2
  echo "  Download a 3B-class GGUF (e.g. Qwen2.5-3B-Instruct-Q4_K_M) to ~/.jarvis/models/ and set the path in ~/.jarvisrc" >&2
  exit 2
fi

# --- Launch via the perf-core pinning wrapper ------------------------------
exec "$HERE/taskset-wrapper.sh" \
  "$SERVER_BIN" \
  --model "$MODEL_PATH" \
  --host "$HOST" \
  --port "$PORT" \
  --ctx-size "$CTX_SIZE" \
  --threads "$N_THREADS" \
  --n-gpu-layers "$GPU_LAYERS" \
  --metrics
