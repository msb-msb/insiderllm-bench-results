#!/bin/bash
# Strata HotRod lock (c06003fc) H4/H8, Rushuna, after one arm's measurements: record what setup produced, then free the
# NVMe for the next arm by deleting ONLY this arm's own pack and MTP layer (H4: arm packs may be deleted between arms).
#   after_arm.sh ARM      (W=~/hotrod-2026-11; record into W/rec/rushuna/ARM/install/)
set -eu
A=$1; W=$HOME/hotrod-2026-11
R=$W/$A/src; [ "$A" = U ] && R=$R/terminal
O=$W/rec/rushuna/$A/install; mkdir -p "$O"
grep -qE "ARM $A DONE|STOP: memory floor" "$W/rec/rushuna/$A/sequence-$A.log"   # only after the arm finished or was ended (H5)
cp -p "$W/$A"/setup-pass-*.log "$O/"
cp -p "$R"/strata-*.json "$O/" 2>/dev/null || true
cp -p "$R"/run-*.sh "$O/" 2>/dev/null || true
cp -p "$R"/engine/BUILD.json "$O/" 2>/dev/null || true
{ echo "# commit"; git -C "$W/$A/src" rev-parse HEAD; git -C "$W/$A/src" status --short | head -20
  echo "# engine"; sha256sum "$R"/engine/strata "$R"/build/strata 2>/dev/null
  echo "# llama.cpp zip"; cat "$W/fetch/llama.cpp.sha256" 2>/dev/null
  echo "# data files (predictor, profiles, env) under the tree"; find "$R/data" -maxdepth 1 -type f -newer "$W/setup_arm.sh" -exec sha256sum {} + 2>/dev/null
  echo "# pack + MTP (deleted after this listing)"
  find "$W/$A/data" -type f ! -name '*.lock' -exec sha256sum {} + ; } > "$O/hashes-$A.txt"
cp -p "$W/fetch/pip-freeze-$A"*.txt "$O/" 2>/dev/null || true
du -sh "$W/$A/data" >> "$O/hashes-$A.txt"
rm -rf "$W/$A/data/packs" "$W/$A/data/mtp"
echo "$(date -u +%FT%T) $A: recorded, pack + MTP deleted; NVMe $(df -h / | awk 'NR==2{print $4}') free" | tee -a "$W/rec/rushuna/between-arms.log"
