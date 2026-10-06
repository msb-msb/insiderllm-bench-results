#!/bin/bash
# The pre-registered sequence, unattended: prep, stage, S1, S2-2048/4096/8192, S0, L1, L2, L3.
# Each step runs under memwatch.py --count-swap (only MemAvailable < 2 GiB stops it); a trip ends the sequence.
set -u
cd "$(dirname "$0")"
SC=$HOME/strata/strata-coder-iq1_m.json
mkcfg() {  # arm, then python edits to the args list
python3 - "$SC" "$1" "$2" <<'P'
import json, sys
src, arm, edit = sys.argv[1:]
c = json.load(open(src)); a = c["args"]
def setv(flag, val):
    i = a.index(flag); a[i + 1] = val
if edit.startswith("prefill="): setv("--prefill", edit.split("=")[1])
elif edit.startswith("spec="): setv("--spec", edit.split("=")[1])
c["log"] = f"{c['cwd']}/strata-coder-iq1_m-{arm}.log"
json.dump(c, open(f"cfg-{arm}.json", "w"), indent=1)
print(arm, " ".join(a))
P
}
step() {  # name, then bench_coder.py args
  name=$1; shift
  echo "$(date -u +%T) === $name: $*" >> sequence.log
  python3 bench_coder.py "$@" > "out-$name.txt" 2>&1 &
  P=$!
  python3 memwatch.py . "$P" --count-swap > /dev/null 2>&1 &
  W=$!
  wait "$P"; rc=$?
  wait "$W"
  mv memwatch.log "memwatch-$name.log"; mv memwatch-summary.json "memwatch-summary-$name.json" 2>/dev/null
  echo "$(date -u +%T) === $name rc=$rc" >> sequence.log
  if [ -e TRIPPED ]; then mv TRIPPED "TRIPPED-$name"; echo "STOP: floor tripped in $name" >> sequence.log; exit 1; fi
  return $rc
}
step prep prep || exit 1
step stage stage || exit 1
N=$(python3 -c "import json;print(json.load(open('stage.json'))['lowest_ncmoe_that_serves_32512_with_ub4096'])")
[ "$N" = "None" ] && { echo "STOP: no -ncmoe served 32,512 at ub 4096" >> sequence.log; exit 1; }
mkcfg S1 none >> sequence.log
mkcfg S2-2048 prefill=2048 >> sequence.log
mkcfg S2-4096 prefill=4096 >> sequence.log
mkcfg S2-8192 prefill=8192 >> sequence.log
mkcfg S0 spec=0 >> sequence.log
for arm in S1 S2-2048 S2-4096 S2-8192 S0; do
  step "$arm" strata "$arm" "$PWD/cfg-$arm.json" || echo "$(date -u +%T) $arm failed, recorded, continuing" >> sequence.log
  cp "$HOME/strata/strata-coder-iq1_m-$arm.log" "engine-$arm.log" 2>/dev/null
done
for arm in L1 L2 L3; do
  step "$arm" llama "$arm" "$N" || echo "$(date -u +%T) $arm failed, recorded, continuing" >> sequence.log
done
echo "$(date -u +%T) === ALL DONE" >> sequence.log
