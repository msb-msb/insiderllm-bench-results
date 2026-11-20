#!/bin/bash
# Qwen3.5-27B-Q4_K_M (MTP repo) at 88fb5663, 8 ranged curls, then assemble + hash. Lock a39c4818 M2.
set -euo pipefail
U=https://huggingface.co/unsloth/Qwen3.5-27B-MTP-GGUF/resolve/88fb5663d646bc78e1140648e8d8cb7d3e849908/Qwen3.5-27B-Q4_K_M.gguf
SIZE=17106773056; D=~/bench-models/qwen3.5-27b-mtp; P=$D/.parts; mkdir -p $P
echo "start $(date -Is)"
CH=$(( (SIZE + 7) / 8 ))
for i in 0 1 2 3 4 5 6 7; do s=$((i*CH)); e=$(( s+CH-1 )); [ $e -ge $SIZE ] && e=$((SIZE-1))
  curl -sfL --retry 5 -r $s-$e "$U" -o $P/part.$i & done
wait
cat $P/part.{0..7} > $D/Qwen3.5-27B-Q4_K_M.gguf; rm -r $P
stat -c %s $D/Qwen3.5-27B-Q4_K_M.gguf
cd $D && sha256sum Qwen3.5-27B-Q4_K_M.gguf | tee SHA256SUMS
echo "done $(date -Is)"
