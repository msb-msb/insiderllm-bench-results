#!/bin/bash
# Lock I6.4: GPU configurations against the CPU references (ref-inkling already run: 5.8308)
set -u; . "$(dirname "$0")/env.sh"
G="-ngl 99 -cmoe -ctk q8_0 -ctv q8_0 -fa auto"
$H/gate.sh gpu-L        $LB $M $G
$H/gate.sh gpu-U        $UB $M $G
$H/gate.sh gpu-U-ub2048 $UB $M $G -ub 2048 -b 2048
$H/gate.sh ref-qwen     $LB $Q
$H/gate.sh gpu-Q        $LB $Q $G
echo GATES_DONE
