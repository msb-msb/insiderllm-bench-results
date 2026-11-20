# Community benchmark on NVIDIA GeForce RTX 3060

Measured on 2026-11-20 with `tools/strata_bench.py` (suite 1, 3 runs per test, medians with ranges). Speeds are the engine's own timings; first-token times are measured by the client over HTTP. Speed only: no correctness check was run.

## Hardware and software

- GPU and VRAM: NVIDIA GeForce RTX 3060, 12 GiB VRAM
- CPU: Intel(R) Core(TM) i7-7700 CPU @ 3.60GHz (? cores, 8 threads); installed RAM: 31.3 GiB; storage: not measured
- OS: Linux 6.8.0-136-generic; GPU driver: 580.173.02; CUDA: 13.0
- Strata: project 0.1.45, commit 251dec43; engine not read
- Background workloads and power limits: not recorded

## Model and configuration

- Model and quantization: qwen3.8-flash-next-iq3_s
- Context: not read tokens; parallel slots: 1
- Settings: the install's own configuration, unchanged; thinking off for the suite; temperature 0

```text
strata --pack iq3_s --native Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf --ple-gguf Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00002-of-00002.gguf --expert-profile expert-profile.bin --expert-cache auto --prefill auto:16384 --spec 4 --spec-min-p 0.5 --mtp rt --max-context 131072 --kv int8 --mmap-experts --kv-resident 32768
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
| short chat | 46 (43-51) | 0 | 100 (100-100) | 9 | not measured | 28.0 (24.0-34.8) | 0.99 (0.88-1.04) |
| 4K prompt, fresh | 4019 (4019-4019) | 0 (0-0) | 24 cap | 3 | 647.9 (640.1-700.3) | not measured | 6.26 (5.79-6.34) |
| 16K prompt, fresh | not measured | not measured | 24 cap | 0 | not measured | not measured | not measured |
| agent session, follow-up turns | not measured at the last turn | see below | up to 64 | 0 | see below | not measured | not measured |

Ranges are the lowest and highest of the runs; `Runs` counts requests that returned a token.

### Agent session (conversation cache)

Cache hit over the follow-up turns: not measured; earlier-turn tokens read again per session: 0 (0-0) (earlier turns that the cache did not hold; the 0 (0-0) new tokens of the files are read once); first turn (nothing cached) first token: not measured.

| Turn (run 1) | Prompt tokens | Reused | Read | Prompt tok/s | First token (s) | Decode tok/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |

### Skipped and failed

- failed 16K: no token came back
- failed 16K: ConnectionResetError(104, 'Connection reset by peer')
- failed 16K: URLError(ConnectionRefusedError(111, 'Connection refused'))
- failed agent: URLError(ConnectionRefusedError(111, 'Connection refused'))
- failed agent: URLError(ConnectionRefusedError(111, 'Connection refused'))
- failed agent: URLError(ConnectionRefusedError(111, 'Connection refused'))

Per-request data: `results.json`. Engine log lines from the start: `engine-log-excerpt.txt` (when this run started the server).

## Correctness and limitations

Not measured: this is a speed suite. The conversation uses the model's own replies, so token counts differ a little between runs. Machine details come from the server, `nvidia-smi`/`rocm-smi` and the OS; background load and power limits are not recorded. Total time of the suite: 80 s.
