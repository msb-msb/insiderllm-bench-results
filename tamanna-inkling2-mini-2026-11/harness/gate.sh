#!/bin/bash
# Lock I6.4 correctness gate. gate.sh NAME BIN_DIR MODEL [extra flags...]   (NAME "ref-*" = CPU-only reference, f16 KV)
set -u; . "$(dirname "$0")/env.sh"
NAME=$1; BD=$2; MOD=$3; shift 3
O=$REC/gate; mkdir -p $O; WIKI=$W/wikitext-2-raw/wiki.test.raw
if [[ $NAME == ref-* ]]; then
  ( export CUDA_VISIBLE_DEVICES=""; LD_LIBRARY_PATH=$BD:$LD_LIBRARY_PATH $BD/llama-perplexity -m $MOD -f $WIKI -c 4096 --chunks 4 -t 4 "$@" ) > $O/$NAME.log 2>&1
else
  LD_LIBRARY_PATH=$BD:$LD_LIBRARY_PATH $BD/llama-perplexity -m $MOD -f $WIKI -c 4096 --chunks 4 -t 4 --fit off "$@" > $O/$NAME.log 2>&1
fi
rc=$?
ppl=$(grep -oE "Final estimate: PPL = [0-9.naif]+" $O/$NAME.log | awk '{print $NF}')
echo "$NAME rc=$rc ppl=${ppl:-none} flags: $*" | tee -a $O/gate-summary.txt
