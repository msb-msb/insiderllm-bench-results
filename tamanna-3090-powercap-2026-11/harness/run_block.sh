#!/bin/bash
# Arm P, one block (lock tamanna-3090-offload-powercap-2026-11.md, P2/P6).  run_block.sh BLOCK EXPECTED_W
# Run from ~/powercap-2026-11/rec. Precheck, temperature wait (<= 50 C, max 10 min), then bench_p.py under memwatch v3.
set -u
B=$1; W=$2; H=$HOME/powercap-2026-11/harness
export LD_LIBRARY_PATH=$HOME/nariq-t/cuda-libs
seq() { echo "$(date -u +%FT%T) $*" | tee -a sequence.log; }
seq "=== block $B (expect $W W)"
used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
[ "$used" -gt 50 ] && { seq "STOP: card not empty ($used MiB)"; exit 1; }
procs=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -c .)
[ "$procs" -gt 0 ] && { seq "STOP: $procs GPU compute processes"; exit 1; }
t0=$(date +%s)
while :; do
  T=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits | head -1)
  [ "$T" -le 50 ] && break
  [ $(( $(date +%s) - t0 )) -gt 600 ] && { seq "STOP: card still $T C after 10 min"; exit 1; }
  sleep 10
done
{ echo "# $B $(date -u +%FT%T)"; echo "card ${used} MiB, temp ${T} C, waited $(( $(date +%s) - t0 )) s"
  nvidia-smi --query-gpu=power.limit,enforced.power.limit,power.default_limit,power.draw.instant,pstate,clocks.sm,clocks.mem,pcie.link.gen.current,pcie.link.width.current --format=csv
  grep -E 'MemAvailable|MemFree|SwapTotal|SwapFree' /proc/meminfo; swapon --show
  echo "governor $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)"; uptime
  grep -E 'pswpin|pswpout' /proc/vmstat; } > state-$B.txt 2>&1
seq "precheck ok: card $used MiB, temp $T C"
python3 "$H/bench_p.py" "$B" "$W" > out-$B.txt 2>&1 & P=$!
python3 "$H/memwatch.py" . "$P" --count-swap > /dev/null 2>&1 & G=$!
wait "$P"; rc=$?; wait "$G"
mv memwatch.log memwatch-$B.log; mv memwatch-summary.json memwatch-summary-$B.json 2>/dev/null
pkill -KILL -x llama-server 2>/dev/null; sleep 3
nvidia-smi --query-gpu=power.limit,enforced.power.limit,power.default_limit,memory.used,temperature.gpu --format=csv >> state-$B.txt
seq "=== $B rc=$rc card $(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1) MiB"
[ -e TRIPPED ] && { mv TRIPPED TRIPPED-$B; seq "STOP: memory floor tripped in $B"; exit 1; }
exit $rc
