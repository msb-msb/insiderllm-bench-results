# Qwen3.6-35B-A3B UD-Q4_K_M, -ncmoe sweep and mmap-vs-none, llama.cpp v0.4.0 — Rushuna GTX 1650 4 GB, 32 GB RAM, 2026-09-11

Results record; facts as measured. Harness `ncmoe_sweep.py rushuna1650` (this directory), run 11:18–11:46 PDT (log timestamps UTC). Table from `../miu-flashnext-ncmoe-2026-09-08/summarize.py results.json`. Sub-8 GB tier bench: same box, RAM and NVMe as the 2026-09-08 RTX 3060 rows, card swapped 2026-09-08 evening.

## Design

| | |
|---|---|
| Pre-registered | the two GTX 1060 6 GB claims for this model are 17 tok/s; expect the 1650 to land 12–18; under 10 means the dense layers do not fit and it is a different regime |
| Sweep | `-ncmoe 40` (every routed expert on host) downward by 1 to the first failure |
| Harness | `llama-bench -ngl 99 -ncmoe N -fa 1 -p 0 -n 128 -d 0,4096 -r 3 -t 4 -lm mmap -o json`, 3 invocations per setting; peak VRAM from nvidia-smi at 0.5 s |
| Server | `llama-server -ngl 99 -ncmoe N -fa on -c 4096 -t 4 --load-mode <mode> -np 1 --no-warmup`, 2,343-token prompt, n_predict 128, temperature 0, streamed; `/proc/diskstats` at start, first token, end; `iostat -dxt nvme0n1 1` alongside. Stock first (3 reps), then best fit (3 reps) |
| none pass | at the best fit: 3 llama-bench invocations at `-lm none`, then the server at `--load-mode none`, 3 reps with iostat. The 22.1 GB file fits 32 GB, so this is the case the video says `none` wins and the 09-08 Flash-Next result on Miu (45 GiB set on 62 GB) says it loses |
| Model | `~/bench-models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf`, 22,134,528,992 bytes, sha256 `ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61`, verified on this box after copy from Miu's NVMe (same digest as the 09-07 gate and the published rows); 40 layers |
| Engine | llama.cpp v0.4.0 `5266f24`, rebuilt on Miu 2026-09-11 with `CMAKE_CUDA_ARCHITECTURES="75;86"` (`~/llama-v0.4.0/build-sm75`), same flags as the sm_86 bundle otherwise (CUDA 12.8, shared libs, Release, GGML_NATIVE=OFF), shipped to `~/llama-v0.4.0-sm75/` on Rushuna; `cuobjdump` shows sm_75 and sm_86 in libggml-cuda.so. llama.cpp warns at every load: "suboptimal performance due to a lack of tensor cores … consider CMAKE_CUDA_ARCHITECTURES=61-virtual;80-virtual and DGGML_CUDA_FORCE_MMQ to force the use of the Pascal code for Turing." Not done; recorded as an open variable |
| Machine | Rushuna: GTX 1650 4 GB (TU117, cc 7.5, 3,714 MiB usable, PCI 01:00.0, the slot the 3060 was in), i7-7700 4c/8t, 31 GB DDR4-2133, SSSTC CA6 256 GB NVMe, Ubuntu 24.04, driver 580.173.02, headless. System Ollama on 11434, idle, not in the path |
| Gate | card idle 0 MiB; `free -g` available 30 GB; the file was already in page cache from the copy (Cached 23.6 GB at start) |

## Result (mmap, 4 threads)

| -ncmoe | expert layers on GPU | peak VRAM MiB | tg128 d=0 | tg128 d=4096 | gain d=0 | per layer d=0 |
|---:|---:|---:|---|---|---:|---:|
| 40 | 0 | 2,701 | 20.22 [20.19..20.24] | 19.76 [19.74..19.77] | — | — |
| 39 | 1 | 3,167 | 20.43 [20.41..20.44] | 19.95 [19.92..19.98] | +0.21 (+1.1%) | +0.21 |
| 38 | 2 | 3,665 | 20.63 [20.62..20.65] | 20.15 [20.12..20.17] | +0.41 (+2.0%) | +0.21 |
| 37 | 3 | — | failed_to_create_context | | | |

**Against the pre-registration: above the range.** Stock decode is 20.2 tok/s at depth 0, 19.8 at depth 4,096, against an expected 12–18 and the two 1060 claims of 17. The dense layers fit with 1.3 GB to spare at stock. Per-sample spread inside an invocation is 0.05 tok/s (rep 1 at 38: 20.62 / 20.67 / 20.66); the page cache holds the whole file and the disk counters read zero during every decode.

**Two expert layers fit, at about 480 MiB each** (2,701 → 3,167 → 3,665). **-ncmoe 37 loads its weights and fails at context creation**: `oom-confirm-ncmoe37.log` shows `allocating 283.00 MiB on device 0: cudaMalloc failed: out of memory` in `graph_reserve: failed to allocate compute buffers` → `failed to allocate compute pp buffers`. In the dataset's terms the load cliff and the usable cliff are the same here at 38; llama-bench's `failed to create context` is the 4,096-context reservation, not the weights. Each layer moved is worth +0.21 tok/s at depth 0, +0.2 at depth 4,096; two layers buy 2 percent.

## mmap vs none at the best fit (-ncmoe 38)

| | tg128 d=0 | tg128 d=4096 | peak VRAM | server prefill (3 reps) | server decode (3 reps) | server load | RSS after load | disk read during decode |
|---|---|---|---:|---|---|---:|---:|---:|
| mmap | 20.63 [20.62..20.65] | 20.15 [20.12..20.17] | 3,665 | 66.4 / 66.0 / 66.0 | 20.17 / 20.16 / 20.19 | 4.7 s | 20,085 MiB | 0 |
| none | 20.70 [20.68..20.72] | 20.22 [20.21..20.24] | 3,699 | 70.8 / 70.5 / 70.5 | 20.24 / 20.26 / 20.25 | 27.7 s | 18,641 MiB | 0 |
| none − mmap | +0.07 (+0.3%) | +0.07 (+0.3%) | | +4.5 (+6.8%) | +0.08 (+0.4%) | +23 s | | |

Decode: `none` is +0.3 percent on both depths, inside the 0.05 tok/s per-sample spread but consistent in sign across all six invocations. Prefill: +6.8 percent on the server path (66.0 → 70.5 tok/s on a 2,343-token prompt), the only cell where the mode is visible. Load: 4.7 s from a warm cache under mmap against 27.7 s for `none`, which reads the file into anonymous memory (Cached rose from 23.6 to 30.6 GB during the read, RSS 18.6 GB). Nothing was read from disk during any decode in either mode. **On a 22 GB file in 32 GB of RAM, `none` is a prefill setting worth about 7 percent and a decode setting worth nothing measurable, and it costs 23 s at every load.** The video's "three and a half tokens a second" for the same switch on a 1060 did not appear here; the video's own description says the advice reverses when the model outgrows RAM, which is the 09-08 Miu case.

## Server, 2,343-token prompt, stock (-ncmoe 40, mmap), 3 reps

| rep | prefill | decode | disk read prefill / decode | RSS after | Cached |
|---|---:|---:|---|---:|---:|
| 1 | 65.2 tok/s | 19.66 tok/s | 0 / 0 MiB | 21,446 MiB | 23,636 MiB |
| 2 | 64.9 | 19.73 | 0 / 0 | 21,447 | 23,636 |
| 3 | 64.9 | 19.76 | 0 / 0 | 21,450 | 23,636 |

`iostat-stock-ncmoe40.log`: 128 one-second samples, mean 0.9 kB/s read, peak 76 kB/s. The page cache holds the file; the 09-08 Flash-Next stock run on this same box read 25–28 MiB per decoded token because that set was 1.5x the RAM.

## Reading

Decode on this card is set by the host side. With 38 of 40 expert layers in DDR4-2133 the card's share of the work barely moves the number (+2 percent for two layers), and the two 1060 6 GB claims of 17 tok/s sit under a 1650 4 GB at 20 with fewer layers resident, which points at RAM speed and thread count on those boxes rather than the GPU. The 3060 in this slot on 2026-07 (published rows, b10088) reached 28.1 tok/s at full offload (-ncmoe 40) on the same DDR4-2133; the 1650 at full offload is 20.2 on v0.4.0. Whether that 8 tok/s gap is card, build, or the tensor-core warning above is not separated by this run.

## Files

`run.log`, `results.json`, `raw-ncmoe{40,39,38}-mmap-rep{1,2,3}.json`, `raw-ncmoe37-mmap-rep1.json`, `raw-ncmoe38-none-rep{1,2,3}.json`, `server-stock-ncmoe40.log`, `server-best-ncmoe38.log`, `server-best-ncmoe38-none.log`, `iostat-*.log`, `oom-confirm-ncmoe37.log`, `ncmoe_sweep.py`, `prompt-2k.txt`, `nohup.out`.
