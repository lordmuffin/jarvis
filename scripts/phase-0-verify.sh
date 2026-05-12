#!/usr/bin/env bash
# Phase 0 environment verifier — run inside Termux on the target device.
#
# Asserts that Tailscale reaches the homelab, Shizuku is alive via rish, and the
# Syncthing-mounted vault is in place. Exits 0 on success. On any failure, exits
# non-zero and prints a single-line remediation hint per failed check.
#
# Usage:
#   bash scripts/phase-0-verify.sh
#
# Required environment (sourced from ~/.jarvisrc if not exported):
#   JARVIS_HOMELAB_HOST           tailscale hostname of the homelab
#   JARVIS_HOMELAB_HEALTH_PORT    port serving /healthz on the homelab
#   JARVIS_VAULT_PATH             absolute path to the Syncthing-mounted vault

set -u  # noundef: surface typos in env var names loudly
# Intentionally NOT set -e — we want to run every check and report all failures,
# not bail at the first miss.

# ---- pretty output --------------------------------------------------------

if [ -t 1 ]; then
  C_OK="\033[32m"
  C_FAIL="\033[31m"
  C_DIM="\033[2m"
  C_RESET="\033[0m"
else
  C_OK=""
  C_FAIL=""
  C_DIM=""
  C_RESET=""
fi

FAILURES=0
TOTAL=0

check() {
  # check <name> <command...>
  # On failure, prints a remediation hint passed via JARVIS_REMEDIATION.
  local name="$1"; shift
  TOTAL=$((TOTAL + 1))
  if "$@" >/dev/null 2>&1; then
    printf "%b  PASS%b  %s\n" "$C_OK" "$C_RESET" "$name"
  else
    FAILURES=$((FAILURES + 1))
    printf "%b  FAIL%b  %s\n" "$C_FAIL" "$C_RESET" "$name"
    if [ -n "${JARVIS_REMEDIATION:-}" ]; then
      printf "        %b→ %s%b\n" "$C_DIM" "$JARVIS_REMEDIATION" "$C_RESET"
    fi
  fi
  unset JARVIS_REMEDIATION
}

# ---- load config ----------------------------------------------------------

if [ -f "$HOME/.jarvisrc" ]; then
  # shellcheck disable=SC1091
  . "$HOME/.jarvisrc"
fi

# ---- 1: required env vars are set ----------------------------------------

JARVIS_REMEDIATION="set JARVIS_HOMELAB_HOST in ~/.jarvisrc (see docs/phase-0-bringup.md §5)"
check "JARVIS_HOMELAB_HOST is set"           test -n "${JARVIS_HOMELAB_HOST:-}"

JARVIS_REMEDIATION="set JARVIS_HOMELAB_HEALTH_PORT in ~/.jarvisrc"
check "JARVIS_HOMELAB_HEALTH_PORT is set"    test -n "${JARVIS_HOMELAB_HEALTH_PORT:-}"

JARVIS_REMEDIATION="set JARVIS_VAULT_PATH in ~/.jarvisrc"
check "JARVIS_VAULT_PATH is set"             test -n "${JARVIS_VAULT_PATH:-}"

# Without these we can't run the rest of the checks meaningfully.
if [ $FAILURES -ne 0 ]; then
  echo
  echo "Config missing. Fix the above before re-running. See docs/phase-0-bringup.md §5."
  exit 1
fi

# ---- 2: tailscale reachability -------------------------------------------

JARVIS_REMEDIATION="open the Tailscale app and confirm the tailnet is connected; check that $JARVIS_HOMELAB_HOST is online in your tailnet"
# `ping -c 1 -W 3` is portable across Termux's iputils and macOS ping.
check "ping $JARVIS_HOMELAB_HOST over Tailscale"  \
  ping -c 1 -W 3 "$JARVIS_HOMELAB_HOST"

JARVIS_REMEDIATION="confirm the homelab is exposing /healthz on port $JARVIS_HOMELAB_HEALTH_PORT (try from another tailnet node: curl http://$JARVIS_HOMELAB_HOST:$JARVIS_HOMELAB_HEALTH_PORT/healthz)"
check "GET http://$JARVIS_HOMELAB_HOST:$JARVIS_HOMELAB_HEALTH_PORT/healthz returns 2xx"  \
  curl -fsS --max-time 5 "http://$JARVIS_HOMELAB_HOST:$JARVIS_HOMELAB_HEALTH_PORT/healthz"

# ---- 3: shizuku via rish --------------------------------------------------

JARVIS_REMEDIATION="open Shizuku app → tap 'Start via wireless debugging'; if first-time setup, also go to Authorized applications and toggle Termux on"
check "rish is reachable in PATH"  command -v rish

# rish -v should print a version; if Shizuku service is down rish hangs, so cap with timeout.
JARVIS_REMEDIATION="restart Shizuku from the app; if Wireless Debugging was disabled after a reboot, re-enable it under Developer options"
check "rish -v returns a version"  bash -c 'timeout 5 rish -v 2>&1 | grep -qiE "shizuku|version"'

# ---- 4: vault is mounted and has at least one markdown file --------------

JARVIS_REMEDIATION="check Syncthing is running, the vault folder is paired Receive Only, and its path matches \$JARVIS_VAULT_PATH"
check "JARVIS_VAULT_PATH exists and is a directory"  test -d "$JARVIS_VAULT_PATH"

JARVIS_REMEDIATION="Syncthing finished pairing but no files have synced yet — wait for initial sync to complete"
# -quit on first match for speed on large vaults.
check "vault contains at least one .md file"  \
  bash -c 'find "$JARVIS_VAULT_PATH" -maxdepth 8 -name "*.md" -print -quit 2>/dev/null | grep -q .'

JARVIS_REMEDIATION="create \$JARVIS_VAULT_PATH/.jarvisrc per docs/phase-0-bringup.md §5"
check "vault has a readable .jarvisrc"  test -r "$JARVIS_VAULT_PATH/.jarvisrc"

# ---- 5: outbox can be created (write probe) ------------------------------
#
# The Receive-Only Syncthing setup must still permit writes from the phone into
# outbox/. If the homelab forgot the !outbox/** ignore pattern, Syncthing will
# revert this file within seconds — that's caught by the verify-script being run
# again later, not here. Here we only verify the directory can be created.

JARVIS_REMEDIATION="confirm \$JARVIS_VAULT_PATH is on a writable filesystem; if Syncthing is configured fully read-only this will fail and that's a config error on the homelab — see docs/phase-0-bringup.md §4.2"
check "can create vault outbox/ for jarvis writes"  \
  bash -c 'mkdir -p "$JARVIS_VAULT_PATH/outbox/jarvis-decisions" && touch "$JARVIS_VAULT_PATH/outbox/jarvis-decisions/.phase-0-write-probe" && rm "$JARVIS_VAULT_PATH/outbox/jarvis-decisions/.phase-0-write-probe"'

# ---- 6: helper tools used by Phase 1 -------------------------------------

JARVIS_REMEDIATION="pkg install sqlite (used by smoke-test to inspect the decision log)"
check "sqlite3 binary available"  command -v sqlite3

JARVIS_REMEDIATION="pkg install jq (used by training pipeline + smoke-test)"
check "jq binary available"  command -v jq

JARVIS_REMEDIATION="pkg install vulkan-loader vulkan-headers (used by Termux llama.cpp build)"
check "vulkaninfo or libvulkan present"  \
  bash -c 'command -v vulkaninfo >/dev/null 2>&1 || ls $PREFIX/lib/libvulkan* >/dev/null 2>&1'

# ---- summary --------------------------------------------------------------

echo
if [ $FAILURES -eq 0 ]; then
  printf "%b%d/%d checks passed.%b Phase 0 verified.\n" "$C_OK" "$TOTAL" "$TOTAL" "$C_RESET"
  exit 0
else
  printf "%b%d/%d checks failed.%b See remediation hints above.\n" "$C_FAIL" "$FAILURES" "$TOTAL" "$C_RESET"
  exit 1
fi
