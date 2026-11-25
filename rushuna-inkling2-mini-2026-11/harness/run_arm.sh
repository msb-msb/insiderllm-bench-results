#!/bin/bash
# One arm under the memory guard: run_arm.sh ARM [bench_inkling.py args ...]
set -u; . "$(dirname "$0")/env.sh"
ARM=$1; shift
mkdir -p $REC/arms; cd $REC/arms
python3 $H/bench_inkling.py $ARM "$@" &
BP=$!
python3 $H/memwatch.py $REC/arms $BP --count-swap &
MP=$!
wait $BP; rc=$?
sleep 3; kill $MP 2>/dev/null; wait $MP 2>/dev/null
[ -f $REC/arms/TRIPPED ] && { echo "TRIPPED: $(cat $REC/arms/TRIPPED)"; exit 9; }
exit $rc
