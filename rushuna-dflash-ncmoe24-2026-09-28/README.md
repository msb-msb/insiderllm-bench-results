# DFlash drafter under -ncmoe offload on the RTX 3060 — Rushuna, 2026-09-28

PRE-REGISTRATION, written 2026-09-28 before the first measured run. Clears (when run) the 2026-09-29 marker
in `dated-markers.md`. Runner: `rushuna_ncmoe_bench.py` (docstring repeats the design). Everything in this
section was fixed before any measured run and is not edited afterwards; results go below it.

## Claim under test

The published row `rushuna-qwen36-35b-a3b-udq4km-specdec-qwen35-08b` says speculative decoding hurts the
Qwen3.6-35B-A3B under `-ncmoe` offload, because batched verification pulls more experts per token through a
card that is already streaming experts from system RAM. The 2026-09-22 Tamanna run overturned the negative on
a *resident* 3090 (1.092x). This run tests the offload regime on the 3060 the row is attributed to.

## Findings made before the measured runs

**1. DFlash does not fit at `-ncmoe 24` on 12 GB.** Load-only fit checks (`fitcheck/`, no benchmark prompts;
one 16-token "Hello" request per arm to allocate decode/verify buffers), all at `-ngl 99 -fa on -c 8192 -np 1`:

| arm | `-ncmoe` | result | VRAM after load / after request (12,288 MiB card) |
|---|---:|---|---|
| no drafter | 24 | loads | 10,075 / 10,075 MiB |
| Qwen3.5-0.8B Q8_0, draft-simple, n_max 15 | 24 | loads | 11,007 / 11,029 MiB |
| DFlash Q8_0, draft-dflash, n_max 15 | 24 | **fails**: `cudaMalloc` of 489.00 MiB for the draft context's compute buffer | — |
| DFlash, same, `-ub 256` | 24 | **fails**: 487.95 MiB short, same buffer | — |
| DFlash, same | 26 | loads | 11,587 / 11,631 MiB |
| DFlash, same | 28 | loads | 10,659 / 10,703 MiB |

So the article's recommended config cannot take the drafter on a 12 GB card; the closest that fits is
`-ncmoe 26`, two more expert layers in system RAM. That is a finding in its own right, and it is why the
reader's comparison below is across two offload settings.

**2. The published negative row is not a Rushuna measurement.** Traced through git:

- `ad400474` (2026-05-07) added the sentence to the 35B-A3B article inside a section on YouTube creator
  Codacus's GTX 1060 6 GB / i3-8100 / 24 GB DDR4 build: his 0.8B drafter took *his* 17 tok/s config to
  11 tok/s at 65% acceptance, i.e. about 0.65x on that rig.
- `00621c29` (2026-07-22) folded the firsthand 3060 bench into the article and moved the sentence into the
  3060 section; the Codacus attribution did not travel with it.
- `2c405ee8` (2026-07-27) entered it in benchmarks.json as a Rushuna `measured` row and computed 0.28x by
  dividing 11 by Rushuna's own 38.9 tok/s baseline — a GTX 1060 number over a 3060 number.

The row breaks the dataset's own inclusion rule (community figures excluded). Consequently arm (c) below
cannot *reproduce* that row; it is the first firsthand measurement of the 0.8B drafter on this card. The
brief's "within 10% of 11 tok/s" test is reported as asked, but read it knowing 11 tok/s was never a 3060
figure.

**3. What the build does with a verify batch under `-ncmoe` (source, not measured).** In v0.4.0
`ggml-cuda.cu`, a CPU-resident `MUL_MAT_ID` (the MoE expert matmul) is moved to the GPU — weights copied over
PCIe — only when its batch is at least `GGML_OP_OFFLOAD_MIN_BATCH`, default 32 (`get_op_batch_size` returns
`ne[2]`, the token count). A DFlash verify batch is 16 tokens (n_max 15 + 1), so its CPU-resident experts are
computed on the CPU, reading weights from DDR4-2133, not streamed to the card. **Prediction:** PCIe rx per
generated token will not rise materially with a drafter; any cost of wide verification shows up as CPU/DRAM
time for the union of experts the 16 tokens route to, not as PCIe traffic. `nvidia-smi dmon -s t` rx/tx at 1 s
is the test.

## Design

| | |
|---|---|
| box | Rushuna: RTX 3060 12 GB (driver 580.173.02), i7-7700 4c/8t, 4x8 GB DDR4-2133 dual channel, PCIe 3.0 x16 |
| build | `~/llama-v0.4.0` on Rushuna: v0.4.0 **`5266f24`**, Release, `CMAKE_CUDA_ARCHITECTURES=86`, `GGML_NATIVE=OFF`, `GGML_CUDA=ON` — the 09-22 commit and flags. Built on Miu 2026-09-07 with **nvcc 12.8 / gcc 13.3** and shipped with CUDA 12.8 cudart/cublas; byte-identical to Miu's `build/bin` (`libggml-cuda.so.0.23.0` `3f3035e0…8b3a`, `llama-server` `0b4ef4e0…b6c6`). The 09-22 run used Tamanna's build of the same commit with nvcc 12.4 / gcc 13.4; those exact binaries were copied over and refused to start (they need glibc 2.43, Rushuna has Ubuntu 24.04's), so the toolchain differs and nothing else does |
| target | `~/bench-models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf`, sha256 `ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61`, re-hashed on Rushuna today = the 09-22 record |
| DFlash drafter | `Qwen3.6-35B-A3B-DFlash-Q8_0.gguf`, sha256 `17f7a3989c4b49392d79b9801f606cf8b627f0f97055a693d6044999d1a64634`, re-hashed on Rushuna = the 09-22 record (from `LLM_repo/qwen3.6-35b-a3b-dflash-gguf/`) |
| 0.8B drafter | `unsloth/Qwen3.5-0.8B-GGUF` revision `6ab46149`, `Qwen3.5-0.8B-Q8_0.gguf`, 811,843,840 B, sha256 `0ad885ffd4bb022fc4f0d33a3308fa108ef8613159d3b3a67e23abca056b7a6c` = the LFS record; downloaded 2026-09-28 to `LLM_repo/qwen3.5-0.8b-gguf/`. The quant of the original (Codacus) run is not on record; Q8_0 is our choice |
| prompts / sampling | `~/am17an_bench.py` sha256 `cca7f169…b510` = `docs/bench-results/mtp-2026-05-06/am17an_bench.sh` = Tamanna's copy; nine prompts by AST; `/completion`, `n_predict 192, temperature 0, seed 42, cache_prompt false` — identical to 09-22 |
| common flags | `-ngl 99 -fa on -c 8192 -np 1` |
| drafter flags | DFlash: `-md DRAFT -ngld 99 --spec-type draft-dflash --spec-draft-n-max 15` (as 09-22). 0.8B: `-md DRAFT08 -ngld 99 --spec-type draft-simple --spec-draft-n-max 15`, `p-min` at its default 0 — same verification width as DFlash, so the two drafter arms differ in the drafter only |

Five configs:

| id | `-ncmoe` | drafter |
|---|---:|---|
| `base24` | 24 | none — the article's recommended config |
| `q08b24` | 24 | Qwen3.5-0.8B |
| `base26` | 26 | none |
| `dflash26` | 26 | DFlash |
| `q08b26` | 26 | Qwen3.5-0.8B |

Order: base24, q08b24, base26, dflash26, q08b26, repeated for 3 reps; **every measured run is immediately
preceded by a discarded priming run of the same config** (`raw-prime-*`). Fresh `llama-server` per run.
Target + both drafters (23.3 GB) fit in page cache on 31 GiB. Ollama stopped for the duration. 1 s
`nvidia-smi` sampler (09-22 fields) and 1 s `nvidia-smi dmon -s t` (PCIe rx/tx MB/s) per run.

Metric: aggregate generation tok/s = sum(predicted_n) / sum(predicted_ms) over the nine prompts, from the
server's timings; mean of 3 reps, spread = min..max. Per-prompt tok/s and acceptance
(`draft_n_accepted / draft_n`) as in 09-22. PCIe rx MB per generated token = mean dmon rx over the
nine-prompt window x window length / tokens generated (includes the short prefills).

## Verdicts, pre-registered

- **(A) mechanism: `dflash26 / base26`.** Below 1.00x CONFIRMS the published negative (a drafter hurts under
  offload); 1.05x or above OVERTURNS it; 1.00-1.05x is INCONCLUSIVE.
- **(B) reader: `dflash26 / base24`.** Same thresholds. This is the choice a 12 GB owner actually has — the
  article's config without a drafter versus the closest config that takes one — and it decides what the
  article recommends.
- Resolvability (08-28 rule: gap exceeds the larger same-config rep spread) is reported beside each, not
  folded into the verdict.
- Per-prompt results reported as on 09-22, since coding and translation went opposite ways there.
- Secondary, no verdict: `q08b24 / base24` and `q08b26 / base26`; `q08b24` against 11 tok/s (brief's
  10% test, with finding 2's caveat); PCIe rx per token across all five against finding 3's prediction.

Nothing else is read into the run. Not run by design: other `-ncmoe` values, F16 draft, other n_max, MTP.

## Results

RUN AND COMPLETE, 2026-09-28 19:21:27 to 19:58:41 UTC (Rushuna's clock; 12:21 to 12:58 PDT). 30 server runs,
15 measured, no failures, no config change after the pre-registration commit (`62e7cfd9`). Ollama was stopped
by Mark before launch and the card read 0 MiB. Every measured rep of every config produced the same text per
prompt (content hashes identical across reps) and, for the drafter arms, the same draft/accept counts.

### Verdicts, by the pre-registered rule

**(A) mechanism: CONFIRMS the negative.** `dflash26 / base26` = **0.611x** (22.04 vs 36.09 tok/s), gap
-14.05 tok/s against a larger same-config spread of 0.53; resolvable.

**(B) reader: CONFIRMS the negative.** `dflash26 / base24` = **0.576x** (22.04 vs 38.25 tok/s), gap
-16.21 tok/s against a spread of 0.11; resolvable. On a 12 GB 3060 the article's no-drafter config is 1.74x
faster than the closest config that takes the DFlash drafter.

| config | `-ncmoe` | drafter | aggregate tok/s, mean [min..max] | per-prompt mean | acceptance | vs base24 | vs base26 | VRAM after load / peak | wall, nine prompts |
|---|---:|---|---:|---:|---:|---:|---:|---|---:|
| `base24` | 24 | none | **38.25** [38.20..38.31] | 37.91 | — | 1.000 | — | 10,075 / 10,099 MiB | 39.5 s |
| `q08b24` | 24 | Qwen3.5-0.8B Q8_0 | 15.92 [15.91..15.93] | 17.21 | 0.262 (850 / 3,244) | 0.416 | — | 11,007 / 11,047 MiB | 86.9 s |
| `base26` | 26 | none | 36.09 [35.80..36.33] | 35.78 | — | 0.944 | 1.000 | 9,147 / 9,171 MiB | 41.9 s |
| `dflash26` | 26 | DFlash Q8_0 | **22.04** [22.02..22.05] | 21.82 | 0.227 (976 / 4,308) | **0.576** | **0.611** | 11,587 / 11,671 MiB | 65.0 s |
| `q08b26` | 26 | Qwen3.5-0.8B Q8_0 | 15.22 [15.21..15.23] | 16.39 | 0.261 (849 / 3,250) | 0.398 | 0.422 | 10,079 / 10,117 MiB | 91.0 s |

Telemetry, all 15 measured runs: PCIe gen 3 x16 under load, SM clock median 1965 MHz, 48-53 °C start and
58-59 °C max, 69-87 W mean power against a 170 W limit. Clock-event reasons were clear in every sample
except six single samples, at most one per run, in the drafter arms: five `0x4` (SW power cap) and one `0x24`
(SW power cap + SW thermal slowdown), each at 88-94 W, 52-59 °C and SM 1920-1972 MHz. Isolated one-second
flags with no clock drop; not treated as throttling.

### Per prompt (mean of 3 reps)

| prompt | base24 | q08b24 | base26 | dflash26 | q08b26 | dflash26 / base26 | dflash26 / base24 | DFlash acceptance | 0.8B acceptance (at 24) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| code_python | 37.95 | 29.80 | 36.07 | **40.24** | 28.64 | **1.116** | **1.060** | 0.509 | 0.647 |
| code_cpp | 37.89 | 24.71 | 35.45 | 24.40 | 23.64 | 0.688 | 0.644 | 0.250 | 0.522 |
| explain_concept | 38.07 | 11.00 | 35.76 | 20.83 | 10.68 | 0.582 | 0.547 | 0.211 | 0.125 |
| summarize | 37.87 | 13.61 | 36.09 | 18.51 | 13.01 | 0.513 | 0.489 | 0.181 | 0.233 |
| qa_factual | 37.97 | 19.55 | 35.76 | 19.43 | 18.95 | 0.543 | 0.512 | 0.192 | 0.358 |
| translation | 37.42 | 11.34 | 35.38 | **7.89** | 10.18 | **0.223** | **0.211** | 0.033 | 0.187 |
| creative_short | 38.07 | 13.39 | 35.70 | 19.26 | 12.86 | 0.539 | 0.506 | 0.186 | 0.191 |
| stepwise_math | 38.03 | 18.32 | 36.04 | 25.13 | 17.01 | 0.697 | 0.661 | 0.276 | 0.334 |
| long_code_review | 37.90 | 13.19 | 35.80 | 20.67 | 12.55 | 0.577 | 0.545 | 0.214 | 0.195 |

The same shape as 09-22, shifted down. DFlash's per-prompt acceptance is almost exactly the Tamanna run's
(code_python 0.509 both times, translation 0.033 both times): the drafter predicts the same, the verify step
costs more. Only code_python clears break-even under offload (1.12x at -ncmoe 26, 1.06x even against base24);
translation is the worst case in both regimes. The coding/translation split survives; everything between
them flips from roughly flat to roughly half speed.

### Secondary results

- **The 0.8B drafter does not reproduce the published 11 tok/s.** `q08b24` is 15.92 tok/s, 45% above 11, well
  outside the brief's 10% window. Given finding 2 that is expected: 11 tok/s was a GTX 1060 figure. The
  firsthand 3060 ratio is **0.416x** at -ncmoe 24 (0.422x at 26), between Codacus's ~0.65x on his rig and the
  row's 0.28x. The row's 65% acceptance is not reproduced either: 26.2% here, draft length 15. (explain_concept
  on its own lands on 11.00 tok/s; a coincidence of one prompt, not a reproduction.)
- **The 0.8B is worse than DFlash under offload** (0.422x vs 0.611x at -ncmoe 26) despite higher acceptance
  on 7 of 9 prompts, because it is a full 24-layer model drafting token by token where DFlash drafts a block
  in one pass of six layers.
- **Offload cost of making room:** -ncmoe 24 -> 26 costs 5.6% on its own (38.25 -> 36.09).

### PCIe traffic, and finding 3's prediction (POST-HOC analysis, `posthoc-pcie-and-step-cost.txt`)

The pre-registered metric (mean dmon rx over the nine-prompt window / tokens) came out at 32.2, 45.3, 23.7,
28.4, 48.6 MB per token for base24, q08b24, base26, dflash26, q08b26. It turned out to be dominated by the
prefills: dmon shows 4-11 one-second bursts of 7.6-11.2 GB/s per run (prompts of 32+ tokens cross
`GGML_OP_OFFLOAD_MIN_BATCH`, and the CPU-resident experts are copied to the card for the prefill), with
~60-170 MB/s in every other second. A 1 s sampler catches those bursts at random, so the registered number is
noisy and says little about decode. Separating them after the fact (bursts >= 2000 MB/s excluded):

| config | decode-second PCIe rx, median | decode MB per generated token |
|---|---:|---:|
| base24 | 61-64 MB/s | 1.8 |
| q08b24 | 165-174 MB/s | 12.7 |
| base26 | 63-67 MB/s | 2.0 |
| dflash26 | 165 MB/s | 7.5 |
| q08b26 | 174 MB/s | 15.5 |

A drafter roughly triples decode-time PCIe traffic, but to ~170 MB/s, about 1% of a gen 3 x16 link's usable
bandwidth. One Q4_K_M expert layer of this model is on the order of 0.5 GB; nothing close to that crosses the
bus per token. **Prediction held: verification does not stream experts over PCIe in this build.**

### Mechanism

The published row said batched verification under offload loses because it "pulls from up to 64 experts per
layer" through "a card already streaming experts across PCIe from system RAM". The first half is right in
spirit and the second half is wrong for llama.cpp v0.4.0. At -ncmoe 24-26 the card does not stream experts
during decode at all: a CPU-resident expert matmul is only shipped to the GPU when its batch reaches 32
tokens (`GGML_OP_OFFLOAD_MIN_BATCH`), a 16-token DFlash verify batch stays below that, and dmon shows decode
traffic of ~165 MB/s, activations rather than weights. What grows is the CPU side. For each of the 24-26
expert layers held in system RAM, the i7-7700 has to compute the verify batch itself, reading from DDR4-2133
every expert that any of the 16 tokens routes to; one token touches 8 routed experts per layer, and 16 tokens
touch the union of theirs, several times that. Measured cost (POST-HOC, per-step arithmetic from the server's
own timings, blocks = draft_n / 15): a DFlash verify step takes **203 ms at -ncmoe 26, 7.33x a plain decode
step (27.7 ms)**, where on the resident 3090 it took 4.19x. Tokens delivered per step are nearly the same in
both regimes (4.47 here, 4.57 on Tamanna), because acceptance is the same. On the 3090 4.57 tokens for 4.19
steps' worth of time is a small win; on the 3060 4.47 tokens for 7.33 steps' worth is a 39% loss, and only
code_python (about 8.6 tokens per step) clears the 7.33 bar. GPU utilization agrees: ~40% busy while the
no-drafter configs decode, ~22% under DFlash, so the card spends more of each step waiting for the CPU. The
per-step figure includes the drafter's own forward pass, which this run cannot separate; the expert-union
explanation is inferred from the source and these measurements, not measured per layer. A direct test would
be `GGML_OP_OFFLOAD_MIN_BATCH=16`, which forces verify batches onto the card and would make the published
PCIe mechanism real; that is a follow-up, not part of this result.

### Things to know before quoting this

- **Build toolchain differs from 09-22** (nvcc 12.8 / gcc 13.3 vs 12.4 / 13.4, same commit and flags); see
  Design. The Tamanna comparison in the mechanism paragraph crosses both a toolchain and a rig.
- **n_max 15 for the 0.8B is our choice**, made to match DFlash's verification width. A shorter draft (the
  build's default is 3) would cost less per verify step; the 0.8B's best-case setting on this card was not
  searched.
- **Greedy text differs between arms**, as on 09-22 (batch-shape dependence of the target's logits, upstream
  #25618); throughput is unaffected, and every arm generated 1,285 tokens.
- **Nine short prompts, 192-token cap, raw `/completion`**, no chat template, no thinking. The published
  harness, not a workload study.
- Priming runs (`raw-prime-*`) match their measured runs to within 0.4% everywhere; the page cache held all
  three model files throughout (load 4.3-5.8 s).
