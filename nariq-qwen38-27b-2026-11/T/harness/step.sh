#!/bin/bash
# Tamanna: run one section T step detached from ssh.   step.sh NAME CMD...   -> ~/nariq-t/logs/NAME.{out,rc}
export A1_SHA=0f4e9b497e3cfd8b14d039dbbb86c2e71f9498e33d0b9d867f4201b1523a5372
n=$1; shift; mkdir -p ~/nariq-t/logs; rm -f ~/nariq-t/logs/$n.rc
"$@" > ~/nariq-t/logs/$n.out 2>&1
echo $? > ~/nariq-t/logs/$n.rc
