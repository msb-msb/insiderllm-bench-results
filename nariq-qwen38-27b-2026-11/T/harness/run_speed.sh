#!/bin/bash
# Section T speed arms (lock A1, T5) on Tamanna: M-IQ3, F-IQ3, F-N3, F-N25, R-Q4. No fit probe. Unattended.
#   run_all.sh OUT        (OUT = record folder; the harness folder holds the prompts)
# Each arm runs bench_t.py under memwatch.py v3 (--count-swap: only the 2 GiB MemAvailable floor stops a run).
set -u
OUT=$1; H=$(cd "$(dirname "$0")" && pwd)
export LD_LIBRARY_PATH=$HOME/nariq-t/cuda-libs
mkdir -p "$OUT"; cd "$OUT"
seq() { echo "$(date -u +%FT%T) $*" | tee -a sequence.log; }
IQ3=Qwen3.8-27B-UD-IQ3_XXS.gguf; Q4=Qwen3.8-27B-UD-Q4_K_XL.gguf; N3=Qwen3.8-27B-NariQ-3.0bpw.gguf; N25=Qwen3.8-27B-NariQ-2.5bpw.gguf

daemons() {  # CPU seconds (utime+stime) of mycoswarm and ollama processes (lock N5)
  python3 - <<'P'
import os
tck = os.sysconf("SC_CLK_TCK"); tot = {}
for pid in filter(str.isdigit, os.listdir("/proc")):
    try:
        cmd = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode()
        st = open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()
    except OSError:
        continue
    for k in ("mycoswarm", "ollama"):
        if k in cmd and "python3 -" not in cmd:
            tot[k] = tot.get(k, 0) + (int(st[11]) + int(st[12])) / tck
print(" ".join(f"{k}={v:.2f}" for k, v in sorted(tot.items())))
P
}

precheck() {  # lock N10.4: card <= 50 MiB, ollama ps empty
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
  [ "$used" -gt 50 ] && { seq "STOP: card not empty ($used MiB) before $1"; exit 1; }
  [ "$(ollama ps 2>/dev/null | tail -n +2 | grep -c .)" -gt 0 ] && { seq "STOP: ollama has a model loaded before $1"; exit 1; }
  { echo "# $1 $(date -u +%FT%T) card ${used} MiB"; grep -E 'MemAvailable|SwapTotal|SwapFree' /proc/meminfo; swapon --show
    echo "daemons-before $(daemons)"; } > state-$1.txt 2>&1
}

guarded() {  # name, then the command; memwatch v3 around it
  n=$1; shift; seq "=== $n: $*"
  "$@" > out-$n.txt 2>&1 & P=$!
  python3 "$H/memwatch.py" . "$P" --count-swap > /dev/null 2>&1 & G=$!
  wait "$P"; rc=$?; wait "$G"
  mv memwatch.log memwatch-$n.log; mv memwatch-summary.json memwatch-summary-$n.json 2>/dev/null
  pkill -KILL -x llama-server 2>/dev/null; sleep 3
  echo "daemons-after $(daemons)" >> state-$n.txt
  seq "=== $n rc=$rc card $(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1) MiB"
  [ -e TRIPPED ] && { mv TRIPPED TRIPPED-$n; seq "STOP: memory floor tripped in $n"; exit 1; }
  return $rc
}

# lock N2: an arm that does not load at -c 8192 is reported and the run goes on
arm() { precheck "$1"; guarded "$1" python3 "$H/bench_t.py" "$@" || seq "arm $1 FAILED (reported, run continues: lock N2)"; }
# (no fit probe in section T)
_unused_probe() { precheck "$1"; export PROBE=1; guarded "$1" python3 "$H/bench_t.py" "$@" || seq "probe $1 did not load/answer (reported)"; unset PROBE; }

seq "run start; lock A1 sha256 ${A1_SHA:-unset} (env A1_SHA)"
arm M-IQ3 mainline $IQ3
arm F-IQ3 fork $IQ3
arm F-N3 fork $N3
arm F-N25 fork $N25
arm R-Q4 mainline $Q4
seq "=== ALL DONE"
