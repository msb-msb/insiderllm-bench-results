#!/bin/bash
W=$HOME/hotrod-2026-11
$W/harness/after_arm.sh B || { echo "after B failed"; exit 1; }
mv $W/U/setup-pass-a.log $W/U/setup-pass-a-first.log; mv $W/U/setup-pass-b.log $W/U/setup-pass-b-first.log
$W/setup_arm.sh U a; echo "U pass a rc=$?"
$W/setup_arm.sh U b || { echo "U pass b failed"; exit 1; }
cmp <(python3 -c "import json;print(json.load(open(\"$W/U/src/terminal/strata-iq3_s.json\"))[\"args\"])") <(python3 -c "import json;print(json.load(open(\"$W/rec/rushuna/U/install/strata-iq3_s.json\"))[\"args\"])") && echo "U config args identical to the scored run"
$W/harness/rerun_cell.sh U $W/U/src/terminal $W/U/src/terminal/strata-iq3_s.json $W/rec/rushuna/U $W/model/IQ3_S 32512
echo "CHAIN U32 END"
