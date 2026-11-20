#!/bin/bash
W=$HOME/hotrod-2026-11
$W/harness/after_arm.sh H || { echo "after H failed"; exit 1; }
$W/setup_arm.sh B a; echo "B pass a rc=$?"
$W/setup_arm.sh B b || { echo "B pass b failed"; exit 1; }
[ -x $W/B/src/engine/strata ] || { echo "B engine missing"; exit 1; }
grep -q "rc=0" $W/B/setup-pass-b.log || exit 1
SB_PRESTART=1 $W/harness/run_arm.sh B $W/B/src $W/B/src/strata-iq3_s.json $W/rec/rushuna/B $W/model/IQ3_S
echo "CHAIN B END rc=$?"
