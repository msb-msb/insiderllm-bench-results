# Community benchmark on NVIDIA GeForce RTX 3060

Measured on 2026-11-20 with `tools/strata_bench.py` (suite 1, 3 runs per test, medians with ranges). Speeds are the engine's own timings; first-token times are measured by the client over HTTP. Speed only: no correctness check was run.

## Hardware and software

- GPU and VRAM: NVIDIA GeForce RTX 3060, 12 GiB VRAM
- CPU: Intel(R) Core(TM) i7-7700 CPU @ 3.60GHz (4 cores, 8 threads); installed RAM: 31.3 GiB; storage: sda     HGST HUS728T8TAL       sata; sdb     Multi-Card             usb; sr0     HL-DT-ST DVD-RAM GHC0N sata; nvme0n1 SSSTC CA6-8D256-HP     nvme
- OS: Linux 6.8.0-136-generic; GPU driver: 580.173.02; CUDA (driver supports up to): 13.0
- Strata: project 0.1.62, commit not a git checkout; engine 0.1.62
- GPU detail (after the run, near idle): power_limit_w=170.00, power_draw_w=87.10, pcie=gen3 x16, pstate=P2, temp_c=53
- Background workloads: not recorded (GPU power limit/draw read above)

## Model and configuration

- Model and quantization: qwen3.8-flash-next-iq3_s
- Context: 131072 tokens; parallel slots: 1
- Settings: the install's own configuration, unchanged; thinking off for the suite; temperature 0

```text
strata --pack iq3_s --native Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf --ple-gguf Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00002-of-00002.gguf --expert-profile expert-profile.bin --expert-cache auto --prefill auto --spec 4 --spec-min-p 0.5 --mtp rt --max-context 131072 --kv int8 --mmap-experts
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
| short chat | 46 (43-51) | 0 | 100 (100-100) | 9 | not measured | 17.2 (9.6-18.7) | 2.07 (1.70-5.11) |
| 4K prompt, fresh | 4019 (4019-4019) | 0 (0-0) | 24 cap | 3 | 170.7 (162.7-190.3) | not measured | 23.62 (21.22-24.79) |
| 16K prompt, fresh | 16058 (16058-16058) | 0 (0-0) | 24 cap | 3 | 315.6 (309.1-329.4) | not measured | 50.96 (48.84-52.02) |
| agent session, follow-up turns | 9071 (9002-9099) at the last turn | see below | up to 64 | 3 | see below | 15.2 (11.8-21.4) | 10.26 (6.66-12.79) |

Ranges are the lowest and highest of the runs; `Runs` counts requests that returned a token.

### Agent session (conversation cache)

Cache hit over the follow-up turns: 71.1 % (71.0-71.1); earlier-turn tokens read again per session: 5 (5-5) (earlier turns that the cache did not hold; the 8207 (8207-8209) new tokens of the files are read once); first turn (nothing cached) first token: 19.59 s (18.80-21.62).

| Turn (run 1) | Prompt tokens | Reused | Read | Prompt tok/s | First token (s) | Decode tok/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 609 | 0 | 609 | 31.6 | 19.594 | 12.4 |
| 1 | 2273 | 631 | 1642 | 197.5 | 8.398 | 18.4 |
| 2 | 3979 | 2336 | 1643 | 249.6 | 6.66 | 14.9 |
| 3 | 5685 | 4042 | 1643 | 178.8 | 9.278 | 11.8 |
| 4 | 7352 | 5710 | 1642 | 129.2 | 12.788 | 14.9 |
| 5 | 9002 | 7360 | 1642 | 158.3 | 10.434 | 15.2 |

Per-request data: `results.json`. Engine log lines from the start: `engine-log-excerpt.txt` (when this run started the server).

## Correctness and limitations

Not measured: this is a speed suite. The conversation uses the model's own replies, so token counts differ a little between runs. Machine details come from the server, `nvidia-smi`/`rocm-smi` and the OS; background load is not recorded. Total time of the suite: 605 s.
