#!/bin/bash
# P4 re-runs of the three cells A1 (stricter prompt_n reading, 2026-11-17) made void, one each:
#   Coder-30B L2 16384 + 32512 at N = 30, Coder-Next L2 4096 at N = 34 (stage.json). Under memwatch as run_all.sh.
set -u
cd "$(dirname "$0")"
echo "$(date -u +%T) === A1 RERUNS start $(date -u +%F)" >> sequence.log
( cd ~/bench-models/qwen-coder && sha256sum -c SHA256SUMS ) >> sequence.log 2>&1 || { echo "STOP: hash mismatch" >> sequence.log; exit 1; }
for spec in "coder30b L2 30 16384 32512" "codernext L2 34 4096"; do
  set -- $spec; m=$1; arm=$2; n=$3; shift 3
  cd "$m"
  echo "$(date -u +%T) === $m rerun-a1 $arm N=$n: $*" >> ../sequence.log
  python3 rerun_a1_qc.py "$arm" "$n" "$@" > "out-rerun-a1-$arm.txt" 2>&1 & P=$!
  python3 memwatch.py . "$P" --count-swap > /dev/null 2>&1 & W=$!
  wait "$P"; rc=$?; wait "$W"
  mv memwatch.log "memwatch-rerun-a1-$arm.log"; mv memwatch-summary.json "memwatch-summary-rerun-a1-$arm.json" 2>/dev/null
  echo "$(date -u +%T) === $m rerun-a1 $arm rc=$rc" >> ../sequence.log
  if [ -e TRIPPED ]; then mv TRIPPED "TRIPPED-rerun-a1-$arm"; echo "STOP: floor tripped in $m rerun-a1 $arm" >> ../sequence.log; exit 1; fi
  cd ..
done
echo "$(date -u +%T) === A1 RERUNS DONE" >> sequence.log
