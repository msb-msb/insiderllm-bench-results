#!/bin/bash
# Lock A1 machine state on Tamanna (once, before arm U) + A1.2 hashes. machine_state_a1.sh
set -u; . "$(dirname "$0")/env.sh"
O=$REC/machine-state.txt
{ echo "# machine state $(date -u +%FT%T) (before arm U, lock A1)"; hostname; uname -r; uptime; cat /sys/class/dmi/id/board_name /sys/class/dmi/id/bios_version
  lscpu | grep -E "Model name|^CPU\(s\)|L3"
  nvidia-smi --query-gpu=name,driver_version,vbios_version,memory.used,memory.total,pcie.link.gen.current,pcie.link.width.current,pcie.link.gen.max,pcie.link.width.max --format=csv
  nvidia-smi --query-compute-apps=pid,name --format=csv,noheader; pgrep -a llama-server
  echo "# free / swap"; free -m; swapon --show; grep -E "pswpin|pswpout" /proc/vmstat
  echo "# units (recorded)"; for u in nvidia-persistenced ollama fwupd ModemManager apt-daily.timer apt-daily-upgrade.timer; do echo "$u $(systemctl is-active $u 2>/dev/null)"; done
  echo "# A1.2 model hashes (lock I3)"; ls -lL $M $DS $SQ10; sha256sum $M $DS $SQ10
  echo "# A1.2 builds (Rushuna binaries by sha256)"; sha256sum $LB/llama-server $LB/llama-perplexity $LB/llama-tokenize; $LB/llama-server --version 2>&1 | tail -2
  sha256sum $W/uns/app.tar.gz $UB/llama-server $UB/llama-perplexity; LD_LIBRARY_PATH=$UB:$LD_LIBRARY_PATH $UB/llama-server --version 2>&1 | tail -2
  sha256sum $W/cuda12-lib/*
  env HOME=$W/strata/home $W/strata/home/.local/bin/strata --version; sha256sum $W/strata/home/.local/share/strata/components/shapes/inkling2/engine/*/strata-inkling
  echo "# wikitext"; sha256sum $W/wikitext-2-raw/wiki.test.raw
  echo "# harness"; sha256sum $H/*.py $H/*.sh $H/ballast.cu $H/corpus.txt $H/prompts/*
  echo "# NVMe sequential read: dd of the Inkling file, iflag=direct, 8 GiB"; dd if=$M of=/dev/null bs=1M count=8192 iflag=direct 2>&1 | tail -1
  echo "# PCIe at idle"; nvidia-smi --query-gpu=pcie.link.gen.current,pcie.link.width.current --format=csv,noheader
  echo "# disk"; df -h $W
} > $O 2>&1
for h in 78fcedcf93c5d1bfe83e225513b71392bb52259be0eaa5f8899c856a2e5834ae 3da00cf7c31bbe5662b3c0d373ecf782d74d32ef43990acc158ce60c2add72e0 ac4d452ad03e4930abd9d46f9c5eec22b2f75a1da45a1e49bd24ccd58b065934 bfbbfe4ad0e8caf641ff3c7a89334f00245a646e83123eb763d517988f4c89eb 390cc60c68d8a75c9d5a060a6a15eccb916cd398c31ac788fb9b8bc34be476b3 c9745b618a3b01c2ad91984c5a1ca79080605a3e57696dc1249fa1555a4bd689 2132fdf5c4e89301ba2417c7d0f2cf4e070ee7a63fda1aba1ba2d6d19f403d29 f3362a140944c6413fdcede7626b3ec6c6e92a217d68d7f803212f9d792985c7 a0105917cb5fd9506656ce1604c2bedcf052f398d6ead9bb57816e7e1aebf012 173c87a53759e0201f33e0ccf978e510c2042d7f2cb78229d9a50d79b9e7dd08; do
  grep -q $h $O || { echo "STOP: $h missing from machine state"; exit 1; }; done
echo "machine state OK"
