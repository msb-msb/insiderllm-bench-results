#!/bin/bash
# NariQ section T on Tamanna, driven from Miu (lock A1 0f4e9b49…3a5372, T9 phases). Stops at any failed gate.
#   orchestrate.sh [FROM_PHASE]   phases: speed bf16 rebase tokcheck arms fetch   (rebase = lock A2: re-run the BF16 base once)
set -u
A1=0f4e9b497e3cfd8b14d039dbbb86c2e71f9498e33d0b9d867f4201b1523a5372; A2=1f9ba443cf437168a55a7803502f8c5199c2ff1893e326e15b8340c451d21862
S=/media/minotaur/Storage_Disk_1/LLM_repo
REC=/home/minotaur/Desktop/InsiderLLM/docs/bench-results/nariq-qwen38-27b-2026-11/T
LOG=$HOME/nariq-t/orch.log
GIB=1073741824
FROM=${1:-speed}
log() { echo "$(date -Is) $*" | tee -a "$LOG"; }
die() { log "STOP: $*"; exit 1; }
declare -A HASH=(
  [Qwen3.8-27B-NariQ-3.0bpw.gguf]=1eaad934aa05579b8eba47ed9b26450392f9875fc2354efe8cfa8b29be8f4419
  [Qwen3.8-27B-NariQ-2.5bpw.gguf]=2445372e6de20620b940fbfab53aa718af9ba741f202da30cd2f02b5df78d05c
  [Qwen3.8-27B-UD-IQ3_XXS.gguf]=c0b7c3038681ed2e3040456c1dd45f9858b6c2290bed172c70388a94874f3eee
  [Qwen3.8-27B-UD-Q4_K_XL.gguf]=bee238bbeb3dc0a34bde4d0dedbaee1f98c009e8bb4226f03070054c12fb1372
  [Qwen3.8-27B-BF16-00001-of-00002.gguf]=b9966e82b7a4d87028b5eae061d578ee826305ebf8baea5bfc6e09bad0ba191f
  [Qwen3.8-27B-BF16-00002-of-00002.gguf]=92e3943c4f9bd6292a7bef82369f65fed9bfed088b9df0fb2fa2ce17c9edfa02 )
declare -A SRC=(
  [Qwen3.8-27B-NariQ-3.0bpw.gguf]=$S/qwen3.8-27b-nariq-gguf
  [Qwen3.8-27B-NariQ-2.5bpw.gguf]=$S/qwen3.8-27b-nariq-gguf
  [Qwen3.8-27B-UD-IQ3_XXS.gguf]=$S/qwen3.8-27b-gguf
  [Qwen3.8-27B-UD-Q4_K_XL.gguf]=$S/qwen3.8-27b-gguf
  [Qwen3.8-27B-BF16-00001-of-00002.gguf]=$S/qwen3.8-27b-gguf/BF16
  [Qwen3.8-27B-BF16-00002-of-00002.gguf]=$S/qwen3.8-27b-gguf/BF16 )
ARMS=(Qwen3.8-27B-UD-IQ3_XXS.gguf Qwen3.8-27B-NariQ-3.0bpw.gguf Qwen3.8-27B-NariQ-2.5bpw.gguf Qwen3.8-27B-UD-Q4_K_XL.gguf)
BF=(Qwen3.8-27B-BF16-00001-of-00002.gguf Qwen3.8-27B-BF16-00002-of-00002.gguf)

free_gib() { ssh tamanna "df -B1 --output=avail / | tail -1" | awk -v g=$GIB '{printf "%.2f", $1/g}'; }
store_hash() {  # files...: re-hash LLM_repo copies against A1 (T2)
  for f in "$@"; do h=$(sha256sum "${SRC[$f]}/$f" | cut -d' ' -f1)
    log "store $f $h"; [ "$h" = "${HASH[$f]}" ] || die "store hash mismatch $f"; done; }
copy_in() {  # dir files...: rsync to Tamanna, hash there
  d=$1; shift
  for f in "$@"; do rsync -a "${SRC[$f]}/$f" "tamanna:nariq-t/$d/" || die "rsync $f"
    h=$(ssh tamanna "sha256sum ~/nariq-t/$d/$f" | cut -d' ' -f1)
    log "tamanna $d/$f $h"; [ "$h" = "${HASH[$f]}" ] || die "tamanna hash mismatch $f"; done
  log "free after copy: $(free_gib) GiB"; }
rrun() {  # name cmd...: detached on Tamanna, poll until done
  n=$1; shift; log "remote $n: $*"
  ssh tamanna "setsid nohup ~/nariq-t/step.sh $n $* > /dev/null 2>&1 < /dev/null &"
  sleep 20; while ! ssh -o ConnectTimeout=20 tamanna "test -f ~/nariq-t/logs/$n.rc" 2>/dev/null; do sleep 60; done
  rc=$(ssh tamanna "cat ~/nariq-t/logs/$n.rc"); log "remote $n rc=$rc"; return "$rc"; }
seen=0; at() { [ "$1" = "$FROM" ] && seen=1; [ $seen = 1 ]; }

log "=== orchestrate start (from $FROM), A1 $A1, A2 $A2; Tamanna free $(free_gib) GiB"
rsync -a --delete "$REC/harness/" tamanna:nariq-t/harness/ && rsync -a ~/nariq-t/step.sh tamanna:nariq-t/ || die "harness copy"
ssh tamanna "mkdir -p ~/nariq-t/model ~/nariq-t/ref ~/nariq-t/out ~/nariq-t/logs"

if at speed; then
  log "--- phase speed (T5)"
  store_hash "${ARMS[@]}"; copy_in model "${ARMS[@]}"
  rrun speed bash /home/minotaur/nariq-t/harness/run_speed.sh /home/minotaur/nariq-t/out/speed || log "speed rc non-zero (see logs/speed.out; arms report their own failures)"
  ssh tamanna "grep -q 'ALL DONE' ~/nariq-t/out/speed/sequence.log" || die "speed run did not reach ALL DONE"
  rsync -a tamanna:nariq-t/out/speed/ "$REC/run-speed/"; rsync -a tamanna:nariq-t/logs/speed.out "$REC/run-speed/"
fi

if at bf16; then
  log "--- phase bf16 base run (T4)"
  ssh tamanna "rm -v ~/nariq-t/model/*.gguf" | tee -a "$LOG"   # our own working copies (T9), re-copied for the arms
  f=$(free_gib); log "free before BF16: $f GiB"
  awk -v f=$f 'BEGIN{exit !(f >= 50.90 + 30.30 + 20)}' || die "not enough room for BF16 + logits + floor ($f GiB)"
  store_hash "${BF[@]}"; copy_in ref "${BF[@]}"
  rrun ngl bash /home/minotaur/nariq-t/harness/kld.sh /home/minotaur/nariq-t/out/kld ngl-search || true
  NGL=$(ssh tamanna "grep -o 'NGL=[0-9]*' ~/nariq-t/out/kld/sequence.log | tail -1 | cut -d= -f2")
  [ -n "$NGL" ] || die "ngl-search gave no NGL"
  log "NGL=$NGL"
  rrun base bash /home/minotaur/nariq-t/harness/kld.sh /home/minotaur/nariq-t/out/kld base "$NGL"; rc=$?
  line=$(ssh tamanna "grep '=== base rc=' ~/nariq-t/out/kld/sequence.log | tail -1"); log "base: $line"
  echo "$line" | grep -q "rc=0 swap-out 0 KiB override-lines [1-9]" \
    || die "BF16 base run failed the A1 rule (rc/swap/override); Q8_0 fallback needs a manual step (store copy, download)"
  log "free after base: $(free_gib) GiB"
  ssh tamanna "head -c $((20 + 4 * 4096 * 32)) ~/nariq-t/ref.kld" > "$REC/rec/ref-head.kld"
  log "ref-head.kld $(sha256sum "$REC/rec/ref-head.kld" | cut -d' ' -f1)"
  # BF16 working copy goes once the LLM_repo copy re-hashes OK today (T9)
  store_hash "${BF[@]}"
  ssh tamanna "rm -v ~/nariq-t/ref/Qwen3.8-27B-BF16-0000*.gguf" | tee -a "$LOG"
  log "free after BF16 removal: $(free_gib) GiB"
fi

if at rebase; then
  log "--- phase rebase (lock A2 $A2): BF16 base re-run once, -v, -ngl 30"
  for f in "${BF[@]}"; do h=$(ssh tamanna "sha256sum ~/nariq-t/ref/$f" | cut -d' ' -f1)
    log "tamanna ref/$f $h"; [ "$h" = "${HASH[$f]}" ] || die "tamanna BF16 hash mismatch $f"; done
  ssh tamanna "rm -v ~/nariq-t/ref.kld" | tee -a "$LOG"; log "free before re-run: $(free_gib) GiB"
  rrun base bash /home/minotaur/nariq-t/harness/kld.sh /home/minotaur/nariq-t/out/kld base 30
  line=$(ssh tamanna "grep '=== base rc=' ~/nariq-t/out/kld/sequence.log | tail -1"); log "base (A2): $line"
  echo "$line" | grep -q "rc=0 swap-out [0-9]* KiB override-lines [1-9]" \
    || die "BF16 base re-run failed A2 (rc or override line); Q8_0 fallback needs a manual step"
  log "free after base: $(free_gib) GiB"
  ssh tamanna "head -c $((20 + 4 * 4096 * 32)) ~/nariq-t/ref.kld" > "$REC/rec/ref-head-A2.kld"
  log "ref-head-A2.kld $(sha256sum "$REC/rec/ref-head-A2.kld" | cut -d' ' -f1); identical to first run's: $(cmp -s "$REC/rec/ref-head.kld" "$REC/rec/ref-head-A2.kld" && echo yes || echo no)"
  store_hash "${BF[@]}"
  ssh tamanna "rm -v ~/nariq-t/ref/Qwen3.8-27B-BF16-0000*.gguf" | tee -a "$LOG"
  log "free after BF16 removal: $(free_gib) GiB"
fi

if at tokcheck; then
  log "--- phase tokcheck + bpb (T4)"
  store_hash "${ARMS[@]}"; copy_in model "${ARMS[@]}"
  rrun tokcheck python3 /home/minotaur/nariq-t/harness/tokcheck.py /home/minotaur/nariq-t/ref.kld /home/minotaur/nariq-t/evalset/evalset.txt \
    mainline:Qwen3.8-27B-UD-IQ3_XXS.gguf fork:Qwen3.8-27B-UD-IQ3_XXS.gguf fork:Qwen3.8-27B-NariQ-3.0bpw.gguf \
    fork:Qwen3.8-27B-NariQ-2.5bpw.gguf mainline:Qwen3.8-27B-UD-Q4_K_XL.gguf || log "tokcheck MISMATCH (reported; voids per A1)"
  mkdir -p "$REC/run-kld"; rsync -a tamanna:nariq-t/logs/tokcheck.out "$REC/run-kld/tokcheck.txt"; cat "$REC/run-kld/tokcheck.txt" >> "$LOG"
  PYTHONPATH=$HOME/nariq-t/llama.cpp/gguf-py python3 "$REC/harness/bpb.py" "$REC/rec/ref-head-A2.kld" "$REC/evalset/evalset.txt" \
    "$S/qwen3.8-27b-gguf/Qwen3.8-27B-UD-IQ3_XXS.gguf" "$REC/run-kld/bpb.json" >> "$LOG" 2>&1 || log "bpb check failed (bpb not reported, per A1)"
fi

if at arms; then
  log "--- phase KLD arms (T4)"
  rrun arms bash /home/minotaur/nariq-t/harness/kld.sh /home/minotaur/nariq-t/out/kld arms || log "arms rc non-zero"
fi

if at fetch; then
  log "--- fetch"
  rsync -a tamanna:nariq-t/out/kld/ "$REC/run-kld/" && rsync -a tamanna:nariq-t/logs/ "$REC/run-kld/remote-logs/"
  ssh tamanna "grep -q '=== arms DONE' ~/nariq-t/out/kld/sequence.log" && ssh tamanna "rm -v ~/nariq-t/ref.kld" | tee -a "$LOG"
  log "Tamanna free at end: $(free_gib) GiB; card $(ssh tamanna nvidia-smi --query-gpu=memory.used --format=csv,noheader)"
fi
log "=== orchestrate DONE"
