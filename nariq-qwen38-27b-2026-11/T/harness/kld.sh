#!/bin/bash
# Section T quality (lock A1, T4) on Tamanna.   kld.sh OUT STEP
#   STEP = ngl-search | base NGL | arms
# Every llama-perplexity call: -c 4096 -b 2048 -ub 512 --chunks 32 -fa on -t 8 --fit off
#   --override-kv tokenizer.ggml.add_bos_token=bool:false   (BOS pinned, Mark's N5 gate decision)
set -u
OUT=$1; STEP=$2; H=$(cd "$(dirname "$0")" && pwd); W=$HOME/nariq-t
export LD_LIBRARY_PATH=$W/cuda-libs
mkdir -p "$OUT"; cd "$OUT"
REF=$W/ref/Qwen3.8-27B-BF16-00001-of-00002.gguf; KLD=$W/ref.kld; SET=$W/evalset/evalset.txt
COMMON=(-f "$SET" -c 4096 -b 2048 -ub 512 -fa on -t 8 --fit off --override-kv tokenizer.ggml.add_bos_token=bool:false)
seq() { echo "$(date -u +%FT%T) $*" | tee -a sequence.log; }
swapout() { awk '/^pswpout/ {print $2}' /proc/vmstat; }
pre() { used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
  [ "$used" -gt 50 ] && { seq "STOP: card not empty ($used MiB) before $1"; exit 1; }
  [ "$(ollama ps 2>/dev/null | tail -n +2 | grep -c .)" -gt 0 ] && { seq "STOP: ollama has a model loaded before $1"; exit 1; }; }
run() {  # name, binary, then args; memwatch v3 (--count-swap) around it; swap-out delta recorded
  n=$1; b=$2; shift 2; pre "$n"; s0=$(swapout); seq "=== $n: $b $*"
  "$HOME/nariq-2026-11/$b/build/bin/llama-perplexity" "$@" > log-$n.txt 2>&1 & P=$!
  python3 "$H/memwatch.py" . "$P" --count-swap > /dev/null 2>&1 & G=$!
  wait "$P"; rc=$?; wait "$G"; mv memwatch.log memwatch-$n.log; mv memwatch-summary.json memwatch-summary-$n.json 2>/dev/null
  s1=$(swapout); so=$(( (s1 - s0) * 4 ))
  ov=$(grep -c "Using metadata override.*add_bos_token" log-$n.txt)
  seq "=== $n rc=$rc swap-out ${so} KiB override-lines $ov"
  [ -e TRIPPED ] && { mv TRIPPED TRIPPED-$n; seq "STOP: memory floor tripped in $n"; exit 1; }
  return $rc
}
case $STEP in
  ngl-search)   # largest -ngl that loads and finishes one chunk at -c 4096 (recorded; not a measurement)
    lo=8; hi=40
    while [ $lo -lt $hi ]; do m=$(( (lo + hi + 1) / 2 ))
      if run ngl-$m mainline -m "$REF" "${COMMON[@]}" --chunks 1 -ngl $m; then lo=$m; else hi=$((m - 1)); fi; done
    seq "NGL=$lo" ;;
  base)
    NGL=$3
    run base mainline -m "$REF" "${COMMON[@]}" --chunks 32 -ngl "$NGL" --kl-divergence-base "$KLD"
    seq "base file $(stat -c %s "$KLD") bytes" ;;
  arms)
    for a in "Q-M-IQ3 mainline Qwen3.8-27B-UD-IQ3_XXS.gguf" "Q-F-IQ3 fork Qwen3.8-27B-UD-IQ3_XXS.gguf" \
             "Q-F-N3 fork Qwen3.8-27B-NariQ-3.0bpw.gguf" "Q-F-N25 fork Qwen3.8-27B-NariQ-2.5bpw.gguf" \
             "Q-R-Q4 mainline Qwen3.8-27B-UD-Q4_K_XL.gguf"; do
      set -- $a
      run "$1" "$2" -m "$W/model/$3" "${COMMON[@]}" --chunks 32 -ngl 99 --kl-divergence-base "$KLD" --kl-divergence \
        || seq "arm $1 FAILED (reported)"
    done ;;
esac
seq "=== $STEP DONE (lock A1 sha256 ${A1_SHA:-unset})"
