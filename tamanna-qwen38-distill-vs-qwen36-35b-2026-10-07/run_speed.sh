#!/bin/bash
# Launch the speed half with the memory watchdog (memwatch.py --count-swap, the v3 rule Mark set 2026-10-05:
# only MemAvailable < 2 GiB stops a run; swap is counted per phase and published). Run from the record dir on Tamanna.
set -u
cd "$(dirname "$0")"
./conditions.sh conditions.txt "speed start"
nohup python3 speed_cmp.py > speed/harness.out 2>&1 < /dev/null &
HP=$!
echo "$HP" > speed/harness.pid
nohup python3 memwatch.py speed "$HP" --count-swap > speed/memwatch.out 2>&1 < /dev/null &
echo "harness $HP watchdog $!"
