# Jarvis

**Sovereign mobile AI executive assistant** — Phase 0/1 daily-driver MVP.

A small on-device classifier (MobileBERT, LiteRT, ~25 MB INT8) running as a foreground
service on a Pixel 8, classifying incoming events into 7 intent categories, surfacing
them as interactive Approve / Edit / Dismiss toasts, with a Termux-hosted llama.cpp
mid-tier for burst escalation. No Gemini Nano, no Firebase ML, no Play Services ML.
Network egress is Tailscale-only.

## Layout

| Path | What |
|---|---|
| [android/](android/) | Jetpack Compose + Kotlin app, foreground `IntentRouterService` |
| [training/](training/) | Python pipeline: vault → Gemini synth → MobileBERT fine-tune → LiteRT |
| [termux/](termux/) | Mid-tier llama.cpp Vulkan build + perf-core launcher |
| [docs/](docs/) | Bring-up runbook, architecture, KPIs, ADRs |
| [scripts/](scripts/) | Host-side verify + smoke-test scripts |

## Status

| Phase | State |
|---|---|
| 0 — Environment foundation | in progress |
| 1 — Daily-driver MVP | not started |
| 2 — Soul loop / vault writeback | out of scope |
| 3 — MCP UI atoms beyond Approve/Edit | out of scope |

See [docs/phase-1-architecture.md](docs/phase-1-architecture.md) for the intent schema
and event-to-toast flow. See [docs/kpis.md](docs/kpis.md) for the three KPIs (accept
rate, toast volume, p95 latency) and acceptance gates.

## Legacy homelab stack

The previous content of this repo — `jarvis-console`, `services/router` (Intelligent
Burst Router), `services/provocateur-interviewer`, and the `infrastructure/components`
+ `clusters/np-home-homelab` K8s tree — is preserved on the **`legacy/homelab-stack`**
branch. The Phase 1 mid-tier (Termux llama.cpp) deliberately does not consume that
router; sovereignty principle keeps escalation on-device by default.

## Quickstart

You are not expected to build any of this until Phase 0 verification passes on the
target device. Start with:

1. Read [docs/phase-0-bringup.md](docs/phase-0-bringup.md).
2. Set `JARVIS_HOMELAB_HOST` and `JARVIS_VAULT_PATH` in `~/.jarvisrc` on the phone.
3. Run [scripts/phase-0-verify.sh](scripts/phase-0-verify.sh) in Termux.
4. Proceed to Phase 1 once verify exits 0.
