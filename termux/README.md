# Termux mid-tier — llama.cpp on the phone

A Vulkan-accelerated llama.cpp server pinned to the Tensor G3 performance cores.
The Android service POSTs `escalate.burst` intents to `127.0.0.1:8080` and renders
the response as an `EditableTextAtom`. If the server is down, the toast falls
back to "Mid-tier offline — saved to queue" and the request is persisted in the
app's `pending/` dir for a later replay.

## Scripts

| File | What |
|---|---|
| [build-llama.sh](build-llama.sh) | Clone llama.cpp at the pinned SHA, build with Vulkan, install to `~/.jarvis/llama.cpp` |
| [taskset-wrapper.sh](taskset-wrapper.sh) | Derive a perf-core CPU mask from `/sys/devices/system/cpu/cpufreq/policy*/cpuinfo_max_freq` and exec the wrapped command via `taskset` |
| [run-mid-tier.sh](run-mid-tier.sh) | Start the llama.cpp HTTP server on `127.0.0.1:8080`, pinned to perf cores, model path from `$JARVIS_MID_TIER_MODEL_PATH` |

## Pinned upstream SHA

The build script pins llama.cpp at `LLAMA_CPP_PINNED_SHA` near the top of
[build-llama.sh](build-llama.sh). To bump: update the constant, rerun
`build-llama.sh`, and validate manually with a few `escalate.burst` toasts.
Don't auto-update — llama.cpp is a fast-moving target and silent breakage is
the failure mode we're spending sovereignty effort to avoid.

## CPU pinning

`taskset-wrapper.sh` is deliberately not hardcoded to a CPU mask. The Tensor G3
has 1 X3 (P-core), 4 A715/A710 (M-cores), 4 A510 (E-cores) at different max
frequencies. The wrapper reads each `cpufreq/policy*` directory's
`cpuinfo_max_freq`, picks the two policies with the highest max frequency, and
exec()s `taskset` against the union of their CPU lists. On a Pixel 8 that ends
up pinning to the X3 + the A715 cluster — the two policies that can drive
prompt processing fastest without thermal cliffing into the E-cores.

If you're running on a non-Tensor-G3 device (the runbook says Pixel 8 only, but
Termux runs anywhere) the wrapper still picks the top-2 policies by frequency.
That's the right behavior for any heterogeneous big.LITTLE Android device.

## Termux:Boot integration

To have the server auto-start on phone boot:

```sh
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/jarvis-mid-tier <<'EOF'
#!/data/data/com.termux/files/usr/bin/sh
~/.jarvis/jarvis/termux/run-mid-tier.sh > ~/.jarvis/mid-tier.log 2>&1 &
EOF
chmod +x ~/.termux/boot/jarvis-mid-tier
```

The Termux:Boot app then triggers this on `BOOT_COMPLETED`. Verify after the
next reboot with `curl http://127.0.0.1:8080/health`.
