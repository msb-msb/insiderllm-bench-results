# b10088 vs v0.4.0 on the two canonical 3090 rows — gate (b) for the 2026-09-08 marker

Miu, RTX 3090, 2026-09-07 13:30:52 to 13:36:07 PDT. Results record; facts as measured.

## Design

| | |
|---|---|
| Question | Does moving the dataset pin from llama.cpp b10088 (`67b9b0e`, 2026-07-22) to v0.4.0 (`5266f24da75dc449bd56cbed7addb9c8e4a6a73e`, 2026-09-04) change the two published 3090 rows? |
| Harness | `llama-bench -ngl 99 -fa 1 -p 512 -n 128 -d 0,4096,8192 -r 5` — byte-identical to the published rows and the 08-28 A-B-B-A |
| Models | Ornith-1.5-35B-A3B Q4_K_M (bartowski, sha256 `12d8d5c0…2614a`) and Qwen3.6-35B-A3B UD-Q4_K_M (Unsloth, `ac0e2c11…31a61`), both re-verified against the upstream digests on the NVMe before the run |
| Reps | 3 per model per build, builds alternating within each rep, starting build flipped on rep 2: b10088→v0.4.0, v0.4.0→b10088, b10088→v0.4.0 |
| Pre-registered | \|delta\| < 3% is "no change"; ≥ 3% either way is a stated build effect and gets recorded in the pin note |
| Gate | Brave closed; `free -g` available 57 GB (threshold 40); card idle at 364 MiB before first load, 280 MiB after |
| Soak | paused 13:30:52, resumed 13:36:07, timer confirmed active |
| Not done | the 08-28 page-cache eviction bracket, which needs root. Both builds read the same warm cache; symmetric for a build delta |
| Concurrent | the 82 GB Qwen3.8-Flash-Next download was running on Storage_Disk_1 and the WiFi link throughout (hf Xet backend, ~6.5 MB/s) |
| Builds | b10088 `/home/minotaur/llama-bench-src/build/bin/llama-bench`; v0.4.0 `/home/minotaur/llama-v0.4.0/build/bin/llama-bench`, CUDA 12.8, sm_86, GGML_NATIVE=OFF |

## Result

Mean of 3 reps of llama-bench's own 5-repeat average; brackets are min..max over the 3 reps. Delta is v0.4.0 relative to b10088.

| model | metric | b10088 | v0.4.0 | delta | verdict |
|---|---|---:|---:|---:|---|
| Ornith 1.5-35B-A3B | tg128 d=0 | 167.68 [164.59..169.53] | 171.23 [169.42..172.44] | +2.11% | no change |
| | tg128 d=4096 | 165.44 [162.78..168.73] | 167.90 [162.85..170.72] | +1.49% | no change |
| | tg128 d=8192 | 163.71 [159.96..165.61] | 165.95 [163.29..167.35] | +1.37% | no change |
| | pp512 d=0 | 3,464.6 [3,348.6..3,531.7] | 3,543.6 [3,511.9..3,566.0] | +2.28% | no change |
| | pp512 d=4096 | 3,257.3 [3,206.5..3,320.2] | 3,333.9 [3,242.0..3,380.5] | +2.35% | no change |
| | pp512 d=8192 | 3,157.0 [3,094.5..3,197.4] | 3,219.8 [3,126.6..3,271.3] | +1.99% | no change |
| Qwen3.6-35B-A3B | tg128 d=0 | 156.54 [156.25..157.02] | 154.11 [145.82..158.55] | −1.55% | no change |
| | tg128 d=4096 | 155.77 [155.47..156.19] | 152.79 [144.79..156.86] | −1.91% | no change |
| | tg128 d=8192 | 152.52 [152.35..152.72] | 148.52 [142.15..154.15] | −2.62% | no change |
| | pp512 d=0 | 3,618.6 [3,606.6..3,639.7] | 3,638.2 [3,572.3..3,675.0] | +0.54% | no change |
| | pp512 d=4096 | 3,440.2 [3,434.5..3,445.6] | 3,432.6 [3,287.9..3,516.4] | −0.22% | no change |
| | pp512 d=8192 | 3,311.9 [3,304.1..3,316.1] | 3,210.7 [3,106.9..3,364.1] | **−3.05%** | **v0.4.0 SLOWER** (crosses the line) |

Eleven of twelve cells are inside the 3% band. The twelfth, Qwen pp512 at d=8192, crosses it by 0.05 points.

**What the twelfth cell rests on.** The v0.4.0 Qwen rep 2 run (13:33:32) was low on every metric at once: tg 145.82 / 144.79 / 142.15 against 158.55 / 156.73 / 149.26 and 157.96 / 156.86 / 154.15 in reps 1 and 3, and pp 3,572 / 3,288 / 3,107 against 3,675 / 3,516 / 3,161 and 3,667 / 3,494 / 3,364. Every Qwen v0.4.0 spread in the table is that one run. Without rep 2 the d=8192 pp delta is +0.05% and the three Qwen tg deltas are −0.0%, −0.0% and −0.5%. b10088's Qwen spreads are 0.4 to 0.8 tok/s and 6 to 33 tok/s on pp; v0.4.0's are 12.7 tok/s and 257 tok/s on the same cells. The per-run 5-repeat stddev inside that rep is in `raw-v0.4.0-qwen3.6-35b-a3b-rep2.json`.

Per the pre-registration the cell is recorded as it landed. It is one rep wide and a re-run of that cell would settle it in under two minutes.

## Block 2 — Qwen replication, 2026-09-07 18:16:30 to 18:19:04 (`block2/`)

Same harness, Qwen only, both builds, 3 reps, order b10088→v0.4.0, v0.4.0→b10088, b10088→v0.4.0. Soak paused 18:16:07. Card idle 302 MiB before, 280 MiB after.

| metric | block 1 b10088 | block 1 v0.4.0 | Δ1 | block 2 b10088 | block 2 v0.4.0 | Δ2 | pooled b10088 (n=6) | pooled v0.4.0 (n=6) | Δ pooled |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tg128 d=0 | 156.54 | 154.11 | −1.55% | 154.80 | 158.51 | +2.40% | 155.67 | 156.31 | +0.41% |
| tg128 d=4096 | 155.77 | 152.79 | −1.91% | 153.46 | 156.76 | +2.15% | 154.62 | 154.78 | +0.10% |
| tg128 d=8192 | 152.52 | 148.52 | −2.62% | 150.12 | 153.99 | +2.58% | 151.32 | 151.25 | −0.04% |
| pp512 d=0 | 3,618.6 | 3,638.2 | +0.54% | 3,535.8 | 3,684.3 | +4.20% | 3,577.2 | 3,661.3 | +2.35% |
| pp512 d=4096 | 3,440.2 | 3,432.6 | −0.22% | 3,401.2 | 3,520.0 | +3.49% | 3,420.7 | 3,476.3 | +1.63% |
| pp512 d=8192 | 3,311.9 | 3,210.7 | −3.05% | 3,275.8 | 3,376.6 | +3.08% | 3,293.8 | 3,293.7 | −0.00% |

Block 2 crossed the 3% line on all three prefill cells in v0.4.0's favour, the mirror of block 1's single crossing against it. In block 2 the low run was b10088 rep 1 (3,490 / 3,348 / 3,195, the first run of the block); in block 1 it was v0.4.0 rep 2. Pooled over six reps per build, no cell exceeds 2.4% and the d=8192 prefill crossings cancel to −0.00%. Read as: **no build effect on the Qwen row at the 3% line**; single-block prefill deltas of ±3–4% are within what one wobbly rep produces on this harness. Ornith (block 1 only) was +1.4 to +2.4% in v0.4.0's favour on every cell.

## Against the 28 August published figures (b10088 both times)

| model | metric | 08-28 (root, cache evicted, nothing else running) | today b10088 | drift |
|---|---|---:|---:|---:|
| Ornith | tg128 d=0 | 172.44 | 167.68 | −2.8% |
| Ornith | pp512 d=0 | 3,602.9 | 3,464.6 | −3.8% |
| Qwen | tg128 d=0 | 158.18 | 156.54 | −1.0% |
| Qwen | pp512 d=0 | 3,694.2 | 3,618.6 | −2.0% |

Today's absolute numbers are a few percent under the published rows for both models on the same build. The environment differs: no root bracket, the download's disk and CPU activity, and Ornith's first slot ran seconds after its 21.9 GB copy back to the NVMe. The build delta was measured with both builds under the same conditions, which is what the gate asks.

## Files

| path | content |
|---|---|
| `build_ab.py` | the runner, harness string and order |
| `run.log` | timestamps, soak pause/resume, per-run lines, summary |
| `results.json`, `summary.json` | all 12 runs; the 12-cell table with spreads and verdicts |
| `raw-<build>-<model>-rep<n>.json` | llama-bench JSON output and stderr tail per run |
