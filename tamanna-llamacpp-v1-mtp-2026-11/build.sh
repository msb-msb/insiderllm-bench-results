#!/bin/bash
# Arms O/Z/V, lock a39c4818 M2/M3. Same recipe as build-llama-v0.7.0.sh. Attempt 2: full clone (attempt 1 used
# --depth 1, so CMake saw build number 1 and the UI-asset step fetched mismatched "latest" assets for b12199).
# Attempt 3: -DLLAMA_USE_PREBUILT_UI=OFF on all arms (no prebuilt UI bucket for b12352; the UI is not in the inference path).
set -euo pipefail
B=~/llamacpp-v1-mtp-2026-11
[ -d $B/llama.cpp.git ] || git clone -q --bare https://github.com/ggml-org/llama.cpp $B/llama.cpp.git
build() { local arm=$1 tag=$2 want=$3; local d=$B/llama-$arm
  echo "== $arm $tag start $(date -Is)"
  [ -d $d ] || git -C $B/llama.cpp.git worktree add -q --detach $d $tag
  local h=$(git -C $d rev-parse HEAD); echo "$arm HEAD $h  describe $(git -C $d describe --tags)  count $(git -C $d rev-list --count HEAD)"
  [ "$h" = "$want" ] || { echo "UNEXPECTED COMMIT $arm"; return 3; }
  cd $d
  cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=86 -DGGML_NATIVE=OFF -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF -DLLAMA_USE_PREBUILT_UI=OFF \
    -DCMAKE_C_COMPILER=gcc-13 -DCMAKE_CXX_COMPILER=g++-13 -DCMAKE_CUDA_HOST_COMPILER=g++-13 > $B/cmake-$arm.log 2>&1
  nice -n 10 cmake --build build --config Release -j 8 --target llama-server > $B/build-$arm.log 2>&1
  ./build/bin/llama-server --version 2>&1 | tail -2
  sha256sum build/bin/llama-server $(readlink -f build/bin/libggml-cuda.so)
  echo "== $arm done $(date -Is)"; }
build O b12199 372dc5ca157276beb6c67b2e92477e8d662e964a
build Z b12352 5676dfbe01e7ebe0387913680eee0ed39bf4a363
build V v1.0.0 b1b770d90d94cad9e9ea5b993bdbc383a522fb28
echo ALL_BUILT
