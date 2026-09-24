# Qwen3.8-Flash-Next UD-IQ3_XXS, -ncmoe sweep, stock llama.cpp v0.4.0 — Rushuna RTX 3060 12 GB, 32 GB RAM, 2026-09-08

Results record; facts as measured. Harness `ncmoe_sweep.py rushuna` (copy in this directory, identical to Miu's), run 13:38–14:08 PDT (log timestamps are UTC). Table from `../miu-flashnext-ncmoe-2026-09-08/summarize.py results.json`. No fork, no expert cache, no MTP.

## Design

| | |
|---|---|
| Pre-registered | same as Miu: decode scales roughly with the fraction of routed-expert layers resident in VRAM |
| Order | stock server first (3 reps, `iostat -dxt nvme0n1 1` in the background) because the page-cache question is the point of this rig; then `-ncmoe 48, 44, 41, 38` to OOM; then server at the best fit |
| Harness | `llama-bench -ngl 99 -ncmoe N -fa 1 -p 0 -n 128 -d 0,4096 -r 3 -t 4 -lm mmap -o json`, 3 invocations per setting |
| Server | `llama-server -ngl 99 -ncmoe N -fa on -c 4096 -t 4 --load-mode mmap`, 2,343-token prompt, n_predict 128, temperature 0, streamed; `/proc/diskstats` at start, first token, end |
| Load mode | `mmap` only. `--load-mode none` needs the 45.3 GiB expert set in anonymous memory and the box has 31 GB; not attempted |
| Model | same three shards as Miu, sha256 verified on this box (`SHA256SUMS.rushuna` matches) |
| Engine | portable v0.4.0 `5266f24` bundle at `~/llama-v0.4.0/` (built on Miu, CUDA 12.8, sm_86), driver 580.173.02 |
| Machine | Rushuna: RTX 3060 12 GB (11,909 MiB usable), i7-7700 4c/8t, 31 GB DDR4-2133, SSSTC CA6 256 GB NVMe (85 GB free), Ubuntu 24.04. Ollama 0.30.0 idle in a tmux, nothing loaded |
| Gate | `free -g` available 30 GB of 31 (the Miu threshold of 40 cannot be met here); card idle 0 MiB |
| Threads | 4 = physical cores (Miu ran 6 on a 6-core) |

## Does the page cache hold? No. The SSD streams every token at stock.

Stock server, `-ncmoe 48`, 3 reps back to back:

| rep | prefill | decode | disk read, prefill | disk read, decode | per token | RSS after | Cached |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 31.2 tok/s | 8.71 tok/s | 56,832 MiB | 3,603 MiB (246.8 MiB/s) | 28.15 MiB | 29,025 MiB | 30,529 MiB |
| 2 | 31.8 | 8.72 | 51,725 | 3,230 (221.4 MiB/s) | 25.24 | 29,461 | 30,581 |
| 3 | 41.1 | 8.90 | 27,102 | 3,158 (221.2 MiB/s) | 24.67 | 29,351 | 30,592 |

Server RSS sits at the RAM ceiling (30.4 GB at load), Cached stays at 30.5 GB, and every decoded token pulls 25–28 MiB from the NVMe at 220–250 MiB/s sustained. Each 2,343-token prefill reads 27–57 GB, more than the 45 GiB expert set once, because the cache cannot hold it. `iostat-stock-ncmoe48.log`: 251 one-second samples above 1 MB/s read, mean 596 MB/s, peak 1.47 GB/s (prefill). Three reps do not settle it; the set is 1.5x the RAM.

## Result (load-mode mmap, 4 threads)

| -ncmoe | expert layers on GPU | peak VRAM MiB | tg128 d=0 | tg128 d=4096 | gain d=0 | per layer d=0 | per layer d=4096 |
|---:|---:|---:|---|---|---:|---:|---:|
| 48 | 0 | 4,929 | 8.66 [8.55..8.73] | 10.92 [10.89..10.97] | — | — | — |
| 44 | 4 | 8,779 | 9.22 [9.07..9.34] | 11.65 [11.61..11.68] | +0.56 (+6.4%) | +0.140 | +0.183 |
| 41 | 7 | 11,665 | 9.64 [9.51..9.71] | 12.22 [12.21..12.23] | +0.98 (+11.3%) | +0.140 | +0.186 |
| 38 | 10 | — | OOM | OOM | | | |

**Read d=4096 as the decode number on this rig.** The d=0 per-sample values climb inside every invocation (stock rep 1: 7.18 / 9.04 / 9.91; `-ncmoe 41` rep 1: 8.06 / 9.89 / 11.17) because each tg128 repeat at depth 0 starts on whatever the last one left in a 30 GB cache; the ±1.2–1.9 stddevs are that. At d=4096 the 4,096-token prefill runs first and the three repeats agree to 0.0–0.2 tok/s. d=4096 is faster than d=0 here for the same reason.

**OOM at 38.** `oom-confirm-ncmoe38.log`: `allocating 13441.16 MiB on device 0: cudaMalloc failed: out of memory` on 11,909 MiB. Last value that fits: **41**, 11,665 MiB peak, 244 MiB headroom. About 960 MiB per expert layer moved (11,665 − 4,929 over 7).

**Per-token time** (d=4096): 91.6 ms → 85.8 → 81.8 ms, about 1.4 ms per layer moved over 7; Miu's was 0.8 ms per layer at d=0 on DDR4-2667 with the expert set fully cached.

## Server, 2,343-token prompt, `-ncmoe 41`, 3 reps

| rep | prefill | decode | disk read, prefill | disk read, decode | per token | RSS after |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 41.9 tok/s | 11.11 tok/s | 36,091 MiB | 879 MiB (76.7 MiB/s) | 6.87 MiB | 30,028 MiB |
| 2 | 69.5 | 11.26 | 5,852 | 596 (52.7 MiB/s) | 4.65 | 30,361 |
| 3 | 70.5 | 11.45 | 5,082 | 674 (60.6 MiB/s) | 5.27 | 30,226 |

Load 22.1 s, RSS 22,511 MiB at load, card 11,561 MiB. With 7 of 48 expert layers on the card the host-side set drops to about 38.7 GiB, and per-token disk traffic falls from 25–28 MiB to 5–7 MiB; prefill on a settled cache doubles (31–41 → 70 tok/s). It still does not fit: reps 2–3 read 5–6 GB per prefill.

## Both rigs at their best fit, same file, same build, same harness

| | Miu 3090 (`-ncmoe 29`, 19 layers on card) | Rushuna 3060 (`-ncmoe 41`, 7 layers) | ratio |
|---|---:|---:|---:|
| tg128 d=0 | 22.60 | 9.64 | 2.3x |
| tg128 d=4096 | 24.48 | 12.22 | 2.0x |
| stock tg128 d=0 (reps 2–3 on Miu) | 16.85 | 8.66 | 1.9x |
| server decode | 20.84 | 11.11–11.45 | 1.8x |
| server prefill (settled) | 137.2 | 69.5–70.5 | 2.0x |
| disk read per decoded token | 0.33 MiB | 4.7–6.9 MiB (25–28 at stock) | |

Cross-rig offload comparisons on these two boxes are directional: DDR4-2667 vs 2133, PCIe 3.0 x16 on both, 62 vs 31 GB, and the expert set is cached on one and streamed on the other.

## Files

`run.log`, `results.json`, `raw-*.json`, `server-stock-ncmoe48.log`, `server-best-ncmoe41.log`, `iostat-stock-ncmoe48.log`, `iostat-best-ncmoe41.log`, `oom-confirm-ncmoe38.log`, `ncmoe_sweep.py`, `prompt-2k.txt`, `nohup.out`.
