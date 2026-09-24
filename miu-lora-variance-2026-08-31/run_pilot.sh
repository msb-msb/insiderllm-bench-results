#!/bin/bash
export PYTORCH_ALLOC_CONF=expandable_segments:True
for s in 1 2; do
  echo "=== seed $s start $(date '+%H:%M:%S') ==="
  /home/minotaur/lora-venv/bin/python train_adapter.py --seed $s 2>&1 \
    | tr '\r' '\n' | grep -viE "loading weights|it/s\]|^\s*$|warning" | tail -14
  echo "=== seed $s end $(date '+%H:%M:%S') ==="
done
