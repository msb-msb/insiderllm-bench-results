# Re-measuring the ten unbacked July 2026 rushuna rows — 2026-09-28

PRE-REGISTRATION, written before the first measured run. Runner: `remeasure.py` (docstring repeats the design).
Context: the 2026-09-28 provenance audit (`INSIDERLLM-PROJECT.md`, "Measurement Provenance"; benchmarks.json
v1.10.0 changelog) found ten rushuna rows labelled measured with no record behind them; the session that
produced them in July is gone. This record re-measures them on the same card so each row either gets a record
or gets a new value.

## Rows under test

| row id | published value | what is re-measured |
|---|---|---|
| `rushuna-qwen36-35b-a3b-udq4km-ncmoe32-d0` | 31.8 tok/s, 6.1 GB VRAM | tg128 at d=0 |
| `rushuna-qwen36-35b-a3b-udq4km-ncmoe20-d0` | 42.6 tok/s, 11.7 GB; "OOM as soon as real context arrived" | tg128 at d=0; server load-and-serve at -c 8192 and 16384 |
| `rushuna-qwen36-35b-a3b-udq4km-ncmoe24-d8192` | 38.2 tok/s, pp 386 | tg128 and pp512 at d=8192 |
| `rushuna-qwen36-35b-a3b-udq4km-ncmoe24-d0` (prompt_tok_s only) | pp 413 | pp512 at d=0 |
| `rushuna-qwen36-35b-a3b-udq4km-ncmoe24-d4096` (prompt_tok_s only) | pp 394 | pp512 at d=4096 |
| `rushuna-qwen3-14b-q4km-ngl41` | 35.9 tok/s | tg128, `-ngl 41` |
| `rushuna-qwen3-14b-q4km-half-ram` | 5.7 tok/s | tg128, `-ngl 20` |
| `rushuna-qwen3-14b-q4km-all-ram` | 3.05 tok/s | tg128, `-ngl 0` |

The 24 d=0 / d=4096 generation figures (38.9 / 38.5) were already re-measured within 1% on 2026-09-11
(`../rushuna-3060-qwen36-ncmoe-2026-09-11/`); this run measures them again as a by-product of `-d 0,4096,8192`.

## Decision rule (from the brief)

Per figure: delta = (new − published) / published. **|delta| ≤ 3%: keep the published value**, set the row's
`raw_log` to this record, add the hash. **|delta| > 3%: replace the value** with the new one and add a dated
correction (2026-09-28) wherever the old figure is published. VRAM figures are reported beside the throughput
but the 3% rule is applied to throughput (tok/s) only; VRAM differences are stated, not ruled on.

The `-ncmoe 20` claim is tested as stated: *does it load, and does it serve a request that fills the context?*
at -c 8192 and -c 16384. If it serves at both, the "OOM under real context" sentence is wrong and gets a
correction. `-ncmoe 24` at the same two contexts is a control for the article's "holds steady under load".

## Design

| | |
|---|---|
| box | Rushuna: RTX 3060 12 GB (580.173.02), i7-7700, 4x8 GB DDR4-2133, PCIe 3.0 x16, headless |
| build | `~/llama-v0.4.0`, v0.4.0 `5266f24`, sm_86, `GGML_NATIVE=OFF` (the pin; byte-identical to Miu's build, see `../rushuna-dflash-ncmoe24-2026-09-28/`). The July rows were b10088 `67b9b0e`; the 09-11 record measured the build effect on this card at −0.9..+0.1% |
| 35B file | `Qwen3.6-35B-A3B-UD-Q4_K_M.gguf`, sha256 `ac0e2c11…31a61`, re-hashed on Rushuna 2026-09-28 |
| 14B file | `bartowski/Qwen_Qwen3-14B-GGUF` rev `bd080f76`, `Qwen_Qwen3-14B-Q4_K_M.gguf`, 9,001,753,632 B, sha256 `915913e22399475dbe6c968ac014d9f1fbe08975e489279aede9d5c7b2c98eb6` = the upstream LFS object id, verified 2026-09-28 on the store copy (`LLM_repo/rushuna-bench-models/`, dated 2026-07-22, the day of the July runs) and again on Rushuna after copy. Whether it is byte-for-byte the July file cannot be shown; it is the only 14B Q4_K_M in the store and its date matches |
| 35B harness | `llama-bench -ngl 99 -ncmoe N -fa 1 -p 512 -n 128 -d D -r 3`, the July harness string, threads and load mode at v0.4.0 defaults (4 threads, auto) |
| 14B harness | `llama-bench -ngl {41,20,0} -p 512 -n 128 -r 3`; the July rows state only `-ngl`, so flash attention and threads are v0.4.0 defaults, recorded as resolved in the JSON. **`-ngl 20` for "half in RAM" is our reading** (Qwen3-14B has 40 repeating layers; the July row left n_gpu_layers null) |
| design | block 3 (09-21 convention): every measured invocation immediately preceded by a discarded priming invocation of the identical command; 3 measured invocations per config, each `-r 3`. Value = mean of the three invocation means; spread = max − min. 35B configs first, then 14B, so the page cache holds one model at a time |
| VRAM | peak nvidia-smi `memory.used` at 0.5 s during each invocation |
| server | `llama-server -ngl 99 -ncmoe {20,24} -fa on -c {8192,16384} -np 1`; one request of C − 256 prompt tokens (the 09-11 2k prompt, repeated), `n_predict 128`, temperature 0 |
| Ollama | stopped for the run |

## Results

RUN AND COMPLETE, 2026-09-29 18:28:48 to 19:05:26 (Rushuna's clock, UTC; 11:28-12:05 PDT). Pre-registration
committed first (`859958b9`). Ollama stopped, card at 0 MiB before the first run. All measured llama-bench
output resolved to build `5266f24`, 4 threads; flash attention `1` on the 35B configs and `-1` (auto) on the 14B.
Raw per-invocation JSON in `raw-*.json`, priming runs in `raw-prime-*.json`, summaries in `results.json`.

### Per figure, by the pre-registered rule

| row | figure | published (July, b10088) | re-measured (v0.4.0, mean of 3 [min..max]) | delta | rule |
|---|---|---:|---:|---:|---|
| `...-ncmoe32-d0` | tg128 | 31.8 | 32.37 [31.96..32.58] | +1.8% | **keep** |
| `...-ncmoe20-d0` | tg128 | 42.6 | **does not load**: `failed to create context`, 3 of 3 measured + 3 of 3 priming invocations, weights resident at 11,417 MiB peak | — | **replace** |
| `...-ncmoe24-d0` | pp512 | 413 | 415.85 [413.84..417.46] | +0.7% | **keep** |
| `...-ncmoe24-d4096` | pp512 | 394 | 395.84 [394.56..397.12] | +0.5% | **keep** |
| `...-ncmoe24-d8192` | tg128 | 38.2 | 37.79 [37.47..38.07] | −1.1% | **keep** |
| `...-ncmoe24-d8192` | pp512 | 386 | 387.88 [386.28..389.47] | +0.5% | **keep** |
| `rushuna-qwen3-14b-q4km-ngl41` | tg128 | 35.9 | 35.99 [35.98..36.00] | +0.3% | **keep** |
| `rushuna-qwen3-14b-q4km-half-ram` | tg128 | 5.7 | 5.70 [5.70..5.71] (`-ngl 20`) | 0.0% | **keep** |
| `rushuna-qwen3-14b-q4km-all-ram` | tg128 | 3.05 | 3.03 [3.02..3.03] | −0.7% | **keep** |

Nine of ten figures reproduce within 1.8%, on a different build. The `-ngl 20` reading of "half in RAM"
lands on the July figure exactly. By-products, not rows under test: `-ncmoe 24` tg128 at d=0 38.70 (July 38.9,
09-11 38.55) and at d=4096 38.36 (July 38.5); 14B pp512 1,170 / 579 / 392 at `-ngl 41 / 20 / 0`.

VRAM, stated and not ruled on (peak `memory.used` across the invocation, which includes the pp512 and
deepest-depth tests): `-ncmoe 32` 6,481 MiB against the published 6.1 GB; `-ncmoe 24` 10,351 MiB with d=8192
in the same invocation against 9.8 GB at d=0; 14B 8,693 / 4,721 / 1,217 MiB.

### The `-ncmoe 20` claim

The published sentence: fastest config that loads, 42.6 tok/s at 11.7 GB, "threw an out-of-memory error the
moment we fed it real context". Tested as registered:

| config | loads? | serves a context-filling request? | detail |
|---|---|---|---|
| `-ncmoe 20 -c 8192` | **no** | no | weights and buffers allocate, then `CUDA error: out of memory` in the first graph compute (warm-up); server aborts (exit −6); peak 11,841 of 11,909 MiB |
| `-ncmoe 20 -c 16384` | **no** | no | `cudaMalloc failed: out of memory` allocating 269 MiB at context creation; exit 1 |
| `-ncmoe 24 -c 8192` (control) | yes, 10,075 MiB | **yes**: 7,936-token prompt at 357 tok/s, 128 tokens at 36.98 tok/s | peak 10,099 MiB |
| `-ncmoe 24 -c 16384` (control) | yes, 10,243 MiB | **yes**: 16,128-token prompt at 353 tok/s, 128 tokens at 35.83 tok/s | peak 10,267 MiB |

So the claim's practical advice holds and its premise does not: `-ncmoe 20` is not "the fastest that loads" on
this card today. It does not load at all, in llama-bench (default n_ctx = 640) or the server. `-ncmoe 24`
"holds steady under load" is confirmed: 16K of real context served, decode down 3% from an empty context.

**Diagnostic outside the pre-registration: the July build.** Because v0.4.0 could not reproduce the figure at
all, the same llama-bench command was run on the July bundle still on Rushuna (`~/llama-bench`, b10088
`67b9b0e`), block 3, n=3 (`diag-b10088/`). It also fails: `failed to create context` in all six invocations,
peak 11,417 MiB. The same bundle runs `-ncmoe 24` (37.0 tok/s, tg16 smoke check), so the build works. What
differs from July is not established here; the NVIDIA driver moved from 580.159.03 to 580.173.02 in between,
and a larger driver reservation would be enough to push an 11.7 GB config over a 11,909 MiB card, but that was
not tested. The 42.6 figure cannot be reproduced on this card with either build, and the row is replaced by
the failure under the pre-registered rule.

### Actions taken (same commit as this README)

- Nine figures kept; their rows point `raw_log` at this record and carry the file hashes. `rushuna-qwen3-14b-q4km-half-ram`
  gets `n_gpu_layers: 20` with the note that this is the re-measure's reading of the July description.
- `rushuna-qwen36-35b-a3b-udq4km-ncmoe20-d0` becomes `status: failed_to_create_context`, throughput and VRAM
  null, dated 2026-09-28, with the July figure recorded in its notes. Dated corrections on the two pages that
  publish 42.6: `best-way-run-qwen-3-6-35b-moe-locally` (sweep table and the sentence under it) and `/benchmarks/`.
- Not in scope, found while locating publications: the 14B figure **28.5 tok/s at `-ngl 40`** (the off-by-one
  example) is published in `why-local-llm-slow` and `newsletter-2026-07-28` and has no record either. Listed for the maintainer, not measured here.
