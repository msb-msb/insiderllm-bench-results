#!/bin/bash
export PYTORCH_ALLOC_CONF=expandable_segments:True
for s in 3 4 5 6 7 8 9 10; do
  echo "=== seed $s start $(date '+%H:%M:%S') ==="
  /home/minotaur/lora-venv/bin/python train_adapter.py --seed $s 2>&1 \
    | tr '\r' '\n' | grep -viE "loading weights|it/s\]|^\s*$|warning" | grep -E "load |epoch 10|saved|Error"
  echo "=== seed $s end $(date '+%H:%M:%S') ==="
done
echo "ALL TRAINING DONE $(date '+%H:%M:%S')"
