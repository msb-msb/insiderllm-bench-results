#!/bin/bash
set -euo pipefail
cd ~
echo "start $(date -Is)"
git clone --depth 1 --branch prism-b10709-9a9394a https://github.com/PrismML-Eng/llama.cpp ~/llama-prismml
cd ~/llama-prismml
git log -1 --format="%H %d %s"
git describe --tags --always
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=86 -DGGML_NATIVE=OFF -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF \
  -DCMAKE_C_COMPILER=gcc-13 -DCMAKE_CXX_COMPILER=g++-13 -DCMAKE_CUDA_HOST_COMPILER=g++-13
cmake --build build --config Release -j 16
echo "build done $(date -Is)"
