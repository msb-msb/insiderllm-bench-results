#!/bin/bash
# v0.4.0 re-run of the section-7 runtime-LoRA-scale checks (for the upstream issue).
# Three server launches, twelve 47-item scoring runs. Every launch line, every
# /lora-adapters call and its reply, and every scorer summary go to logs/v040_repro.log.
# Server stdout/stderr per launch: logs/v040_server_<name>.log. Results: scored_v040/.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"
B=${LLAMA_SERVER:-/home/minotaur/llama-v0.4.0/build/bin/llama-server}
MODEL=/media/minotaur/Storage_Disk_1/LLM_repo/qwen3.6-27b-gguf/Qwen_Qwen3.6-27B-Q4_K_M.gguf
A1=$HERE/adapters/seed1-f16.gguf; A2=$HERE/adapters/seed2-f16.gguf
COMMON="-ngl 99 -fa on -c 4096 --jinja --no-mmap --port 8081"   # section-7 flags, unchanged
URL=http://127.0.0.1:8081
LOG=logs/v040_repro.log
OUT=${OUTDIR:-scored_v040}
PID=

log() { echo "$(date -Is) $*" | tee -a "$LOG"; }
launch() {   # launch NAME extra-args...
    local name=$1; shift
    log "LAUNCH $name: $B -m $MODEL $COMMON $*"
    "$B" -m "$MODEL" $COMMON "$@" > "logs/v040_server_$name.log" 2>&1 &
    PID=$!
    for i in $(seq 1 240); do
        sleep 2.5
        if curl -sf "$URL/health" >/dev/null 2>&1; then log "READY $name after ~$((i*5/2))s pid=$PID"; return 0; fi
        kill -0 $PID 2>/dev/null || { log "DIED $name — see logs/v040_server_$name.log"; return 1; }
    done
    log "TIMEOUT waiting for $name"; return 1
}
stop() { log "STOP pid=$PID"; kill $PID 2>/dev/null; wait $PID 2>/dev/null; PID=; sleep 3; }
adapters() { log "GET /lora-adapters -> $(curl -s $URL/lora-adapters)"; }
run() { log "RUN $*"; python3 repro_v040_score.py --outdir "$OUT" "$@" 2>&1 | tee -a "$LOG"; }
trap 'if [ -n "$PID" ]; then kill $PID 2>/dev/null; fi' EXIT

log "==== v0.4.0 repro start; $("$B" --version 2>&1 | head -1)"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader | tee -a "$LOG"

# --- Server N: no adapters. The v0.4.0 baseline and its noise floor. ---
launch noadapter || exit 1
run baseline_rep0 --note "no adapters loaded"
run baseline_rep1 --note "no adapters loaded, repeat"
stop

# --- Server L: both adapters via --lora, --lora-init-without-apply. ---
launch initwithoutapply --lora "$A1,$A2" --lora-init-without-apply || exit 1
adapters
run L_nofield        --note "lora field omitted; --lora-init-without-apply should mean scale 0 for both"
run L_alloff  --id -1 --note "lora: [] — every adapter explicitly off"
run L_id0     --id 0  --note "lora: [{id:0, scale:1.0}] — seed 1 active"
run L_id1     --id 1  --note "lora: [{id:1, scale:1.0}] — seed 2 active"
log "POST /lora-adapters [{id:0,scale:0},{id:1,scale:0}] -> $(curl -s -X POST $URL/lora-adapters -H 'Content-Type: application/json' -d '[{"id":0,"scale":0.0},{"id":1,"scale":0.0}]')"
adapters
run L_zeroed_rep0                        --note "runtime scales 0 via POST /lora-adapters; lora field omitted; cache_prompt server default"
run L_zeroed_rep1                        --note "same, repeat"
run L_zeroed_nocache_rep0 --cache-prompt false --note "runtime scales 0; cache_prompt:false to rule out KV reuse (#26207)"
run L_zeroed_nocache_rep1 --cache-prompt false --note "same, repeat"
stop

# --- Server S: both adapters at launch scale 0.0 via --lora-scaled. ---
launch scaled0 --lora-scaled "$A1:0.0,$A2:0.0" || exit 1
adapters
run S_scaled0_rep0 --note "--lora-scaled FILE:0.0 at launch; lora field omitted"
run S_scaled0_rep1 --note "same, repeat"
stop

log "==== compare against baseline_rep0"
python3 compare_preds.py "$OUT"/baseline_rep0.json "$OUT"/baseline_rep1.json \
    "$OUT"/L_nofield.json "$OUT"/L_alloff.json "$OUT"/L_id0.json "$OUT"/L_id1.json \
    "$OUT"/L_zeroed_rep0.json "$OUT"/L_zeroed_rep1.json \
    "$OUT"/L_zeroed_nocache_rep0.json "$OUT"/L_zeroed_nocache_rep1.json \
    "$OUT"/S_scaled0_rep0.json "$OUT"/S_scaled0_rep1.json | tee -a "$LOG"
log "==== zeroed rep0 vs rep1 (stability)"
python3 compare_preds.py "$OUT"/L_zeroed_rep0.json "$OUT"/L_zeroed_rep1.json | tee -a "$LOG"
python3 compare_preds.py "$OUT"/L_zeroed_nocache_rep0.json "$OUT"/L_zeroed_nocache_rep1.json | tee -a "$LOG"
log "==== done"
