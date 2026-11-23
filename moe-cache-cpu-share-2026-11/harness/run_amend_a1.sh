#!/bin/bash
# Lock c22ff41b, Amendment A1 (post-results, commit 8ea4a796): arm (c) only. The tuner is run once on the (a27)
# command (-ncmoe 27, else the M2 base command), in a fresh --out; its recommended: line is appended verbatim to the
# (a27) command, and that arm runs under the same harness, guard, A1 conditions and void rules as a24/a27/b27.
# If the tuner still runs out of memory: stop and report, no further amendment.
#   run_amend_a1.sh OUT     (OUT = the same record folder as run_all.sh, absolute)
set -u
OUT=$1; H=$(cd "$(dirname "$0")" && pwd); W=$HOME/moecache-2026-11
export LD_LIBRARY_PATH=$HOME/cuda-12.8/lib64
cd "$OUT"
seq() { echo "$(date -u +%FT%T) [A1] $*" | tee -a sequence.log; }
UNITS="mycoswarm ollama fwupd ModemManager apt-daily.timer apt-daily-upgrade.timer fwupd-refresh.timer"

precheck() {
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
  [ "$used" -gt 50 ] && { seq "STOP: card not empty ($used MiB) before $1"; exit 1; }
  [ -n "$(swapon --show --noheadings)" ] && { seq "STOP: swap is on (A1 conditions) before $1"; exit 1; }
  for u in $UNITS; do systemctl is-active -q $u && { seq "STOP: $u is active (A1 conditions) before $1"; exit 1; }; done
  { echo "# $1 $(date -u +%FT%T) card ${used} MiB"; grep -E 'MemAvailable|SwapTotal' /proc/meminfo; swapon --show
    for u in $UNITS; do echo "$u $(systemctl is-active $u 2>/dev/null)"; done; } > state-$1.txt 2>&1
}

guarded() {
  n=$1; shift; seq "=== $n: $*"
  "$@" > out-$n.txt 2>&1 & P=$!
  python3 "$H/memwatch.py" . "$P" --count-swap > /dev/null 2>&1 & G=$!
  wait "$P"; rc=$?; wait "$G"
  mv memwatch.log memwatch-$n.log; mv memwatch-summary.json memwatch-summary-$n.json 2>/dev/null
  pkill -KILL -x llama-server 2>/dev/null; sleep 3
  seq "=== $n rc=$rc card $(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1) MiB"
  [ -e TRIPPED ] && { mv TRIPPED TRIPPED-$n; seq "STOP: memory floor tripped in $n"; exit 1; }
  return $rc
}

seq "amendment A1 start; amended lock file sha256 ed172d567d0a17097b853e739a20a0d90fc72821273a2bedfad7001f3cf41e77"
precheck tuner-A1
TUNE_OUT=$OUT/tune-rushuna-a27; [ -e "$TUNE_OUT" ] && { seq "STOP: $TUNE_OUT exists (fresh --out)"; exit 1; }
BASE27="$W/llama.cpp/build/bin/llama-server -m $W/model/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf -ngl 99 -ncmoe 27 -fa on -c 16384 -np 1 --fit off -lm mmap -t 4 --port 8081"
seq "tuner start UTC $(date -u +%FT%T)"
guarded tuner-A1 python3 "$W/llama.cpp/scripts/moe-cache-tune.py" --out "$TUNE_OUT" -- $BASE27 || { seq "STOP: tuner failed (A1: no further amendment)"; exit 1; }
seq "tuner end UTC $(date -u +%FT%T)"
REC=$(grep -o 'recommended:.*' out-tuner-A1.txt | tail -1); seq "tuner: $REC"
FLAGS=$(echo "$REC" | grep -oE -- '--moe-cache-mib [0-9]+ --moe-cache-cpu-share [0-9.]+')
[ -n "$FLAGS" ] || { seq "STOP: no recommended line parsed"; exit 1; }
echo "$FLAGS" > tuner-A1-flags.txt
precheck c-A1
guarded c-A1 python3 "$H/bench_moecache.py" c-A1 27 $FLAGS || { seq "STOP: arm c-A1 failed"; exit 1; }
seq "=== AMENDED ARM (c) DONE"
