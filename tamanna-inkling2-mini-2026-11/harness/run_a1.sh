#!/bin/bash
# Lock A1.3 arms on Tamanna, in order: U (8K, 32K, 256K), L (same), S10d (8K, 16K). Same arm() / sarm() as run_llama.sh /
# run_strata.sh; the f16 fallback now matches only an error-level refusal line (fixes Rushuna deviation 2).
set -u; . "$(dirname "$0")/env.sh"
preread() { cat "$1" > /dev/null; }
busy() { nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -q . || pgrep -x llama-server >/dev/null; }
arm() {
  local name=$1 tag=$2 cells=$3 bd=$4 mod=$5; shift 5
  local opts=(); while [ "$1" != "--" ]; do opts+=("$1"); shift; done; shift
  while busy; do echo "$(date +%T) I11.4: card or llama-server busy, waiting"; sleep 60; done
  preread $mod
  LD_LIBRARY_PATH=$bd:$LD_LIBRARY_PATH $H/run_arm.sh $name --tag $tag --cells $cells "${opts[@]}" -- $bd/llama-server -m $mod $COMMON "$@"
  local rc=$?
  if [ $rc -eq 2 ] && grep -E "^[0-9.]+ E " $REC/arms/server-$name.log | grep -qiE "quantized V cache|V cache quantization|requires flash.?attn"; then
    echo "$(date +%T) $name refused q8_0 KV; re-run with f16 (I5)"
    LD_LIBRARY_PATH=$bd:$LD_LIBRARY_PATH $H/run_arm.sh $name-f16kv --tag $tag --cells $cells "${opts[@]}" -- $bd/llama-server -m $mod ${COMMON/-ctk q8_0 -ctv q8_0/-ctk f16 -ctv f16} "$@"
  fi
}
SH=$W/strata/home; ST="env HOME=$SH $SH/.local/bin/strata"
BASE="launch --model-path $SQ10 --model sq-10 --family inkling-2-mini --vision off --parallel 1 --tune skip --access local --port 8090 --no-api-key --no-tui --yes --restart"
sarm() {
  local name=$1 cells=$2; shift 2
  local opts=(); while [ "$1" != "--" ]; do opts+=("$1"); shift; done; shift
  while busy; do echo "$(date +%T) I11.4: card busy, waiting"; sleep 60; done
  MEMWATCH_EXTRA_NAMES=strata-inkling $H/run_arm.sh $name --tag inkling --cells $cells --kind strata --port 8090 \
     --engine-name strata-inkling --stop-cmd "$ST launch --stop" "${opts[@]}" -- $ST $BASE "$@"
  local rc=$?
  cp $SH/.local/state/strata/launch/*.engine.log $REC/arms/ 2>/dev/null
  for f in $SH/.local/state/strata/launch/*.json; do cp $f $REC/arms/$name-$(basename $f); done
  return $rc
}
c8=short:512:3,deep:7372:3; c32=short:512:3,deep:29491:3; c256=short:512:3,deep:235929:1
ALL="U-8k U-32k U-256k L-8k L-32k L-256k S10d-8k S10d-16k"
for a in ${@:-$ALL}; do case $a in
  U-8k)   arm $a inkling $c8   $UB $M -- -cmoe -c 8192 ;;
  U-32k)  arm $a inkling $c32  $UB $M -- -cmoe -c 32768 ;;
  U-256k) arm $a inkling $c256 $UB $M -- -cmoe -c 262144 ;;
  L-8k)   arm $a inkling $c8   $LB $M -- -cmoe -c 8192 ;;
  L-32k)  arm $a inkling $c32  $LB $M -- -cmoe -c 32768 ;;
  L-256k) arm $a inkling $c256 $LB $M -- -cmoe -c 262144 ;;
  S10d-8k)  sarm $a short:512:3,deep:7372:3  -- --context 8k ;;
  S10d-16k) sarm $a short:512:3,deep:14746:3 -- --context 16k ;;
  *) echo "unknown arm $a"; exit 1 ;;
esac; done
