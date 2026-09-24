#!/bin/bash
# Same flags as the ten-seeds section-7 / v0.4.0 runs, plus the fork's --decision-seqs.
# The fork (b9891) has dropped --no-mmap; --load-mode mmap is the same thing (file read into
# process memory rather than mapped), see the 1650-vs-3060 article.
# --decision-seqs 3 is the fork's minimum (cached prefix, trunk, one branch). 16 was tried first and
# failed (cudaMalloc 202 MiB refused at 22 GB used beside the desktop's 4.4 GB); at 3 the endpoint
# still scores all 21 rows of this schema in one round (timings.rounds = 1 on every request).
# Original plan was 16 slots: 1 cached instructions+schema prefix, 1 context in flight, 14 for the parallel
# field paths (3 enum fields x 4 choices = 12 leaves).
set -u
B=/home/minotaur/llama-jev/build/bin/llama-server
M=/media/minotaur/Storage_Disk_1/LLM_repo/qwen3.6-27b-gguf/Qwen_Qwen3.6-27B-Q4_K_M.gguf
LOG=${SERVER_LOG:-$(dirname "$0")/logs/server.log}
echo "launch $(date -Is): $B -m $M -ngl 99 -fa on -c 4096 --jinja --load-mode mmap --port 8081 -kvu --decision-seqs 3" >> "$LOG"
exec "$B" -m "$M" -ngl 99 -fa on -c 4096 --jinja --load-mode mmap --port 8081 -kvu --decision-seqs 3 >> "$LOG" 2>&1
