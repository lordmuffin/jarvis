#!/usr/bin/env bash
# Clone and build llama.cpp at a pinned SHA into ~/.jarvis/llama.cpp.
#
# Vulkan is the on-device GPU backend on Tensor G3 (Mali-G715). Falls back to
# CPU automatically if Vulkan loader is missing — but the verify script in
# Phase 0 catches that before we get here.
set -euo pipefail

# --------------------------------------------------------------------------
# Pinned upstream SHA. To bump:
#   1. Skim llama.cpp release notes since the current SHA.
#   2. Update this constant.
#   3. Rerun this script and validate manually with a few escalate.burst toasts.
# --------------------------------------------------------------------------
LLAMA_CPP_PINNED_SHA="${LLAMA_CPP_PINNED_SHA:-9e75c4960dc55a2ff96bbf24e5dee99cd8ce1ebd}"
LLAMA_CPP_REPO="${LLAMA_CPP_REPO:-https://github.com/ggerganov/llama.cpp}"
INSTALL_ROOT="${INSTALL_ROOT:-$HOME/.jarvis/llama.cpp}"
BUILD_DIR="${BUILD_DIR:-$INSTALL_ROOT/build}"

log() { printf "[build-llama] %s\n" "$*"; }

require() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required tool: $1" >&2
    echo "Run docs/phase-0-bringup.md §1.1 'pkg install' first." >&2
    exit 2
  fi
}

require git
require cmake
require clang
require make

mkdir -p "$INSTALL_ROOT"

# --------- Clone or fetch -------------------------------------------------
if [ ! -d "$INSTALL_ROOT/.git" ]; then
  log "cloning $LLAMA_CPP_REPO → $INSTALL_ROOT"
  git clone --filter=blob:none "$LLAMA_CPP_REPO" "$INSTALL_ROOT"
fi

cd "$INSTALL_ROOT"
git fetch --all --tags --quiet
log "checking out pinned SHA $LLAMA_CPP_PINNED_SHA"
git checkout --quiet "$LLAMA_CPP_PINNED_SHA"

# --------- Build ----------------------------------------------------------
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Vulkan is requested; if the headers are missing cmake will tell us loudly.
log "configuring (Vulkan ON)"
cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DGGML_VULKAN=ON \
  -DLLAMA_BUILD_SERVER=ON \
  -DLLAMA_BUILD_TESTS=OFF \
  -DLLAMA_BUILD_EXAMPLES=OFF

log "compiling (this can take 10-30 min on a Pixel 8)"
cmake --build . --config Release --target llama-server --parallel "$(nproc)"

# --------- Verify ---------------------------------------------------------
SERVER_BIN="$BUILD_DIR/bin/llama-server"
if [ ! -x "$SERVER_BIN" ]; then
  echo "Build finished but $SERVER_BIN is missing." >&2
  exit 3
fi

# Smoke check — just ensure it can print --help without crashing.
if ! "$SERVER_BIN" --help >/dev/null 2>&1; then
  echo "llama-server --help failed; check Vulkan loader is functioning." >&2
  exit 3
fi

log "build OK: $SERVER_BIN"
log "to run: termux/run-mid-tier.sh"
