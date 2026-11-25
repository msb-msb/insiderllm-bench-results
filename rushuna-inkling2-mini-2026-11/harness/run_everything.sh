#!/bin/bash
# Lock I5 order: machine state -> llama.cpp arms -> Strata arms -> smoke
set -u; . "$(dirname "$0")/env.sh"
$H/machine_state.sh || exit 1
$H/run_llama.sh
$H/run_strata.sh
$H/run_smoke.sh
echo ALL_DONE $(date -u +%FT%T)
