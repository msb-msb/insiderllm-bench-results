#!/bin/bash
# Lock A1.5: CPU reference re-run on Tamanna, then the two llama.cpp configurations (Rushuna CPU reference 5.8308)
set -u; . "$(dirname "$0")/env.sh"
G="-ngl 99 -cmoe -ctk q8_0 -ctv q8_0 -fa auto"
$H/gate.sh ref-inkling $LB $M
$H/gate.sh gpu-U       $UB $M $G
$H/gate.sh gpu-L       $LB $M $G
echo GATES_DONE
