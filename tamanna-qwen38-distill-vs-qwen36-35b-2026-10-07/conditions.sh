#!/bin/bash
# Snapshot of Tamanna's state, written before each phase. Usage: conditions.sh OUTFILE LABEL
{ echo "== $2  $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
  echo "board: $(cat /sys/class/dmi/id/board_vendor) $(cat /sys/class/dmi/id/board_name)  BIOS $(cat /sys/class/dmi/id/bios_version) ($(cat /sys/class/dmi/id/bios_date))"
  echo "cpu: $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2-)"
  echo "RAM: DDR4-2133 per the 10-05 DOCP record (dmidecode needs root, not re-read); MemTotal $(grep MemTotal /proc/meminfo | awk '{print $2}') kB"
  echo "kernel: $(uname -r)  uptime: $(uptime -p)  vm.swappiness $(cat /proc/sys/vm/swappiness)"
  free -m; grep -E "^(MemAvailable|Cached|SwapTotal|SwapFree)" /proc/meminfo; grep -E "^pswp" /proc/vmstat
  df -h / | tail -1
  nvidia-smi --query-gpu=name,driver_version,memory.used,temperature.gpu,pcie.link.gen.max,pcie.link.width.max,power.limit --format=csv,noheader
  echo "llama procs: $(pgrep -a -x 'llama-server|llama-bench' || echo none)  ollama: $(systemctl is-active ollama)  sessions: $(who | wc -l)"
  echo "build: $(cd ~/llama-v0.4.0 && git describe --tags) $(cd ~/llama-v0.4.0 && git rev-parse HEAD)"
  sha256sum ~/bench-models/qwen3.6-35b-a3b-Q4_K_M.gguf ~/bench-models/Qwen3.8-35B-A3B-Distill-Q4_K_M.gguf 2>/dev/null
  echo; } >> "$1"
