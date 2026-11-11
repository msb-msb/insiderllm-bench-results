#!/bin/bash
# P4 re-runs, Coder-Next, N = 34 (stage.json): L1-16384, L2-16384, L2-32512. Under memwatch as run_all.sh.
set -u
cd "$(dirname "$0")/codernext"
for spec in "L1 16384" "L2 16384 32512"; do
  set -- $spec; arm=$1; shift
  echo "$(date -u +%T) === codernext rerun $arm: $*" >> ../sequence.log
  python3 rerun_qc.py "$arm" 34 "$@" > "out-rerun-$arm.txt" 2>&1 & P=$!
  python3 memwatch.py . "$P" --count-swap > /dev/null 2>&1 & W=$!
  wait "$P"; rc=$?; wait "$W"
  mv memwatch.log "memwatch-rerun-$arm.log"; mv memwatch-summary.json "memwatch-summary-rerun-$arm.json" 2>/dev/null
  echo "$(date -u +%T) === codernext rerun $arm rc=$rc" >> ../sequence.log
  if [ -e TRIPPED ]; then mv TRIPPED "TRIPPED-rerun-$arm"; echo "STOP: floor tripped in rerun $arm" >> ../sequence.log; exit 1; fi
done
echo "$(date -u +%T) === RERUNS DONE" >> ../sequence.log
