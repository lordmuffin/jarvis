#!/usr/bin/env bash
# Pin the wrapped command to the two highest-frequency CPU policies.
#
# Tensor G3 layout: cpufreq/policy0..policy2 cover E/M/P clusters. The two
# policies with the highest cpuinfo_max_freq map to the X3 + the A715 cores.
# We deliberately do NOT hardcode a mask — picking dynamically means this
# wrapper works on any heterogeneous big.LITTLE device.
set -euo pipefail

CPUFREQ_ROOT="${CPUFREQ_ROOT:-/sys/devices/system/cpu/cpufreq}"

if [ "$#" -lt 1 ]; then
  echo "usage: $0 <command> [args...]" >&2
  exit 64
fi

if [ ! -d "$CPUFREQ_ROOT" ]; then
  echo "[taskset-wrapper] $CPUFREQ_ROOT not present — running without pinning" >&2
  exec "$@"
fi

# Collect (max_freq, related_cpus) per policy.
declare -A POLICY_FREQ
declare -A POLICY_CPUS
for p in "$CPUFREQ_ROOT"/policy*; do
  [ -d "$p" ] || continue
  freq_file="$p/cpuinfo_max_freq"
  cpus_file="$p/related_cpus"
  [ -r "$freq_file" ] && [ -r "$cpus_file" ] || continue
  freq=$(<"$freq_file")
  cpus=$(<"$cpus_file")
  POLICY_FREQ["$p"]=$freq
  POLICY_CPUS["$p"]=$cpus
done

if [ "${#POLICY_FREQ[@]}" -eq 0 ]; then
  echo "[taskset-wrapper] no readable cpufreq policies — running without pinning" >&2
  exec "$@"
fi

# Sort policies by descending max_freq, take the top two.
top_two_cpus=$(
  for p in "${!POLICY_FREQ[@]}"; do
    printf "%s\t%s\n" "${POLICY_FREQ[$p]}" "$p"
  done | sort -rn -k1,1 | head -n 2 | awk -F'\t' '{print $2}' \
       | while read -r policy; do echo "${POLICY_CPUS[$policy]}"; done \
       | tr ' \n' ',,' | sed 's/,$//; s/,,/,/g'
)

if [ -z "$top_two_cpus" ]; then
  echo "[taskset-wrapper] could not derive cpu list — running without pinning" >&2
  exec "$@"
fi

if ! command -v taskset >/dev/null 2>&1; then
  echo "[taskset-wrapper] taskset not installed — running without pinning" >&2
  exec "$@"
fi

echo "[taskset-wrapper] pinning to CPUs: $top_two_cpus"
exec taskset -c "$top_two_cpus" "$@"
