#!/bin/bash
cd ~/llama-v0.4.0; export LD_LIBRARY_PATH=$PWD
T=~/bench-models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf
D="-md $HOME/bench-models/Qwen3.6-35B-A3B-DFlash-Q8_0.gguf -ngld 99 --spec-type draft-dflash --spec-draft-n-max 15"
for cfg in "ncmoe24-ub256|-ncmoe 24 -ub 256" "ncmoe26|-ncmoe 26" "ncmoe28|-ncmoe 28"; do
  name=${cfg%%|*}; f=${cfg#*|}
  L=~/rushuna-dflash-ncmoe24-2026-09-28/fitcheck/server-dflash-$name.log
  ./llama-server -m $T -ngl 99 $f -fa on -c 8192 -np 1 --host 127.0.0.1 --port 8080 $D > $L 2>&1 & P=$!
  ok=0; for i in $(seq 1 240); do kill -0 $P 2>/dev/null || break; curl -s 127.0.0.1:8080/health | grep -q ok && { ok=1; break; }; sleep 0.5; done
  if [ $ok = 1 ]; then
    v1=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
    r=$(curl -s 127.0.0.1:8080/completion -d '{"prompt":"Hello","n_predict":16,"temperature":0}' | python3 -c "import json,sys; t=json.load(sys.stdin)['timings']; print(t['predicted_n'], t.get('draft_n'), t.get('draft_n_accepted'))")
    v2=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
    echo "dflash $name: LOADED vram_after_load=${v1}MiB after_request=${v2}MiB pred/draft/acc=$r"
  else echo "dflash $name: FAILED"; grep -E "cudaMalloc|failed to allocate" $L | head -2; fi
  kill -INT $P 2>/dev/null; wait $P 2>/dev/null; sleep 2
done
