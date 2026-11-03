#!/bin/bash
# Stock-card GEMM check with 0.5 s nvidia-smi telemetry (2026-11-03).
cd ~/llamacpp-v0.7-nemotron-bolt-2026-10 || exit 1
nvidia-smi --query-gpu=timestamp,temperature.gpu,clocks.sm,clocks.mem,power.draw,utilization.gpu,memory.used,pstate,clocks_event_reasons.active \
  --format=csv,noheader,nounits -lms 500 > telemetry-gemm.csv &
S=$!
sleep 1
~/voice-01/envs/train/bin/python gemm_check.py gemm-check.json 2>&1 | tee gemm-check.txt
sleep 1
kill -INT $S; wait $S
awk -F', ' '$6>50{n++; p+=$5; if($5>m)m=$5} END{printf "under load: n=%d mean %.1f W max %.1f W\n", n, p/n, m}' telemetry-gemm.csv | tee -a gemm-check.txt
echo "sm MHz / mem MHz / pstate / reasons under load (count):" | tee -a gemm-check.txt
awk -F', ' '$6>50{print $3, $4, $8, $9}' telemetry-gemm.csv | sort | uniq -c | sort -rn | head -6 | tee -a gemm-check.txt
