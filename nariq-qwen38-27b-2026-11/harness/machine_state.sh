#!/bin/bash
# Lock 03361fb7 N5 "machine state, once before the first arm" and N4 run-day re-hash.   machine_state.sh OUT
set -u
OUT=$1; H=$(cd "$(dirname "$0")" && pwd); W=$HOME/nariq-2026-11
export LD_LIBRARY_PATH=$HOME/cuda-12.8/lib64
mkdir -p "$OUT"; cd "$OUT"
{ echo "# machine state $(date -u +%FT%T) (before the first arm)"; hostname; uname -r; uptime
  nvidia-smi --query-gpu=name,driver_version,vbios_version,memory.used,memory.total,pcie.link.gen.current,pcie.link.width.current,pcie.link.gen.max,pcie.link.width.max --format=csv
  echo "# free / swap (A1 not in force, lock N5)"; free -m; swapon --show
  echo "# units (recorded, not stopped)"; for u in mycoswarm ollama fwupd ModemManager apt-daily.timer apt-daily-upgrade.timer fwupd-refresh.timer; do echo "$u $(systemctl is-active $u 2>/dev/null)"; done
  echo "# ollama ps"; ollama ps 2>&1
  echo "# models run-day re-hash (N4)"; ls -l "$W/model/"*.gguf; (cd "$W/model" && sha256sum -c SHA256SUMS)
  echo "# PCIe at idle"; nvidia-smi --query-gpu=pcie.link.gen.current,pcie.link.width.current --format=csv,noheader
  for b in mainline fork; do echo "# build $b"; git -C "$W/$b" rev-parse HEAD; "$W/$b/build/bin/llama-server" --version 2>&1 | tail -2
    sha256sum "$W/$b/build/bin/llama-server" "$W/$b/build/bin/llama-tokenize"; done
} > machine-state.txt 2>&1
[ "$(grep -c ': OK$' machine-state.txt)" = 3 ] || { echo "STOP: model hash mismatch (N4)"; exit 1; }
echo "machine state OK"
