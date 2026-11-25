#!/bin/bash
# Lock I6 void rule: re-run ONE void cell once with a fresh server, its own cold request, then the cell's requests,
# using the arm's exact recorded command. rerun_cell.sh ARM CELL     (result: results-ARM-rerun-CELL.json)
set -u; . "$(dirname "$0")/env.sh"
ARM=$1; CELL=$2; J=$REC/arms/results-$ARM.json
read -r TAG SPEC TEMP KIND BAL < <(python3 - "$J" "$CELL" <<'PY'
import json, sys
R = json.load(open(sys.argv[1])); c = R["cells"][sys.argv[2]]
print(R["tag"], f'{sys.argv[2]}:{c["prompt_target"]}:{len(c["reqs"])}', R["temp"], R["kind"], R["ballast_mib_target"])
PY
)
mapfile -t CMD < <(python3 -c "import json,sys; print('\n'.join(json.load(open(sys.argv[1]))['cmd']))" "$J")
BD=$(dirname "${CMD[0]}")
EXTRA=(); [ "$BAL" != "0" ] && EXTRA=(--ballast $BAL)
cat "$(printf '%s\n' "${CMD[@]}" | grep -A1 -x -- -m | tail -1)" > /dev/null   # page-cache pre-read (I5)
LD_LIBRARY_PATH=$BD:$LD_LIBRARY_PATH $H/run_arm.sh $ARM-rerun-$CELL --tag $TAG --cells $SPEC --temp $TEMP "${EXTRA[@]}" -- "${CMD[@]}"
