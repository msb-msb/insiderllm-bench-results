# Community benchmark on NVIDIA GeForce RTX 3090

Measured on 2026-11-20 with `tools/strata_bench.py` (suite 1, 3 runs per test, medians with ranges). Speeds are the engine's own timings; first-token times are measured by the client over HTTP. Speed only: no correctness check was run.

## Hardware and software

- GPU and VRAM: NVIDIA GeForce RTX 3090, 24 GiB VRAM
- CPU: AMD Ryzen 7 5700X 8-Core Processor (8 cores, 16 threads); installed RAM: 62.7 GiB; storage: nvme0n1 MTFDKBA512TFH-1BC1AABHA nvme
- OS: Linux 7.0.0-38-generic; GPU driver: 580.178.04; CUDA (driver supports up to): 13.0
- Strata: project 0.1.62, commit not a git checkout; engine 0.1.62
- GPU detail (after the run, near idle): power_limit_w=420.00, power_draw_w=358.21, pcie=gen4 x16, pstate=P2, temp_c=65
- Background workloads: not recorded (GPU power limit/draw read above)

## Model and configuration

- Model and quantization: qwen3.8-flash-next-iq3_s
- Context: 131072 tokens; parallel slots: 1
- Settings: the install's own configuration, unchanged; thinking off for the suite; temperature 0

```text
strata --pack iq3_s --native Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf --ple-gguf Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00002-of-00002.gguf --expert-profile expert-profile.bin --expert-cache auto --prefill auto --spec 4 --spec-min-p 0.5 --mtp rt --max-context 131072 --kv int8 --kv-resident 32768
```

## Method

Run by `python tools/strata_bench.py` against the HTTP API of a Strata server (started by the benchmark from the install configuration); model loading is not timed. One warm-up chat and a 1K prompt are discarded first. Every prompt starts with a unique tag, so the conversation cache cannot help the fresh-prompt tests.

- short chat: the three questions of `tools/ab_engine.py`, up to 100 new tokens, 3 runs
- 4K / 16K prompts: generated word lists sized by a calibration request, 24 new tokens, 3 fresh prompts each
- agent session: system prompt and four tools, then 5 turns that each add about 1500 words of a project file and continue from the model's own earlier answers (the way agent clients resend a conversation), 64 new tokens per turn, 3 sessions; the cache numbers come from the answer's usage (`cached_tokens`) and timings (`prompt_n`)
- concurrency (when run): N requests sent at the same moment, total tokens over the wall time of the burst, latency over all requests

## Results

| Configuration | Actual prompt tokens | Reused tokens | Generated tokens | Runs | Prompt tok/s median and range | Decode tok/s median and range | TTFT seconds median and range |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| short chat | 46 (43-51) | 0 | 100 (100-100) | 9 | not measured | 116.5 (94.6-139.4) | 0.34 (0.29-0.42) |
| 4K prompt, fresh | 4019 (4019-4019) | 0 (0-0) | 24 cap | 3 | 2393.0 (2298.5-2393.5) | not measured | 1.70 (1.69-1.76) |
| 16K prompt, fresh | 16058 (16058-16058) | 0 (0-0) | 24 cap | 3 | 3176.8 (3097.1-3182.1) | not measured | 5.08 (5.07-5.21) |
| agent session, follow-up turns | 9086 (9079-9097) at the last turn | see below | up to 64 | 3 | see below | 144.6 (108.4-183.7) | 1.02 (0.86-1.09) |

Ranges are the lowest and highest of the runs; `Runs` counts requests that returned a token.

### Agent session (conversation cache)

Cache hit over the follow-up turns: 71.1 % (71.0-71.1); earlier-turn tokens read again per session: 5 (5-5) (earlier turns that the cache did not hold; the 8209 (8208-8209) new tokens of the files are read once); first turn (nothing cached) first token: 1.33 s (1.13-1.42).

| Turn (run 1) | Prompt tokens | Reused | Read | Prompt tok/s | First token (s) | Decode tok/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 609 | 0 | 609 | 548.5 | 1.127 | 97.2 |
| 1 | 2262 | 620 | 1642 | 1847.4 | 0.904 | 108.4 |
| 2 | 3968 | 2325 | 1643 | 1769.3 | 0.944 | 129.5 |
| 3 | 5674 | 4031 | 1643 | 1632.6 | 1.023 | 144.6 |
| 4 | 7380 | 5737 | 1643 | 1589.9 | 1.049 | 158.1 |
| 5 | 9086 | 7443 | 1643 | 1559.4 | 1.071 | 164.5 |

Per-request data: `results.json`. Engine log lines from the start: `engine-log-excerpt.txt` (when this run started the server).

## Correctness and limitations

Not measured: this is a speed suite. The conversation uses the model's own replies, so token counts differ a little between runs. Machine details come from the server, `nvidia-smi`/`rocm-smi` and the OS; background load is not recorded. Total time of the suite: 61 s.
