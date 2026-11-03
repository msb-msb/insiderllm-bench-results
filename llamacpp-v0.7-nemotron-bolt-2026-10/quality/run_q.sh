#!/bin/bash
# Arm Q driver, run from Miu (2026-11-03). For each TAG/MODEL: start `harness.py serve` on Tamanna (v0.7.0 llama-server,
# the prereg's Q command + --host 0.0.0.0, under the sampler and the esp32 guard), wait for its ready file, run the
# unchanged run_quality.py (2 passes) against it, then SIGTERM the serve process. Order: Q1 Bolt, then Q0 control.
# The base URL takes Tamanna's LAN address from ~/.ssh/config at run time; it is not written into this record.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
IP=$(ssh -G tamanna | awk '$1=="hostname"{print $2}')
for pair in "bolt-24gb:bolt" "qwen3.6-35b-a3b-q4km-v070:q0"; do
  TAG=${pair%%:*}; MODEL=${pair##*:}
  echo "$(date +%T) Q start $TAG"
  # `&` must cover only the nohup: on 11-03 a `cd && ... & ` chain kept ssh attached and put the subshell's pid in the file.
  ssh tamanna "cd ~/llamacpp-v0.7-nemotron-bolt-2026-10 || exit 1; rm -f serve-$TAG.ready; nohup python3 harness.py serve $TAG $MODEL > serve-$TAG.out 2>&1 < /dev/null & echo \$! > serve-$TAG.pid"
  until ssh tamanna "test -f ~/llamacpp-v0.7-nemotron-bolt-2026-10/serve-$TAG.ready"; do
    ssh tamanna "kill -0 \$(cat ~/llamacpp-v0.7-nemotron-bolt-2026-10/serve-$TAG.pid)" || { echo "serve $TAG died before ready"; exit 1; }
    sleep 5
  done
  python3 "$HERE/run_quality.py" "$TAG" --base "http://$IP:8081" --passes 2 | tee -a "$HERE/run_q.log"
  ssh tamanna "kill -TERM \$(cat ~/llamacpp-v0.7-nemotron-bolt-2026-10/serve-$TAG.pid)"
  while ssh tamanna "kill -0 \$(cat ~/llamacpp-v0.7-nemotron-bolt-2026-10/serve-$TAG.pid) 2>/dev/null"; do sleep 2; done
  echo "$(date +%T) Q done $TAG"
done
