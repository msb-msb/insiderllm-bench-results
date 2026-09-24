# Qwen3.8-Flash-Next UD-IQ3_XXS, -ncmoe sweep, stock llama.cpp v0.4.0 — Miu RTX 3090, 2026-09-08

Results record; facts as measured. Harness `ncmoe_sweep.py miu`, table from `summarize.py results.json`. No fork, no expert cache, no MTP.

## Design

| | |
|---|---|
| Pre-registered | decode scales roughly with the fraction of routed-expert layers resident in VRAM. Stock (`-ncmoe 48`) is the baseline: 16.3 tok/s server decode, 17.1 tok/s llama-bench tg128 d=0 on 2026-09-07 |
| Sweep | `-ncmoe 48, 40, 34, 29, 26`; stop at first OOM |
| Harness | `llama-bench -ngl 99 -ncmoe N -fa 1 -p 0 -n 128 -d 0,4096 -r 3 -t 6 -lm mmap -o json`, 3 invocations per setting; peak VRAM from nvidia-smi sampled at 0.5 s |
| Server | one rep at the best fitting setting: `llama-server -ngl 99 -ncmoe 29 -fa on -c 4096 -t 6 --load-mode mmap`, 2,343-token prompt, n_predict 128, temperature 0, streamed; `/proc/diskstats` read at start, first token, end |
| Model | `~/bench-models/qwen3.8-flash-next/` UD-IQ3_XXS 3 shards, 81.96 GB, sha256 as in the 09-07 stock record; 48 layers, 512 experts, 10 used |
| Engine | llama.cpp v0.4.0 `5266f24`, CUDA 12.8, sm_86, `~/llama-v0.4.0/build/bin` |
| Machine | Miu: RTX 3090 24 GB (24,123 MiB usable), i7-8086K, 62 GB DDR4-2667, Samsung 980 PRO NVMe, Ubuntu 24.04, governor powersave |
| Gate | `free -g` available 59 GB (threshold 40); card idle 270–290 MiB |
| Soak | paused 13:36:12 PDT (`~/.soak-pause`), resumed 13:57:00 PDT, timer confirmed active |
| Load mode | **Pre-registered as `--load-mode none`, the loader's recommendation. Abandoned after two reps at stock — see below. Sweep ran at `mmap`, the stock baseline's mode.** |

## Load-mode none: does not fit in 62 GB

Two llama-bench reps at `-ncmoe 48 -lm none` (`raw-ncmoe48-none-rep*.json`, `results-none-attempt.json`):

| rep | peak VRAM | tg128 d=0 | tg128 d=4096 | d=4096 per-sample tok/s |
|---|---:|---:|---:|---|
| 1 | 5,480 | 15.45 ± 1.13 | 13.24 ± 3.37 | 10.3 / 16.9 / 12.5 |
| 2 | 5,460 | 15.57 ± 0.66 | 11.34 ± 4.74 | 8.4 / 8.9 / 16.8 |

Sampled during rep 3 at 13:42:09: llama-bench VmRSS 48,355,092 kB; `free -m` available 12,426 of 64,232 MiB, swap used 2,061 MiB; `vmstat` si/so 1,108 / 3,940 KB/s, bi 2,089,432 KB/s (NVMe read at 2.0 GB/s during decode); GPU util 1%. The 45.3 GiB of routed experts in anonymous memory plus the 27 GB lazily mmapped `per_layer_token_embd.weight` exceed 62 GB; the box swaps and re-reads. Rep 3 was killed, `results.json` moved to `results-none-attempt.json`, sweep restarted at `mmap` 13:43:11. These two reps stand as the control: **at stock, `none` measures memory pressure on this box, not the loader's recommendation.**

## Result (load-mode mmap, 6 threads)

Mean of 3 invocations of llama-bench's own 3-repeat average; brackets min..max over the 3 invocations. Gain and per-layer against the stock row as measured (n=3).

| -ncmoe | expert layers on GPU | peak VRAM MiB | tg128 d=0 | tg128 d=4096 | gain d=0 | per layer d=0 | per layer d=4096 |
|---:|---:|---:|---|---|---:|---:|---:|
| 48 | 0 | 5,368 | 15.78 [13.65..16.85] | 16.84 [15.46..17.57] | — | — | — |
| 40 | 8 | 13,068 | 17.84 [17.54..18.18] | 19.78 [19.53..19.96] | +2.05 (+13.0%) | +0.256 | +0.368 |
| 34 | 14 | 18,840 | 20.01 [19.65..20.55] | 22.05 [21.89..22.14] | +4.22 (+26.8%) | +0.302 | +0.372 |
| 29 | 19 | 23,652 | 22.60 [22.04..23.29] | 24.48 [24.32..24.71] | +6.81 (+43.2%) | +0.359 | +0.402 |
| 26 | 22 | — | OOM | OOM | | | |

**Stock rep 1 caveat.** The abort left the page cache at 11.4 GB, so `ncmoe48-mmap-rep1` (13.65 d=0, per-sample 10.7 / 14.3 / 16.0) re-read the expert set from NVMe. Reps 2–3 are 16.84 / 16.85 at d=0 and 17.50 / 17.57 at d=4096, matching the 09-07 stock record. Against the clean stock (16.85) the d=0 gains are +0.99 / +3.16 / +5.75 tok/s, +0.124 / +0.226 / +0.303 per layer. Every later setting ran on a warm cache.

**OOM at 26.** llama-bench prints only `failed to load model`; the verbose load (`oom-confirm-ncmoe26.log`) shows `ggml_backend_cuda_buffer_type_alloc_buffer: allocating 24991.16 MiB on device 0: cudaMalloc failed: out of memory`. Last value that fits: **29**, 23,652 MiB peak of 24,123 usable. About 960 MiB per expert layer moved (13,068 − 5,368 over 8 layers; 23,652 − 5,368 over 19).

**Per-token time** (d=0, clean stock): 59.3 ms → 56.1 → 50.0 → 44.2 ms, about 0.8 ms per layer moved over the 19; the per-layer gain in tok/s rises as the total falls.

## Server, 2,343-token prompt, `-ncmoe 29`, one rep

| load | RSS after load | card | prefill | decode | disk read during decode |
|---|---:|---:|---:|---:|---|
| 6.5 s (warm) | 13,635 MiB | 23,550 MiB | 137.2 tok/s | 20.84 tok/s | 42 MiB total, 0.33 MiB/token, 7.0 MiB/s |

Stock server on 09-07 (same prompt, `--cpu-moe`, mmap): prefill 65.6 / 125.6 / 132.0, decode 16.26 / 15.23 / 17.49 tok/s.

## Files

`run.log` (every step, the abort, the evidence line, soak times), `results.json` (mmap sweep + server), `results-none-attempt.json`, `raw-*.json` (llama-bench JSON + stderr per invocation), `server-best-ncmoe29.log`, `oom-confirm-ncmoe26.log`, `ncmoe_sweep.py`, `summarize.py`, `prompt-2k.txt`.
