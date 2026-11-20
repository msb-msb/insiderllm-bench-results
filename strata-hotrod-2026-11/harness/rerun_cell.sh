#!/bin/bash
# H6: "A void cell is re-run once." Re-runs one length of our cells for one arm, same harness, memwatch and egress watch.
#   rerun_cell.sh ARM ROOT CFG OUT MODEL_DIR LENGTH [BWRAP]   -> results-ARM-rerunLENGTH.json in OUT
#   BWRAP = 1 on Tamanna: the bench runs inside `bwrap --dev-bind / / --unshare-net`, as in run_arm.sh
set -u
A=$1; ROOT=$2; CFG=$3; OUT=$4; export MODEL_DIR=$5 HOTROD_LENGTHS=$6
H=$(cd "$(dirname "$0")" && pwd); T="$A-rerun$6"; cd "$OUT"
PFX=(); [ "${7:-0}" = 1 ] && PFX=(bwrap --dev-bind / / --unshare-net)
used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
echo "$(date -u +%FT%T) rerun $T card $used MiB swap [$(swapon --show --noheadings)]" | tee -a sequence-$A.log
[ "$used" -gt 50 ] && exit 1
"${PFX[@]}" python3 "$H/bench_hotrod.py" strata "$T" "$CFG" "$ROOT" > out-cells-$T.txt 2>&1 & P=$!
python3 "$H/memwatch.py" . "$P" --count-swap > /dev/null 2>&1 & W=$!
wait $P; rc=$?; wait $W
mv memwatch.log memwatch-cells-$T.log; mv memwatch-summary.json memwatch-summary-cells-$T.json 2>/dev/null
if [ -e TRIPPED ]; then pkill -f "$ROOT/serve/server.p[y]"; sleep 5; pkill -9 -f "$ROOT/engine/strat[a] "; mv TRIPPED TRIPPED-$T; fi
echo "$(date -u +%FT%T) rerun $T rc=$rc" | tee -a sequence-$A.log
