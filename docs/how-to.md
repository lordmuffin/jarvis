# Jarvis — How to Use the Implemented Features

This guide is ordered by the natural bring-up sequence: environment first, then
training pipeline, then the Android app, then the Termux mid-tier. Each section
starts with what it requires from earlier sections.

---

## 1. Environment setup (Phase 0)

**Requires:** Pixel 8 with Android 14, F-Droid, and an existing Tailscale tailnet +
Syncthing vault.

### 1.1 First-time bring-up

Follow `docs/phase-0-bringup.md` in order. The short version:

```sh
# On the phone in Termux
pkg update && pkg upgrade -y
pkg install -y python nodejs git openssh proot-distro \
  build-essential cmake clang pkg-config \
  vulkan-headers vulkan-loader libomp \
  curl jq sqlite termux-api
```

Then install Shizuku, Tailscale, and Syncthing per the runbook's §2–4.

### 1.2 Configure ~/.jarvisrc

Create `~/.jarvisrc` in Termux before running the verifier or any script:

```sh
cat > ~/.jarvisrc <<'EOF'
export JARVIS_HOMELAB_HOST=your-homelab-hostname      # tailscale name
export JARVIS_HOMELAB_HEALTH_PORT=8080                # port serving /healthz
export JARVIS_VAULT_PATH=/storage/emulated/0/vault    # Syncthing mount point

# Required when running the mid-tier server:
export JARVIS_MID_TIER_MODEL_PATH=~/.jarvis/models/qwen2.5-3b-q4_k_m.gguf

# Required when running the training synth step from this device:
export JARVIS_CLOUD_LLM_API_KEY=your-gemini-api-key
EOF
source ~/.jarvisrc
```

### 1.3 Verify the environment

```sh
# From Termux on the phone:
bash scripts/phase-0-verify.sh
```

Each of the 9 checks prints `PASS` or `FAIL` with a one-line remediation hint.
The script exits 0 only when all pass. Run it again after any config change.

Sample passing output:

```
  PASS  JARVIS_HOMELAB_HOST is set
  PASS  JARVIS_HOMELAB_HEALTH_PORT is set
  PASS  JARVIS_VAULT_PATH is set
  PASS  ping your-homelab over Tailscale
  PASS  GET http://your-homelab:8080/healthz returns 2xx
  PASS  rish is reachable in PATH
  PASS  rish -v returns a version
  PASS  JARVIS_VAULT_PATH exists and is a directory
  PASS  vault contains at least one .md file
  PASS  vault has a readable .jarvisrc
  PASS  can create vault outbox/ for jarvis writes
  PASS  sqlite3 binary available
  PASS  jq binary available
  PASS  vulkaninfo or libvulkan present

14/14 checks passed. Phase 0 verified.
```

---

## 2. Training pipeline (Phase 1.2 — synth + validate)

**Requires:** A host machine (not the phone) with Python 3.11+, access to the vault
directory, and a Gemini API key.

### 2.1 Install

```sh
cd training
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,gemini]"
```

Add `[train]` when step 1.3 is implemented, `[convert]` for 1.4.

### 2.2 Run the unit tests

```sh
make test
# or directly:
pytest tests/ -q
```

All 56 tests run without a vault or API key (Gemini SDK is mocked).

### 2.3 Lint

```sh
make lint
# or:
ruff check jarvis_training tests
```

### 2.4 Review the grounding prompt (informational)

Before running synth, inspect the system prompt that will be sent to Gemini.
The user approved the 1.2 gate prompt in `docs/prompt-review-1.2.txt`; if you
change `prompt_builder.py`, regenerate and review it again:

```sh
make review-prompt
```

This prints the rendered system + user prompt to stdout. No API call is made.

### 2.5 Generate synthetic training data

```sh
# Set env vars (or source ~/.jarvisrc if running from the homelab):
export JARVIS_VAULT_PATH=/path/to/your/vault
export JARVIS_CLOUD_LLM_API_KEY=your-gemini-api-key

make synth
# Equivalent to:
# python -m jarvis_training.synth.cli_generate \
#     --vault "$JARVIS_VAULT_PATH" \
#     --raw   training/data/raw/intents.jsonl
```

The generator is **idempotent**: if `data/raw/intents.jsonl` already has records
for an intent, that intent is skipped. Target is 10,000 records per intent
(70,000 total). Expect 30–60 minutes for a full run at Gemini 2.5 Pro's rate limits.

Progress is printed per-batch:
```
[generate] device.action  2000/10000 (batch=20, usable=19, dup_skipped=1)
[generate] draft.email     100/10000 (batch=20, usable=20, dup_skipped=0)
...
```

### 2.6 Validate raw data

```sh
make validate
# or:
# python -m jarvis_training.synth.cli_validate \
#     --vault "$JARVIS_VAULT_PATH" \
#     --raw   training/data/raw/intents.jsonl \
#     --clean training/data/clean/intents.jsonl
```

The validator prints a summary of rejection counts:

```
[validate] raw=70000 valid=69412 invalid_label=32 dangling_chunk=84 duplicate=472
[validate] clean JSONL written → training/data/clean/intents.jsonl
```

Steps 1.3 (train) and 1.4 (convert) are not yet implemented — `make train` and
`make convert` will exit with an error until those scripts are added.

---

## 3. Android app

**Requires:** Android Studio (or the Gradle CLI) and `adb` with the Pixel 8 connected.

### 3.1 Build the debug APK

```sh
cd android
./gradlew :app:assembleDebug
# APK lands at: android/app/build/outputs/apk/debug/app-debug.apk
```

The `preBuild` task runs `verifyForbiddenDependencies` automatically, which fails
the build if any `org.tensorflow:tensorflow-lite*` artifact is on the classpath.

### 3.2 Install

```sh
adb install -r -t android/app/build/outputs/apk/debug/app-debug.apk
```

The debug app ID is `dev.jarvis.debug` (release is `dev.jarvis`).

### 3.3 Run unit tests

```sh
./gradlew :app:testDebugUnitTest
```

Tests use Robolectric (no emulator needed). They cover:
- `IntentTest` — ordinal order, wire values, `fromWire`/`fromOrdinal`, schema version
- `WordPieceTokenizerTest` — tokenization, `[CLS]`/`[SEP]` insertion, padding, truncation
- `DecisionDaoTest` — Room queries for accept rate, latency, toast count
- `OutboxWriterTest` — JSONL append, day rotation, newline rejection, vault path assertion
- `VaultPathsTest` — write-allowed guard, path traversal rejection
- `StubClassifierTest` — output shape, ULID generation

### 3.4 What the app does at launch

1. `JarvisApp.onCreate` registers the two notification channels (`jarvis.toasts`,
   `jarvis.service`), starts `IntentRouterService` as a foreground service, and
   schedules the `HeartbeatWorker` (15-min WorkManager periodic task).
2. `IntentRouterService` tries to load `assets/intent_router.tflite` via LiteRT.
   **Until that asset exists (steps 1.3 + 1.4), it falls back to `StubClassifier`.**
   The persistent notification subtitle shows which accelerator was selected
   (e.g., `Classifier ready · NPU accelerator`; shows `AUTO_UNKNOWN` with stub).
3. `MainActivity` shows the manual trigger button and the three stats tiles.

### 3.5 Manual trigger

Tap "Open manual trigger" in `MainActivity`. Paste any event text and tap "Classify".
The result appears inline:

```
device.action · 0.99 · NPU · 12ms
```

This calls `ToastPipeline.process()`, which writes a `Decision` row to Room **and**
posts a HUN notification (if the predicted intent is not `dismiss` and confidence
≥ 0.40). After returning, check the notification shade to interact with the HUN.

### 3.6 Interacting with a HUN toast

For `ApproveDismissAtom` intents (`device.action`, `schedule.event`, `escalate.burst`):
- **Approve** — records `user_action=approve` in Room; stub action handler logs the intent.
- **Dismiss** — records `user_action=dismiss`.

For `EditableTextAtom` intents (`draft.email`, `draft.reply`, `note.capture`):
- **Approve** — same as above.
- **Edit** — dismisses the HUN and opens `EditActivity` (a Compose bottom sheet
  pre-seeded with the event text). Edit the draft and tap **Send**; records
  `user_action=edit` in Room. Tap **Cancel** to close without recording an action
  (the 30-minute timeout alarm is still running).
- **Dismiss** — records `user_action=dismiss`.

If you ignore the HUN for 30 minutes, `TimeoutReceiver` fires, cancels the
notification, and records `user_action=timeout` — but only if no action was already set.

### 3.7 Stats screen

The three tiles at the bottom of `MainActivity` refresh from Room on each load.
Tap **Refresh** to re-query. Tile colors:

| Tile | Green | Amber | Red |
|---|---|---|---|
| Accept rate (30d) | ≥ 75% | 60–75% | < 60% |
| Toast volume (7d) | — | — | heartbeats > 0 and toasts == 0 (⚠ DOZE_KILLED?) |
| p95 latency (24h) | < 400 ms | 400–500 ms | ≥ 500 ms |

The toast volume tile shows `${toastCount} / ${heartbeatCount} heartbeats`.
If the `HeartbeatWorker` is firing but no toasts are recorded, Android's Doze
mode likely killed the foreground service between heartbeat windows.

### 3.8 Inspect the decision log directly

```sh
# Pull the database while the debug app is installed:
adb exec-out run-as dev.jarvis.debug cat databases/jarvis.db > /tmp/jarvis.db

# Accept rate over the last 30 days:
sqlite3 /tmp/jarvis.db "
SELECT
    SUM(user_action IN ('approve','edit')) * 1.0 /
    NULLIF(SUM(user_action IN ('approve','edit','dismiss')), 0) AS accept_rate
  FROM decisions
 WHERE created_at >= (strftime('%s','now','-30 days') * 1000);"

# Last 10 decisions:
sqlite3 /tmp/jarvis.db "
SELECT event_id, predicted_intent, confidence, user_action, inference_latency_ms
  FROM decisions
 ORDER BY created_at DESC
 LIMIT 10;" | column -t -s '|'

# p95 latency for the past 24 hours:
sqlite3 /tmp/jarvis.db "
SELECT inference_latency_ms FROM decisions
 WHERE created_at >= (strftime('%s','now','-1 day') * 1000)
 ORDER BY inference_latency_ms ASC;" \
| awk 'BEGIN{n=0} {v[n++]=$1} END {
    if (n==0) {print "no data"; exit}
    idx = int(0.95*(n-1)+0.5)
    printf "p95 = %d ms (n=%d)\n", v[idx], n
  }'
```

---

## 4. Termux mid-tier (llama.cpp)

**Requires:** Phase 0 complete, `JARVIS_MID_TIER_MODEL_PATH` set in `~/.jarvisrc`.

### 4.1 Build llama.cpp

Run this once (or when updating the pinned SHA):

```sh
# From inside Termux on the phone:
bash termux/build-llama.sh
```

This clones llama.cpp at the pinned SHA (`LLAMA_CPP_PINNED_SHA` in the script),
builds with Vulkan enabled, and installs the binary to `~/.jarvis/llama.cpp/build/bin/llama-server`.
Expect 10–30 minutes on a Pixel 8.

To override the pinned SHA (e.g. to test an upstream fix):
```sh
LLAMA_CPP_PINNED_SHA=<new-sha> bash termux/build-llama.sh
```

### 4.2 Download a model

The server expects a 3B-class GGUF. Qwen2.5-3B-Instruct-Q4_K_M is the recommended
starting point (~2 GB):

```sh
mkdir -p ~/.jarvis/models
# From the phone in Termux (or copy via adb push):
curl -L -o ~/.jarvis/models/qwen2.5-3b-q4_k_m.gguf \
  "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf"

# Set the path in ~/.jarvisrc:
echo 'export JARVIS_MID_TIER_MODEL_PATH=~/.jarvis/models/qwen2.5-3b-q4_k_m.gguf' >> ~/.jarvisrc
source ~/.jarvisrc
```

### 4.3 Start the server

```sh
bash termux/run-mid-tier.sh
```

The server starts on `127.0.0.1:8080` (phone-local only — not exposed to LAN or WAN).
`taskset-wrapper.sh` auto-detects the two highest-frequency CPU clusters on Tensor G3
and pins the process to them.

Expected startup output:
```
[taskset-wrapper] pinning to CPUs: 4,5,6,7
llama server listening at http://127.0.0.1:8080
```

### 4.4 Verify the server is running

```sh
curl -s http://127.0.0.1:8080/health | jq .
# Expected: {"status":"ok"}

# Test an inference:
curl -s http://127.0.0.1:8080/completion \
  -H "Content-Type: application/json" \
  -d '{"prompt":"What is 2+2?","n_predict":32}' | jq .content
```

### 4.5 Auto-start on boot (optional)

Termux:Boot can start the server automatically. Create the hook:

```sh
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start-mid-tier.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
source ~/.jarvisrc
bash ~/path/to/repo/termux/run-mid-tier.sh &
EOF
chmod +x ~/.termux/boot/start-mid-tier.sh
```

Replace `~/path/to/repo` with the actual repo clone path inside Termux.

---

## 5. Phase 1 smoke test

**Requires:** The debug APK installed on the Pixel 8 via USB/wireless ADB, `sqlite3`
and `awk` on the host machine.

```sh
# From the host machine:
bash scripts/phase-1-smoke-test.sh
```

The script:
1. Installs `android/app/build/outputs/apk/debug/app-debug.apk` via `adb install -r`.
2. Fires 100 `am broadcast` events to `dev.jarvis.debug/dev.jarvis.testing.SmokeTestReceiver`
   cycling through 7 text fixtures covering all intents.
3. Waits 2 seconds for background Room writes to land.
4. Pulls `databases/jarvis.db` via `adb exec-out run-as`.
5. Asserts with `sqlite3` + `awk`:
   - ≥ 95 `Decision` rows written during the run window.
   - p95 inference latency < 500 ms.
   - No `Heartbeat` row with `service_alive = 0` during the run.

Override any threshold via environment variables:
```sh
EVENT_COUNT=50 P95_BUDGET_MS=300 bash scripts/phase-1-smoke-test.sh
```

Sample passing output:
```
OK   found android/app/build/outputs/apk/debug/app-debug.apk
OK   installed dev.jarvis.debug
OK   rish present in PATH
OK   fired 100 events in 18s
OK   pulled jarvis.db (45056 bytes)
OK   classified 100/100 events
OK   p95 latency 38 ms < 500 ms
OK   heartbeat continuity intact
OK   phase-1 smoke test PASSED
```

**Note:** With `StubClassifier` (no real model yet), classification always succeeds
and latency is ~0 ms — the smoke test passes trivially. Once `intent_router.tflite`
is installed the latency assertion becomes meaningful.

---

## 6. CI — running checks locally

### Training pipeline

```sh
cd training
make install   # pip install -e ".[dev]"
make lint      # ruff
make test      # pytest
```

### Android

```sh
cd android
./gradlew :app:testDebugUnitTest          # Robolectric unit tests
./gradlew :app:assembleDebug              # build + forbidden-dep check
```

The `ci-android.yml` workflow also greps `.kt`/`.java` files for
`import org.tensorflow` imports. To run that check locally:

```sh
grep -rn --include="*.kt" --include="*.java" \
  "^[[:space:]]*import[[:space:]]\+org\.tensorflow" \
  android/app/src/main android/app/src/debug android/app/src/test
# Should print nothing.
```

### Shell scripts (Termux + scripts)

```sh
shellcheck termux/*.sh scripts/*.sh
for f in termux/*.sh scripts/*.sh; do bash -n "$f" && echo "OK: $f"; done
```

---

## 7. Querying the outbox JSONL (once vault wiring is complete)

Once the vault path is configured in the Android app (a settings screen is pending
— see `docs/status.md`), finalized decisions are also appended to:

```
<vault>/outbox/jarvis-decisions/YYYY-MM-DD.jsonl
```

Each line is one `OutboxDecisionRecord`:

```json
{
  "event_id": "01JFKQ...",
  "event_source": "manual_test",
  "event_text": "reply to mom about dinner Sunday",
  "predicted_intent": "draft.reply",
  "confidence": 0.87,
  "accelerator_used": "NPU",
  "inference_latency_ms": 14,
  "user_action": "approve",
  "created_at_ms": 1747000000000,
  "acted_at_ms":  1747000015000,
  "intent_schema_version": "1.0.0"
}
```

To run analytics from the homelab once files are syncing:

```sh
# Approve rate for a day
jq -s 'map(select(.user_action != null and .predicted_intent != "dismiss"))
       | { total: length,
           approved: map(select(.user_action == "approve" or .user_action == "edit")) | length }
       | .approved / .total' \
  "$JARVIS_VAULT_PATH/outbox/jarvis-decisions/$(date +%Y-%m-%d).jsonl"

# p95 latency for a day
jq -r '.inference_latency_ms' \
  "$JARVIS_VAULT_PATH/outbox/jarvis-decisions/$(date +%Y-%m-%d).jsonl" \
| sort -n \
| awk 'BEGIN{n=0} {v[n++]=$1} END {
    idx=int(0.95*(n-1)+0.5)
    printf "p95 = %d ms  (n=%d)\n", v[idx], n
  }'
```
