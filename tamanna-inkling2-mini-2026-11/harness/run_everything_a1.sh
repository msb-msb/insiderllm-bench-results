#!/bin/bash
# Lock A1 order: machine state -> (bandwidth and gates run before, separately) -> U -> L -> S10d
set -u; . "$(dirname "$0")/env.sh"
$H/machine_state_a1.sh || exit 1
$H/run_a1.sh
echo ALL_DONE $(date -u +%FT%T)
