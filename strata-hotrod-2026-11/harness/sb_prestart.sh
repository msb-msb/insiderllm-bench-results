#!/bin/bash
# Deviation (2026-11-19, recorded in the record's README): H's and B's tools/strata_bench.py (v0.1.45 lineage) crash with
# "NameError: name 'port' is not defined" when they must start the server themselves. The tool uses a Strata server
# already answering at the config's address, so this starts the arm's own server.py from its config (the launch U's
# tool did itself), waits for /health, runs the tool with the same options as U, then stops the server.
#   sb_prestart.sh ROOT CFG OUTDIR [prefix...]
set -u
ROOT=$1; CFG=$2; OUTD=$3; shift 3
PORT=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('port',8080))" "$CFG")
"$@" "$ROOT/.venv/bin/python" "$ROOT/serve/server.py" --engine strata --config "$CFG" --port "$PORT" > "$OUTD.server.log" 2>&1 &
S=$!
for i in $(seq 1 1800); do b=$(curl -sf "http://127.0.0.1:$PORT/health") && ! echo "$b" | grep -qi loading && break; kill -0 $S 2>/dev/null || { echo "server died"; exit 1; }; sleep 1; done
echo "server ready after ${i}s on $PORT"
"$@" "$ROOT/.venv/bin/python" "$ROOT/tools/strata_bench.py" --config "$CFG" --out "$OUTD"; rc=$?
kill $S; for i in $(seq 1 60); do kill -0 $S 2>/dev/null || break; sleep 1; done; kill -9 $S 2>/dev/null
pkill -f "^$ROOT/engine/[s]trata " 2>/dev/null; sleep 3
exit $rc
