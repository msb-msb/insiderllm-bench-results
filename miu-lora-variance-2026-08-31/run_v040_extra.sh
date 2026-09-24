#!/bin/bash
# Extra control for the v0.4.0 repro: no-adapter baseline with cache_prompt:false,
# so the cache-off runtime-zeroed runs are compared against the same request path.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"
B=/home/minotaur/llama-v0.4.0/build/bin/llama-server
MODEL=/media/minotaur/Storage_Disk_1/LLM_repo/qwen3.6-27b-gguf/Qwen_Qwen3.6-27B-Q4_K_M.gguf
COMMON="-ngl 99 -fa on -c 4096 --jinja --no-mmap --port 8081"
URL=http://127.0.0.1:8081; LOG=logs/v040_repro.log; OUT=scored_v040; PID=
log() { echo "$(date -Is) $*" | tee -a "$LOG"; }
trap 'if [ -n "$PID" ]; then kill $PID 2>/dev/null; fi' EXIT
log "LAUNCH noadapter_nocache: $B -m $MODEL $COMMON"
"$B" -m "$MODEL" $COMMON > logs/v040_server_noadapter_nocache.log 2>&1 & PID=$!
for i in $(seq 1 240); do sleep 2.5; curl -sf $URL/health >/dev/null 2>&1 && { log "READY noadapter_nocache pid=$PID"; break; }; kill -0 $PID 2>/dev/null || { log "DIED"; exit 1; }; done
log "RUN baseline_nocache_rep0 --cache-prompt false"
python3 repro_v040_score.py --outdir $OUT baseline_nocache_rep0 --cache-prompt false --note "no adapters loaded; cache_prompt:false control" 2>&1 | tee -a "$LOG"
log "RUN baseline_nocache_rep1 --cache-prompt false"
python3 repro_v040_score.py --outdir $OUT baseline_nocache_rep1 --cache-prompt false --note "same, repeat" 2>&1 | tee -a "$LOG"
kill $PID; wait $PID 2>/dev/null; PID=
log "==== extra compare"
python3 compare_preds.py $OUT/baseline_rep0.json $OUT/baseline_nocache_rep0.json $OUT/baseline_nocache_rep1.json | tee -a "$LOG"
python3 compare_preds.py $OUT/baseline_nocache_rep0.json $OUT/baseline_nocache_rep1.json $OUT/L_zeroed_nocache_rep0.json $OUT/L_zeroed_nocache_rep1.json | tee -a "$LOG"
log "==== extra done"
