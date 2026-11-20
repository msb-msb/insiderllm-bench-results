# Community benchmark on NVIDIA GeForce RTX 3090

Measured on 2026-11-20 with `tools/strata_bench.py` (suite 1, 3 runs per test, medians with ranges). Speeds are the engine's own timings; first-token times are measured by the client over HTTP. Speed only: no correctness check was run.

## Hardware and software

- GPU and VRAM: NVIDIA GeForce RTX 3090, 24 GiB VRAM
- CPU: AMD Ryzen 7 5700X 8-Core Processor (8 cores, 16 threads); installed RAM: 62.7 GiB; storage: not measured
- OS: Linux 7.0.0-38-generic; GPU driver: 580.178.04; CUDA: 13.0
- Strata: project 0.1.45, commit 251dec43; engine 0.1.45
- Background workloads and power limits: not recorded

## Model and configuration

- Model and quantization: qwen3.8-flash-next-iq3_s
- Context: 131072 tokens; parallel slots: 1
- Settings: the install's own configuration, unchanged; thinking off for the suite; temperature 0

```text
strata --pack iq3_s --native Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf --ple-gguf Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00002-of-00002.gguf --expert-profile expert-profile.bin --expert-cache auto --prefill auto:16384 --spec 4 --spec-min-p 0.5 --mtp rt --max-context 131072 --kv int8
```

Environment of the config: `STRATA_ROUTE_RESIDENT=1e30`, `STRATA_ROUTE_RESIDENT_RANKS=3-9`, `STRATA_ROUTE_RESIDENT_EDGE=1`, `STRATA_SWAP2_MAX=2`, `STRATA_SWAP2_GAP=1`, `STRATA_KV_GROW_INIT=4096`

## Method

Run by `python tools/strata_bench.py` against the HTTP API of a Strata server (already running); model loading is not timed. One warm-up chat and a 1K prompt are discarded first. Every prompt starts with a unique tag, so the conversation cache cannot help the fresh-prompt tests.

- short chat: the three questions of `tools/ab_engine.py`, up to 100 new tokens, 3 runs
- 4K / 16K prompts: generated word lists sized by a calibration request, 24 new tokens, 3 fresh prompts each
- agent session: system prompt and four tools, then 5 turns that each add about 1500 words of a project file and continue from the model's own earlier answers (the way agent clients resend a conversation), 64 new tokens per turn, 3 sessions; the cache numbers come from the answer's usage (`cached_tokens`) and timings (`prompt_n`)
- concurrency (when run): N requests sent at the same moment, total tokens over the wall time of the burst, latency over all requests

## Results

| Configuration | Actual prompt tokens | Reused tokens | Generated tokens | Runs | Prompt tok/s median and range | Decode tok/s median and range | TTFT seconds median and range |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| short chat | 46 (43-51) | 0 | 100 (100-100) | 9 | not measured | 89.4 (74.7-120.3) | 0.34 (0.31-0.38) |
| 4K prompt, fresh | 4019 (4019-4019) | 0 (0-0) | 24 cap | 3 | 2575.3 (2407.7-2633.0) | not measured | 1.58 (1.55-1.69) |
| 16K prompt, fresh | 16058 (16058-16058) | 0 (0-0) | 24 cap | 3 | 3053.3 (2912.5-3058.0) | not measured | 5.29 (5.28-5.54) |
| agent session, follow-up turns | 15402 (15357-15419) at the last turn | see below | up to 64 | 3 | see below | 92.8 (63.4-115.3) | 1.54 (0.89-1.98) |

Ranges are the lowest and highest of the runs; `Runs` counts requests that returned a token.

### Agent session (conversation cache)

Cache hit over the follow-up turns: 69.7 % (69.7-69.8); earlier-turn tokens read again per session: 5 (5-5) (earlier turns that the cache did not hold; the 14541 (14540-14542) new tokens of the files are read once); first turn (nothing cached) first token: 0.67 s (0.67-0.72).

| Turn (run 1) | Prompt tokens | Reused | Read | Prompt tok/s | First token (s) | Decode tok/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 609 | 0 | 609 | 872.6 | 0.725 | 88.7 |
| 1 | 4585 | 640 | 3945 | 2021.1 | 1.976 | 92.8 |
| 2 | 6118 | 4648 | 1470 | 1440.0 | 1.043 | 90.6 |
| 3 | 9551 | 6181 | 3370 | 1947.1 | 1.755 | 77.1 |
| 4 | 12461 | 9599 | 2862 | 1834.4 | 1.584 | 108.3 |
| 5 | 15402 | 12503 | 2899 | 1913.2 | 1.539 | 96.4 |

Per-request data: `results.json`. Engine log lines from the start: `engine-log-excerpt.txt` (when this run started the server).

## Correctness and limitations

Not measured: this is a speed suite. The conversation uses the model's own replies, so token counts differ a little between runs. Machine details come from the server, `nvidia-smi`/`rocm-smi` and the OS; background load and power limits are not recorded. Total time of the suite: 71 s.
