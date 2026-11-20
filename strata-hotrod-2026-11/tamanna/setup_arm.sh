#!/bin/bash
# Strata HotRod lock (c06003fc) H2/H3 on Tamanna: one setup pass per arm, network on (packages, pack, MTP, predictor).
# No compile here: the engine is the Rushuna build (same sha256), copied into the tree; setup must say "engine already built".
set -u
A=$1; W=$HOME/hotrod-2026-11
R=$W/$A/src; [ "$A" = U ] && R=$R/terminal
export XDG_CONFIG_HOME=$W/$A/xdg STRATA_NVCC=$HOME/cuda-13.0/bin/nvcc PATH=$HOME/cuda-13.0/bin:$PATH
FLAGS="--model IQ3_S --gguf-dir $HOME/bench-models/qwen3.8-flash-next-iq3s --context 131072 --vision no --build --no-start --yes --no-browser --data-dir $W/$A/data"
LOG=$W/$A/setup-tamanna.log; cd $R
echo "$(date -u +%FT%T) $R/.venv/bin/python setup.py $FLAGS" | tee $LOG
$R/.venv/bin/python setup.py $FLAGS >> $LOG 2>&1; rc=$?
echo "$(date -u +%FT%T) rc=$rc" | tee -a $LOG; exit $rc
