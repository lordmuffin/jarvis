# Jarvis Phase 0 / Phase 1 — Implementation Status

Last updated: 2026-05-12 (commit `ded7f9f`). Branch: `claude/friendly-chatterjee`.

---

## Complete and tested

### Phase 0 — Environment foundation

| Item | Files | Test coverage |
|---|---|---|
| **0.1 Bring-up runbook** | `docs/phase-0-bringup.md` | Manual (follows checklist) |
| **0.2 Phase-0 verifier** | `scripts/phase-0-verify.sh` | shellcheck + `bash -n` via CI |

The runbook covers F-Droid Termux install, all `pkg install` deps, proot Ubuntu escape hatch, Shizuku Wireless Debugging pairing, Tailscale, and Syncthing (ReceiveOnly on phone + `!outbox/**` ignore pattern on homelab side).

The verifier asserts: Tailscale ping, homelab healthcheck, `rish -v`, vault directory/`.md` file/`.jarvisrc` readable, outbox write permission, and presence of `sqlite3`/`jq`/`vulkan_info`.

---

### Phase 1.1 — Intent schema

| Item | Files |
|---|---|
| **Architecture doc + intent schema** | `docs/phase-1-architecture.md` |
| **Seven canonical intents** | `training/jarvis_training/intents.py`, `android/.../service/model/Intent.kt` |

Seven intents defined (`device.action`, `draft.email`, `draft.reply`, `schedule.event`, `escalate.burst`, `note.capture`, `dismiss`). Wire values, ordinal order, `INTENT_SCHEMA_VERSION = "1.0.0"` are frozen and matched between the Python training package and the Android Kotlin enum.

Unit tests:
- `IntentTest.kt` — ordinal order frozen, wire values correct, `fromWire`/`fromOrdinal` round-trip, schema version constant.

---

### Phase 1.2 — Synthetic data pipeline (Gemini 2.5 Pro client)

| Item | Files | Test coverage |
|---|---|---|
| Vault loader | `training/jarvis_training/synth/vault_loader.py` | `test_vault_loader.py` (6 tests) |
| Prompt builder | `training/jarvis_training/synth/prompt_builder.py` | `test_prompt_builder.py` (5 tests) |
| Gemini client adapter | `training/jarvis_training/synth/gemini_client.py` | `test_gemini_client.py` (7 tests) |
| Generator (idempotent) | `training/jarvis_training/synth/generate.py` | `test_generate.py` (8 tests) |
| Validator | `training/jarvis_training/synth/validate.py` | `test_validate.py` (6 tests) |
| CLI entry points | `training/jarvis_training/synth/cli_generate.py`, `cli_validate.py` | — |
| Prompt review artifact | `docs/prompt-review-1.2.txt` | User-approved gate |

All 56 Python unit tests pass (Gemini SDK is mocked; no real API calls in CI). The `generate.py` loop is idempotent — re-runs skip intents already at quota and break cleanly on zero usable vault chunks. The validator rejects invalid intent labels, dangling `vault_source_chunk_id`s, texts duplicated more than 3 times, and malformed JSON lines.

**What is NOT present:** No actual training data in `training/data/` — the pipeline is ready to run but requires `JARVIS_CLOUD_LLM_API_KEY` and a vault on disk. Run `make synth` to generate.

CI: `ci-training.yml` runs pytest + ruff on every push to paths under `training/`.

---

### Phase 1.5 — Android scaffold + foreground service + WordPiece tokenizer

| Item | Files | Test coverage |
|---|---|---|
| Gradle KTS project | `android/app/build.gradle.kts`, `android/gradle/libs.versions.toml` | Build task + `verifyForbiddenDependencies` |
| `IntentRouterService` | `android/.../service/IntentRouterService.kt` | — |
| `LiteRtClassifier` | `android/.../service/inference/LiteRtClassifier.kt` | Indirect via `StubClassifierTest` |
| `WordPieceTokenizer` | `android/.../service/inference/WordPieceTokenizer.kt` | `WordPieceTokenizerTest.kt` (8 tests) |
| `StubClassifier` | `android/.../service/inference/StubClassifier.kt` | `StubClassifierTest.kt` (3 tests) |
| `ClassifierHolder` | `android/.../service/inference/ClassifierHolder.kt` | — |
| `IntentRouterClient` | `android/.../service/IntentRouterClient.kt` | — |
| `BootReceiver` | `android/.../service/BootReceiver.kt` | — |
| `ManualTriggerActivity` | `android/.../ManualTriggerActivity.kt` | — |
| Forbidden-import CI check | `ci-android.yml` + `verifyForbiddenDependencies` task | CI |

The foreground service starts at boot (via `BootReceiver`) and on `Application.onCreate`. It attempts to load `assets/intent_router.tflite` via `LiteRtClassifier.tryCreate()`; if the asset is absent it falls back to `StubClassifier` with a loud `Log.w`. The accelerator selected by `Accelerator.AUTO` (NPU/GPU/CPU) is logged on every cold start.

The `WordPieceTokenizer` reads a huggingface `tokenizer.json`, does basic tokenization (lowercase + whitespace/punctuation split), greedy WordPiece with `##` prefixes, and pads/truncates to 128 tokens with `[CLS]`/`[SEP]`.

**What is NOT present:** The `intent_router.tflite` model asset itself — training steps 1.3 and 1.4 have not been run. The service falls back to `StubClassifier` until the asset is added. See [Partially implemented](#partially-implemented) below.

---

### Phase 1.6 — Toast surface (UiAtom + HUN pipeline)

| Item | Files | Test coverage |
|---|---|---|
| `UiAtom` sealed class | `android/.../ui/UiAtom.kt` | Covered by integration path |
| `ToastPipeline` | `android/.../service/ToastPipeline.kt` | Smoke test (end-to-end) |
| `HunDispatcher` | `android/.../ui/notif/HunDispatcher.kt` | — |
| `ToastActionReceiver` | `android/.../ui/notif/ToastActionReceiver.kt` | — |
| `TimeoutReceiver` | `android/.../ui/notif/TimeoutReceiver.kt` | — |
| `EditActivity` | `android/.../ui/edit/EditActivity.kt` | — |

**Flow:** `ToastPipeline.process(event)` classifies synchronously, then on `Dispatchers.IO` inserts a `Decision` row into Room and either (a) auto-dismisses `dismiss` intents or sub-threshold confidence events, or (b) calls `HunDispatcher.post()` to show a high-importance HUN.

`HunDispatcher` posts notifications per atom type:
- `ApproveDismissAtom` → [Approve] [Dismiss] actions
- `EditableTextAtom` → [Approve] [Edit] [Dismiss] actions
- `ChoiceAtom` → no-op (Phase 3 stub; dispatch shape is forward-proven)

An inexact `AlarmManager` alarm fires after 30 minutes; `TimeoutReceiver` writes `user_action=timeout` if no user action was recorded. `ToastActionReceiver` handles taps, cancels the alarm, and writes `user_action` to Room. Edit taps launch `EditActivity` (a Compose bottom sheet pre-seeded with the draft text).

**Limitation:** The HUN notification pipeline is wired end-to-end in code but **has not been exercised on a physical device** as part of this implementation (no device available in CI). The smoke test validates the Room DB writes; the notification UI requires manual on-device verification.

---

### Phase 1.7 — Decision log (Room + JSONL outbox)

| Item | Files | Test coverage |
|---|---|---|
| Room schema (`Decision`, `Heartbeat`) | `android/.../data/Decision.kt`, `Heartbeat.kt`, `JarvisDatabase.kt` | `DecisionDaoTest.kt` (5 tests) |
| `DecisionDao` | `android/.../data/DecisionDao.kt` | `DecisionDaoTest.kt` |
| `HeartbeatDao` | `android/.../data/HeartbeatDao.kt` | — |
| `VaultPaths` | `android/.../data/VaultPaths.kt` | `VaultPathsTest.kt` (7 tests) |
| `OutboxWriter` | `android/.../data/OutboxWriter.kt` | `OutboxWriterTest.kt` (6 tests) |
| `OutboxDecisionRecord` | `android/.../data/OutboxRecord.kt` | Tested via `OutboxWriterTest` |
| `UserAction` enum | `android/.../data/UserAction.kt` | — |

The `VaultPaths` class enforces the vault write invariant at the API level (phone writes only to `<vault>/outbox/jarvis-*`). This is defense layer 3; layers 1 and 2 are Syncthing ReceiveOnly and SAF scope.

`OutboxWriter` appends one JSONL record per decision to a per-day file (`YYYY-MM-DD.jsonl`) under `<vault>/outbox/jarvis-decisions/`. Each append is one `appendText` + `fsync`; SQLite Room is the source of truth.

**Limitation:** The `OutboxWriter` is implemented and tested, but **not yet wired into `ToastPipeline` or `ToastActionReceiver`** — Room writes happen on every action but outbox JSONL writes are pending a `VaultManager` that stores the vault root path in SharedPreferences. Currently the app runs in SQLite-only mode.

---

### Phase 1.8 — Termux llama.cpp mid-tier

| Item | Files | Test coverage |
|---|---|---|
| `build-llama.sh` | `termux/build-llama.sh` | shellcheck + `bash -n` via CI |
| `taskset-wrapper.sh` | `termux/taskset-wrapper.sh` | shellcheck + `bash -n` via CI |
| `run-mid-tier.sh` | `termux/run-mid-tier.sh` | shellcheck + `bash -n` via CI |
| `termux/README.md` | Documents pinned SHA and install steps | — |

The build script clones llama.cpp at a pinned SHA and builds with `-DGGML_VULKAN=ON -DLLAMA_BUILD_SERVER=ON`. The taskset wrapper dynamically reads `/sys/devices/system/cpu/cpufreq/policy*/cpuinfo_max_freq`, picks the two highest-frequency policies, and pins the wrapped process with `taskset -c`. No hardcoded CPU mask.

**Limitation:** The Android service's `escalate.burst` HTTP call to `127.0.0.1:8080` is **not yet implemented** — the escalation path from the Android side ends at the `dispatchStubAction()` log in `ToastActionReceiver`. The Termux server is ready to accept connections; the Android HTTP client call is deferred to Phase 2.

---

### Phase 1.9 — KPIs and observability

| Item | Files | Test coverage |
|---|---|---|
| KPI definitions | `docs/kpis.md` | Reference doc |
| `HeartbeatWorker` | `android/.../service/HeartbeatWorker.kt` | — |
| `StatsViewModel` | `android/.../stats/StatsViewModel.kt` | — |
| `StatsScreen` | `android/.../stats/StatsScreen.kt` | — |

`HeartbeatWorker` is a WorkManager `CoroutineWorker` scheduled at 15-minute intervals via `JarvisApp.onCreate`. It samples `ClassifierHolder.get() != null`, writes a `Heartbeat` row, and restarts `IntentRouterService` if the classifier is dead.

`StatsScreen` shows three color-coded tiles embedded in `MainActivity`:
- **Accept rate (30d):** green ≥ 75%, amber 60–75%, red < 60%
- **Toast volume (7d):** shows heartbeat count; flags `⚠ DOZE_KILLED?` when heartbeats > 0 and toasts == 0
- **Inference latency (24h):** green < 400 ms, amber 400–500 ms, red ≥ 500 ms

All tile data is loaded asynchronously via `StatsViewModel` (no blocking on the main thread).

---

### Phase 1.10 — Host-side smoke test

| Item | Files |
|---|---|
| Smoke test script | `scripts/phase-1-smoke-test.sh` |

Drives the connected Pixel 8 over ADB: installs the debug APK, fires 100 synthetic events via `am broadcast` to `SmokeTestReceiver` (debug manifest only), pulls `jarvis.db` via `adb exec-out run-as`, and asserts with `sqlite3` + `awk`:
- ≥ 95 events classified (Decision rows in DB)
- p95 inference latency < 500 ms
- No heartbeat sample with `service_alive = 0`

---

### CI

| Workflow | What it checks |
|---|---|
| `ci-training.yml` | pytest + ruff for `training/`; tokenizer hash drift check |
| `ci-android.yml` | `assembleDebug` + `testDebugUnitTest` + `verifyForbiddenDependencies`; forbidden `org.tensorflow:tensorflow-lite*` import grep on `.kt`/`.java` files |
| `ci-termux.yml` | `shellcheck` + `bash -n` on `termux/*.sh` and `scripts/*.sh` |

---

## Partially implemented

### 1.3 — MobileBERT fine-tune

**Status:** Not started.

The training data pipeline (1.2) is ready; the `training/jarvis_training/train/` directory is a stub placeholder. No `train.py`, no Keras checkpoint, no `tokenizer.json` artifact exists yet.

**Blocking:** Requires a vault with `.md` files and `JARVIS_CLOUD_LLM_API_KEY` to run `make synth` first, producing `training/data/clean/intents.jsonl`. Then `make train` can be implemented.

**Impact:** The Android app runs with `StubClassifier` — it classifies every event as `device.action` with 0.99 confidence. The Room DB, HUN pipeline, and smoke test all work end-to-end, but intent classification is meaningless until a real model asset is installed.

---

### 1.4 — LiteRT conversion (PTQ + QAT fallback)

**Status:** Not started.

`training/jarvis_training/convert/` is a stub placeholder. No `to_litert_ptq.py`, no `intent_router.tflite`, no `model_metadata.json` exists. The tokenizer hash guard (`.tokenizer.sha256`) and the `ci-training.yml` hash-drift check are wired; the artifact they reference does not exist yet.

**Impact:** Same as 1.3 — `LiteRtClassifier.tryCreate()` returns null on every cold start.

---

### 1.7 — JSONL outbox write (vault path wiring)

**Status:** ~70% complete.

`OutboxWriter` and `VaultPaths` are fully implemented and unit-tested. The `OutboxDecisionRecord` serialization is correct. What is missing:

- A `VaultManager` that persists the vault root path in SharedPreferences and exposes `getVaultPaths(): VaultPaths?`.
- Wiring in `ToastPipeline` and `ToastActionReceiver` to call `OutboxWriter.append()` after writing to Room.
- UI for the user to configure the vault path (a settings screen or a one-time SAF `OPEN_DOCUMENT_TREE` picker storing the URI).

Until this is done the app runs in SQLite-only mode — the "setup incomplete" notification channel is registered but the notification is not yet posted.

---

### 1.8 — `escalate.burst` Android → Termux HTTP call

**Status:** Stub only.

`ToastActionReceiver.dispatchStubAction()` logs the predicted intent but makes no HTTP call. The Termux llama.cpp server (`run-mid-tier.sh`) is ready to accept connections on `127.0.0.1:8080`, but the Android side has no `OkHttp` (or similar) client wired up. This path is deferred to Phase 2.

---

## Definition of Done — Phase 1 gate status

| Gate | Status |
|---|---|
| `scripts/phase-1-smoke-test.sh` exits 0 on Pixel 8 | **Not yet run** — requires device + debug APK with real model |
| p95 < 500 ms on Pixel 8 / Android 14 | **Not yet run** — requires `intent_router.tflite` (steps 1.3 + 1.4) |
| Overnight idle test — morning event surfaces toast without manual restart | **Not yet run** — requires device |
| ≥ 75% accept rate on 50-event hand-graded set | **Not yet started** — requires real model + user grading session |
| Architecture doc, KPI doc, and decision ADRs current at tag time | **Complete** — `docs/phase-1-architecture.md`, `docs/kpis.md` |

Tag `v0.1.0-mvp` is blocked on completing training steps 1.3 and 1.4, then running the smoke test and hand-graded eval on a Pixel 8.
