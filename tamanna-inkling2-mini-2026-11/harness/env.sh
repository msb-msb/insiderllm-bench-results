# Inkling lock 35324447 + A1: paths on Tamanna (sourced by every script). A1.2: only paths change
W=$HOME/inkling2-2026-11
H=$W/harness
REC=$W/rec
LB=$W/build/llama.cpp/build/bin            # L: mainline 33aeb17f
UB=$W/uns/app                              # U: Unsloth b12675-mix-d14fe45 (cuda12-newer)
M=$W/model/Inkling-2-Mini-UD-Q4_K_M.gguf
DS=$W/model/dspark-Inkling-2-Mini-Q8_0.gguf
Q=$W/model/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf
SQ10=$W/model/Inkling-2-Mini-SQ-10.strata
export LD_LIBRARY_PATH=$W/cuda12-lib   # A1: libcudart/libcublas/libcublasLt 12.8 copied from Rushuna ~/cuda-12.8/lib64
# lock I5 common llama.cpp flags (L, U, Q); -c and placement per arm
COMMON="-ngl 99 -np 1 -ctk q8_0 -ctv q8_0 -fa auto -t 4 --cache-ram 0 --fit off -lm mmap --jinja --port 8081 -lv 4"   # -lv 4: logging only (I6.5 needs the load lines; the pin logs almost nothing by default)
