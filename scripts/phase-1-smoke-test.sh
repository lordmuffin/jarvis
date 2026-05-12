#!/usr/bin/env bash
# Phase 1 host-side smoke test.
#
# Drives the connected Pixel 8 over ADB:
#   1. Install the latest debug APK.
#   2. Grant Shizuku permission via rish (sanity, doesn't gate the smoke test).
#   3. Fire 100 synthetic events via `am broadcast` to the debug-only
#      SmokeTestReceiver.
#   4. Pull the decision log from the app's databases/ dir.
#   5. Assert: >=95 classified, p95 latency < 500ms, no service restarts.
#
# Loud structured failure messages naming the offending metric.
set -euo pipefail

ADB="${ADB:-adb}"
APK="${APK:-android/app/build/outputs/apk/debug/app-debug.apk}"
PKG="${PKG:-dev.jarvis.debug}"
RECEIVER_ACTION="${RECEIVER_ACTION:-dev.jarvis.testing.SMOKE_EVENT}"
EVENT_COUNT="${EVENT_COUNT:-100}"
P95_BUDGET_MS="${P95_BUDGET_MS:-500}"
ACCEPTED_FLOOR="${ACCEPTED_FLOOR:-95}"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

c_ok=$'\033[32m'; c_fail=$'\033[31m'; c_reset=$'\033[0m'
ok()   { printf "%bOK%b   %s\n" "$c_ok" "$c_reset" "$*"; }
fail() { printf "%bFAIL%b %s\n" "$c_fail" "$c_reset" "$*"; exit 1; }

require_cmd() { command -v "$1" >/dev/null 2>&1 || fail "missing required tool: $1"; }
require_cmd "$ADB"
require_cmd sqlite3
require_cmd awk

# ---------- 1. Install ------------------------------------------------------

if [ ! -f "$APK" ]; then
  fail "APK not found at $APK — run ./gradlew :app:assembleDebug first"
fi
ok "found $APK"

"$ADB" install -r -t "$APK" >/dev/null || fail "adb install failed"
ok "installed $PKG"

# ---------- 2. Sanity: rish reachable --------------------------------------
# This is informational; the smoke test doesn't fail if Shizuku is off.
if "$ADB" shell command -v rish >/dev/null 2>&1; then
  ok "rish present in PATH"
else
  echo "warn: rish not in adb-shell PATH — Shizuku-gated paths won't be exercised"
fi

# ---------- 3. Fire events --------------------------------------------------

# Tiny corpus of test events covering all seven intents. The classifier is
# allowed to be wrong on these — we only require it to classify SOMETHING with
# bounded latency. Accuracy is checked separately in the hand-graded eval set.
EVENTS=(
  "reply to mom about dinner Sunday"
  "marketing email don't miss our spring sale"
  "subject: invoice paid #4471"
  "block 2 hours for deep work tomorrow morning"
  "summarize the last three emails from the contractor"
  "the dog seems lethargic today"
  "set focus mode until 5pm"
)

start_ts=$(date +%s)
for i in $(seq 1 "$EVENT_COUNT"); do
  txt="${EVENTS[$((i % ${#EVENTS[@]}))]} -- iter $i"
  "$ADB" shell am broadcast \
      -n "$PKG/dev.jarvis.testing.SmokeTestReceiver" \
      -a "$RECEIVER_ACTION" \
      --es text "$txt" \
      --es source "manual_test" \
    >/dev/null \
    || fail "am broadcast failed at iter $i"
done
end_ts=$(date +%s)
ok "fired $EVENT_COUNT events in $((end_ts - start_ts))s"

# Give the service a moment to drain.
sleep 2

# ---------- 4. Pull DB ------------------------------------------------------

DB_LOCAL="$WORKDIR/jarvis.db"
# `run-as` is debug-only and gives us read access to /data/data/<pkg>/databases.
"$ADB" exec-out run-as "$PKG" cat databases/jarvis.db > "$DB_LOCAL" || \
    fail "could not pull jarvis.db; is the debug build installed?"

bytes=$(wc -c < "$DB_LOCAL")
[ "$bytes" -gt 0 ] || fail "pulled jarvis.db is empty"
ok "pulled jarvis.db ($bytes bytes)"

# ---------- 5. Assertions --------------------------------------------------

classified=$(sqlite3 "$DB_LOCAL" "SELECT COUNT(*) FROM decisions WHERE created_at >= $((start_ts * 1000));")
if [ "$classified" -lt "$ACCEPTED_FLOOR" ]; then
  fail "only $classified/$EVENT_COUNT events classified (floor=$ACCEPTED_FLOOR)"
fi
ok "classified $classified/$EVENT_COUNT events"

# Compute p95 latency using awk over the ascending-ordered latencies.
p95=$(sqlite3 "$DB_LOCAL" \
    "SELECT inference_latency_ms FROM decisions WHERE created_at >= $((start_ts * 1000)) ORDER BY inference_latency_ms ASC;" \
  | awk 'BEGIN{n=0} {v[n++]=$1} END {
      if (n==0) {print "NA"; exit}
      idx = int(0.95 * (n-1) + 0.5)
      print v[idx]
    }')
if [ "$p95" = "NA" ]; then
  fail "no latencies recorded"
fi
if [ "$p95" -ge "$P95_BUDGET_MS" ]; then
  fail "p95 latency $p95 ms >= budget $P95_BUDGET_MS ms"
fi
ok "p95 latency $p95 ms < $P95_BUDGET_MS ms"

# Heartbeat continuity — fail if the service died and came back during the run.
restarts=$(sqlite3 "$DB_LOCAL" \
    "SELECT COUNT(*) FROM heartbeats WHERE recorded_at >= $((start_ts * 1000)) AND service_alive = 0;")
if [ "$restarts" -gt 0 ]; then
  fail "$restarts heartbeat samples reported the service was not alive during the run"
fi
ok "heartbeat continuity intact"

ok "phase-1 smoke test PASSED"
