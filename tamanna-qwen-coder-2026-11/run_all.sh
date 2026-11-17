#!/bin/bash
# Qwen Coder pre-registration (lock 918e33f8), Tamanna speed runs, unattended. P3, P4, P7.
# 1. sha256 of every working copy just before load (P7); any mismatch stops everything.
# 2. Day-0 load check (P3) on all three files: coder30b and codernext via prep (which also re-cuts the prompts with each
#    model's tokenizer, P4), codernext3 (UD-IQ3_XXS, the CN3 file) via prep. Any failure: STOP and ask.
# 3. Per model (coder30b, then codernext): stage, L1, L2 at the stage N. No sweep on Tamanna (P4).
# Each step runs under memwatch.py --count-swap, as Rushuna's run_all.sh. Voice environments are not touched (P7).
set -u
TOP="$(cd "$(dirname "$0")" && pwd)"
SEQ="$TOP/sequence.log"
echo "$(date -u +%T) === start; df: $(df -h ~ | tail -1)" >> "$SEQ"
( cd ~/bench-models/qwen-coder && sha256sum -c SHA256SUMS ) > "$TOP/sha256-before-load.txt" 2>&1 \
  || { echo "$(date -u +%T) STOP: sha256 mismatch before load" >> "$SEQ"; exit 1; }
echo "$(date -u +%T) === sha256 before load OK" >> "$SEQ"
step() {
  M=$1; name=$2; shift 2
  cd "$TOP/$M"
  echo "$(date -u +%T) === $M $name: $*" >> "$SEQ"
  python3 bench_qc.py "$@" > "out-$name.txt" 2>&1 &
  P=$!
  python3 memwatch.py . "$P" --count-swap > /dev/null 2>&1 &
  W=$!
  wait "$P"; rc=$?
  wait "$W"
  mv memwatch.log "memwatch-$name.log"; mv memwatch-summary.json "memwatch-summary-$name.json" 2>/dev/null
  echo "$(date -u +%T) === $M $name rc=$rc" >> "$SEQ"
  if [ -e TRIPPED ]; then mv TRIPPED "TRIPPED-$name"; echo "STOP: floor tripped in $M $name" >> "$SEQ"; exit 1; fi
  return $rc
}
for M in coder30b codernext codernext3; do
  step $M prep prep || { echo "STOP: $M day-0 load check failed (P3: STOP and ask)" >> "$SEQ"; exit 1; }
done
for M in coder30b codernext; do
  step $M stage stage || echo "$(date -u +%T) $M stage failed" >> "$SEQ"
  N=$(python3 -c "import json;print(json.load(open('$TOP/$M/stage.json'))['lowest_ncmoe_that_serves_32512_with_ub4096'])" 2>/dev/null)
  if [ -z "$N" ] || [ "$N" = "None" ]; then echo "STOP: $M no -ncmoe served 32,512 at ub 4096" >> "$SEQ"; continue; fi
  for arm in L1 L2; do
    step $M "$arm" llama "$arm" "$N" || echo "$(date -u +%T) $M $arm failed, recorded, continuing" >> "$SEQ"
  done
done
( cd ~/bench-models/qwen-coder && sha256sum -c SHA256SUMS ) > "$TOP/sha256-after.txt" 2>&1
echo "$(date -u +%T) === sha256 after: $(grep -c ': OK' "$TOP/sha256-after.txt") OK of $(wc -l < ~/bench-models/qwen-coder/SHA256SUMS)" >> "$SEQ"
echo "$(date -u +%T) === ALL DONE" >> "$SEQ"
