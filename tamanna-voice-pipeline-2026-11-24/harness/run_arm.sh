#!/bin/bash
# One arm of the voice-pipeline run, driven from Miu (pre-registration section 3; A1-A4).
# Order of the four arms, fixed before the first warm-up: S1, S2, S3, R0 (run_arm.sh is called once per arm).
#   1. Miu-Tamanna clock offset (median of 5 ssh round trips), for matching server logs to clips.
#   2. serve.py up ARM on Tamanna: servers, warm-ups, -ncmoe fit, Open WebUI config, 300 s idle, A1 check.
#      ABORT_A1 or NOFIT stops the arm here and is recorded.
#   3. client.py: one discarded warm-up pass over all 25 clips, then measured passes 1, 2, 3, same clip order.
#   4. serve.py down ARM; Tamanna's arm folder is copied next to the client logs.
# A1 item 1: an interrupted arm is voided (its folder renamed <ARM>.void-1) and re-run once from step 1.
set -uo pipefail
ARM=$1
DIR=${2:-$1}        # exploratory pass (A4 item 4): run_arm.sh ARM X-ARM tools=off
SOPT="${3:-}"
H=/home/minotaur/Desktop/InsiderLLM/docs/bench-results/tamanna-voice-pipeline-2026-11-24/harness
C=~/voice-pipeline-client/run-2026-11-24
OUT=$C/$DIR
mkdir -p "$OUT"
py=~/voice-pipeline-client/.venv/bin/python
$py - "$OUT/clock.json" <<'PY'
import json, subprocess, sys, time, statistics
s = []
for _ in range(5):
    a = time.time(); t = float(subprocess.run(["ssh", "tamanna", "python3 -c 'import time;print(time.time())'"], capture_output=True, text=True).stdout); b = time.time()
    s.append((t - (a + b) / 2, b - a))
json.dump({"tamanna_minus_miu_s": statistics.median(x for x, _ in s), "samples": s}, open(sys.argv[1], "w"), indent=1)
print("clock offset", statistics.median(x for x, _ in s))
PY
echo "== $(date -Is) serve up $ARM"
READY=$(ssh tamanna "cd ~/voice-pipeline && python3 harness/serve.py up $ARM ${2:+dir=$DIR} $SOPT" 2>&1 | tee "$OUT/serve-up.out" | tail -1)
echo "$READY"
case "$READY" in READY*) ;; *) echo "arm $ARM did not reach READY"; ssh tamanna "cd ~/voice-pipeline && python3 harness/serve.py down $ARM ${2:+dir=$DIR}"; exit 2;; esac
for P in warmup 1 2 3; do
  echo "== $(date -Is) $ARM pass $P"
  $py $H/client.py $ARM $P $C/clips/clips.tsv $C/clips "$OUT" --tamanna-dir $DIR || { echo "client exited non-zero in pass $P"; exit 3; }
done
echo "== $(date -Is) serve down $ARM"
ssh tamanna "cd ~/voice-pipeline && python3 harness/serve.py down $ARM ${2:+dir=$DIR}"
rsync -a tamanna:voice-pipeline/run-2026-11-24/$DIR/ "$OUT/"
echo "== $(date -Is) done $ARM"
