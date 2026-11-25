#!/bin/bash
# Lock I7 smoke test: L (gate passed), U, S10 at 8K, temperature 0. run_smoke.sh
set -u; . "$(dirname "$0")/env.sh"
O=$REC/smoke; mkdir -p $O
up() { for i in $(seq 1 600); do curl -sf localhost:$1/health >/dev/null && return 0; curl -sf localhost:$1/v1/models >/dev/null && return 0; sleep 2; done; return 1; }
for X in L U; do
  BD=$LB; [ $X = U ] && BD=$UB
  LD_LIBRARY_PATH=$BD:$LD_LIBRARY_PATH $BD/llama-server -m $M $COMMON -cmoe -c 8192 > $O/server-$X.log 2>&1 &
  up 8081 && python3 $H/smoke.py 8081 $O/smoke-$X.json | sed "s/^/$X: /" | tee -a $O/summary.txt
  pkill -x llama-server; sleep 5
done
SH=$W/strata/home
env HOME=$SH $SH/.local/bin/strata launch --model-path $SQ10 --model sq-10 --family inkling-2-mini --vision off --parallel 1 --tune skip --access local --port 8090 --no-api-key --no-tui --yes --restart --context 8k > $O/strata-launch.log 2>&1
up 8090 && python3 $H/smoke.py 8090 $O/smoke-S10.json | sed "s/^/S10: /" | tee -a $O/summary.txt
env HOME=$SH $SH/.local/bin/strata launch --stop; sleep 5; pkill -x strata-inkling
echo SMOKE_DONE
