# Phase 0 — Manual Bring-Up Runbook (Pixel 8 / Android 14)

This phase installs nothing automatically. You run each step on the phone by hand and
finish by running `scripts/phase-0-verify.sh` from inside Termux. When that exits 0,
Phase 0 is done and you can move to Phase 1.

**Target device:** Pixel 8 or Pixel 8 Pro on Android 14 (build UD1A or later). Other
Pixels on Android 13+ may work but are not the validation target.

**Required before you start:**
- A host machine on the same LAN as the phone, with `adb` installed.
- The user's existing Tailscale tailnet, with a homelab host you can reach by hostname.
- The user's existing Syncthing setup, with the Obsidian vault folder shared to a
  device ID that will become the phone.

---

## 1. Termux from F-Droid

Termux on the Play Store is unmaintained. **Install from F-Droid only.**

1. On the phone, install F-Droid: <https://f-droid.org/>.
2. Open F-Droid and install **Termux**: <https://f-droid.org/packages/com.termux/>.
3. Also install:
   - **Termux:Boot** (lets the mid-tier llama.cpp server auto-start on boot):
     <https://f-droid.org/packages/com.termux.boot/>
   - **Termux:API** (used by some helper scripts to fire intents at the Android app
     from inside Termux): <https://f-droid.org/packages/com.termux.api/>
4. Open Termux once so it provisions storage. Run `termux-setup-storage` and grant
   the permission dialog — this creates `~/storage/shared` pointing at
   `/storage/emulated/0`, which is where Syncthing will land the vault.

### 1.1 Termux package list

```sh
pkg update && pkg upgrade -y
pkg install -y \
  python \
  nodejs \
  git \
  openssh \
  proot-distro \
  build-essential \
  cmake \
  clang \
  pkg-config \
  vulkan-headers \
  vulkan-loader \
  libomp \
  curl \
  jq \
  sqlite \
  termux-api
```

These cover: Python for the training pipeline's eval helpers, Node for any host-side
tooling, Git, an SSH server you can use to drive the phone from your laptop,
proot-distro as an Ubuntu escape hatch if Termux package versions diverge from llama.cpp
requirements, and the full C/C++/Vulkan toolchain for `termux/build-llama.sh`.

### 1.2 Optional: Ubuntu under proot

You only need this if a future llama.cpp commit demands a glibc version or library that
Termux's musl-based environment can't supply. Don't run it preemptively.

```sh
proot-distro install ubuntu
proot-distro login ubuntu
# inside the proot:
apt update && apt install -y build-essential cmake clang pkg-config libvulkan-dev
```

---

## 2. Shizuku (no root, via Wireless Debugging)

Shizuku gives the Jarvis app system-level access (notification listener, accessibility
hooks, foreground service exceptions) without root. The pairing is done **once** via
ADB over Wireless Debugging. After that the Shizuku service must be restarted each
boot — Termux:Boot handles this automatically.

1. Install Shizuku from F-Droid: <https://f-droid.org/packages/moe.shizuku.privileged.api/>.
2. On the phone: **Settings → System → Developer options → Wireless debugging → On**.
   Tap "Pair device with pairing code". You'll see an IP, port, and 6-digit code.
3. On the host machine on the same LAN:
   ```sh
   adb pair <phone-ip>:<pair-port>
   # enter the 6-digit pairing code when prompted
   adb connect <phone-ip>:<debug-port>
   ```
4. Open the Shizuku app. Choose **"Start via wireless debugging"** and follow its
   prompts. The Shizuku UI will show **"Running"** with the PID.
5. **Allow Shizuku to access terminal apps**: open Shizuku → Authorized applications →
   toggle **Termux** to allow. This installs the `rish` shim into Termux's PATH.
6. From inside Termux, verify:
   ```sh
   rish -v
   ```
   You should see a version string.

**Important:** if the phone reboots, Wireless Debugging is normally off by default.
Either keep Wireless Debugging always on (Developer options), or use Termux:Boot to
re-pair from the phone itself. The verify script will catch this on every run.

---

## 3. Tailscale

1. Install Tailscale from F-Droid: <https://f-droid.org/packages/com.tailscale.ipn/>
   (or Play Store — Tailscale's Play release is the same binary; F-Droid build is
   preferred for sovereignty).
2. Open Tailscale, sign into the user's existing tailnet, accept the VPN profile.
3. From Termux:
   ```sh
   curl -fsS http://$JARVIS_HOMELAB_HOST:$JARVIS_HOMELAB_HEALTH_PORT/healthz
   ```
   This must return HTTP 200 over the tailnet, not the public internet.
4. Optional: enable Tailscale's "Always-on VPN" in **Settings → Network & internet →
   VPN → Tailscale → Always-on**. This is how the phone reaches the homelab from
   anywhere; without it, the verify script will fail on cellular.

---

## 4. Syncthing — read-only vault on the phone

The phone is **read-only** with respect to the user's markdown vault. This is enforced
in three places (defense in depth):

1. **Protocol level (this section).** Syncthing folder type set to **"Receive Only"**
   on the phone and **"Send Only"** on the homelab.
2. **App level.** The Android app's storage access is scoped read-only via SAF; only
   `$JARVIS_VAULT_PATH/outbox/jarvis-*` is opened for writing.
3. **Test level.** A unit test in `android/app/src/test/` asserts any write outside
   `outbox/` raises.

### 4.1 Install + pair

1. Install Syncthing from F-Droid: <https://f-droid.org/packages/com.github.catfriend1.syncthingandroid/>
   (the maintained fork; the upstream `com.nutomic.syncthingandroid` is no longer
   updated).
2. Open Syncthing on the phone. Note its **device ID** (settings → identification).
3. On the homelab, add the phone's device ID to the vault folder and **share** the
   folder.
4. On the phone, accept the share. Set:
   - **Folder type: Receive Only**
   - **Folder path:** somewhere under `~/storage/shared/` (default
     `~/storage/shared/Documents/JarvisVault` is fine; whatever path you choose, put
     it in `~/.jarvisrc` as `JARVIS_VAULT_PATH`).
   - **Ignore patterns:** leave empty.

### 4.2 Outbox directory

The phone writes its decision log JSONL to `$JARVIS_VAULT_PATH/outbox/jarvis-decisions/`.
For the Receive-Only setup to accept those writes, the **outbox/ subtree must be
excluded on the homelab side** so the homelab Syncthing sends an empty `outbox/`
initially, and the phone is then free to create files there which Syncthing will
push back up.

On the homelab Syncthing instance, edit the vault folder and add to **Ignore Patterns**:

```
// Outbox is phone-authored; do not send phone-conflict files back down
!outbox/**
.stversions
```

This is per-folder Syncthing config, not a Jarvis concern, but the runbook flags it
because forgetting this step is the most common cause of "phone wrote decisions but
they never showed up on the laptop".

---

## 5. The `.jarvisrc` config file

The phone's app and the verify script both read `$VAULT/.jarvisrc` (and fall back to
`~/.jarvisrc` in Termux for the parts the Android app doesn't need to see).

Create `~/.jarvisrc` in Termux:

```sh
# ~/.jarvisrc — Jarvis Phase 0/1 config (sourced by phase-0-verify.sh)
export JARVIS_HOMELAB_HOST="<your-homelab-tailscale-hostname>"
export JARVIS_HOMELAB_HEALTH_PORT="<port-with-a-/healthz-endpoint-on-the-homelab>"
export JARVIS_VAULT_PATH="$HOME/storage/shared/Documents/JarvisVault"
export JARVIS_MID_TIER_MODEL_PATH="$HOME/.jarvis/models/qwen2.5-3b-instruct-q4_k_m.gguf"
```

Then copy a minimal version into the vault so the Android app can find it via SAF:

```sh
mkdir -p "$JARVIS_VAULT_PATH"
cat > "$JARVIS_VAULT_PATH/.jarvisrc" <<'EOF'
# Read by the Android app; only paths it needs to know about.
JARVIS_HOMELAB_HOST=<your-homelab-tailscale-hostname>
JARVIS_HOMELAB_HEALTH_PORT=<port>
EOF
```

---

## 6. Verify

From Termux:

```sh
cd ~ && git clone <this-repo-url> jarvis && cd jarvis
bash scripts/phase-0-verify.sh
```

Exit code 0 means Phase 0 is complete. Any non-zero exit will print a single-line
remediation hint per failed check. Re-run after fixing.
