#!/bin/bash
# after arm $1 finishes: record + free (after_arm.sh), then next arm $2 setup pass a (offline), then pass b (network)
W=$HOME/hotrod-2026-11; P=$1; N=$2
until grep -qE "ARM $P DONE|STOP" $W/rec/rushuna/$P/sequence-$P.log; do sleep 30; done
grep -q "ARM $P DONE" $W/rec/rushuna/$P/sequence-$P.log || { echo "arm $P stopped"; exit 1; }
$W/harness/after_arm.sh $P || exit 1
$W/setup_arm.sh $N a || { echo "pass a failed"; exit 1; }
$W/setup_arm.sh $N b || { echo "pass b failed"; exit 1; }
echo "CHAIN $P->$N DONE"
