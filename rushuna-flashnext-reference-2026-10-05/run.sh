#!/bin/bash
# Launch the reference re-run with the v2 stop-rule watchdog. Run from ~/flashnext-reference-2026-10-05.
set -u
cd "$(dirname "$0")"
{ date -u; free -m; grep -E "^(MemAvailable|Cached|SwapTotal|SwapFree)" /proc/meminfo; grep -E "^pswp" /proc/vmstat;
  df -h / | tail -1; nvidia-smi --query-gpu=memory.used,temperature.gpu,pcie.link.gen.max --format=csv,noheader;
  echo "ollama: $(systemctl is-active ollama)"; } > conditions-at-start.txt
nohup python3 ncmoe_sweep.py rushuna > nohup.out 2>&1 < /dev/null &
HP=$!
echo "$HP" > harness.pid
nohup python3 memwatch.py . "$HP" --count-swap > memwatch.out 2>&1 < /dev/null &
echo "harness $HP watchdog $!"
