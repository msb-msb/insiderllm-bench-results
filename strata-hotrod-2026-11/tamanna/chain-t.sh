#!/bin/bash
# Strata HotRod lock (c06003fc), Tamanna: machine state, shard re-hash (H4), then arms U, H, B (H5 order), bwrap (H3).
set -u
W=$HOME/hotrod-2026-11; M=$HOME/bench-models/qwen3.8-flash-next-iq3s; H=$W/harness; O=$W/rec/tamanna; mkdir -p $O
log() { echo "$(date -u +%FT%T) $*" | tee -a $O/chain.log; }
free20() { a=$(df --output=avail -BG / | tail -1 | tr -dc 0-9); log "free ${a}G"; [ "$a" -ge 20 ] || { log "STOP: under 20 GB free (H4)"; exit 1; }; }
log "chain start"; free20
{ echo "# machine state $(date -u +%FT%T)"; uname -r; nvidia-smi --query-gpu=name,driver_version,pcie.link.gen.max,pcie.link.width.max --format=csv
  grep -E 'MemTotal|MemAvailable|SwapTotal|SwapFree' /proc/meminfo; swapon --show
  echo "# dd shard 1, 8 GiB, iflag=direct"; dd if=$M/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf of=/dev/null bs=16M count=512 iflag=direct 2>&1 | tail -1
  echo "# engine sha256 (must match Rushuna)"; sha256sum $W/U/src/terminal/engine/strata $W/H/src/engine/strata $W/B/src/engine/strata $W/H/src/engine/libstrata_kq.so $W/B/src/engine/libstrata_kq.so
} > $O/machine-state-2026-11-20.txt 2>&1
log "shard re-hash"
( cd $M && sha256sum Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-0000*-of-00002.gguf ) > $O/model-sha256.txt
grep -q '^4c1eb2ceb4915e1192f4f386021897bde56a97f40a0bb78bb86465e0f7d2aca3 ' $O/model-sha256.txt && \
grep -q '^316b46f3a2dbd68c900f43136ab9449f9dcc3725dfd8c794847c204bc161e113 ' $O/model-sha256.txt || { log "STOP: shard hash mismatch"; exit 1; }
log "shards match the lock"
$H/run_arm.sh U $W/U/src/terminal $W/U/src/terminal/strata-iq3_s.json $O/U $M 1 >> $O/run-U.out 2>&1; log "U rc=$?"; free20
SB_PRESTART=1 $H/run_arm.sh H $W/H/src $W/H/src/strata-iq3_s.json $O/H $M 1 >> $O/run-H.out 2>&1; log "H rc=$?"; free20
SB_PRESTART=1 $H/run_arm.sh B $W/B/src $W/B/src/strata-iq3_s.json $O/B $M 1 >> $O/run-B.out 2>&1; log "B rc=$?"; free20
log "CHAIN T END"
