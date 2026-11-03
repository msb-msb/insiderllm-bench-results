#!/bin/bash
# Supplementary to C1 (2026-11-03, after all measured arms): the v0.7.0 server prints no KV / RS / compute buffer
# lines at default verbosity, so each C1 command is re-loaded once with -lv 4 added, health-checked, and stopped.
# Not measured runs; only the buffer lines are read from these logs.
cd ~/llamacpp-v0.7-nemotron-bolt-2026-10 || exit 1
B=~/llama-v0.7.0/build/bin
M=~/bench-models/nemotron-3.5-bolt-24gb/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB.gguf
for K in f16 q8_0; do for C in 32768 131072; do
  [ -z "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader)" ] || { echo "guard: compute apps busy"; exit 1; }
  L=buffers-C1-$K-$C.log
  LD_LIBRARY_PATH=$B $B/llama-server -m $M -ngl 99 -fa on -c $C -np 1 -ctk $K -ctv $K --fit off -lm mmap -t 8 --port 8081 -lv 4 > $L 2>&1 &
  P=$!
  until curl -s http://127.0.0.1:8081/health | grep -q ok; do kill -0 $P 2>/dev/null || break; sleep 1; done
  echo "== $K $C: $(nvidia-smi --query-gpu=memory.used --format=csv,noheader) after load"
  kill -INT $P; wait $P
  grep -E -i "KV buffer size|RS buffer size|compute buffer size|model buffer size|memory breakdown|\| +- CUDA0|graph splits" $L | sed 's/^[0-9.]* //' | head -20
done; done
