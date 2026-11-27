#!/bin/bash
# Lock A1 optional arm T-2133 (step 3): U-8k short and U-32k short at DDR4-2133. Same arm() and the same U commands as
# run_a1.sh; only the cells change (short:512:3, A1.3 T-2133 step 3). Each arm starts a fresh server with its own cold request.
set -u; . "$(dirname "$0")/env.sh"
preread() { cat "$1" > /dev/null; }
busy() { nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -q . || pgrep -x llama-server >/dev/null; }
arm() {
  local name=$1 tag=$2 cells=$3 bd=$4 mod=$5; shift 5
  local opts=(); while [ "$1" != "--" ]; do opts+=("$1"); shift; done; shift
  while busy; do echo "$(date +%T) I11.4: card or llama-server busy, waiting"; sleep 60; done
  preread $mod
  LD_LIBRARY_PATH=$bd:$LD_LIBRARY_PATH $H/run_arm.sh $name --tag $tag --cells $cells "${opts[@]}" -- $bd/llama-server -m $mod $COMMON "$@"
}
for a in ${@:-T2133-U-8k T2133-U-32k}; do case $a in
  T2133-U-8k)  arm $a inkling short:512:3 $UB $M -- -cmoe -c 8192 ;;
  T2133-U-32k) arm $a inkling short:512:3 $UB $M -- -cmoe -c 32768 ;;
  *) echo "unknown arm $a"; exit 1 ;;
esac; done
