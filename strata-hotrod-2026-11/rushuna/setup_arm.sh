#!/bin/bash
# Strata HotRod lock (c06003fc) H2/H3: one arm`s setup, same flags in every arm.
#   setup_arm.sh ARM a   -> inside `unshare -Un` (no network): steps up to the compile, pack and low-RAM copy
#   setup_arm.sh ARM b   -> network on: whatever pass a could not fetch (MTP layer, predictor); engine already built
# Isolation from older installs: own XDG_CONFIG_HOME (Strata`s settings.json), own --data-dir, and no strata* folder
# one or two levels above the install (setup scans those and moves model files from them).
set -u
A=$1; PASS=$2; W=$HOME/hotrod-2026-11
R=$W/$A/src; [ "$A" = U ] && R=$R/terminal
export XDG_CONFIG_HOME=$W/$A/xdg STRATA_NVCC=$HOME/cuda-13.0/bin/nvcc PATH=$HOME/cuda-13.0/bin:$PATH
FLAGS="--model IQ3_S --gguf-dir $W/model/IQ3_S --context 131072 --vision no --build --no-start --yes --no-browser --data-dir $W/$A/data"
LOG=$W/$A/setup-pass-$PASS.log
cd $R
echo "$(date -u +%FT%T) pass $PASS: $R/.venv/bin/python setup.py $FLAGS" | tee $LOG
if [ "$PASS" = a ]; then unshare -Un $R/.venv/bin/python setup.py $FLAGS >> $LOG 2>&1
else $R/.venv/bin/python setup.py $FLAGS >> $LOG 2>&1; fi
rc=$?; echo "$(date -u +%FT%T) rc=$rc" | tee -a $LOG; exit $rc
