#!/bin/bash
# Start one llama-server for a quality pass, with the same memory watchdog as the speed half (--count-swap).
# Usage: serve_watch.sh TAG MODEL_FILE CTX   (logs and watchdog files go to quality/TAG.*)
# Stop: kill $(cat quality/TAG.server.pid)  -- by PID, never pkill -f.
set -u
cd "$(dirname "$0")"
T="$1"; M="$2"; C="$3"
./conditions.sh conditions.txt "quality server $T (ctx $C)"
mkdir -p "quality/watch-$T"
nohup ./serve.sh "$M" "quality/server-$T.log" "$C" > /dev/null 2>&1 < /dev/null &
SP=$!
echo "$SP" > "quality/$T.server.pid"
nohup python3 memwatch.py "quality/watch-$T" "$SP" --count-swap > "quality/watch-$T/memwatch.out" 2>&1 < /dev/null &
echo "server $SP watchdog $!"
