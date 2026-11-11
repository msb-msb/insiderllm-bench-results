#!/bin/bash
# Qwen Coder pre-registration (lock 918e33f8), Rushuna, unattended.
# Per model (coder30b, then codernext): prep (= day-0 load check + prompt re-cut), sweep, stage, L1, L2.
# Each step runs under memwatch.py --count-swap (only MemAvailable < 2 GiB stops it), as the Strata record.
# A failed day-0 load check stops everything (lock P3: STOP and ask).
set -u
TOP="$(cd "$(dirname "$0")" && pwd)"
for M in coder30b codernext; do
  cd "$TOP/$M"
  step() {
    name=$1; shift
    echo "$(date -u +%T) === $M $name: $*" >> "$TOP/sequence.log"
    python3 bench_qc.py "$@" > "out-$name.txt" 2>&1 &
    P=$!
    python3 memwatch.py . "$P" --count-swap > /dev/null 2>&1 &
    W=$!
    wait "$P"; rc=$?
    wait "$W"
    mv memwatch.log "memwatch-$name.log"; mv memwatch-summary.json "memwatch-summary-$name.json" 2>/dev/null
    echo "$(date -u +%T) === $M $name rc=$rc" >> "$TOP/sequence.log"
    if [ -e TRIPPED ]; then mv TRIPPED "TRIPPED-$name"; echo "STOP: floor tripped in $M $name" >> "$TOP/sequence.log"; exit 1; fi
    return $rc
  }
  step prep prep || { echo "STOP: $M day-0 load check failed" >> "$TOP/sequence.log"; exit 1; }
  step sweep sweep || echo "$(date -u +%T) $M sweep failed, recorded, continuing" >> "$TOP/sequence.log"
  step stage stage || echo "$(date -u +%T) $M stage failed" >> "$TOP/sequence.log"
  N=$(python3 -c "import json;print(json.load(open('stage.json'))['lowest_ncmoe_that_serves_32512_with_ub4096'])" 2>/dev/null)
  if [ -z "$N" ] || [ "$N" = "None" ]; then echo "STOP: $M no -ncmoe served 32,512 at ub 4096" >> "$TOP/sequence.log"; continue; fi
  for arm in L1 L2; do
    step "$arm" llama "$arm" "$N" || echo "$(date -u +%T) $M $arm failed, recorded, continuing" >> "$TOP/sequence.log"
  done
done
echo "$(date -u +%T) === ALL DONE" >> "$TOP/sequence.log"
