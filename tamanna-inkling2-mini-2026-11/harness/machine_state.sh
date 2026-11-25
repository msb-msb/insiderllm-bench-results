#!/bin/bash
# Lock I5 "machine state" (once, before arm L) + I6.2/I6.3 hashes. machine_state.sh
set -u; . "$(dirname "$0")/env.sh"
O=$REC/machine-state.txt
{ echo "# machine state $(date -u +%FT%T) (before arm L)"; hostname; uname -r; uptime
  nvidia-smi --query-gpu=name,driver_version,vbios_version,memory.used,memory.total,pcie.link.gen.current,pcie.link.width.current,pcie.link.gen.max,pcie.link.width.max --format=csv
  nvidia-smi --query-compute-apps=pid,name --format=csv,noheader; pgrep -a llama-server
  echo "# free / swap"; free -m; swapon --show; grep -E "pswpin|pswpout" /proc/vmstat
  echo "# units (recorded, not required by this lock)"; for u in mycoswarm ollama fwupd ModemManager apt-daily.timer apt-daily-upgrade.timer fwupd-refresh.timer; do echo "$u $(systemctl is-active $u 2>/dev/null)"; done
  echo "# I6.2 model hashes (lock I3)"; ls -lL $M $DS $Q $SQ10; sha256sum $M $DS $SQ10; sha256sum -b $Q
  echo "# I6.3 builds"; git -C $W/build/llama.cpp rev-parse HEAD; sha256sum $LB/llama-server $LB/llama-perplexity $LB/llama-tokenize; $LB/llama-server --version 2>&1 | tail -2
  sha256sum $W/uns/app.tar.gz $UB/llama-server $UB/llama-perplexity; LD_LIBRARY_PATH=$UB:$LD_LIBRARY_PATH $UB/llama-server --version 2>&1 | tail -2
  echo "# wikitext"; sha256sum $W/wikitext-2-raw/w.zip $W/wikitext-2-raw/wiki.test.raw
  echo "# harness"; sha256sum $H/*.py $H/*.sh $H/ballast.cu $H/ballast $H/corpus.txt $H/prompts/*
  echo "# NVMe sequential read: dd of the Inkling file, iflag=direct, 8 GiB"; dd if=$M of=/dev/null bs=1M count=8192 iflag=direct 2>&1 | tail -1
  echo "# DDR read bandwidth: stream_read.c, gcc -O3 -fopenmp, OMP_NUM_THREADS=4 x3"
  gcc -O3 -fopenmp -o $W/stream_read $H/stream_read.c && for i in 1 2 3; do OMP_NUM_THREADS=4 $W/stream_read; done
  echo "# PCIe at idle"; nvidia-smi --query-gpu=pcie.link.gen.current,pcie.link.width.current --format=csv,noheader
  echo "# disk"; df -h $W
} > $O 2>&1
for h in 78fcedcf93c5d1bfe83e225513b71392bb52259be0eaa5f8899c856a2e5834ae 3da00cf7c31bbe5662b3c0d373ecf782d74d32ef43990acc158ce60c2add72e0 ac4d452ad03e4930abd9d46f9c5eec22b2f75a1da45a1e49bd24ccd58b065934 ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61 33aeb17f85869279e3821f746bc645357139bc2c c9745b618a3b01c2ad91984c5a1ca79080605a3e57696dc1249fa1555a4bd689; do
  grep -q $h $O || { echo "STOP: $h missing from machine state"; exit 1; }; done
echo "machine state OK"
