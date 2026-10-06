#!/bin/bash
# Amendment 2: the S3 arm (no drafts), under memwatch.py --count-swap like every other arm.
set -u
cd "$(dirname "$0")"
echo "$(date -u +%T) === S3: strata S3 $PWD/cfg-S3.json" >> sequence.log
python3 bench_coder.py strata S3 "$PWD/cfg-S3.json" > out-S3.txt 2>&1 &
P=$!
python3 memwatch.py . "$P" --count-swap > /dev/null 2>&1 &
W=$!
wait "$P"; rc=$?
wait "$W"
mv memwatch.log memwatch-S3.log; mv memwatch-summary.json memwatch-summary-S3.json 2>/dev/null
cp "$HOME/strata/strata-coder-iq1_m-S3.log" engine-S3.log 2>/dev/null
echo "$(date -u +%T) === S3 rc=$rc" >> sequence.log
[ -e TRIPPED ] && { mv TRIPPED TRIPPED-S3; echo "STOP: floor tripped in S3" >> sequence.log; }
echo "$(date -u +%T) === S3 DONE" >> sequence.log
