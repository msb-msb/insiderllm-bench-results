#!/bin/bash
# Drive one model through -np 1, 4, 8, 16 with -c scaled so every slot gets 4k of context.
# Server is the v0.4.0 pin. Each level: start server, wait for /health, record VRAM after load,
# run the client (1 warm-up + 3 measured rounds), stop server. A level that fails to load is
# recorded as a result and stops that model, per the brief.
set -u
MODEL_PATH="$1"; TAG="$2"; OUT="$3"
BIN=/home/minotaur/llama-v0.4.0/build/bin
mkdir -p "$OUT"
for NP in 1 4 8 16; do
  CTX=$(( NP * 4096 ))
  LOG="$OUT/server-$TAG-np$NP.log"
  echo "=== $TAG  -np $NP  -c $CTX"
  echo "launch $(date -Is): llama-server -m $MODEL_PATH -ngl 99 -fa on --jinja -np $NP -c $CTX" > "$LOG"
  LD_LIBRARY_PATH=$BIN nohup $BIN/llama-server -m "$MODEL_PATH" -ngl 99 -fa on --jinja \
      -np $NP -c $CTX --host 127.0.0.1 --port 8081 >> "$LOG" 2>&1 &
  PID=$!
  UP=0
  for i in $(seq 1 180); do
    if ! kill -0 $PID 2>/dev/null; then break; fi
    if curl -s -m 2 http://127.0.0.1:8081/health 2>/dev/null | grep -q '"ok"'; then UP=1; break; fi
    sleep 2
  done
  if [ "$UP" != "1" ]; then
    echo "  DID NOT LOAD — recording and stopping this model here"
    ERR=$(grep -iE "out of memory|cudaMalloc|failed to|error|ggml_backend" "$LOG" | tail -4 | tr '\n' ' | ')
    python3 - "$OUT/$TAG-np$NP.json" "$NP" "$CTX" "$ERR" <<'PY'
import json,sys,subprocess
q="memory.used,memory.total"
r=subprocess.run(["nvidia-smi",f"--query-gpu={q}","--format=csv,noheader,nounits"],capture_output=True,text=True).stdout.strip()
json.dump({"tag":sys.argv[1],"n":int(sys.argv[2]),"ctx":int(sys.argv[3]),"loaded":False,
           "error":sys.argv[4],"vram_at_failure":r},open(sys.argv[1],"w"),indent=1)
PY
    kill $PID 2>/dev/null; wait $PID 2>/dev/null
    echo "STOPPED_AT=$NP"
    break
  fi
  sleep 3
  VRAM=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  echo "  loaded, VRAM after load: ${VRAM} MiB"
  python3 ~/concurrency_client.py --n $NP --tag "$TAG-np$NP" --out "$OUT/$TAG-np$NP.json"
  python3 - "$OUT/$TAG-np$NP.json" "$VRAM" "$CTX" <<'PY'
import json,sys
p=sys.argv[1]; d=json.load(open(p)); d["loaded"]=True
d["vram_after_load_mib"]=int(sys.argv[2]); d["ctx"]=int(sys.argv[3]); d["ctx_per_slot"]=d["ctx"]//d["n"]
json.dump(d,open(p,"w"),indent=1)
PY
  kill $PID 2>/dev/null; wait $PID 2>/dev/null   # exact PID, never pkill -f: invariant (y)
  sleep 4
done
echo "done $TAG"
