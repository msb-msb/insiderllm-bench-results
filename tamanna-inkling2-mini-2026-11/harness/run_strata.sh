#!/bin/bash
# Lock I5 Strata arms (S10, S10d, S10-greedy, S10max, S10-split). run_strata.sh [ARM ...]
set -u; . "$(dirname "$0")/env.sh"
SH=$W/strata/home; ST="env HOME=$SH $SH/.local/bin/strata"
BASE="launch --model-path $SQ10 --model sq-10 --family inkling-2-mini --vision off --parallel 1 --tune skip --access local --port 8090 --no-api-key --no-tui --yes --restart"
busy() { nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -q . || pgrep -x llama-server >/dev/null; }
sarm() {  # sarm NAME CELLS [--temp X] -- launch extras
  local name=$1 cells=$2; shift 2
  local opts=(); while [ "$1" != "--" ]; do opts+=("$1"); shift; done; shift
  while busy; do echo "$(date +%T) I11.4: card busy, waiting"; sleep 60; done
  MEMWATCH_EXTRA_NAMES=strata-inkling $H/run_arm.sh $name --tag inkling --cells $cells --kind strata --port 8090 \
     --engine-name strata-inkling --stop-cmd "$ST launch --stop" "${opts[@]}" -- $ST $BASE "$@"
  local rc=$?
  cp $SH/.local/state/strata/launch/*.engine.log $REC/arms/ 2>/dev/null
  for f in $SH/.local/state/strata/launch/*.json; do cp $f $REC/arms/$name-$(basename $f); done
  return $rc
}
ALL="S10-8k S10-16k S10d-8k S10d-16k S10-greedy S10max S10-split"
for a in ${@:-$ALL}; do case $a in
  S10-8k)   sarm $a short:512:3,deep:7372:3  -- --context 8k  --drafting off ;;
  S10-16k)  sarm $a short:512:3,deep:14746:3 -- --context 16k --drafting off ;;
  S10d-8k)  sarm $a short:512:3,deep:7372:3  -- --context 8k ;;
  S10d-16k) sarm $a short:512:3,deep:14746:3 -- --context 16k ;;
  S10-greedy) sarm $a short:512:3 --temp 0 -- --context 8k ;;
  S10max)
    for c in 24576:22118 32768:29491 49152:44237 65536:58982; do
      sarm S10max-${c%%:*} deep:${c##*:}:1 -- --context ${c%%:*} || { echo "S10max: ${c%%:*} failed (I5: largest passing context is the maximum)"; break; }
    done ;;
  S10-split) sarm $a short:512:1 -- --context 64k --set vram-experts-gb=5 ;;
  *) echo "unknown arm $a"; exit 1 ;;
esac; done
