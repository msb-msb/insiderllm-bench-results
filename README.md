# InsiderLLM bench records

The raw records behind the benchmark articles on [InsiderLLM.com](https://insiderllm.com): the harness scripts as run, the
orchestrator logs, per-run llama-bench JSON, 1-second `nvidia-smi` telemetry, server logs, and the README each run was written
up with. One directory per run, named `<rig>-<what>-<date>`. Everything here was measured on hardware the site owns, and every
number an article quotes from a record can be found in the file the article names.

This is a read-only mirror of `docs/bench-results/` in the site's private repository, synced on every deploy. The published
dataset that summarises the throughput rows is [`/benchmarks.json`](https://insiderllm.com/benchmarks.json) (CC BY 4.0), with
its human-readable page at [/benchmarks/](https://insiderllm.com/benchmarks/); the `raw_log` field of each dataset row points
into a directory here.

## How article links map to this repo

An article that says "the record is at `tamanna-bonsai-2-vs-qwen38-27b-2026-09-24/`" means the directory of that name at the
root of this repo:

| link in an article | here |
|---|---|
| `https://github.com/msb-msb/insiderllm-bench-results/tree/main/<record>/` | the run's directory: README, runner, logs, raw JSON |
| `https://github.com/msb-msb/insiderllm-bench-results/blob/main/<record>/<file>` | one file in it (a per-item table, a results JSON) |

Three rigs appear: **miu** (RTX 3090 on an i7-8086K, PCIe 3.0, the bench box until September 2026), **rushuna** (RTX 3060 12 GB
and GTX 1650 4 GB on an i7-7700, the offload box), and **tamanna** (the same RTX 3090 on a Ryzen 7 5700X, PCIe 4.0, from
2026-09-21). The rig block in each README and in each dataset row says which.

## The pinned build

Throughput rows on the site are measured on a pinned llama.cpp build so numbers stay comparable across months. The pin was
**b10088** (`67b9b0e`) through early September 2026 and is **v0.4.0** (`5266f24da75dc449bd56cbed7addb9c8e4a6a73e`, tag b10809)
from 2026-09-08, gated by a back-to-back re-bench of the two canonical 3090 rows on both builds
(`miu-build-ab-2026-09-07/`). A record made on any other build says so in its README and carries that build's own tag in the
dataset; it is never re-labelled to the pin. Build recipe, where a record built its own binary: CUDA, sm_86, `GGML_NATIVE=OFF`,
`-DLLAMA_CURL=OFF`, and the record's `build-flags.txt` holds the resulting CMake cache.

## What is not here

- Model files. Every record names its GGUF by file name, size and SHA-256 (verified against the hub's LFS object id where the
  hub still serves the same file), so a run can be reproduced from a fresh download.
- The LoRA adapters of `miu-lora-variance-2026-08-31/` (eleven 318 MB safetensors); the scored outputs and the training
  scripts are here.
- Private LAN addresses, which are masked to `192.168.x.x` in logs and READMEs.

## Licence

CC BY 4.0, the same as the dataset. Cite the article and the record directory.
