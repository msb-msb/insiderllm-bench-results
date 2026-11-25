#!/bin/bash
# Lock I5 llama.cpp arms in order. run_llama.sh [ARM ...]  (default: all, in lock order)
set -u; . "$(dirname "$0")/env.sh"
preread() { cat "$1" > /dev/null; }
busy() { nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -q . || pgrep -x llama-server >/dev/null; }
arm() {  # arm NAME TAG CELLS BIN MODEL [--temp X] [--ballast N] -- placement/extra flags
  local name=$1 tag=$2 cells=$3 bd=$4 mod=$5; shift 5
  local opts=(); while [ "$1" != "--" ]; do opts+=("$1"); shift; done; shift
  while busy; do echo "$(date +%T) I11.4: card or llama-server busy, waiting"; sleep 60; done
  preread $mod
  LD_LIBRARY_PATH=$bd:$LD_LIBRARY_PATH $H/run_arm.sh $name --tag $tag --cells $cells "${opts[@]}" -- $bd/llama-server -m $mod $COMMON "$@"
  local rc=$?
  # I5: q8_0 V refused -> one re-run with f16 KV, labelled
  if [ $rc -eq 2 ] && grep -qiE "quantized V cache|V cache quantization|requires flash.?attn" $REC/arms/server-$name.log; then
    echo "$(date +%T) $name refused q8_0 KV; re-run with f16 (I5)"
    LD_LIBRARY_PATH=$bd:$LD_LIBRARY_PATH $H/run_arm.sh $name-f16kv --tag $tag --cells $cells "${opts[@]}" -- $bd/llama-server -m $mod ${COMMON/-ctk q8_0 -ctv q8_0/-ctk f16 -ctv f16} "$@"
  fi
}
c8=short:512:3,deep:7372:3; c32=short:512:3,deep:29491:3; c64=short:512:3,deep:58982:3; c256=short:512:3,deep:235929:1
ALL="L-8k L-32k L-64k L-256k L-d-8k L-d-greedy L4g U-8k U-32k U-64k U-256k U-ub2048 U-d-8k U-d-greedy U4g Q-cmoe-8k Q-cmoe-32k Q-cmoe-256k Q-best-8k"
for a in ${@:-$ALL}; do case $a in
  L-8k)   arm $a inkling $c8   $LB $M -- -cmoe -c 8192 ;;
  L-32k)  arm $a inkling $c32  $LB $M -- -cmoe -c 32768 ;;
  L-64k)  arm $a inkling $c64  $LB $M -- -cmoe -c 65536 ;;
  L-256k) arm $a inkling $c256 $LB $M -- -cmoe -c 262144 ;;
  L-d-8k) arm $a inkling $c8   $LB $M -- -cmoe -c 8192 -md $DS -ngld 99 --spec-type draft-dspark --spec-draft-n-max 3 ;;
  L-d-greedy) arm $a inkling short:512:3 $LB $M --temp 0 -- -cmoe -c 8192 -md $DS -ngld 99 --spec-type draft-dspark --spec-draft-n-max 3 ;;
  L4g)    arm $a inkling short:512:1,deep:58982:1 $LB $M --ballast 4096 -- -cmoe -c 65536 ;;
  U-8k)   arm $a inkling $c8   $UB $M -- -cmoe -c 8192 ;;
  U-32k)  arm $a inkling $c32  $UB $M -- -cmoe -c 32768 ;;
  U-64k)  arm $a inkling $c64  $UB $M -- -cmoe -c 65536 ;;
  U-256k) arm $a inkling $c256 $UB $M -- -cmoe -c 262144 ;;
  U-ub2048) arm $a inkling deep:29491:3 $UB $M -- -cmoe -c 32768 -ub 2048 -b 2048 ;;
  U-d-8k) arm $a inkling $c8   $UB $M -- -cmoe -c 8192 -md $DS -ngld 99 --spec-type draft-dspark --spec-draft-n-max 3 ;;
  U-d-greedy) arm $a inkling short:512:3 $UB $M --temp 0 -- -cmoe -c 8192 -md $DS -ngld 99 --spec-type draft-dspark --spec-draft-n-max 3 ;;
  U4g)    arm $a inkling short:512:1,deep:58982:1 $UB $M --ballast 4096 -- -cmoe -c 65536 ;;
  Q-cmoe-8k)   arm $a qwen $c8  $LB $Q -- -cmoe -c 8192 ;;
  Q-cmoe-32k)  arm $a qwen $c32 $LB $Q -- -cmoe -c 32768 ;;
  Q-cmoe-256k) arm $a qwen short:512:3 $LB $Q -- -cmoe -c 262144 ;;
  Q-best-8k)   arm $a qwen $c8  $LB $Q -- -ncmoe 24 -c 8192 ;;
  *) echo "unknown arm $a"; exit 1 ;;
esac; done
