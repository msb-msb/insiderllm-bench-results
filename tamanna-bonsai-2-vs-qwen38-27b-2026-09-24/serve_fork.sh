#!/bin/bash
# llama-server from the PrismML fork for the 47-item write-path run. Same flags as the Jev-mode server line minus the
# decision fork extras: -ngl 99 -fa on -c 4096 --jinja, mmap default, bound to the LAN so the scorer runs from Miu.
set -u
B=/home/minotaur/llama-prismml/build/bin/llama-server
M="$1"; LOG="$2"
echo "launch $(date -Is): $B -m $M -ngl 99 -fa on -c 4096 --jinja --host 0.0.0.0 --port 8081" >> "$LOG"
exec env LD_LIBRARY_PATH=/home/minotaur/llama-prismml/build/bin "$B" -m "$M" -ngl 99 -fa on -c 4096 --jinja --host 0.0.0.0 --port 8081 >> "$LOG" 2>&1
