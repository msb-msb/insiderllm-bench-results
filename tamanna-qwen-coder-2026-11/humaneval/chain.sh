#!/bin/bash
# 2026-11-17 chain (Miu): Coder-30B re-runs -> 27B anchor copies + hash -> HumanEval (he_run.py). Stops on any mismatch.
set -u
H=/home/minotaur/tamanna-qwen-coder-he-2026-11; SEQ=$H/sequence.log; T=192.168.x.x
R=/media/minotaur/Storage_Disk_1/LLM_repo
SH=/tmp/claude-1000/-home-minotaur-Desktop-InsiderLLM/d8115928-6b30-4dda-88b1-dba277ea913b/scratchpad/he
say(){ echo "$(date +%T) $*" | tee -a "$SEQ"; }
tseq(){ ssh -o BatchMode=yes $T "cat ~/tamanna-qwen-coder-2026-11/sequence.log"; }
say "=== chain start"
until tseq | grep -q "RERUNS DONE\|STOP"; do sleep 20; done
tseq | grep -q "STOP" && { say "STOP: Tamanna L1 re-run stopped"; exit 1; }
say "L1 re-runs done; starting L2-16K re-run"
ssh -o BatchMode=yes $T "cd ~/tamanna-qwen-coder-2026-11 && ./rerun_coder30b_L2.sh > rerun-L2.out 2>&1"
tseq | grep -q "RERUN L2 DONE" || { say "STOP: L2 re-run did not finish"; exit 1; }
say "L2 re-run done"
until [ "$(wc -l < $SH/store-hash.txt 2>/dev/null || echo 0)" -ge 2 ]; do sleep 20; done
for f in Qwen3.6-27B-UD-Q4_K_XL.gguf Qwen3.8-27B-UD-Q4_K_XL.gguf; do
  want=$(grep " $f\$" $SH/SHA256SUMS.anchors | cut -d' ' -f1); got=$(grep "/$f\$" $SH/store-hash.txt | cut -d' ' -f1)
  [ "$want" = "$got" ] || { say "STOP: LLM_repo $f hashes $got, want $want"; exit 1; }
done
say "LLM_repo anchors verified against upstream"
free=$(ssh -o BatchMode=yes $T "df --output=avail -B1 ~ | tail -1")
need=$((17612564704 + 17923394624 + 20*1024*1024*1024))
[ "$free" -gt "$need" ] || { say "STOP: Tamanna free $free < copy + 20 GiB ($need)"; exit 1; }
say "Tamanna free $(($free/1024/1024/1024)) GiB; copying"
scp -q $SH/SHA256SUMS.anchors $T:bench-models/qwen-coder/SHA256SUMS.anchors
rsync -a $R/from-miu/Desktop/lucebox-hub/dflash/models/unsloth/Qwen3.6-27B-UD-Q4_K_XL.gguf $R/qwen3.8-27b-gguf/Qwen3.8-27B-UD-Q4_K_XL.gguf $T:bench-models/qwen-coder/ \
  || { say "STOP: rsync failed"; exit 1; }
ssh -o BatchMode=yes $T "cd ~/bench-models/qwen-coder && sha256sum -c SHA256SUMS.anchors" > $H/anchors-arrival.txt 2>&1 \
  || { say "STOP: anchor sha256 mismatch on Tamanna: $(cat $H/anchors-arrival.txt)"; exit 1; }
say "anchors on Tamanna, sha256 OK: $(tr '\n' ' ' < $H/anchors-arrival.txt); df $(ssh -o BatchMode=yes $T 'df -h ~ | tail -1')"
cd $H && python3 he_run.py > he_run.out 2>&1
say "=== chain done (he_run rc=$?)"
