#!/bin/bash
# Step 4: 20 concurrent requests, 3 reps each, alternating direct (Miu Ollama) vs PAIR proxy.
# Captures the Miu TUI Logs tab during each PAIR rep so per-request node attribution survives.
set -u
cd ~/pair-bench
MODEL=${MODEL:-qwen3.5:9b}
N=${N:-20}
DIRECT=http://127.0.0.1:11434
PAIR=http://127.0.0.1:11435
OUT=${OUT:-~/pair-bench/results-step4.jsonl}
LOGDIR=${LOGDIR:-~/pair-bench/pairlogs}; mkdir -p $LOGDIR

capture_loop() { # $1 = outfile
  : > "$1"
  while [ -f /tmp/pair-cap-run ]; do tmux capture-pane -t pair -p >> "$1"; sleep 1; done
}

warm() {
  curl -s -m 300 $DIRECT/api/generate -d "{\"model\":\"$MODEL\",\"prompt\":\"hi\",\"stream\":false,\"options\":{\"num_predict\":4},\"keep_alive\":\"30m\"}" >/dev/null
  ssh -o BatchMode=yes minotaur@192.168.x.x "curl -s -m 300 http://127.0.0.1:11434/api/generate -d '{\"model\":\"$MODEL\",\"prompt\":\"hi\",\"stream\":false,\"options\":{\"num_predict\":4},\"keep_alive\":\"30m\"}' >/dev/null"
}

echo "step4 start $(date '+%H:%M:%S')  model=$MODEL n=$N"
warm
for rep in 1 2 3; do
  echo "--- direct rep $rep $(date '+%H:%M:%S')"
  python3 bench.py --base $DIRECT --label direct --rep $rep --model $MODEL --n $N --out $OUT
  sleep 5
  echo "--- pair rep $rep $(date '+%H:%M:%S')"
  START=$(date '+%H:%M:%S')
  touch /tmp/pair-cap-run
  capture_loop $LOGDIR/pair-rep$rep.raw &
  CAP=$!
  python3 bench.py --base $PAIR --label pair --rep $rep --model $MODEL --n $N --out $OUT
  sleep 3
  rm -f /tmp/pair-cap-run; wait $CAP
  # dedupe captured screen lines, keep request-complete lines at/after rep start
  grep -h "proxy request complete" $LOGDIR/pair-rep$rep.raw | sort -u | awk -v s="$START" '$1 >= s' > $LOGDIR/pair-rep$rep.complete
  echo "attribution rep $rep (start $START): $(wc -l < $LOGDIR/pair-rep$rep.complete) complete lines"
  grep -o "node_id=[0-9a-f-]*" $LOGDIR/pair-rep$rep.complete | sort | uniq -c | sed 's/a9489f3b-3ae8-4183-8d06-dc901eadc0ea/Miu/; s/70506f7d-649d-4600-b0af-2fa46de57b6c/rushuna/'
  sleep 5
done
echo "step4 end $(date '+%H:%M:%S')"
