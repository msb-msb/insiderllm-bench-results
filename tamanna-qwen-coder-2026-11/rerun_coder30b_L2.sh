#!/bin/bash
# P4 re-runs, Coder-30B, N = 0 (stage.json): L2-16384 (prompt_n spread 4 across its 6 requests: void under the stricter reading, A1 2026-11-17).
# One re-run each, no second. rerun_qc.py is Rushuna's, unchanged (imports bench_qc.py unchanged). Under memwatch as run_all.sh.
set -u
TOP="$(cd "$(dirname "$0")" && pwd)"; SEQ="$TOP/sequence.log"
F=Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf
echo "$(date -u +%T) === coder30b rerun L2 start; df: $(df -h ~ | tail -1)" >> "$SEQ"
( cd ~/bench-models/qwen-coder && grep " $F\$" SHA256SUMS | sha256sum -c ) > "$TOP/sha256-before-rerun-L2.txt" 2>&1 \
  || { echo "$(date -u +%T) STOP: sha256 mismatch before rerun" >> "$SEQ"; exit 1; }
cd "$TOP/coder30b"
echo "$(date -u +%T) === coder30b rerun L2: 16384" >> "$SEQ"
python3 rerun_qc.py L2 0 16384 > out-rerun-L2.txt 2>&1 & P=$!
python3 memwatch.py . "$P" --count-swap > /dev/null 2>&1 & W=$!
wait "$P"; rc=$?; wait "$W"
mv memwatch.log memwatch-rerun-L2.log; mv memwatch-summary.json memwatch-summary-rerun-L2.json 2>/dev/null
echo "$(date -u +%T) === coder30b rerun L2 rc=$rc" >> "$SEQ"
[ -e TRIPPED ] && { mv TRIPPED TRIPPED-rerun-L2; echo "STOP: floor tripped in rerun L2" >> "$SEQ"; exit 1; }
( cd ~/bench-models/qwen-coder && grep " $F\$" SHA256SUMS | sha256sum -c ) > "$TOP/sha256-after-rerun-L2.txt" 2>&1
echo "$(date -u +%T) === sha256 after rerun: $(cat $TOP/sha256-after-rerun-L2.txt)" >> "$SEQ"
echo "$(date -u +%T) === RERUN L2 DONE" >> "$SEQ"
