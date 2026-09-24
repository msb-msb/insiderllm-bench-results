# Qwen3.8-Flash-Next UD-IQ3_XXS, stock llama.cpp v0.4.0 — Miu RTX 3090, 2026-09-07

Results record. Facts as measured; every number is reproducible from `run.log`, `results.json`, `bench-*.json`, `server-*.log`. Baseline for phase 3 (fork, expert cache, MTP); none of those was used here.

## Setup

| item | value |
|---|---|
| model | `~/bench-models/qwen3.8-flash-next/Qwen3.8-Flash-Next-UD-IQ3_XXS-0000{1,2,3}-of-00003.gguf`, 81.96 GB, sha256 verified against the Hugging Face listing (268f81fd…, cfe600b2…, f1912ba3…) |
| model meta (loader) | arch `qwen4exp`, 176.94 B params, IQ3_XXS 3.0625 bpw, 48 layers, 512 experts, 10 used, n_embd 2560; `per_layer_token_embd.weight` 27,466 MiB with lazy read enabled |
| engine | llama.cpp v0.4.0, commit `5266f24da75dc449bd56cbed7addb9c8e4a6a73e`, CUDA 12.8, sm_86, `~/llama-v0.4.0/build/bin` |
| machine | Miu: RTX 3090 24 GB, i7-8086K 6c/12t, 62 GB DDR4-2667, Samsung 980 PRO NVMe, Ubuntu 24.04 |
| gate | Brave closed; `free -g` available 59 GB (threshold 40); card idle 280–302 MiB |
| soak | paused 18:16:07, resumed 18:31:22 (covers block 2 of the gate as well), timer active |
| offload flag | server: `-ngl 99 --cpu-moe -fa on -c 4096 -np 1 --no-warmup`. bench: `-ngl 99 -ncmoe 48 -fa 1`. `--cpu-moe` ≡ `-ncmoe 48` on a 48-layer model: every routed-expert tensor (`ffn_{gate,up,down}_exps`) is overridden to `CUDA_Host`; the shared-expert tensors (`ffn_*_shexp`) are not matched and stay on CUDA0 |
| load mode | default (`auto` → mmap). The loader warns: "tensor overrides to CPU are used with mmap enabled - consider using --load-mode none for better performance". Left at stock for this baseline; `--load-mode none` is a phase-3 variable |
| threads | llama-bench default on this build is 6 |

## Placement after load (verbose loader, `server-verbose-load.log`)

| where | what | size |
|---|---|---:|
| CUDA0 | dense layers, shared experts, output | 3,816 MiB model + 132 MiB KV (4096 ctx) + 634 MiB compute |
| host (CUDA_Host override) | 144 routed-expert tensors: 48 × down 450 MiB iq4_nl, 46 × gate/up 256 MiB iq2_s, 2 × gate/up 343 MiB iq3_s | ≈ 45.3 GiB |
| mmap, lazy | n-gram embedding table `per_layer_token_embd.weight` | 27,466 MiB |
| card total after load | | 5,274 MiB |

(The verbose log prints every loader line twice because `--fit` does a dry-run pass first; counts above are per real load.)

## Load

| | cold (model pages evicted via `posix_fadvise DONTNEED`, no root) | warm (immediately after) |
|---|---:|---:|
| time to `/health` ok | 15.1 s | 3.9 s |
| server RSS | 33,222 MiB | 33,225 MiB |
| card | 5,274 MiB | 5,274 MiB |

Cold here is "file pages dropped from cache", not a reboot. Cached fell from ~59 GB to 24.9 GB on eviction. RSS rose from 33.2 GB to 45.1 GB over the three 2k-token reps as experts were touched.

## Server, 2,343-token prompt, n_predict 128, temperature 0, 3 reps

| rep | prefill | decode |
|---|---:|---:|
| 1 (experts cold) | 65.6 tok/s (35.7 s) | 16.26 tok/s |
| 2 | 125.6 tok/s (18.7 s) | 15.23 tok/s |
| 3 | 132.0 tok/s (17.8 s) | 17.49 tok/s |
| warm mean (2–3) | **128.8** [125.6..132.0] | |
| mean (1–3) | | **16.33** [15.23..17.49] |

## llama-bench, `-p 512 -n 128 -d 0,4096 -r 3`, threads 6, 3 reps

| metric | rep 1 | rep 2 | rep 3 | mean | mean excl. rep 1 |
|---|---:|---:|---:|---:|---:|
| pp512 d=0 | 158.62 | 220.57 | 215.92 | 198.4 | **218.2** |
| tg128 d=0 | 16.68 | 17.02 | 17.63 | **17.11** | 17.33 |
| pp512 d=4096 | 159.17 | 208.59 | 204.20 | 190.7 | **206.4** |
| tg128 d=4096 | 16.58 | 17.84 | 16.36 | **16.93** | 17.10 |

Rep 1 of each fresh llama-bench process pays the expert page-in again (the server had just been stopped), which is why its pp is 27% low; decode barely moves. Each bench run took 85–105 s including load.

## Thread sweep, decode only, `-p 0 -n 128 -t 3,6,12 -r 3`, 3 reps

| threads | rep 1 | rep 2 | rep 3 | mean | sd |
|---|---:|---:|---:|---:|---:|
| 3 | 11.66 | 11.56 | 11.83 | **11.68** | 0.13 |
| 6 | 16.00 | 17.65 | 14.77 | **16.14** | 1.45 |
| 12 | 16.15 | 14.24 | 16.45 | **15.61** | 1.20 |

6 vs 12: +3.4%, inside the rep-to-rep noise of ±1.5 tok/s. 3 vs 6: −27.6%, clear. The pre-registered expectation from Codacus's run was 6 beating 12 by ~20%; on this box 6 and 12 are indistinguishable, and only 3 is clearly worse.

## Against the pre-registration

Codacus, RTX 3060 / 61 GB RAM: decode ~22–24, prefill ~115.

| | Miu 3090 / 62 GB | vs 3060 figure | rule |
|---|---:|---:|---|
| decode (server, 2k prompt) | 16.33 | **−29%** vs 23 | under +10% → RAM-bandwidth bound |
| decode (llama-bench tg128) | 17.11 | −26% vs 23 | same |
| prefill (server, warm) | 128.8 | +12% vs 115 | |
| prefill (llama-bench pp512, warm) | 218.2 | (different prompt length; not comparable) | |

The 3090 did not buy decode over a 3060 on this model at stock settings; it lost. Under the pre-registered rule that is the RAM-bandwidth-bound branch, and Miu's DDR4-2667 is on the slow side for a 45 GiB expert working set streamed from host memory every token. Two stock-config caveats that phase 3 should vary before reading more into the gap: the loader's own `--load-mode none` recommendation for CPU-overridden tensors, and the mmap page-in behaviour that made rep 1 of every fresh process slow. Codacus's exact flags, RAM speed and llama.cpp build are not on record here, so the −29% is against a number quoted from a video, not a controlled comparison.

## Files

| path | content |
|---|---|
| `run_stock.py` | the runner: eviction, cold/warm server loads, 3 server reps, 3 bench reps, 3 thread-sweep reps |
| `prompt-2k.txt` | the 1,500-word prompt (2,343 tokens under this tokenizer), built from site prose |
| `run.log` | timestamps and every reported number |
| `results.json` | all steps, machine-readable |
| `bench-default-rep{1,2,3}.json`, `bench-threads-rep{1,2,3}.json` | llama-bench JSON output and stderr tail per run |
| `server-cold.log`, `server-warm.log` | default-verbosity server logs for the two timed loads |
| `server-verbose-load.log` | verbose load-only pass for tensor placement and metadata |
