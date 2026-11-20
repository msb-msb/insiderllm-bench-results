#!/bin/bash
# Strata HotRod lock (c06003fc) H5, one arm on one rig, unattended:
#   0. card must read 0 MiB; machine-state block (RAM, driver, PCIe idle link, model drive)
#   1. the arm's own strata_bench.py, default suite (--config/--out only), under memwatch --count-swap and a
#      whole-machine egress log (strata_bench starts its own server, so the watch is not per-pid)
#   2. bench_hotrod.py (our cells) under memwatch --count-swap; it has its own per-pid egress watch
# usage: run_arm.sh ARM ROOT CFG OUT MODEL_DIR [BWRAP]
#   ROOT = folder with the arm's .venv and serve/ ; CFG = the config the arm's setup wrote ; OUT = record folder
#   BWRAP = 1 on Tamanna: every python step runs inside `bwrap --dev-bind / / --unshare-net` (loopback only)
set -u
A=$1; ROOT=$2; CFG=$3; OUT=$4; export MODEL_DIR=$5; BW=${6:-0}
H=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT"; cd "$OUT"
PFX=(); [ "$BW" = 1 ] && PFX=(bwrap --dev-bind / / --unshare-net)
seq() { echo "$(date -u +%FT%T) $*" | tee -a sequence-$A.log; }

used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
seq "arm $A root $ROOT cfg $CFG model $MODEL_DIR card ${used} MiB bwrap $BW"
[ "$used" -gt 50 ] && { seq "STOP: card not empty"; exit 1; }
if [ "$(hostname)" = rushuna ]; then   # lock A1: no swap, those units stopped
  [ -n "$(swapon --show --noheadings)" ] && { seq "STOP: swap is on (lock A1)"; exit 1; }
  for u in mycoswarm ollama fwupd ModemManager apt-daily.timer apt-daily-upgrade.timer fwupd-refresh.timer; do
    systemctl is-active -q $u && { seq "STOP: $u is active (lock A1)"; exit 1; }; done
fi
{ echo "# machine state $(date -u +%FT%T)"; uname -r; nvidia-smi --query-gpu=name,driver_version,pcie.link.gen.max,pcie.link.width.max --format=csv
  grep -E 'MemTotal|MemAvailable|SwapTotal|SwapFree' /proc/meminfo; df -h "$MODEL_DIR" | tail -1
  echo "# swap (lock A1: off on Rushuna)"; swapon --show; cat /proc/swaps
  echo "# units (lock A1: stopped on Rushuna)"; for u in mycoswarm ollama fwupd ModemManager apt-daily.timer apt-daily-upgrade.timer fwupd-refresh.timer; do echo "$u $(systemctl is-active $u 2>/dev/null)"; done
  readlink -f "$MODEL_DIR"; sha256sum "$CFG"; cat "$CFG"; } > state-$A.txt 2>&1

egress_all() {  # whole machine: established TCP to a non-loopback peer; ssh (:22) and inbound to Rushuna's mycoSwarm
               # daemon (:7890, Mark's, polled from the router; seen in arm U on 2026-11-20) excluded
  while :; do ss -tnpH state established 2>/dev/null | awk '$4 !~ /^(127\.|\[::1\]|\[::ffff:127\.)/ && $3 !~ /:(22|7890)$/ && $4 !~ /:22$/' \
      | sed "s/^/$(date -u +%T) /" >> egress-sb-$A.log; sleep 2; done; }

step() {  # name, then the command
  n=$1; shift; seq "=== $n: $*"
  "$@" > out-$n-$A.txt 2>&1 & P=$!
  python3 "$H/memwatch.py" . "$P" --count-swap > /dev/null 2>&1 & W=$!
  wait "$P"; rc=$?; wait "$W"
  mv memwatch.log memwatch-$n-$A.log; mv memwatch-summary.json memwatch-summary-$n-$A.json 2>/dev/null
  seq "=== $n rc=$rc"
  if [ -e TRIPPED ]; then   # memwatch only kills llama-* by name: stop this arm's server and engine too
    pkill -f "$ROOT/serve/server.p[y]"; sleep 5; pkill -9 -f "$ROOT/engine/strat[a] "; sleep 3
    mv TRIPPED TRIPPED-$n-$A; seq "STOP: memory floor tripped in $n (card $(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1) MiB after cleanup)"; exit 1
  fi
  return $rc
}

touch egress-sb-$A.log; egress_all & E=$!
trap 'kill $E 2>/dev/null' EXIT   # a STOP exit must not leave the watch loop behind (seen after H's trip)
if [ "${SB_PRESTART:-0}" = 1 ]; then   # H, B: see sb_prestart.sh (strata_bench port bug)
  step sb "${PFX[@]}" "$H/sb_prestart.sh" "$ROOT" "$CFG" "$OUT/strata-bench-$A"   # one namespace for server, health check and tool
else
  step sb "${PFX[@]}" "$ROOT/.venv/bin/python" "$ROOT/tools/strata_bench.py" --config "$CFG" --out "$OUT/strata-bench-$A"
fi
[ -e "$OUT/strata-bench-$A" ] || { kill $E 2>/dev/null; seq "STOP: strata_bench produced no results (H5 warm-up missing)"; exit 1; }
kill $E 2>/dev/null
step cells "${PFX[@]}" python3 "$H/bench_hotrod.py" strata "$A" "$CFG" "$ROOT"
seq "=== card after: $(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1) MiB"
seq "=== ARM $A DONE"
