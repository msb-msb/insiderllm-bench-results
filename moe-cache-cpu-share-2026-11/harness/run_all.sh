#!/bin/bash
# Lock c22ff41b (sha256 f047318b...), M2 order: a24, a27, fit gate, b27, tuner, c. Unattended, on Rushuna.
#   run_all.sh OUT        (OUT = record folder; the harness folder holds the prompts)
# Each arm runs bench_moecache.py under memwatch.py v3 (--count-swap: only the 2 GiB MemAvailable floor stops a run).
# A1 is checked before every arm; the card must read 0 MiB before every arm.
set -u
OUT=$1; H=$(cd "$(dirname "$0")" && pwd); W=$HOME/moecache-2026-11
export LD_LIBRARY_PATH=$HOME/cuda-12.8/lib64   # user-space CUDA runtime (no system CUDA on Rushuna)
mkdir -p "$OUT"; cd "$OUT"
seq() { echo "$(date -u +%FT%T) $*" | tee -a sequence.log; }
UNITS="mycoswarm ollama fwupd ModemManager apt-daily.timer apt-daily-upgrade.timer fwupd-refresh.timer"

precheck() {  # lock M5 (A1) and M2 (card at 0 MiB)
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
  [ "$used" -gt 50 ] && { seq "STOP: card not empty ($used MiB) before $1"; exit 1; }
  [ -n "$(swapon --show --noheadings)" ] && { seq "STOP: swap is on (lock A1) before $1"; exit 1; }
  for u in $UNITS; do systemctl is-active -q $u && { seq "STOP: $u is active (lock A1) before $1"; exit 1; }; done
  { echo "# $1 $(date -u +%FT%T) card ${used} MiB"; grep -E 'MemAvailable|SwapTotal' /proc/meminfo; swapon --show
    for u in $UNITS; do echo "$u $(systemctl is-active $u 2>/dev/null)"; done; } > state-$1.txt 2>&1
}

guarded() {  # name, then the command; memwatch v3 around it
  n=$1; shift; seq "=== $n: $*"
  "$@" > out-$n.txt 2>&1 & P=$!
  python3 "$H/memwatch.py" . "$P" --count-swap > /dev/null 2>&1 & G=$!
  wait "$P"; rc=$?; wait "$G"
  mv memwatch.log memwatch-$n.log; mv memwatch-summary.json memwatch-summary-$n.json 2>/dev/null
  pkill -KILL -x llama-server 2>/dev/null; sleep 3   # no server outlives its step (HotRod fix)
  seq "=== $n rc=$rc card $(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1) MiB"
  [ -e TRIPPED ] && { mv TRIPPED TRIPPED-$n; seq "STOP: memory floor tripped in $n"; exit 1; }
  return $rc
}

arm() { precheck "$1"; guarded "$1" python3 "$H/bench_moecache.py" "$@" || { seq "STOP: arm $1 failed"; exit 1; }; }

seq "run start; lock sha256 f047318b9eceb00315e803e94189af1b68484293ab6b187ab0ddc2c07746f6a4"
arm a24 24
arm a27 27

# M2 fit gate (M10.4): (a27)'s measured peak + 1,866 + 1,024 <= 11,909 MiB. Load peak and whole-arm peak are both
# read; the gate uses the larger, so it holds for either reading of "load peak".
python3 - <<'EOF' | tee -a sequence.log fit-gate.txt
import json; r = json.load(open("results-a27.json"))
lp, ap = r["load_peak_mib"], r["arm_peak_mib"]; pk = max(lp, ap); s = pk + 1866 + 1024
print(f"FIT GATE: a27 load peak {lp} MiB, arm peak {ap} MiB; {pk} + 1866 + 1024 = {s} MiB vs 11909 -> {'PASS' if s <= 11909 else 'FAIL'}")
open("fit-gate.result", "w").write("PASS" if s <= 11909 else "FAIL")
EOF
[ "$(cat fit-gate.result)" = PASS ] || { seq "STOP: fit gate failed; no further arm (lock M2: Mark is told)"; exit 2; }

arm b27 27 --moe-cache-mib 1866

# tuner (c): given the (a24) command, fresh --out, run once
precheck tuner
TUNE_OUT=$OUT/tune-rushuna; [ -e "$TUNE_OUT" ] && { seq "STOP: $TUNE_OUT exists (lock M2: fresh --out)"; exit 1; }
BASE24="$W/llama.cpp/build/bin/llama-server -m $W/model/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf -ngl 99 -ncmoe 24 -fa on -c 16384 -np 1 --fit off -lm mmap -t 4 --port 8081"
seq "tuner start UTC $(date -u +%FT%T)"
guarded tuner python3 "$W/llama.cpp/scripts/moe-cache-tune.py" --out "$TUNE_OUT" -- $BASE24 || { seq "STOP: tuner failed"; exit 1; }
seq "tuner end UTC $(date -u +%FT%T)"
REC=$(grep -o 'recommended:.*' out-tuner.txt | tail -1); seq "tuner: $REC"
FLAGS=$(echo "$REC" | grep -oE -- '--moe-cache-mib [0-9]+ --moe-cache-cpu-share [0-9.]+')
[ -n "$FLAGS" ] || { seq "STOP: no recommended line parsed"; exit 1; }
echo "$FLAGS" > tuner-flags.txt
arm c 24 $FLAGS
seq "=== ALL ARMS DONE"
