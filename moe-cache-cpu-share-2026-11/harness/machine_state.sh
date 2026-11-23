#!/bin/bash
# Lock M5 "machine state, once before arm (a24)" and M4 run-day model re-hash.  machine_state.sh OUT
set -u
OUT=$1; H=$(cd "$(dirname "$0")" && pwd); W=$HOME/moecache-2026-11; M=$W/model/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf
export LD_LIBRARY_PATH=$HOME/cuda-12.8/lib64
mkdir -p "$OUT"; cd "$OUT"
{ echo "# machine state $(date -u +%FT%T) (before arm a24)"; hostname; uname -r; uptime
  nvidia-smi --query-gpu=name,driver_version,vbios_version,memory.used,memory.total,pcie.link.gen.current,pcie.link.width.current,pcie.link.gen.max,pcie.link.width.max --format=csv
  echo "# free / swap (A1: off)"; free -m; swapon --show; cat /proc/swaps
  echo "# A1 units (stopped)"; for u in mycoswarm ollama fwupd ModemManager apt-daily.timer apt-daily-upgrade.timer fwupd-refresh.timer; do echo "$u $(systemctl is-active $u 2>/dev/null)"; done
  echo "# model run-day re-hash (M4; must equal ac0e2c11...31a61)"; ls -l "$M"; sha256sum "$M"
  echo "# NVMe sequential read: dd of the model, iflag=direct, 8 GiB"; dd if="$M" of=/dev/null bs=1M count=8192 iflag=direct 2>&1 | tail -1
  echo "# DDR read bandwidth: stream_read.c (md5 $(md5sum < $H/stream_read.c | cut -c1-32)), gcc -O3 -fopenmp, OMP_NUM_THREADS=4 x3"
  gcc -O3 -fopenmp -o "$W/stream_read" "$H/stream_read.c" && for i in 1 2 3; do OMP_NUM_THREADS=4 "$W/stream_read"; done
  echo "# PCIe at idle"; nvidia-smi --query-gpu=pcie.link.gen.current,pcie.link.width.current --format=csv,noheader
  echo "# build"; "$W/llama.cpp/build/bin/llama-server" --version 2>&1 | tail -3; sha256sum "$W/llama.cpp/build/bin/llama-server" "$W/llama.cpp/build/bin/llama-tokenize"
  git -C "$W/llama.cpp" rev-parse HEAD; git -C "$W/llama.cpp" describe --tags; sha256sum "$W/llama.cpp/scripts/moe-cache-tune.py"
} > machine-state.txt 2>&1
grep -q ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61 machine-state.txt || { echo "STOP: model hash mismatch"; exit 1; }
echo "machine state OK"
