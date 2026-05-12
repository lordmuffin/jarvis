# Jarvis — Next Steps and Required Testing

Ordered by priority. P0 = blocks the `v0.1.0-mvp` tag. P1 = must be done before
any real usage. P2 = important but not blocking the tag.

---

## P0 — Blocks v0.1.0-mvp tag

### T1: Implement training steps 1.3 and 1.4

Both `training/jarvis_training/train/` and `training/jarvis_training/convert/`
are empty stubs. `make train` and `make convert` both exit with code 3. Until
these exist, the Android app runs on `StubClassifier` (always predicts
`device.action` at 0.99 confidence), which makes every acceptance gate
meaningless.

**What to build:**

`training/jarvis_training/train/train.py`
- Load `training/data/clean/intents.jsonl`
- 80/10/10 stratified split by intent
- Fine-tune MobileBERT (`google/mobilebert-uncased`) with Keras / TensorFlow
- Save `training/artifacts/mobilebert_intent.keras`
- Save `training/artifacts/tokenizer.json` (the HuggingFace tokenizer output —
  this is the single source of truth consumed by `WordPieceTokenizer.kt`)
- Compute SHA-256 of `tokenizer.json` → `training/artifacts/.tokenizer.sha256`
- Print per-intent val accuracy; fail if any class < 85%

`training/jarvis_training/convert/to_litert_ptq.py`
- Load the Keras checkpoint
- Apply 8-bit dynamic-range PTQ via `ai-edge-litert`
- Write `training/artifacts/intent_router.tflite`
- Write `training/artifacts/model_metadata.json` (tokenizer_hash,
  intent_schema_version, training_data_hash, conversion_mode, size_mb)
- Fail if final `.tflite` size > 30 MB
- Copy both files to `android/app/src/main/assets/`

`training/jarvis_training/convert/to_litert_qat.py`
- QAT fallback for when PTQ shows > 3% per-class accuracy drop
- Same output contract as PTQ

**CI additions needed:**
- Add a `train` job to `ci-training.yml` that runs on a GPU runner (or marks as
  manual/nightly) and asserts per-class accuracy floor
- Add a size check: `wc -c android/app/src/main/assets/intent_router.tflite`

**Before running synth**, you need a vault with `.md` files:
```sh
export JARVIS_CLOUD_LLM_API_KEY=...
export JARVIS_VAULT_PATH=/path/to/your/vault
cd training && make synth validate
```

---

### T2: Run phase-1-smoke-test.sh on a real Pixel 8

The smoke test script exists and is correct, but it has never been executed
against the device with a real model installed. This is required for DoD gate #2.

**Steps:**
1. Complete T1 so `android/app/src/main/assets/intent_router.tflite` exists.
2. Build the debug APK: `./gradlew :app:assembleDebug`
3. Connect Pixel 8 via USB or wireless ADB.
4. Run: `bash scripts/phase-1-smoke-test.sh`
5. Verify: ≥ 95/100 events classified, p95 < 500 ms, heartbeat continuity intact.

**Expected failure modes to watch for:**
- p95 latency ≥ 500 ms — model too large or PTQ degraded too much; try QAT or
  reduce context window
- < 95 classified — service crashed during run; check logcat for
  `ForegroundServiceDidNotStartInTimeException`
- heartbeat `service_alive = 0` — Doze killed the service; see T8

---

### T3: Hand-graded accept rate eval (DoD gate #4)

Collect 50 real notification events from the phone's daily use, label each as
"would approve" or "would dismiss" yourself, then run each through the classifier
and compare.

**Steps:**
1. Collect 50 representative events covering all intent types.
   Save them in `eval/phase-1-acceptance.md` (create this file) with columns:
   `text | true_label | predicted_intent | predicted_confidence | match?`
2. Target: predicted intent's Approve action matches your label on ≥ 75% of the set.
3. If < 75%: look at the failure distribution by intent — which classes are weakest.
   Rebalance the training set for those classes and rebuild.

This is a human-in-the-loop step. Automate data collection with:
```sh
sqlite3 jarvis.db "SELECT event_text, predicted_intent, confidence
  FROM decisions WHERE user_action IN ('approve','dismiss')
  ORDER BY created_at DESC LIMIT 50;"
```

---

### T4: Overnight idle test (DoD gate #3)

After the debug APK is installed and `HeartbeatWorker` is confirmed running:

1. Leave the phone unplugged overnight (~12 hours).
2. In the morning, fire one manual event via `am broadcast`:
   ```sh
   adb shell am broadcast \
     -n dev.jarvis.debug/dev.jarvis.testing.SmokeTestReceiver \
     -a dev.jarvis.testing.SMOKE_EVENT \
     --es text "review draft reply to contractor" \
     --es source manual_test
   ```
3. Verify a HUN toast appears on the device (no manual restart required).
4. Pull the DB and check heartbeat continuity:
   ```sh
   adb exec-out run-as dev.jarvis.debug cat databases/jarvis.db > /tmp/jarvis.db
   sqlite3 /tmp/jarvis.db \
     "SELECT COUNT(*) FROM heartbeats WHERE service_alive = 0;"
   # Should be 0
   ```

If this fails, investigate `ForegroundServiceDidNotStartInTimeException` in
logcat and consider a more aggressive wake-lock strategy or the
notification-listener fallback path.

---

## P1 — Required before real daily use

### T5: Wire OutboxWriter into the action pipeline (JSONL outbox completion)

Currently `ToastPipeline`, `ToastActionReceiver`, and `TimeoutReceiver` all write
to Room but never to the JSONL outbox. The vault path is not stored anywhere.

**What to build:**
1. `android/.../data/VaultManager.kt` — reads/writes vault root path from
   `SharedPreferences("jarvis_vault", MODE_PRIVATE)`. Returns `null` when unset.
2. A one-time vault picker in `MainActivity`: launch `ACTION_OPEN_DOCUMENT_TREE`,
   persist the URI + extract the file path into `VaultManager`.
3. In `ToastPipeline.persist()`, after auto-dismiss actions, call
   `OutboxWriter.append(row.toOutboxRecord(Intent.SCHEMA_VERSION))` if
   `VaultManager.getVaultPaths()` is non-null.
4. In `ToastActionReceiver.recordAction()`, after `setUserAction()`, load the
   updated `Decision` row and call `OutboxWriter.append()`.
5. In `TimeoutReceiver.onReceive()`, same pattern after recording timeout.
6. Post the "setup incomplete" notification when `VaultManager.getVaultPaths()`
   is null at app start (the string resources for this already exist in
   `strings.xml`).

**Test to add:** `OutboxIntegrationTest` — use an in-memory Room DB + temp dir,
process a synthetic event through `ToastPipeline`, tap APPROVE via
`ToastActionReceiver`, and assert the JSONL file contains exactly one finalized
record with `user_action = "approve"`.

---

### T6: Request POST_NOTIFICATIONS permission at runtime

Android 13+ requires a runtime permission request for `POST_NOTIFICATIONS`. The
permission is declared in the manifest but there is no request call in the app.
Without it, HUN notifications are silently dropped on a fresh install.

**Where to add it:** In `MainActivity.onCreate()`, check and request using
`ActivityResultContracts.RequestPermission`. If denied, show an explanation
rationale and a button to open Settings.

**Test:** Manually verify on the Pixel 8 that the permission dialog appears on
first launch and that declining it causes HUNs to be silently skipped (not crash).

---

### T7: Verify LiteRT accelerator selection on Pixel 8

The code logs which accelerator was selected on cold start (`NPU`, `GPU`, or
`CPU`). Once `intent_router.tflite` exists, this needs to be physically verified.

**Expected outcome on Pixel 8 / Tensor G3:** The log should show `NPU`
(EdgeTPU via `Accelerator.AUTO`). If it shows `CPU`, inference will be slower and
may breach the 500 ms p95 budget. If it shows `GPU`, check whether the Vulkan
delegate is loading correctly.

**How to check:**
```sh
adb logcat -s IntentRouterService | grep accelerator
# Expected: Using LiteRT classifier; accelerator=NPU
```

If accelerator is `CPU`, investigate:
- Is the `.tflite` metadata correct (requires `model_metadata.json` to reference
  the correct ops)?
- Is `litert-gpu` on the classpath (it is — see `build.gradle.kts`)?
- Consider adding `Accelerator.NPU` explicitly as a fallback chain.

---

### T8: Doze / battery optimization hardening

The DOZE_KILLED tile in `StatsScreen` detects the symptom but not the cause.
Run a targeted doze test before daily use:

```sh
# Force doze mode on the connected device:
adb shell dumpsys deviceidle force-idle
# Wait 5 minutes, then fire an event:
adb shell am broadcast -n dev.jarvis.debug/dev.jarvis.testing.SmokeTestReceiver \
  -a dev.jarvis.testing.SMOKE_EVENT --es text "test" --es source manual_test
# Exit doze:
adb shell dumpsys deviceidle unforce
# Pull DB and check if the event was classified:
adb exec-out run-as dev.jarvis.debug cat databases/jarvis.db > /tmp/j.db
sqlite3 /tmp/j.db "SELECT COUNT(*) FROM decisions WHERE created_at > (strftime('%s','now','-10 minutes')*1000);"
```

If classification drops to 0 during forced doze, the foreground service is being
killed. Mitigations to consider (in order of invasiveness):
1. Add the app to the device's battery optimization exemption list
   (`Settings → Battery → Unrestricted`).
2. Reduce the `HeartbeatWorker` interval to the WorkManager minimum (15 min is
   already minimum).
3. Add a `NotificationListenerService` as a secondary event source — it gets a
   system-level callback on every new notification, which Android will not kill.

---

## P2 — Important but not blocking the tag

### T9: Fix CoroutineScope leaks in fire-and-forget calls

`ToastPipeline.process()`, `ToastActionReceiver.handleApprove()`, and
`TimeoutReceiver.onReceive()` all create anonymous `CoroutineScope(Dispatchers.IO)`
instances that are never cancelled. These are benign for Phase 1 (each scope
lives < 1 s for a DB write) but will cause issues if the calls are invoked
rapidly or from within a component that has its own lifecycle.

**Preferred fix:** Create a `ProcessScope` singleton:
```kotlin
object ProcessScope {
    val io: CoroutineScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
}
```
Replace all ad-hoc `CoroutineScope(Dispatchers.IO).launch { }` with
`ProcessScope.io.launch { }`. This is a drop-in replacement with proper
`SupervisorJob` semantics (one child failure doesn't cancel the others).

---

### T10: Add unit tests for the 1.6 pipeline

The following classes added in 1.6 have no unit tests:

| Class | What to test |
|---|---|
| `UiAtom.from()` | All 7 intents map to the correct atom type; body is capped at 200 chars |
| `ToastPipeline` | `dismiss` intent → `auto_dismiss_intent` row; low-confidence → `auto_low_confidence` row; normal intent → no auto-action (HunDispatcher call stubbed via interface/mock) |
| `StatsViewModel` | `percentile()` helper — empty list, single element, even/odd sizes, p50 and p95 edge cases |
| `HeartbeatWorker` | `doWork()` inserts a `Heartbeat` row; `serviceAlive = false` path (mock `ClassifierHolder`) |
| `TimeoutReceiver` | Does not overwrite an existing `user_action`; does overwrite null `user_action` |

Use Robolectric for anything that touches Room; use mockk for `ClassifierHolder`
and `NotificationManager`.

---

### T11: Prevent StubClassifier leaking to release builds

`StubClassifier` always returns `device.action` at 0.99 confidence. If the
`.tflite` asset is somehow absent from a release APK, users see every event
routed to `device.action`. This should be a hard crash in release, not a silent
fallback.

**Fix:** In `IntentRouterService.buildClassifier()`, replace the current pattern:
```kotlin
// current — silent fallback in all builds
val litert = LiteRtClassifier.tryCreate(applicationContext)
return if (litert != null) litert else StubClassifier()
```
with:
```kotlin
val litert = LiteRtClassifier.tryCreate(applicationContext)
if (litert == null) {
    check(BuildConfig.DEBUG) {
        "intent_router.tflite missing from assets — this should never happen in a release build"
    }
    Log.w(TAG, "using StubClassifier — debug only")
    return StubClassifier()
}
return litert
```

**Test:** Add `StubClassifierLeakTest` that asserts `LiteRtClassifier.tryCreate()`
returns non-null when the asset is present, and that `IntentRouterService` does
not instantiate `StubClassifier` in a release-variant build.

---

### T12: Wire escalate.burst HTTP call to Termux mid-tier

`dispatchStubAction()` in `ToastActionReceiver` is a log line. The plan calls
for an HTTP POST to `127.0.0.1:8080` (the Termux llama.cpp server) when
`predicted_intent == "escalate.burst"`.

**What to add:**
1. Add `implementation("com.squareup.okhttp3:okhttp:4.12.0")` (or equivalent)
   to `build.gradle.kts`.
2. Create `android/.../service/MidTierClient.kt` with a `suspend fun escalate(prompt: String): String?`.
3. Call `MidTierClient.escalate()` from `dispatchStubAction()` when
   `predicted_intent == "escalate.burst"`.
4. Surface the result: if the server returns a response, post a follow-up
   `ApproveDismissAtom` HUN with the llama.cpp output as the body.
5. Handle server-down gracefully: write to `<APP_INTERNAL>/pending/` queue and
   show "Mid-tier offline — saved to queue" in the toast body.

---

### T13: Add ktlint to ci-android.yml

The Android CI currently checks for build success and forbidden imports but has
no style enforcement. Add ktlint:

```yaml
- name: ktlint
  run: ./gradlew ktlintCheck
```

Add `ktlint` to `libs.versions.toml` and configure via the `jlleitschuh/ktlint`
Gradle plugin. This catches import ordering, spacing, and naming issues that are
currently only enforced by convention.

---

### T14: Verify Syncthing outbox sync on the homelab side

Once the JSONL outbox is wired (T5), verify the homelab actually receives the
files. The phase-0 runbook documents `!outbox/**` in the homelab's ignore
pattern — confirm this is in place and that new files appear within the
Syncthing sync interval.

**Test:**
```sh
# On the phone (Termux), after approving a manual-trigger event:
ls -la "$JARVIS_VAULT_PATH/outbox/jarvis-decisions/"

# On the homelab, after Syncthing syncs:
ls -la "$HOMELAB_VAULT_PATH/outbox/jarvis-decisions/"
# Both should show the same YYYY-MM-DD.jsonl file with matching content.
```

---

### T15: Address CI gaps — training jobs don't run train/convert steps

`ci-training.yml` runs pytest and a tokenizer hash check, but there is no CI job
that exercises the actual MobileBERT fine-tune or LiteRT conversion. For the
long term:

- Add a nightly/manual workflow `ci-training-full.yml` that runs on a
  GPU-enabled runner (GitHub hosted runners with T4 GPU, or self-hosted on the
  homelab).
- Gate: fail if any intent class val accuracy < 85%.
- Gate: fail if `intent_router.tflite` > 30 MB.
- On success, upload the `.tflite` and `model_metadata.json` as workflow artifacts
  for manual download + commit into `android/app/src/main/assets/`.

Until a GPU runner is available, the train + convert steps remain manual.

---

## Summary — priority order

| # | Item | Effort | Blocks |
|---|---|---|---|
| T1 | Implement train.py + LiteRT conversion | Large | Everything |
| T2 | Run smoke test on device | Small (once T1 done) | DoD gate #2 |
| T3 | Hand-graded eval (50 events) | Medium | DoD gate #4 |
| T4 | Overnight idle test | Small | DoD gate #3 |
| T5 | Wire OutboxWriter (VaultManager + settings) | Medium | JSONL sync |
| T6 | Request POST_NOTIFICATIONS at runtime | Small | HUNs on fresh install |
| T7 | Verify NPU accelerator selection on device | Small | Performance confidence |
| T8 | Doze hardening + doze test | Medium | 24/7 reliability |
| T9 | Fix CoroutineScope leaks | Small | Code hygiene |
| T10 | Unit tests for 1.6 pipeline | Medium | Test coverage |
| T11 | Block StubClassifier in release | Small | Correctness safety net |
| T12 | Wire escalate.burst HTTP call | Medium | Phase 1 feature completeness |
| T13 | Add ktlint to CI | Small | Code quality |
| T14 | Verify Syncthing outbox sync | Small | Homelab analytics |
| T15 | GPU CI runner for train + convert | Large | Automated model rebuilds |
