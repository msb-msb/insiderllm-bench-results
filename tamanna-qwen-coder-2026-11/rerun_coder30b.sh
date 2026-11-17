#!/bin/bash
# P4 re-runs, Coder-30B, N = 0 (stage.json): L1-16384, L1-32512 (swap-out > 0 on measured requests, 11-10).
# One re-run each, no second. rerun_qc.py is Rushuna's, unchanged (imports bench_qc.py unchanged). Under memwatch as run_all.sh.
set -u
TOP="$(cd "$(dirname "$0")" && pwd)"; SEQ="$TOP/sequence.log"
F=Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf
echo "$(date -u +%T) === coder30b rerun start; df: $(df -h ~ | tail -1)" >> "$SEQ"
( cd ~/bench-models/qwen-coder && grep " $F\$" SHA256SUMS | sha256sum -c ) > "$TOP/sha256-before-rerun.txt" 2>&1 \
  || { echo "$(date -u +%T) STOP: sha256 mismatch before rerun" >> "$SEQ"; exit 1; }
cd "$TOP/coder30b"
echo "$(date -u +%T) === coder30b rerun L1: 16384 32512" >> "$SEQ"
python3 rerun_qc.py L1 0 16384 32512 > out-rerun-L1.txt 2>&1 & P=$!
python3 memwatch.py . "$P" --count-swap > /dev/null 2>&1 & W=$!
wait "$P"; rc=$?; wait "$W"
mv memwatch.log memwatch-rerun-L1.log; mv memwatch-summary.json memwatch-summary-rerun-L1.json 2>/dev/null
echo "$(date -u +%T) === coder30b rerun L1 rc=$rc" >> "$SEQ"
[ -e TRIPPED ] && { mv TRIPPED TRIPPED-rerun-L1; echo "STOP: floor tripped in rerun L1" >> "$SEQ"; exit 1; }
( cd ~/bench-models/qwen-coder && grep " $F\$" SHA256SUMS | sha256sum -c ) > "$TOP/sha256-after-rerun.txt" 2>&1
echo "$(date -u +%T) === sha256 after rerun: $(cat $TOP/sha256-after-rerun.txt)" >> "$SEQ"
echo "$(date -u +%T) === RERUNS DONE" >> "$SEQ"
