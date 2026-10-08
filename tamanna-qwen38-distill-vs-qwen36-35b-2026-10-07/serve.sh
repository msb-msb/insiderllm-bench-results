#!/bin/bash
# llama-server from the v0.4.0 pin for the 47-item runs. The Bonsai 2 run's serve_fork.sh with the binary changed:
# -ngl 99 -fa on --jinja, mmap default, bound to the LAN so the scorer runs from Miu.
# CTX is 4096 for the primary (thinking off, as Bonsai 2) and 16384 for the thinking-on pass (prompt + 8,192 tokens).
set -u
B=/home/minotaur/llama-v0.4.0/build/bin/llama-server
M="$1"; LOG="$2"; CTX="${3:-4096}"
echo "launch $(date -Is): $B -m $M -ngl 99 -fa on -c $CTX --jinja --host 0.0.0.0 --port 8081" >> "$LOG"
exec env LD_LIBRARY_PATH=/home/minotaur/llama-v0.4.0/build/bin "$B" -m "$M" -ngl 99 -fa on -c "$CTX" --jinja --host 0.0.0.0 --port 8081 >> "$LOG" 2>&1
