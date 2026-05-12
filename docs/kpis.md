# Phase 1 KPIs

Three metrics, each with a formula, a data source, an alert threshold, and an
acceptance gate. Surfaced in the in-app `StatsScreen` (1.9) and asserted by
`scripts/phase-1-smoke-test.sh` (1.10).

## 1. Toast accept rate (30-day rolling)

**Formula**
```
accept_rate = (approves + edits) / (approves + edits + dismisses)
```

`auto_low_confidence` and `timeout` are **not** counted in the denominator —
they represent decisions the user never saw or never had time to respond to,
and the model shouldn't be punished or rewarded for them.

**Data source** — Room `decisions` table, last 30 days:

```sql
SELECT
    SUM(user_action IN ('approve', 'edit')) AS approves,
    SUM(user_action IN ('approve', 'edit', 'dismiss')) AS denom
  FROM decisions
 WHERE created_at >= strftime('%s', 'now', '-30 days') * 1000;
```

**Alert threshold** — accept_rate < 60%. The `StatsScreen` renders the tile
red below this. Action: retrain on the recent decision log to drift the
classifier toward the user's preferences.

**Acceptance gate (Phase 1 DoD #4)** — ≥ 75% accept rate on a 50-event
hand-graded set, captured in [eval/phase-1-acceptance.md](eval/phase-1-acceptance.md).

## 2. Toast volume (7-day daily count) and DOZE_KILLED detection

**Formula**

Per day, the number of decisions where `predicted_intent != 'dismiss'` (i.e.,
events that surfaced a HUN, not auto-suppressed):

```sql
SELECT date(created_at / 1000, 'unixepoch') AS day, COUNT(*) AS toasts
  FROM decisions
 WHERE created_at >= strftime('%s', 'now', '-7 days') * 1000
   AND predicted_intent != 'dismiss'
 GROUP BY day
 ORDER BY day;
```

**DOZE_KILLED detection.** Compare to heartbeat density:

```sql
SELECT date(recorded_at / 1000, 'unixepoch') AS day, COUNT(*) AS heartbeats
  FROM heartbeats
 WHERE recorded_at >= strftime('%s', 'now', '-7 days') * 1000
 GROUP BY day;
```

For any 24-hour window in which `heartbeats > 0` AND `toasts == 0` AND the
device was on (battery-history says so), flag `DOZE_KILLED`. This is the only
way to detect that Android's task killer beat us — the heartbeat says the
WorkManager backstop fired but the foreground service stopped processing
events between fires.

**Alert threshold** — any `DOZE_KILLED` flag in the last 7 days. Action:
inspect logcat for `ForegroundServiceDidNotStartInTimeException` / DropBox
entries; consider a more aggressive ping interval or a notification-listener
fallback path.

## 3. Cold-start inference latency (p50, p95)

**Formula** — over the last 24 hours of decisions, sort
`inference_latency_ms` ascending; p50 is at index `0.5 * (n - 1)`, p95 at
`0.95 * (n - 1)`.

**Data source**

```sql
SELECT inference_latency_ms FROM decisions
 WHERE created_at >= strftime('%s', 'now', '-1 day') * 1000
 ORDER BY inference_latency_ms ASC;
```

(The `DecisionDao.latenciesSince` query in
[android/app/src/main/java/dev/jarvis/data/DecisionDao.kt](../android/app/src/main/java/dev/jarvis/data/DecisionDao.kt)
returns this list.)

**Alert threshold** — p95 ≥ 400 ms (amber); p95 ≥ 500 ms (red).

**Acceptance gate (Phase 1 DoD #2)** — p95 < 500 ms on Pixel 8 / Android 14,
asserted by `scripts/phase-1-smoke-test.sh`.

## Where these are surfaced

- **In-app `StatsScreen`** (Compose) — three tiles, color-coded by threshold,
  with a 7-day chart of toast volume vs heartbeat density.
- **CI smoke test** — fails the build if p95 ≥ 500 ms or `classified < 95`
  out of 100 events.
- **Decision log (Room + JSONL outbox)** — the homelab can run its own
  long-horizon analytics from the synced `outbox/jarvis-decisions/*.jsonl`
  files.

## What's NOT a KPI

- **Per-intent accuracy.** Tracked in `training/`, not in the on-device app.
  The training pipeline's `eval` stage enforces ≥ 85% per-intent val
  accuracy at build time (1.3); drift after deployment is detected by the
  accept rate KPI, not by re-running model evals on-device.
- **Mid-tier (Termux llama.cpp) availability.** Logged but not gated;
  the toast HUN tells the user "Mid-tier offline" inline. We don't surface
  uptime stats because the user's expected reaction is "open Termux, check
  the server", not "let Jarvis silently route around it".
