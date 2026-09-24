#!/bin/bash
# Step 5: heterogeneous case. qwen3.6:27b present on Miu only. Same 20 concurrent requests through PAIR.
# One direct rep first as a reference, then one PAIR rep with attribution capture.
set -u
cd ~/pair-bench
MODEL=qwen3.6:27b
N=${N:-20}
DIRECT=http://127.0.0.1:11434
PAIR=http://127.0.0.1:11435
OUT=${OUT:-~/pair-bench/results-step5.jsonl}
LOGDIR=~/pair-bench/pairlogs; mkdir -p $LOGDIR

capture_loop() { : > "$1"; while [ -f /tmp/pair-cap-run ]; do tmux capture-pane -t pair -p >> "$1"; sleep 1; done; }

echo "step5 start $(date '+%H:%M:%S')"
echo "== inventory via PAIR (who advertises $MODEL)"
curl -s -m 10 $PAIR/api/tags | python3 -c "import json,sys; print(sorted(m['name'] for m in json.load(sys.stdin)['models']))"
echo "== rushuna local tags"
curl -s -m 10 http://192.168.x.x:11434/api/tags | python3 -c "import json,sys; print(sorted(m['name'] for m in json.load(sys.stdin)['models']))"
echo "== warm $MODEL on Miu direct"
curl -s -m 600 $DIRECT/api/generate -d "{\"model\":\"$MODEL\",\"prompt\":\"hi\",\"stream\":false,\"options\":{\"num_predict\":4},\"keep_alive\":\"30m\"}" | python3 -c "import json,sys; d=json.load(sys.stdin); print('load_s',round(d['load_duration']/1e9,1))"
nvidia-smi --query-gpu=memory.used --format=csv,noheader

echo "--- direct rep 1 $(date '+%H:%M:%S')"
python3 bench.py --base $DIRECT --label direct-27b --rep 1 --model $MODEL --n $N --out $OUT
sleep 5
echo "--- pair rep 1 $(date '+%H:%M:%S')"
START=$(date '+%H:%M:%S')
touch /tmp/pair-cap-run; capture_loop $LOGDIR/step5-${TAG:-pair}.raw & CAP=$!
python3 bench.py --base $PAIR --label pair-27b --rep 1 --model $MODEL --n $N --out $OUT
sleep 3; rm -f /tmp/pair-cap-run; wait $CAP
grep -h "proxy request complete" $LOGDIR/step5-${TAG:-pair}.raw | sort -u | awk -v s="$START" '$1 >= s' > $LOGDIR/step5-${TAG:-pair}.complete
echo "attribution (start $START): $(wc -l < $LOGDIR/step5-${TAG:-pair}.complete) complete lines"
grep -o "node_id=[0-9a-f-]*" $LOGDIR/step5-${TAG:-pair}.complete | sort | uniq -c | sed 's/a9489f3b-3ae8-4183-8d06-dc901eadc0ea/Miu/; s/70506f7d-649d-4600-b0af-2fa46de57b6c/rushuna/'
grep -o "status=[0-9]*" $LOGDIR/step5-${TAG:-pair}.complete | sort | uniq -c
echo "== resolveCandidates lines during rep (eligibility)"
grep -h "resolveCandidates" $LOGDIR/step5-${TAG:-pair}.raw | sort -u | awk -v s="$START" '$1 >= s' | tail -3
echo "step5 end $(date '+%H:%M:%S')"
