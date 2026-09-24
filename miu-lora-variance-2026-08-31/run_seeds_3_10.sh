#!/bin/bash
# Seeds 3-10, same config as seeds 1-2 (train_adapter.py untouched).
# Gate: free VRAM >= 21864 MiB before every launch, else stop the batch.
cd "$(dirname "$0")"
export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/home/minotaur/lora-venv/bin/python
MIN=21864
gate() { local f; f=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)
  echo "gate: free VRAM ${f} MiB (need >= ${MIN})"
  if [ "$f" -lt "$MIN" ]; then echo "GATE FAIL: stopping batch at $1"; touch logs/GATE_FAIL; exit 2; fi; }
for s in 3 4 5 6 7 8 9 10; do
  echo "=== seed $s start $(date '+%H:%M:%S') ==="
  gate "seed $s"
  nvidia-smi --query-gpu=timestamp,memory.used --format=csv,noheader,nounits -l 1 > logs/vram_seed$s.csv &
  SMI=$!
  $PY train_wrap.py --seed $s > logs/train_seed$s.raw 2>&1
  rc=$?
  kill $SMI 2>/dev/null; wait $SMI 2>/dev/null
  tr '\r' '\n' < logs/train_seed$s.raw | grep -viE "loading weights|it/s\]|^\s*$|warning" > logs/train_seed$s.log
  grep -E "^load |epoch|saved|peak torch|Error" logs/train_seed$s.log
  echo "seed $s rc=$rc nvidia-smi peak used $(cut -d, -f2 logs/vram_seed$s.csv | sort -n | tail -1) MiB"
  echo "=== seed $s end $(date '+%H:%M:%S') ==="
done
echo "ALL TRAINING DONE $(date '+%H:%M:%S')"
PLAN=""
for s in 3 4 5 6 7 8 9 10; do
  [ -f adapters/seed$s/adapter_model.safetensors ] && PLAN="${PLAN:+$PLAN,}seed$s:adapters/seed$s:1"
done
echo "scoring plan: $PLAN"
if [ -n "$PLAN" ]; then
  gate "scoring"
  $PY score_hf.py --plan "$PLAN" --split test --outdir scored_hf 2>&1 | tr '\r' '\n' | grep -viE "loading weights|it/s\]|^\s*$|warning"
fi
echo "ALL DONE $(date '+%H:%M:%S')"
touch logs/SEEDS_3_10_DONE
