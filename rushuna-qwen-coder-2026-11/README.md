# Rushuna (RTX 3060 12 GB): Qwen3-Coder-30B-A3B and Qwen3-Coder-Next, speed: 2026-11-09, re-runs 2026-11-10 and 2026-11-17

Pre-registration: `docs/candidates/qwen-coder-article-2026-11.md`, LOCKED 2026-11-08 in 918e33f8. The lock file's
sha256 is `caa23d8e5dc88956fe02ef4d6a26c4e027b719f383a20583efe4810fff829db7`, the same as in the lock commit, so it's
unchanged. This is the Rushuna half of P4 (speed) and P9 (record). HumanEval (P5) runs on Tamanna only.

**Times in the raw logs are UTC, Rushuna's clock.** The main run was 2026-11-09 19:48–21:46 UTC (11:48–13:46 PST).
The P4 re-runs were 2026-11-10 19:37–19:56 UTC (11:37–11:56 PST) and 2026-11-17 21:44–21:54 UTC (13:44–13:54 PST).

## Setup

- **Rig:** Rushuna. RTX 3060 12 GB, PCIe 3.0 x16; i7-7700 (4c/8t); 32 GB DDR4-2133; driver 580.173.02.
- **Build:** llama.cpp v0.4.0 `5266f24`, the CUDA 12.8 bundle in `~/llama-v0.4.0`, as pinned in P3.
  `llama-server --version`: `0.4.0-dev (build 1, commit 5266f24)`.
- **Files:** working copies in `~/bench-models/qwen-coder/`. Hashed on arrival (`working-copies.SHA256SUMS`) and
  re-hashed 2026-11-10. Both matched the P2 LFS oids:

  | File | Bytes | sha256 |
  |---|---:|---|
  | Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf (unsloth @ b17cb02d) | 17,665,334,432 | `2841aa314d916434860cfb8990347528dcdfe5c350dbcb9d1461dbee88ff2533` |
  | Qwen3-Coder-Next-UD-IQ3_XXS.gguf (unsloth @ ce09c67b) | 28,482,506,752 | `00a9bf4f9dcb6ef4fb78ef810e6b5dbd13cc604ceb0fa10f56c9ae2529c0ade4` |

- **Harness:** `bench_qc.py`, the same file in both model directories (sha256 `5ecf62b7…`). It's derived from
  `rushuna-strata-coder-2026-10-05/bench_coder.py`, and its header lists the changes the lock names.
  `memwatch.py` is unchanged (`8525f345…`). `run_all.sh` ran per model: prep (day-0 load check + prompt re-cut),
  sweep, stage, L1, L2.
- **Re-run harness:** `codernext/rerun_qc.py` plus `rerun_codernext.sh`, added 2026-11-10. They import
  `bench_qc.py` unchanged and call its own `llama_cmd` / `run_cells` for the named cells only. So the build, flags,
  prompts, reps and per-request recording are identical. Output: `rerun-L1.json`, `rerun-L2.json`, `out-rerun-*.txt`,
  `memwatch-*-rerun-*`.
- **A1 re-run harness (2026-11-17):** `rerun_a1_qc.py` (in both model directories) plus `rerun_a1.sh`. It's
  `rerun_qc.py` with the output names tagged `a1` (`rerun-a1-L2.json`, `server-rerun-a1-L2.log`,
  `out-rerun-a1-L2.txt`, `memwatch-*-rerun-a1-L2*`), so the 11-10 files stay as they were. It still imports
  `bench_qc.py` unchanged (`5ecf62b7…` in both directories on 11-17). Before the runs, the Coder-30B file
  passed `sha256sum -c` against its `SHA256SUMS`. That file only lists Coder-30B, so the Coder-Next file was hashed
  after the runs (hashing it during them would have put 28 GB of NVMe reads into the measured requests). It
  matched `00a9bf4f…`.
- **Server arms** (P4), at the stage N:
  - L1: `llama-server -ngl 99 -ncmoe N -fa on -c 34816 -np 1 --lazy-mode on -t 4`.
  - L2: the same plus `-b 4096 -ub 4096`.
  - Temperature 0, `max_tokens 256`, (prime, measured) × 3 per cell.
- **Sweep:** `llama-bench -ngl 99 -ncmoe N -fa 1 -p 0 -n 128 -d 0,4096 -r 3 -t 4 -lm mmap`. N goes 48 and down by 4,
  then the even N between the last fit and the first failure.
- **Prompts:** re-cut from `corpus.txt` (sha256 `09a0975d…`, as locked) with each model's tokenizer through
  `/tokenize`. Both Coders share Qwen3's tokenizer, and the cuts came out byte-identical for both models:

  | Prompt | sha256 |
  |---|---|
  | 4,096 | `e9ccc20f195a604fafcb4f6297adf114e31f609f726a958f0025cc11b71e8d9f` |
  | 16,384 | `caa6e070fbadc52c8bcbcdf3d82d874292949d8633c8a8572df2940bec66a5cd` |
  | 32,512 | `ffe8e0e8f3f24a7a6f34f6943d50ebcc81c553dbee83f9bf8856905aadd245ae` |

  These are equal token counts from the same source text as the Flash-Next Coder rows, but not the same byte strings.

## Day-0 load check (P3)

Both files loaded on v0.4.0 and completed `def fibonacci(n):` (`*/day0.json`). No errors.

## Result: decode, with the re-runs in place of the void cells

| Model, N | Arm | Decode 4K / 16K / 32K, tok/s | Prefill 4K / 16K / 32K, tok/s |
|---|---|---|---|
| Coder-30B-A3B UD-Q4_K_XL, `-ncmoe 30` | L1 | 28.8 / 26.2 / 23.3 | 397 / 384 / 354 |
| | L2 | 28.7 / 26.1* / 23.3* | 1,394 / 1,259* / 1,025* |
| Coder-Next UD-IQ3_XXS, `-ncmoe 34` | L1 | 20.8 / void‡ / 19.9 | 228 / void‡ / 228 |
| | L2 | void‡ / 20.4* / 19.9* | void‡ / 766* / 761* |

\* = re-run cell (P4): Coder-Next L2-16K and L2-32K on 11-10, Coder-30B L2-16K and L2-32K on 11-17. ‡ = void
twice, not reported: Coder-Next L1-16K (re-run 20.4 / 231) and Coder-Next L2-4K (re-run 20.7 / 694). See "The
prompt_n rule" and "P4 re-runs (2026-11-17)" below.

Means of the 3 measured requests. The per-cell min..max is in the tables below.

- **The fit search and the sweep give different N, as P4 expected.** Coder-30B: the sweep's lowest N is 18 at
  d=4096, the server's N is 30 at 34,816 context. Coder-Next: 30 and 34.
- **PCIe was gen 3 x16 during every prefill of every request,** primes included.
- **The memory floor never tripped.** The lowest MemAvailable was 21,577 MiB.

## P4 re-runs (2026-11-10): one each, verdicts as written

Three Coder-Next cells had swap-out > 0 on a measured request in the 11-09 run, so each was void and re-run once. The
re-run replaces the original. There's no second re-run.

| Cell | 11-09 measured swap-out KiB | 11-09 NVMe MiB | Re-run swap-out KiB | Re-run NVMe MiB | Re-run verdict |
|---|---|---|---|---|---|
| L1-16K | 1,136 / 0 / 0 | 2.5 / 1.9 / 1.8 | 0 / 0 / 0 | 18.4 / 6.9 / 6.8 | ~~pass~~ **VOID** (2026-11-17: prompt_n 16,408..16,412, spread 4; void twice, see below) |
| L2-16K | 0 / 0 / 332 | 0.0 / 0.0 / 77.3 (over the 64 MiB flag) | 0 / 0 / 0 | 0.0 / 0.0 / 0.1 | **pass** |
| L2-32K | 360 / 0 / 0 | 41.3 / 1.6 / 0.5 | 0 / 0 / 0 | 0.0 / 0.0 / 0.0 | **pass** |

- **Re-run speeds match the void cells.** L1-16K: 20.4 against 20.4 tok/s. L2-16K: 20.4 against 20.4. L2-32K: 19.9
  against 19.9. The small swap-outs didn't move the figures.
- **The swapping isn't explained.** The likely cause is a 28.5 GB file on a 32 GB box. On 11-09, swap-out also
  appeared during the Coder-Next model load (prep: 304,072 KiB) and in the L1/L2 primes. On 11-10 the box started
  idle and nothing swapped out. That's a guess, not a diagnosis.

## The prompt_n rule: two readings, decided 2026-11-17 (stricter)

P4 says "prompt_n within ±3 tokens of the cell's other requests". There are two ways to read it:

- **±3 around the cell's centre.** That's the reading the Tamanna Strata record used when it passed cells spanning
  4,123–4,127 ("No cell is void"). It's applied here, by `summarize.py`.
- **Every pair within 3.** Under that reading, the four cells below have a 4-token spread across their 6 requests
  and would be void:
  - Coder-30B L2-16K (16,408..16,412) and L2-32K (32,536..32,540);
  - Coder-Next L2-4K (4,120..4,124);
  - the Coder-Next L1-16K **re-run** (16,408..16,412). It would then be void twice, so reported as void.

The spread comes from the per-request nonce line, which tokenizes to a slightly different length each time. It's not
a cache effect: cache_n was 0 everywhere. None of these cells was re-run for it.

**Decided 2026-11-17 (Mark): the stricter reading, every pair within 3 across the cell's 6 requests.** Recorded as
amendment A1 in the pre-registration. Verdicts under it:

| Cell | prompt_n, 6 requests | Verdict |
|---|---|---|
| Coder-Next L1-16K **re-run** | 16,408..16,412 | **VOID.** Void twice (swap-out on 11-09, prompt_n on the 11-10 re-run), so reported as void, no further re-run (Mark). Its figures (20.4 decode, 231 prefill) stay in the raw files but aren't reported as a measured cell |
| Coder-30B L2-16K | 16,408..16,412 | **VOID** (first time) |
| Coder-30B L2-32K | 32,536..32,540 | **VOID** (first time) |
| Coder-Next L2-4K | 4,120..4,124 | **VOID** (first time) |

- **The three first-time voids were re-run once each on 2026-11-17 (Mark).** Results in the next section.
- Every other Rushuna cell passes under the stricter reading. Since 2026-11-17 `summarize.py` applies A1, so these
  cells print as VOID there.

## P4 re-runs (2026-11-17): the three cells A1 voided, one each, verdicts as written

| Cell | prompt_n, 6 requests | Measured swap-out KiB | Measured NVMe MiB | Decode / prefill, tok/s (void original) | Verdict |
|---|---|---|---|---|---|
| Coder-30B L2-16K | 16,410..16,412 | 0 / 0 / 0 | 0.0 / 15.3 / 16.0 | 26.1 / 1,259 (26.1 / 1,272) | **pass**, replaces the original |
| Coder-30B L2-32K | 32,537..32,540 | 0 / 0 / 0 | 0.0 / 0.7 / 0.0 | 23.3 / 1,025 (23.3 / 1,027) | **pass**, replaces the original |
| Coder-Next L2-4K | 4,122..4,124 | **180 / 84 / 0** | 15.8 / 14.4 / 2.5 | 20.7 / 694 (20.8 / 697) | **VOID** (swap-out). Void twice, reported as void; no further re-run |

- **The Coder-Next L2-4K re-run passed the prompt_n rule but swapped out** on two of its three measured requests.
  P4 voids a cell for any swap-out on a measured request, so it is void twice.
- **The run order probably caused it.** `rerun_a1.sh` ran Coder-Next straight after Coder-30B. When the Coder-Next
  server came up, the page cache held 30,220 MiB, mostly the 17.7 GB Coder-30B file, and 106 MiB of swap was already
  in use. Loading the 28.5 GB Coder-Next file swapped out 44,240 KiB, and the swap-out carried into the first
  requests. On 11-10, Coder-Next re-ran on an idle box and nothing swapped out. That fits the guess under
  "P4 re-runs (2026-11-10)", but it's still not a diagnosis. Dropping the page cache needs sudo, which Rushuna
  doesn't have. The lowest MemAvailable was 28,034 MiB, so the floor wasn't close to tripping.
- **The figures didn't move.** Every re-run speed is within 1% of its void original.
- **Observation only (Mark, 2026-11-17), no rule change:** under A1 the prompt_n spread comes from the harness's
  per-request nonce. `bench_qc.py` opens each request with `request <8 random hex digits>`, and that string
  tokenizes to a varying number of tokens. Whether a cell's 6 requests land within 3 tokens is partly chance. The
  measurement itself is unaffected (cache_n is 0 everywhere). The rule was applied as written, and void twice is
  reported as void.

## P6 predictions, hit or miss (Rushuna's rows)

| Prediction | Band | Measured | |
|---|---|---|---|
| Coder-30B N | 26–36 | 30 | hit |
| Coder-Next UD-IQ3_XXS N | 28–40 | 34 | hit |
| Coder-30B decode 4K / 16K / 32K | 28–45 / 22–40 / 17–35 | 28.8 / 26.2 / 23.3 | hit (4K at the bottom edge) |
| **Coder-Next decode 4K / 16K / 32K** | **7–15 / 7–14 / 6–14** | **20.8 / 20.4 / 19.9** | **MISS: above the band at every length** |
| Coder-30B L2 / L1 prefill 4K, 32K | 800–1,800, 600–1,600 / 200–450 | 1,394, 1,025 / 397, 354 | hit |
| Coder-Next L2 / L1 prefill 4K, 32K | 300–900 / 80–250 | void (L2-4K void twice), 761 / 228, 228 | hit on the three measured cells; L2-4K not judged |
| S-a: Coder-Next 32K decode ≥ 85% of 4K | ≥ 85% | 96% (L1; L2-4K is void) | hit |
| S-c: L2 prefill ≥ 1.5× L1, offloaded | ≥ 1.5× | Coder-30B 3.5× / 2.9×; Coder-Next — / 3.3× (4K / 32K; L2-4K void) | hit |
| S-d: sweep monotonic | monotonic | both monotonic | hit |
| **S-d: tg128 d=0 at N = 48, Coder-30B** | **22–32** | **20.86** | **MISS: below** |
| **S-d: tg128 d=0 at N = 48, Coder-Next** | **6–12** | **16.59** | **MISS: above** |

- **Coder-Next on the 3060 is a miss against the pre-registration.** It decodes at about 20 tok/s, well above the
  7–15 band. The pre-registration doesn't say how the band was derived. Its 30–40 GB file size is close to the
  Flash-Next IQ1_M's, which decodes at 9.1 tok/s at `-ncmoe 44` under llama.cpp on this box. If that comparison set
  the band, it didn't carry over.
- S-b (Coder-30B decode falls with depth) is a Tamanna prediction. For context only: Rushuna's offloaded Coder-30B
  falls to 81% of its 4K speed at 32K.

## Per-cell tables (from `summarize.py`, A1 applied), with swap-out and NVMe for every measured request

### coder30b

Sweep (llama-bench, -ncmoe N): lowest fitting N = 18, first failure 16. Server stage search (L2, -c 34816, 32,512-token request): N = 30.

| -ncmoe N | tg128 d=0, tok/s | tg128 d=4096, tok/s | peak VRAM MiB |
|---:|---:|---:|---:|
| 48 | 20.86 | 20.35 | 1681 |
| 44 | 22.40 | 21.78 | 3071 |
| 40 | 24.41 | 23.67 | 4439 |
| 36 | 26.52 | 25.66 | 5759 |
| 32 | 28.95 | 27.94 | 7057 |
| 28 | 31.76 | 30.51 | 8375 |
| 24 | 35.57 | 34.09 | 9671 |
| 20 | 40.27 | 38.54 | 10993 |
| 18 | 42.96 | 41.04 | 11641 |

| Arm | Prompt | Decode tok/s, mean (min..max) | Prefill tok/s | Swap-out KiB, measured reps | NVMe MiB, measured reps | PCIe | P4 |
|---|---:|---:|---:|---|---|---|---|
| L1 | 4,096 | 28.8 (28.8..28.9) | 396.7 (396.1..397.5) | 0 / 0 / 0 | 0.0 / 0.0 / 0.0 | gen 3 x16 | pass |
| L1 | 16,384 | 26.2 (26.1..26.2) | 383.9 (383.8..384.1) | 0 / 0 / 0 | 0.0 / 0.0 / 0.0 | gen 3 x16 | pass |
| L1 | 32,512 | 23.3 (23.3..23.3) | 354.3 (354.1..354.7) | 0 / 0 / 0 | 0.0 / 0.0 / 0.0 | gen 3 x16 | pass |
| L2 | 4,096 | 28.7 (28.3..28.8) | 1394.2 (1390.0..1397.8) | 0 / 0 / 0 | 0.0 / 0.0 / 0.0 | gen 3 x16 | pass |
| L2 | 16,384 | 26.1 (26.1..26.1) | 1272.3 (1269.7..1273.7) | 0 / 0 / 0 | 0.0 / 0.0 / 0.0 | gen 3 x16 | VOID: prompt_n spread 4 (16408..16412) |
| L2 **re-run** 11-17 (A1) | 16,384 | 26.1 (26.0..26.1) | 1258.6 (1247.7..1266.6) | 0 / 0 / 0 | 0.0 / 15.3 / 16.0 | gen 3 x16 | pass |
| L2 | 32,512 | 23.3 (23.3..23.3) | 1027.0 (1026.7..1027.3) | 0 / 0 / 0 | 0.0 / 0.0 / 0.0 | gen 3 x16 | VOID: prompt_n spread 4 (32536..32540) |
| L2 **re-run** 11-17 (A1) | 32,512 | 23.3 (23.3..23.3) | 1024.9 (1024.4..1025.6) | 0 / 0 / 0 | 0.0 / 0.7 / 0.0 | gen 3 x16 | pass |

### codernext

Sweep (llama-bench, -ncmoe N): lowest fitting N = 30, first failure 28. Server stage search (L2, -c 34816, 32,512-token request): N = 34.

| -ncmoe N | tg128 d=0, tok/s | tg128 d=4096, tok/s | peak VRAM MiB |
|---:|---:|---:|---:|
| 48 | 16.59 | 16.61 | 2459 |
| 44 | 17.70 | 17.59 | 4513 |
| 40 | 18.81 | 18.86 | 6611 |
| 36 | 20.25 | 20.20 | 8703 |
| 32 | 21.93 | 21.82 | 10801 |
| 30 | 22.76 | 22.62 | 11849 |

| Arm | Prompt | Decode tok/s, mean (min..max) | Prefill tok/s | Swap-out KiB, measured reps | NVMe MiB, measured reps | PCIe | P4 |
|---|---:|---:|---:|---|---|---|---|
| L1 | 4,096 | 20.8 (20.8..20.8) | 228.0 (227.8..228.3) | 0 / 0 / 0 | 0.0 / 0.1 / 0.0 | gen 3 x16 | pass |
| L1 | 16,384 | 20.4 (20.3..20.4) | 230.9 (230.7..231.1) | 1136 / 0 / 0 | 2.5 / 1.9 / 1.8 | gen 3 x16 | VOID: swap-out 1136/0/0 KiB |
| L1 **re-run** 11-10 | 16,384 | 20.4 (20.4..20.5) | 231.4 (230.0..232.2) | 0 / 0 / 0 | 18.4 / 6.9 / 6.8 | gen 3 x16 | VOID: prompt_n spread 4 (16408..16412) |
| L1 | 32,512 | 19.9 (19.9..20.0) | 228.4 (228.2..228.6) | 0 / 0 / 0 | 0.7 / 0.1 / 0.3 | gen 3 x16 | pass |
| L2 | 4,096 | 20.8 (20.8..20.8) | 696.6 (694.7..698.1) | 0 / 0 / 0 | 0.1 / 0.0 / 0.0 | gen 3 x16 | VOID: prompt_n spread 4 (4120..4124) |
| L2 **re-run** 11-17 (A1) | 4,096 | 20.7 (20.6..20.7) | 693.5 (691.3..696.8) | 180 / 84 / 0 | 15.8 / 14.4 / 2.5 | gen 3 x16 | VOID: swap-out 180/84/0 KiB |
| L2 | 16,384 | 20.4 (20.3..20.4) | 755.3 (734.5..766.4) | 0 / 0 / 332 | 0.0 / 0.0 / 77.3 | gen 3 x16 | VOID: swap-out 0/0/332 KiB |
| L2 **re-run** 11-10 | 16,384 | 20.4 (20.2..20.4) | 765.9 (764.6..767.0) | 0 / 0 / 0 | 0.0 / 0.0 / 0.1 | gen 3 x16 | pass |
| L2 | 32,512 | 19.9 (19.9..19.9) | 759.4 (759.0..759.6) | 360 / 0 / 0 | 41.3 / 1.6 / 0.5 | gen 3 x16 | VOID: swap-out 360/0/0 KiB |
| L2 **re-run** 11-10 | 32,512 | 19.9 (19.9..19.9) | 760.6 (760.4..761.0) | 0 / 0 / 0 | 0.0 / 0.0 / 0.0 | gen 3 x16 | pass |

## Files

- `run_all.sh`, `sequence.log`: the 11-09 sequence and the 11-10 and 11-17 re-run lines.
- `rerun_codernext.sh`, `rerun.out`: the 11-10 re-runs.
- `rerun_a1.sh`, `rerun_a1.out`, `<model>/rerun_a1_qc.py`: the 11-17 re-runs.
- `<model>/`:
  - `out-*.txt`, `run.log`: the harness logs;
  - `results-L1.json`, `results-L2.json`, `rerun-L*.json`, `rerun-a1-L2.json`: per request, the timings plus swap, NVMe, PCIe, memory
    and process status;
  - `sweep.json`, `stage.json`, `day0.json`, `prompts.json`, `prompt-*.txt`;
  - `server-*.log`: the full llama-server output;
  - `memwatch-*.log`, `memwatch-summary-*.json`.
- `working-copies.SHA256SUMS`: the arrival hashes.

Not yet done (P9): benchmarks.json rows. They'll be added with the Tamanna record.
