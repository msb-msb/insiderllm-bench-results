# Rushuna (RTX 3060 12 GB): Inkling 2 Mini on mainline llama.cpp, Unsloth's prebuilt and Strata, against Codacus's claims, 2026-11-25

Pre-registration: `docs/candidates/inkling-2-mini-3060-2026-11.md`, LOCKED 2026-11-24 in `35324447`. The lock file's
sha256 is `588819cd1274efbdae47cafff66e015d9e650402838f3cf8cf2e56d757d54baf`. The mirror allowlist commit is
`9b96aa81`, and the mirror commit is `650e6dd`. The public raw copy hashed to the same value before the first measured
request (gate I6.1).

The claims under test are Codacus's, from "Inkling 2 Mini, a looped transformer" (YouTube, 20:27). They are listed
K1-K26 with timestamps in lock I1. **His figures are reference points, not results we assumed.** Figures for his RTX
5060 Ti, the RTX 5090 and his two-GPU runs are not scored.

**Times in the raw logs are UTC, Rushuna's clock.**
- Aborted first launch: 2026-11-25 01:55.
- Full run: 01:58 to 05:01:11.
- Void-cell re-runs: 05:02 to 05:08.
- Bandwidth measurement: 05:41 to 05:42.

In Pacific time that is 2026-11-24, from 17:55 to 21:42.

## Setup

- **Rig:** Rushuna.
  - RTX 3060 12 GB, PCIe 3.0 x16 (gen 3 x16 read during every prefill).
  - i7-7700, 4 cores / 8 threads; 32 GB DDR4-2133 (4 × 8 GB, dual channel).
  - Driver 580.173.02; kernel 6.8.0-136.
  - Swap: a 4 GiB swap file was on. Under the lock, any swap-out voids a cell, and no cell had one.
  - Background units running, as recorded in `rec/machine-state.txt`: mycoswarm, ollama, fwupd and ModemManager. All
    were idle, and none held the GPU.
- **Files (lock I3).** All are working copies under `~/inkling2-2026-11/model/`, re-hashed on the day. The canonical
  copies are in Miu `LLM_repo` (invariant (ae)).

  | File | Canonical copy (Miu LLM_repo) | sha256 |
  |---|---|---|
  | Inkling-2-Mini-UD-Q4_K_M.gguf (unsloth/Inkling-2-Mini-GGUF @ `8078d149`) | `inkling-2-mini-gguf/` | `78fcedcf93c5d1bfe83e225513b71392bb52259be0eaa5f8899c856a2e5834ae` |
  | dspark-Inkling-2-Mini-Q8_0.gguf (same repo and revision) | `inkling-2-mini-gguf/` | `3da00cf7c31bbe5662b3c0d373ecf782d74d32ef43990acc158ce60c2add72e0` |
  | Inkling-2-Mini-SQ-10.strata (strata-engine/Inkling-2-Mini-Strata @ `04996a1e`) | `inkling-2-mini-strata/` | `ac4d452ad03e4930abd9d46f9c5eec22b2f75a1da45a1e49bd24ccd58b065934` |
  | Qwen3.6-35B-A3B-UD-Q4_K_M.gguf (existing) | `from-miu/bench-models/` | `ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61` |

  The download log and scripts are in Miu `LLM_repo/inkling2-mini-dl-2026-11-24.{sh,log}` and
  `-via-rushuna.sh`. All three new files matched their HF LFS oids.

- **Builds (lock I4), all as pinned:**
  - **L, mainline:** ggml-org/llama.cpp `33aeb17f85869279e3821f746bc645357139bc2c`, built with CUDA 12.8 for sm_86.
    `--version` reports `1.0.0-dev (build 12720, commit 33aeb17f8)`. Binary hashes: `llama-server` `bfbbfe4a…`,
    `llama-perplexity` `390cc60c…`, `llama-tokenize` `48eb8517…`.
  - **U, Unsloth prebuilt:** release `b12675-mix-d14fe45`, asset `app-b12675-mix-d14fe45-linux-x64-cuda12-newer.tar.gz`.
    The asset sha256 `c9745b61…` matched the release's JSON. `--version` reports
    `1.0.0-dev (build 12675, commit add07b393)`. Binary hashes: `llama-server` `2132fdf5…`, `llama-perplexity`
    `f3362a14…`.
  - **S, Strata:**
    - Installed with the v0.2.21 (`0f8a6b78`) installer into an isolated HOME (`~/inkling2-2026-11/strata/home`). The
      installer checked the checksum and signature.
    - **Terminal version as installed: `strata 0.2.21.1 (build 0.1.68)`.** That is the point release the v0.2.21
      installer fetched on 2026-11-24; the lock names "v0.2.21".
    - **Engine:** `strata-inkling` **0.1.67** (cuda13 prebuilt), as pinned, binary sha256 `a0105917…`.
    - **Codacus's Strata version is unknown.** He says he ran it "2 days after" a release (lock I10), so it was older
      than or equal to what he could get then. The K15 and K19 differences below may be changes between Strata
      versions, not errors in his account.
  - Full hashes: `working-copies-and-builds.SHA256SUMS.txt` (taken after the run) and `rec/machine-state.txt`
    (taken before it).
- **Common llama.cpp flags (lock I5):** `-ngl 99 -np 1 -ctk q8_0 -ctv q8_0 -fa auto -t 4 --cache-ram 0 --fit off
  -lm mmap --jinja --port 8081`, plus `-lv 4` (deviation 3) and the arm's placement and `-c`. Every llama.cpp arm ran
  with `--cache-ram 0`.
- **Sampling:** the model's own settings: temperature 1.0, top-p 1, top-k 0, min-p 0, seed 1234. Greedy cells are
  marked.
- **Requests:** streamed chat completions, `cache_prompt false`, `ignore_eos`, `max_tokens 256`. Each prompt starts
  with a fresh nonce line. One cold request per server is excluded.
  - Prompts were cut from the HotRod corpus. It is the same file as `../strata-hotrod-2026-11/harness/corpus.txt`
    (sha256 `09a0975d…`), so it is not copied here.
  - Prompt files and their sha256s are in `harness/prompts/` and `rec/machine-state.txt`.
- **Harness:** `harness/`, unchanged from the hashes recorded in `rec/machine-state.txt` before the run.
  - `bench_inkling.py` is adapted from the MoE-cache harness.
  - `memwatch.py` is v3 from the Strata records plus one line (deviation 6).
  - `ballast.cu` is the 4 GiB ballast from lock I5. The compiled binary is not committed.

## Gates

| gate | result |
|---|---|
| I6.1 lock public, hash equal | pass (`650e6dd`) |
| I6.2 file hashes on Rushuna | all four match |
| I6.3 builds at pin | pass. Every load log shows `inkling2_loop` and no `check_tensor_dims` error |
| I6.4 PPL, Inkling CPU reference (`-c 4096 --chunks 4`, f16 KV) | **5.8308**, which is ≤ 15 |
| I6.4 L, U and U with `-ub 2048 -b 2048` | 5.8244 / 5.8203 / 5.8229. That is −0.11% / −0.18% / −0.14%, so all pass (limit ±2.0%) |
| I6.4 Qwen: CPU reference, then Q-cmoe | 5.0704, then 5.0796 (+0.18%), pass |

The first line of `rec/gate/gate-summary.txt` (`ref-inkling rc=127`) is a script error, not a measurement: the
remote `$W` was used before `env.sh` was sourced. It was fixed and the reference was re-run, which is the second line.

**FA state from the load logs (I6.5).**
- Every Inkling and Qwen arm logged `enabling flash_attn since it is required for quantized V cache` and
  `flash_attn = enabled`.
- Inkling's CUDA0 model buffer was **1,266.34 MiB** on both L and U. Qwen's was 1,921.34 MiB.
- Inkling KV: non-SWA KV is 136 MiB at 8K and 4,352 MiB at 256K (q8_0, covering 8 layer applications). SWA KV is
  127.5 MiB (40 layer applications). K21 ("every pass keeps its own KV") is consistent with this.
- CUDA0 compute buffers:

  | context | U | L |
  |---|---|---|
  | 8K | 669.95 MiB | 7,567.85 MiB |
  | 32K | — | 9,943.85 MiB, OOM |
  | 64K | — | 13,111.85 MiB, OOM |
  | 256K | 918.95 MiB | **32,119.85 MiB**, OOM |
  | 32K, `-ub 2048` | 1,258.32 MiB | — |

## Results

**Each cell value is the median [min..max] of 3 requests unless marked ×1.** Decode is `predicted_per_second` and
prefill is `prompt_per_second`, in tok/s. VRAM is the peak card `memory.used`. The full per-cell table is in
`rec/summary.txt`. **No cell had a swap-out**, and every prefill read PCIe gen 3 x16.

### Inkling 2 Mini, every expert in RAM (`-cmoe`)

| arm | ctx | loads | decode short | decode deep | prefill deep | VRAM peak |
|---|---|---|---|---|---|---|
| L | 8K | yes | 9.92 [9.91..9.93] | 9.68 [9.66..9.68] | 166.3 | 9,323 MiB |
| L | 32K / 64K / 256K | **no**: compute buffer OOM (above) | – | – | – | – |
| U | 8K | yes | **10.41** [10.39..10.43] (re-run) | 10.22 [10.21..10.22] | 154.4 | 2,401 MiB |
| U | 32K | yes | 10.37 [10.36..10.38] | 9.88 [9.86..9.90] | 156.5 | 2,833 MiB |
| U | 64K | yes | 10.33 [10.31..10.36] | 9.41 [9.40..9.41] | 152.9 | 3,409 MiB |
| U | 256K | yes | 10.36 [10.33..10.39] | 7.32 (×1, 235,931 tokens, TTFT 1,758 s) | 134.2 (×1) | 6,867 MiB |
| U-ub2048 | 32K | yes | – | 9.85 [9.83..9.85] | **384.6** [384.4..385.2] | 3,559 MiB |

- Short prefill (512 tokens) runs about 121 tok/s on U and 143 on L.
- **U-8k short, first run: void.** prompt_n spread 512..516 (4 tokens). Its values (10.40 [10.36..10.41]) agree with
  the re-run.

### DSpark (`-md dspark Q8_0 -ngld 99 --spec-type draft-dspark --spec-draft-n-max 3`, 8K)

| arm | temperature | decode short | decode deep | accepted / drafted |
|---|---|---|---|---|
| L-d | 1.0 | 6.92 [5.87..7.21] | 5.59 [5.56..6.03] | 36% short, 28% deep |
| L-d-greedy | 0 | 6.74 [6.60..7.28] | – | 38% |
| U-d | 1.0 | 6.55 [6.33..6.62] | 5.71 [5.64..6.04] | 34% short, 28% deep |
| U-d-greedy | 0 | 7.54 [7.27..7.61] | – | 44% |

### 4 GiB fit check (64K, ballast holding the card at `free=4095` MiB)

- **U4g: fits in 4 GiB, yes.** The cold, short ×1 and deep ×1 requests all completed: decode 10.40 short and 9.43
  deep, prefill 152.9 deep. Peak card use was 11,220 MiB, which is the ballast's 7,701 MiB plus the server's usage.
  Per lock I5 this is not a 4 GB card speed.
- **L4g: fits in 4 GiB, no.** The failing line was `allocating 13111.85 MiB on device 0: cudaMalloc failed: out of
  memory` (`rec/arms/server-L4g.log`).

### Qwen3.6-35B-A3B UD-Q4_K_M, mainline, same flags

| arm | ctx | decode short | decode deep | prefill deep | VRAM peak |
|---|---|---|---|---|---|
| Q-cmoe | 8K | 26.22 [26.18..26.30] | 25.58 [25.57..25.60] | 259.0 | 2,683 MiB |
| Q-cmoe | 32K | 26.32 [26.30..26.33] | 23.56 [23.53..23.60] | 254.7 | 2,947 MiB |
| Q-cmoe | 256K | 26.25 [26.14..26.29] | – | – | **5,849 MiB** |
| Q-best (`-ncmoe 24`) | 8K | 35.26 [35.22..35.31] | 34.11 [34.07..34.13] | 386.9 | 10,157 MiB |

### Strata SQ-10 (whole pack on the card)

Strata's launcher (`drafting: auto`) ran a drafting probe and chose **on** (`rec/strata-runconfig-sq-10-8k.json`:
mixed gain 1.132, code 1.409, chat 0.909). So **Strata's default at the model's own sampling is S10d**, and that is
the lock's "S10 at model sampling" (deviation 7). The `--drafting off` arms are extra.

| arm | ctx | drafting | decode short | decode deep | prefill deep | accepted / drafted |
|---|---|---|---|---|---|---|
| S10d (default) | 8K | on | **39.9** [39.3..41.1] | 37.7 [36.5..40.7] | 835.3 | 36% / 36% |
| S10d (default) | 16K | on | 39.2 [37.7..39.5] | 19.5 [18.7..20.1] | 790.7 | 31% / 38% |
| S10 (`--drafting off`) | 8K | off | 42.2 [42.1..42.3] | 40.2 [40.1..40.2] | 836.2 | – |
| S10 (`--drafting off`) | 16K | off | 42.1 [41.9..42.1] | 22.8 [22.8..22.9] | 805.3 | – |
| S10-greedy (default) | 8K | on, temperature 0 | 47.2 [46.8..48.5] | – | – | 42% |

**S10max (default launch, one deep request at ~90% fill):**

| requested ctx | completed | decode | prefill | notes |
|---|---|---|---|---|
| 24K | yes | 13.2 | 661.6 | |
| 32K | yes | 9.3 | 703.5 | |
| 48K | yes | 7.4 | 653.8 | |
| 64K | yes | 7.2 | 539.1 | DSpark off for this request (see below) |

- **The largest context tried, 64K, runs.** The search stopped there because the lock's list ends at 64K.
- **Strata did not change the requested context.** The engine logs `max_ctx` equal to the request every time.
- **From 16K up, the engine moves part of the global KV to mapped host RAM on its own.** At 16K the log reads
  `Auto Host KV Offload … global KV = 6912 VRAM + 9472 mapped host tokens`. This is why deep decode falls.
- **At 64K it logged `Tight VRAM while growing global ctx 49152 -> 57344; disabling DSpark gracefully`**, so the deep
  request drafted nothing.
- **Unexplained:** from the 48K launch on, MemAvailable after load was ~9 GB lower than at 32K (19.6 vs 28.5 GB). The
  engine itself reports only 1.16-1.62 GiB of host KV. This is recorded as observed and not explained.
- S10max started at 24K, not 16K (deviation 7).

**S10-split** (`--set vram-experts-gb=5`, 64K, short ×1):
- Both attempts loaded (222 s and 186 s) and completed the request without a crash: decode 17.6 and 18.0, prefill
  331 and 262.
- **Both cells are void:** 10.0 and then 12.5 GiB of NVMe reads during decode, against the 1 GiB rule. Void twice,
  so it is reported as void. The first attempt's files are in `rec/arms/void-first/`.

### Smoke test (I7, 8K, temperature 0)

| runtime | result |
|---|---|
| L | 5/5 |
| U | 5/5 |
| S10 (Strata default launch, drafting auto) | 5/5 |

No answer hit the cap inside its thinking block.

### Host RAM (K9)

- The llama.cpp server's resident set was RssFile 15.18 GiB (the experts, mmapped) plus RssAnon 0.42-0.86 GiB. That is
  **15.6 GiB at 8K and 16.05 GiB after the 256K request**.
- MemAvailable barely moved (minimum 29,570 MiB), because the file had been pre-read into page cache (lock I5).

## Codacus's claims, scored (lock I9)

**How memory is scored:** within ±0.5 GiB, reading his "GB" as decimal GB. **How speed is scored:** within ±15%.

| claim | his figure | ours | verdict |
|---|---|---|---|
| K1 mainline 256K doesn't load | doesn't load | OOM on a 32,119.85 MiB compute buffer. 32K and 64K fail too | **reproduced** |
| K2 GPU holds ~1.7 GB of the model | 1.58 GiB | 1.24 GiB | reproduced (−0.35 GiB) |
| K3 position bias → full score table, 32 GB at 256K | "32 gigs" | 32,119.85 MiB (31.4 GiB) request on L. U, with banded FA, asks for 919 MiB | cause agrees. The figure was recorded, not scored by the lock |
| K4 Unsloth loads 256K at full batch | loads | loads; 256K deep completed | **reproduced** |
| K5 decode ~18 at 8K and 256K | 18 | **10.41** (−42%) | **not reproduced** |
| K5 "flat 8K → 256K" | flat | short 10.41 → 10.36 (−0.5%). Deep falls to 7.32 at 236K | flat holds for short |
| K6 prefill ~175 | 175 | 154.4 / 156.5 / 152.9 deep at 8K / 32K / 64K (−12%, −11%, −13%). Short 121 (−31%) | reproduced on deep cells |
| K6 "> 300 with a bigger batch" | > 300 | 384.6 at `-ub 2048` | **reproduced** |
| K7 VRAM 32K / 64K / 256K | ~3 / >3.5 / ~7.5 GB | 2,833 / 3,409 / 6,867 MiB | reproduced at all three (Δ −0.03 / +0.07 / −0.28 GiB). Read as GiB, 256K would be 0.79 off |
| K8 fits in 4 GiB at 64K (narrowed) | yes | U yes, L no | **reproduced (U)** |
| K9 ~17 GB of system RAM | 15.8 GiB | 15.6-16.05 GiB resident | reproduced |
| K10 Qwen 45 tok/s | 45 | 35.26 at best fit (−22%), 26.22 at `-cmoe` | **not reproduced** |
| K10 "~2.5x Inkling" | 2.5x | 26.22 / 10.41 = **2.52x** at the same placement. 3.39x at Qwen's best fit | ratio reproduced at `-cmoe` |
| K11 Qwen 256K in ~6 GB | 5.59 GiB | 5.71 GiB | reproduced |
| K14 Strata SQ-10 ~35 tok/s | 35 | 39.9 at default (+14%). 42.2 with drafting off (+21%) | reproduced at default |
| K15 Strata tops out at 16K | 16K | 64K completes | **not reproduced**. Possibly a version change |
| K16 split mode crashes every time | crashes | 2/2 loads and 2/2 requests without a crash. Speed void (NVMe reads) | crash not reproduced, speed void |
| K18 DSpark 20 → 18, ~40% accepted | 0.90x, 40% | U-d 0.63x, 34%. L-d 0.70x, 36% | direction reproduced (slower, ranges don't overlap). Size not reproduced |
| K19 Strata's drafter never switches on at model sampling | idle | Default probe chose **on**; 36% accepted at 8K. S10d 39.9 vs S10 42.2, ranges don't overlap: drafting is slower here | **not reproduced**. Possibly a version change: the probe may be newer than his build |

## Our predictions (lock I8)

| prediction | range | measured | verdict |
|---|---|---|---|
| P1 L fails at 256K, loads at 8K | – | as predicted | **inside** |
| P2 U loads at 256K | – | loads | **inside** |
| P3 U decode at 8K short | 14-20 | 10.41 | **outside** |
| P4 Q-cmoe decode at 8K short | 26-30 | 26.22 | **inside** |
| P4 Q-best | 36-40 | 35.26 | **outside** (just under) |
| P4 Q-cmoe / U | 1.4-2.0x | 2.52x | **outside** |
| P5 U4g fits, L4g doesn't | – | as predicted | **inside** |
| P6 S10 at 8K, model sampling (= S10d) | 30-40 | 39.9 | **inside** |
| P6 S10max ≤ 32K | ≤ 32K | ≥ 64K | **outside** |
| P7 U-d / U at temperature 1 | ≤ 1.0x | 0.63x | **inside** |
| P7 U-d-greedy / U | ≥ 1.1x | 0.72x | **outside** |
| P8 S10-greedy drafts; S10 at model sampling doesn't | – | greedy drafts (42%), but the default at temperature 1 also drafts | half: **outside** on the second part |

## Context: Rushuna RAM bandwidth (measured 2026-11-25 05:41 UTC, after the run, card idle)

Tamanna's figure on record is a **read** figure from `stream_read.c`, so the like-for-like Rushuna number is the
same kernel.

| tool | build | threads | 3 runs | **median** |
|---|---|---|---|---|
| `stream_read.c` (sha256 `09858c7f…`, the kernel behind Tamanna's records; each run is best of 8, 320 MB array) | `gcc-13 -O3 -fopenmp` | 4 | 26.94, 27.01, 26.76 | **26.94 GB/s read** |
| same | same | 8 | 27.68, 27.65, 27.63 | 27.65 |
| STREAM 5.10 (`stream.c` from cs.virginia.edu/stream/FTP/Code/, sha256 `a52bae5e…`) | `gcc-13 -O3 -march=native -fopenmp -DSTREAM_ARRAY_SIZE=80000000 -DNTIMES=20`, `OMP_PROC_BIND=spread` | 4 | Triad 20,671.8, 20,645.0, 20,643.4 MB/s | **20.65 GB/s triad** |
| same | same | 8 | Triad 20,037.3, 20,037.1, 20,029.7 MB/s | 20.04 |

- Files: `bandwidth/stream-read-rushuna-2026-11-25.txt` and `bandwidth/stream-triad-rushuna-2026-11-25.txt`.
  `stream.c` itself is not committed; its URL and sha256 are given above.
- The pre-run check in `rec/machine-state.txt` (01:58, page cache full) read 25.84 / 26.35 / 26.05 GB/s at 4
  threads.
- The 2026-07-30 rig document (`docs/bench-rigs-memory-bandwidth.md`, a different, unkept kernel) has 26.60 read at 4
  threads and 20.77 triad.
- **Tamanna's figure** (`../tamanna-ram-speed-offload-2026-10-09/`, `../tamanna-ddr4-3000-verify-2026-10-09/`):
  41.95-42.44 GB/s read at 4 threads at DDR4-3000. That is **~1.56x Rushuna** with the same kernel. No STREAM triad
  figure exists for Tamanna.

## Discussion

**Hypothesis, not a result: the decode gap is RAM bandwidth, multiplied by the loop.**

With `-cmoe`, every routed expert lives in system RAM. Inkling runs layers 6-17 three times (`loop.start` 6,
`loop.end` 18, `loop.count` 3 in the GGUF), and each pass routes again. So a token can pull up to three different sets
of 8 experts from each looped layer.

Routed-expert bytes per token, summed from the GGUF's tensor sizes (`inkling2_loop`, 128 experts, 8 used):

| | routed bytes per token | at 10.41 tok/s | share of 26.94 GB/s read |
|---|---|---|---|
| one pass per layer | 0.924 GB | 9.6 GB/s | 36% |
| layers 6-17 × 3 | 1.784 GB | 18.6 GB/s | **69%** |
| Qwen3.6-35B-A3B (256 experts, 8 used), for comparison | 0.612 GB | 16.0 GB/s at 26.22 tok/s | 60% |

On the earlier rig document's two boxes, Qwen at full offload ran at 63-66% of the measured read ceiling.

If Inkling's three passes each read their own experts, Inkling sits in that same bandwidth-bound band. The "2.5x Qwen"
ratio then follows from bytes per token: 1.784 / 0.612 = 2.9x more bytes, against a measured 2.52x speed ratio.

That would also explain why Codacus's 18 tok/s is out of reach here. His RAM speed and CPU are not stated. At ~69%
efficiency, 18 tok/s needs about 46 GB/s of read bandwidth from this kernel. That is about 90% of dual-channel
DDR4-3200's theoretical 51.2 GB/s, and more than Tamanna's 42 GB/s at DDR4-3000. A dual-channel DDR5 box would clear
it.

**What this run does not show:**
- No bandwidth was varied.
- Decode was not traced per pass.
- Per-pass expert overlap (passes re-using the same experts, which would cut real traffic) was not measured.

Amendment A1 (draft, `docs/candidates/inkling-2-mini-3060-2026-11-amendment-A1-DRAFT.md`) tests the hypothesis on
Tamanna, which has ~1.56x the read bandwidth.

**Other observations.**
- **Strata is 4x faster than llama.cpp here at short context** (39.9 vs 10.4), because the whole 10.5 GB pack sits on
  the card. Once the KV spills to host RAM, the advantage shrinks: at 59K fill Strata decodes 7.2 against U's 9.4 at
  the same fill.
- **DSpark made every runtime slower at temperature 1.0, and both llama.cpp builds slower at temperature 0.** On
  Strata, greedy decoding with drafting (47.2) beat temperature 1 without it (42.2), but the temperature differs, so
  that comparison is not causal.
- The lock's limits (I10) apply in full:
  - one quant, one box, one day's builds;
  - the PPL gate does not reach long context;
  - 256K deep is one request.

## Deviations from the lock

1. **Aborted first launch (01:55).** `argparse.REMAINDER` in `bench_inkling.py` swallowed `--tag` and `--cells`.
   The script exited before any server started. The fix split argv at `--` manually, then the run was relaunched
   (01:58). The aborted logs are in `rec/aborted-argparse/`.
2. **Extra f16-KV mainline arms.** The fallback regex matched the INFO line `enabling flash_attn since it is required
   for quantized V cache`, which is not a refusal. So `L-32k-f16kv`, `L-64k-f16kv`, `L-256k-f16kv` and `L4g-f16kv`
   ran after their q8_0 arms failed on the compute buffer. All failed to start, in about 10 s each, and produced no
   figure. The regex was not edited mid-run.
3. **`-lv 4` added to the common flags.** The pin's default logging omits the buffer and FA lines that I6.5 needs.
   This changes logging only.
4. **WikiText zip extracted with Python's `zipfile`.** Rushuna has no `unzip`. The URL was the same as the pin's
   `scripts/get-wikitext-2.sh`. Hashes: zip `ef7edb56…`, `wiki.test.raw` `173c87a5…`.
5. **Download route switched.** Lock I3 named a Miu fetch (`inkling2-mini-dl-2026-11-24.sh`, 8 ranged curls). At
   about 16:45 PST on 2026-11-24 it was running at ~2 MiB/s, so it was switched to curls running on Rushuna, streamed
   over ssh into Miu's LLM_repo. Nothing was written on Rushuna, and the parts resumed
   (`inkling2-mini-dl-2026-11-24-via-rushuna.sh`). The size and sha256 checks were unchanged, and all three files
   matched their oids.
6. **`memwatch.py` changed by one line.** `MEMWATCH_EXTRA_NAMES` was added so the guard can also signal the Strata
   engine process (`strata-inkling`), as I6.7 requires. Otherwise it is v3 unchanged (`8525f345…` → `34c35b38…`).
7. **Strata arm naming.** The lock's "S10 at model sampling" is Strata's default launch, which turned drafting on
   (S10d here). The `--drafting off` S10 arms are extra, outside the lock. S10max started at 24K, because 16K at the
   default was already covered by S10d-16k (3 deep requests instead of 1).
8. **Strata terminal 0.2.21.1 (build 0.1.68)** came from the pinned v0.2.21 installer. The engine is 0.1.67, as
   pinned.

## Files

- `rec/run_everything.out`, `rec/arms/run.log`: the full run log.
- `rec/summary.txt`: `summarize.py` over every arm, with void reasons.
- `rec/reruns.out`: the void-cell re-runs.
- `rec/arms/`, per arm:
  - `results-*.json`: every request, its timings and the per-cell memory, swap, PCIe and NVMe counters.
  - `server-*.log`: the server load log.
  - `card-1s-*.csv`: card memory polled every second.
  - For Strata arms, `S10*-sq-10-*.json` / `.choices.json` and `sq-10-*.engine.log`.
  - `memwatch.log` and `memwatch-summary.json`.
- `rec/arms/void-first/`: the first, void S10-split attempt.
- `rec/gate/`: the PPL gate logs.
- `rec/loadcheck/`: the 8K mainline load log at `-lv 4`.
- `rec/smoke/`: the smoke test.
- `rec/aborted-argparse/`: deviation 1.
- `rec/machine-state.txt`: hashes, units, NVMe and bandwidth before the run.
- `rec/strata-runconfig-sq-10-8k.json`: Strata's written launch config, including the drafting probe.
- `bandwidth/`: the RAM bandwidth runs above.
- `harness/`: every script, plus `ballast.cu` and the prompts.
- `working-copies-and-builds.SHA256SUMS.txt`: post-run hashes.
