#!/bin/bash
cd ~/pair-bench
until grep -q "step4 end" step4-phase2.log 2>/dev/null; do sleep 10; done
echo "=== step 3 finished, starting mycoSwarm at $(date +%H:%M:%S)"
# warm both engines the way step 3 did (Rushuna's mycoSwarm uses its system Ollama on 11434)
curl -s -m 300 http://127.0.0.1:11434/api/generate -d '{"model":"qwen3.5:9b","prompt":"hi","stream":false,"options":{"num_predict":4},"keep_alive":"30m"}' >/dev/null
curl -s -m 300 http://192.168.x.x:11434/api/generate -d '{"model":"qwen3.5:9b","prompt":"hi","stream":false,"options":{"num_predict":4},"keep_alive":"30m"}' >/dev/null
echo "--- myco smoke $(date +%H:%M:%S)"
python3 bench_myco.py --rep 0 --n 1 --out /dev/null 2>&1 | tail -3
for rep in 1 2 3; do
  echo "--- myco rep $rep $(date +%H:%M:%S)"
  python3 bench_myco.py --rep $rep --n 20 --out ~/pair-bench/results-myco.jsonl 2>&1
  sleep 5
done
echo "=== step 5 with N=8 at $(date +%H:%M:%S)"
N=8 TAG=n8 OUT=~/pair-bench/results-step5-n8.jsonl ./run_step5.sh 2>&1
echo "=== phase2 rest done $(date +%H:%M:%S)"
