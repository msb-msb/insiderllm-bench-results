# Tamanna (RTX 3090 24 GB): Qwen3-Coder-30B-A3B and Qwen3-Coder-Next, speed 2026-11-10 (re-runs 2026-11-17), HumanEval 2026-11-17

Pre-registration: `docs/candidates/qwen-coder-article-2026-11.md`, LOCKED 2026-11-08 in 918e33f8, with amendment
A1 (2026-11-17: the stricter prompt_n reading). This is the Tamanna half of P4 (speed), all of P5 (HumanEval) and P9. HumanEval is below, under
"HumanEval (P5)". The locked scores are the primary result. A post-hoc failure audit (deviation D1) is in
`audit-exploratory/`, labelled there and below as exploratory.

**Times in the raw logs are UTC, Tamanna's clock.** The main run was 2026-11-10 19:54–20:42 UTC (11:54–12:42 PST).
The P4 re-runs were 2026-11-17 18:55–19:00 UTC (10:55–11:00 PST).

## Setup

- **Rig:** Tamanna. RTX 3090 24 GB, PCIe 4.0 x16; Ryzen 7 5700X; 64 GB DDR4-3000 (4 x 16 GB, 1.35 V); driver
  580.178.04. **Every row here is DDR4-3000.** Set beside Rushuna's (DDR4-2133), the RAM speed is a confound on the
  offloaded Coder-Next rows; it doesn't touch the resident Coder-30B rows.
- **Build:** llama.cpp v0.4.0 `5266f24`, the source build in `~/llama-v0.4.0/build/bin`, as pinned in P3.
  `llama-server --version`: `0.4.0-dev (build 1, commit 5266f24)`. `llama-server` sha256 `d0b44631…`,
  `libggml-cuda.so.0.23.0` `3b086837…`.
- **Files:** working copies in `~/bench-models/qwen-coder/`, rsynced from LLM_repo. `working-copies.SHA256SUMS` holds
  the P2 LFS oids. All 6 files matched just before load and again after the run on 11-10 (`sha256-before-load.txt`,
  `sha256-after.txt`). The Coder-30B file matched again before and after each 11-17 re-run (`sha256-*-rerun*.txt`).

  | File | Bytes | sha256 |
  |---|---:|---|
  | Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf (unsloth @ b17cb02d) | 17,665,334,432 | `2841aa314d916434860cfb8990347528dcdfe5c350dbcb9d1461dbee88ff2533` |
  | Qwen3-Coder-Next-Q4_K_M, 4 shards (Qwen @ b82fb738) | 48,411,092,032 | `6bcfc9f9…`, `817def06…`, `23aa634d…`, `249c768c…` |
  | Qwen3-Coder-Next-UD-IQ3_XXS.gguf (unsloth @ ce09c67b), day-0 check only here | 28,482,506,752 | `00a9bf4f9dcb6ef4fb78ef810e6b5dbd13cc604ceb0fa10f56c9ae2529c0ade4` |

- **Harness:** `bench_qc.py`, the same file in all three model directories (sha256 `f833deeb…`). It's the Tamanna copy
  of Rushuna's (`5ecf62b7…`) with the changes P4 names, listed in its header: the source-build path, `-t 8`, the model
  by run directory, and the stage search (48 → 0 for Coder-Next, up from 0 for Coder-30B). No sweep on Tamanna.
  `memwatch.py` is unchanged (`8525f345…`). `run_all.sh` ran: sha256, prep (day-0 load check + prompt re-cut) for all
  three files, then stage, L1, L2 for each model.
- **Re-run harness:** `coder30b/rerun_qc.py`, byte-identical to Rushuna's (`786b51e0…`). It imports `bench_qc.py`
  unchanged and runs only the named cells. Driven by `rerun_coder30b.sh` (L1-16K, L1-32K) and `rerun_coder30b_L2.sh`
  (L2-16K), both under memwatch as `run_all.sh`. Output: `rerun-L*.json`, `out-rerun-*.txt`, `memwatch-*rerun*`.
- **Server arms** (P4), at the stage N:
  - L1: `llama-server -ngl 99 -ncmoe N -fa on -c 34816 -np 1 --lazy-mode on -t 8`.
  - L2: the same plus `-b 4096 -ub 4096`.
  - Temperature 0, `max_tokens 256`, (prime, measured) × 3 per cell.
- **Prompts:** re-cut from `corpus.txt` (sha256 `09a0975d…`) with each model's tokenizer via `/tokenize`. All three
  files cut byte-identical prompts, and they're the same bytes as Rushuna's:

  | Prompt | sha256 |
  |---|---|
  | 4,096 | `e9ccc20f195a604fafcb4f6297adf114e31f609f726a958f0025cc11b71e8d9f` |
  | 16,384 | `caa6e070fbadc52c8bcbcdf3d82d874292949d8633c8a8572df2940bec66a5cd` |
  | 32,512 | `ffe8e0e8f3f24a7a6f34f6943d50ebcc81c553dbee83f9bf8856905aadd245ae` |

## Day-0 load check (P3)

All three files loaded on v0.4.0 and completed `def fibonacci(n):` (`*/day0.json`), including the qwen3next
architecture in both Coder-Next files. No errors.

## Result: speed, with the re-runs in place of the void cells

| Model, N | Arm | Decode 4K / 16K / 32K, tok/s | Prefill 4K / 16K / 32K, tok/s |
|---|---|---|---|
| Coder-30B-A3B UD-Q4_K_XL, `-ncmoe 0` (fully on the card) | L1 | 190.1 / 149.9* / 117.7* | 4,009 / 3,205* / 2,473* |
| | L2 | 190.1 / 149.9* / 117.7 | 6,923 / 5,125* / 3,723 |
| Coder-Next Q4_K_M, `-ncmoe 28` | L1 | 48.0 / 47.0 / 46.0 | 314 / 313 / 308 |
| | L2 | 48.0 / 47.1 / 46.0 | 1,253 / 1,318 / 1,308 |

\* = re-run cell (P4), 2026-11-17. Means of the 3 measured requests; per-cell min..max below. No cell is void after
the re-runs.

- **Stage search:** Coder-30B serves a 32,512-token request at L2 with N = 0. Coder-Next: N = 28 loads and serves,
  26 fails to load (`codernext/stage.json`).
- **PCIe was gen 4 x16 during every prefill of every request,** primes included.
- **The memory floor never tripped.**
- **Re-run speeds match the void cells** to within 0.1 tok/s decode and 0.8% prefill.

## P4 voids and re-runs

| Cell | Why void (11-10) | Re-run 11-17 | Verdict |
|---|---|---|---|
| Coder-30B L1-16K | swap-out 32 / 11,672 / 36 KiB on the measured requests | swap-out 0 / 0 / 0; prompt_n 16,408..16,410 | **pass** |
| Coder-30B L1-32K | swap-out 20 / 0 / 0 KiB | swap-out 0 / 0 / 0; prompt_n 32,538..32,540 | **pass** |
| Coder-30B L2-16K | prompt_n 16,408..16,412, spread 4: void under A1, the stricter reading | prompt_n 16,410..16,412; swap-out 0 | **pass** |

- The L2-16K re-run follows from A1. The 11-10 run passed it under the old centre reading. Mark asked for the two L1
  re-runs on 11-17; this third one is P4's rule applied to A1, on the same day and box.
- **Two outside events overlapped the L1 re-run**, both tiny. At about 10:57 PST an rsync from Miu read this run's
  directory (a few MB of small files), and a 20-second `python3 -m http.server` on port 8099, bound to the LAN
  address, checked that Miu could reach it for HumanEval. The worst measured NVMe read in the re-runs is 16.7 MiB, under
  the 64 MiB flag. No figure moved.
- Every other cell passes under A1. No prompt_n spread is over 3.

## P6 predictions, hit or miss (Tamanna's rows)

| Prediction | Band | Measured | |
|---|---|---|---|
| Coder-30B N | ≤ 2 (predicted 0) | 0 | hit |
| Coder-Next Q4_K_M N | 26–34 | 28 | hit |
| **Coder-30B decode 4K** / 16K / 32K | **120–175** / 90–150 / 65–125 | **190.1** / 149.9 / 117.7 | **MISS at 4K: above**; 16K, 32K hit (16K at the top edge) |
| **Coder-30B L2 prefill 4K / 32K** | **2,500–4,500 / 1,400–3,300** | **6,923 / 3,723** | **MISS: above at both** |
| **Coder-30B L1 prefill 4K** / 32K | **2,000–4,000** / 1,000–2,800 | **4,009** / 2,473 | **MISS at 4K: above, by 9 tok/s**; 32K hit |
| **Coder-Next decode 4K / 16K / 32K** | **22–40 / 20–38 / 18–36** | **48.0 / 47.0 / 46.0** | **MISS: above at every length** |
| Coder-Next L2 prefill 4K / 32K | 700–1,600 / 700–1,700 | 1,253 / 1,308 | hit |
| Coder-Next L1 prefill 4K / 32K | 250–520 / 250–520 | 314 / 308 | hit |
| S-a: Coder-Next 32K decode ≥ 85% of 4K | ≥ 85% | 96% (L1 and L2) | hit |
| S-b: Coder-30B 32K decode ≤ 80% of 4K | ≤ 80% | 62% | hit |
| S-c: L2 prefill ≥ 1.5× L1, offloaded (Coder-Next) | ≥ 1.5× | 4.0× / 4.2× (4K / 32K) | hit |

- **Coder-Next is faster than predicted on both rigs.** Here it decodes at 46–48 tok/s against a 22–40 band; on
  Rushuna at about 20 against 7–15. Same direction, both misses.
- **The resident Coder-30B ran above its band at 4K, in decode and prefill.** Its depth falloff (S-b) came out as
  predicted.
- S-d (the 3060 sweep) is a Rushuna prediction.

## Per-cell tables (from `summarize.py`, A1 applied), with prompt_n, swap-out and NVMe for every cell

### coder30b

Server stage search (L2, -c 34816, 32,512-token request): N = 0.

| Arm | Prompt | Decode tok/s, mean (min..max) | Prefill tok/s | prompt_n, 6 requests | Swap-out KiB, measured reps | NVMe MiB, measured reps | PCIe | P4 |
|---|---:|---:|---:|---|---|---|---|---|
| L1 | 4,096 | 190.1 (189.9..190.3) | 4008.7 (4004.8..4015.8) | 4,120..4,123 | 0 / 0 / 0 | 2.1 / 0.0 / 0.0 | gen 4 x16 | pass |
| L1 | 16,384 | 149.8 (149.6..150.1) | 3181.7 (3179.6..3184.6) | 16,410..16,412 | 32 / 11672 / 36 | 0.0 / 0.3 / 0.0 | gen 4 x16 | VOID: swap-out 32/11672/36 KiB |
| L1 **re-run** | 16,384 | 149.9 (149.7..150.1) | 3204.7 (3192.3..3216.5) | 16,408..16,410 | 0 / 0 / 0 | 0.0 / 16.7 / 0.0 | gen 4 x16 | pass |
| L1 | 32,512 | 117.8 (117.7..117.8) | 2467.9 (2467.1..2468.6) | 32,537..32,540 | 20 / 0 / 0 | 0.0 / 0.2 / 0.0 | gen 4 x16 | VOID: swap-out 20/0/0 KiB |
| L1 **re-run** | 32,512 | 117.7 (117.6..117.8) | 2473.0 (2471.7..2474.8) | 32,538..32,540 | 0 / 0 / 0 | 0.0 / 4.3 / 0.0 | gen 4 x16 | pass |
| L2 | 4,096 | 190.1 (189.8..190.4) | 6923.0 (6919.8..6927.6) | 4,121..4,124 | 0 / 0 / 0 | 0.0 / 0.0 / 0.0 | gen 4 x16 | pass |
| L2 | 16,384 | 149.8 (149.6..150.0) | 5105.8 (5105.0..5107.0) | 16,408..16,412 | 0 / 0 / 0 | 0.0 / 0.0 / 0.0 | gen 4 x16 | VOID: prompt_n spread 4 (16408..16412) |
| L2 **re-run** | 16,384 | 149.9 (149.8..150.0) | 5125.4 (5117.4..5137.4) | 16,410..16,412 | 0 / 0 / 0 | 0.0 / 0.0 / 0.0 | gen 4 x16 | pass |
| L2 | 32,512 | 117.7 (117.4..117.9) | 3723.1 (3721.7..3724.2) | 32,538..32,540 | 0 / 0 / 0 | 0.0 / 0.2 / 0.0 | gen 4 x16 | pass |

### codernext

Server stage search (L2, -c 34816, 32,512-token request): N = 28.

| Arm | Prompt | Decode tok/s, mean (min..max) | Prefill tok/s | prompt_n, 6 requests | Swap-out KiB, measured reps | NVMe MiB, measured reps | PCIe | P4 |
|---|---:|---:|---:|---|---|---|---|---|
| L1 | 4,096 | 48.0 (47.9..48.0) | 314.0 (313.7..314.2) | 4,123..4,124 | 0 / 0 / 0 | 0.1 / 0.1 / 0.4 | gen 4 x16 | pass |
| L1 | 16,384 | 47.0 (47.0..47.1) | 312.7 (312.5..312.9) | 16,409..16,412 | 0 / 0 / 0 | 1.5 / 0.4 / 2.8 | gen 4 x16 | pass |
| L1 | 32,512 | 46.0 (46.0..46.0) | 308.0 (307.7..308.2) | 32,537..32,540 | 0 / 0 / 0 | 0.4 / 0.2 / 0.4 | gen 4 x16 | pass |
| L2 | 4,096 | 48.0 (48.0..48.0) | 1252.7 (1248.9..1255.9) | 4,122..4,124 | 0 / 0 / 0 | 0.0 / 0.1 / 0.0 | gen 4 x16 | pass |
| L2 | 16,384 | 47.1 (47.1..47.1) | 1318.3 (1318.2..1318.3) | 16,409..16,411 | 0 / 0 / 0 | 0.0 / 0.0 / 3.1 | gen 4 x16 | pass |
| L2 | 32,512 | 46.0 (46.0..46.0) | 1308.0 (1307.7..1308.4) | 32,539..32,540 | 0 / 0 / 0 | 0.0 / 0.1 / 0.0 | gen 4 x16 | pass |

The old centre reading isn't printed. Under it, the L2-16K original would have passed.

## HumanEval (P5): the locked result

**Primary result, scored exactly as locked: raw `/v1/completions`, no chat template, lm-eval's five stops, no code
extraction, the official `human-eval` in `he-scorer:b10088`.** Run 2026-11-17 19:17–19:52 UTC (11:17–11:52 PST) on
Tamanna (server) and Miu (generator and scorer).

| Slot | Arm | File (sha256, first 16) | -ncmoe | pass@1 | Band (P6) | |
|---|---|---|---:|---:|---|---|
| 1 | A36 | Qwen3.6-27B-UD-Q4_K_XL (`ff6941ded525b34e`) | — | **137/164 (83.54%)** | 132–138 | hit |
| 2 | A38 | Qwen3.8-27B-UD-Q4_K_XL (`bee238bbeb3dc0a3`) | — | **130/164 (79.27%)** | 129–135 | hit |
| 3 | C30 | Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL (`2841aa314d916434`) | — | **100/164 (60.98%)** | 123–144 (75–88%) | **MISS: below by 23 problems** |
| 4 | CN | Qwen3-Coder-Next-Q4_K_M, 4 shards (`6bcfc9f9…`, `817def06…`, `23aa634d…`, `249c768c…`) | 28 | **120/164 (73.17%)** | 131–153 (80–93%) | **MISS: below by 11** |
| 5 | CN3 | Qwen3-Coder-Next-UD-IQ3_XXS (`00a9bf4f9dcb6ef4`) | 8 | **113/164 (68.90%)** | 123–149 (75–91%) | **MISS: below by 10** |
| 6 | A36 again | as slot 1 | — | 137/164, byte-identical to slot 1 | must be identical | pass |

- **Server:** `llama-server -ngl 99 -fa on -c 4096 --no-jinja --no-mmap --host 192.168.x.x --port 8099`, plus
  `-ncmoe N` where shown. Engine: `llama-server` `d0b44631…`, `libggml-cuda.so.0.23.0` `3b086837…`, v0.4.0
  `5266f24`, driver 580.178.04 (`engine-identity.txt`).
- **CN uses the speed run's N (28).** CN3's N came from the search the lock specifies: -ncmoe 0, 2, 4 and 6 failed to
  load at `-c 4096`, and 8 loaded and answered (`cn3-search.json`).
- **Provenance:** every arm's file was hashed immediately before the server loaded it and again after its eval. All
  pre/post pairs match (`summary-*.json`), so no arm is void. The two 27B anchors were copied from LLM_repo on 11-17
  and matched upstream on arrival (`anchors-arrival.txt`).
- **Generator:** `he_gen.py` is the 08-16 file with one line changed, the URL (`he_gen.diff`), as P5 says.
  Driver: `he_run.py`.
- **Determinism check:** slot 6 (A36 again, after the other four arms) produced completions byte-identical to slot 1,
  for all 164 problems (`drift-check.json`, out_sha16 `fb4c378aba80b1f6` both times). Nothing drifted in between.

### Paired tests (exact McNemar, two-sided, the lock's pairs)

| Pair (X vs Y) | X pass@1 | Y pass@1 | only X passes | only Y passes | exact McNemar p | Under P6's write-up rule |
|---|---:|---:|---:|---:|---:|---|
| C30 vs A36 | 100/164 | 137/164 | 12 | 49 | 1.97e-06 | A36 measurably beats C30 |
| CN vs A36 | 120/164 | 137/164 | 7 | 24 | 0.00333 | A36 measurably beats CN |
| CN3 vs CN | 113/164 | 120/164 | 13 | 20 | 0.296 | statistical tie |
| A38 vs A36 | 130/164 | 137/164 | 11 | 18 | 0.265 | statistical tie |
| CN vs C30 | 120/164 | 100/164 | 42 | 22 | 0.0169 | CN measurably beats C30 |

From `humaneval/mcnemar.py`, which reads each `summary-<ARM>.json` per-problem vector.

### P6 HumanEval predictions, hit or miss

| Prediction | Result | |
|---|---|---|
| Anchors reproduce within ±3 problems (A36 132–138, A38 129–135) | 137, 130 | hit |
| C30 75–88% | 60.98% | **MISS: below** |
| C30 vs A36 not significant (p ≥ 0.05) | p = 1.97e-6, A36 ahead | **MISS** |
| CN 80–93% | 73.17% | **MISS: below** |
| CN's point estimate above A36, A38 and C30 | above C30 only | **MISS** |
| CN vs A36 not significant (p ≥ 0.05) | p = 0.0033, A36 ahead | **MISS** |
| CN3 75–91% | 68.90% | **MISS: below** |
| CN3 at or below CN, within 6 points | 4.27 points below | hit |
| CN3 vs CN not significant (p ≥ 0.05) | p = 0.296 | hit |

**Both Coders scored below their bands. Under the lock, both 27B general models beat both Coders on HumanEval.**
The audit below explains most of Coder-30B's gap as an output-format effect. It's post-hoc, so the result above
stands as the primary one, and a separate pre-registered test (MBPP, `docs/candidates/qwen-coder-mbpp-confirm-2026-11.md`)
checks the explanation.

### Run note: the first attempt hung (11-17 19:06–19:16 UTC)

The first `he_run.py` attempt stopped after A36's "sha256 before load OK". The server had started, but the ssh
command that launched it never returned. The launch line backgrounded the whole `mkdir && cd && llama-server` list
with `&`, so the ssh channel stayed open. The driver was killed, the server stopped, and the launch line was fixed
to background the server alone (braces, comment in `he_run.py`). The run then restarted from slot 1. A36 had
generated nothing in attempt 1 (`he_run.out.attempt1`, `server-logs/server-A36.attempt1.log`, `sequence.log`
11:16:53–11:16:59), so no completion from it exists or was discarded.

## Deviation D1 (2026-11-17): failure audit, POST-HOC and exploratory

**Decided after seeing the results. Not confirmatory. No score above is changed by it.** Full text in the
pre-registration under D1; files and method in `audit-exploratory/README.md`.

- **Every failure was classified** for C30 (64), CN (44) and A36 (27, the control):

  | Failure type | A36 | C30 | CN |
  |---|---:|---:|---:|
  | (a) wrong logic | 23 | 12 | 26 |
  | (b) format: closing ``` then prose; passes if cut there | 0 | 41 | 3 |
  | (b) format: ``` / prose, fails even if cut | 0 | 7 | 1 |
  | (b) format: non-code tokens after the body (`</file>`, `<reponame>`) | 0 | 0 | 4 |
  | (b) helper function cut off by the `\ndef` stop | 0 | 1 | 2 |
  | (c) truncated at 512 tokens | 0 | 3 | 3 |
  | (d) missing stdlib import, or timeout | 4 | 0 | 5 |
  | **Format (b) share** | **0%** | **77% (49/64)** | **23% (10/44)** |

- **The harness treats every arm the same.** No arm gets extraction, a chat template or thinking mode, and all get
  the same stops. The protocol penalises Coder-30B's habit of closing a code fence and then explaining its code.
- **Fence-cut counterfactual, post-hoc:** cut every completion at its first ``` (one rule for all arms), re-score in
  the same sandbox with the lock's flags:

  | Arm | Locked (primary) | Fence-cut (post-hoc) | Change |
  |---|---:|---:|---:|
  | A36 | 137/164 (83.54%) | 137/164 (83.54%) | +0 |
  | A38 | 130/164 (79.27%) | 130/164 (79.27%) | +0 |
  | C30 | 100/164 (60.98%) | 142/164 (86.59%) | +42 |
  | CN | 120/164 (73.17%) | 123/164 (75.00%) | +3 |
  | CN3 | 113/164 (68.90%) | 118/164 (71.95%) | +5 |

  Under the cut, C30 vs A36 is p = 0.458 (17 vs 12), a statistical tie, and CN vs C30 reverses (C30 ahead,
  p = 0.0034). C30's +42 is the 41 class-(b) items plus HumanEval/80, which hit 512 tokens but ended its code before a fence.

## Files

- `run_all.sh`, `sequence.log`: the 11-10 sequence, plus the 11-17 re-run lines.
- `rerun_coder30b.sh`, `rerun_coder30b_L2.sh`, `rerun.out`, `rerun-L2.out`: the 11-17 re-runs.
- `sha256-before-load.txt`, `sha256-after.txt`: all 6 files, 11-10. `sha256-before-rerun*.txt`,
  `sha256-after-rerun*.txt`: the Coder-30B file, 11-17.
- `working-copies.SHA256SUMS`: the P2 oids the copies were checked against.
- `<model>/`:
  - `day0.json`, `out-prep.txt`, `server-prep.log`: the day-0 load check and prompt cut;
  - `stage.json`, `out-stage.txt`, `server-stage-ncmoe*.log`: the stage search;
  - `results-L1.json`, `results-L2.json`, `rerun-L*.json`: per request, the timings plus swap, NVMe, PCIe, memory
    and process status;
  - `out-*.txt`, `run.log`, `server-*.log`: the harness and server logs;
  - `memwatch-*.log`, `memwatch-summary-*.json`: the memory watch;
  - `prompt-*.txt`, `prompts.json`, `corpus.txt`, `corpus-files.txt`: the prompts and their source.
- `codernext3/`: the UD-IQ3_XXS file's day-0 check only. It's the HumanEval arm CN3 here, not a speed arm.
- `summarize.py`: prints the speed tables above from the raw files.
- `humaneval/`: P5.
  - `he_run.py` (driver), `he_gen.py` + `he_gen.diff` (generator, URL change only), `chain.sh`, `chain.out`;
  - `sequence.log`, `he_run.out`, `he_run.out.attempt1`: the run log, including the attempt-1 hang;
  - `engine-identity.txt`, `anchors-arrival.txt`, `cn3-search.json`, `drift-check.json`;
  - `gen-<ARM>.json` / `.log`: the completions, with finish reasons and token counts;
  - `eval/he_<ARM>.jsonl` and `_results.jsonl`: what the scorer saw and its per-problem verdicts;
  - `summary-<ARM>.json`: pass@1, per-problem vector, flags, pre/post sha256; `scorer-<ARM>.txt`: scorer output;
  - `server-logs/`: Tamanna's llama-server logs for every arm and every CN3 search step;
  - `mcnemar.py`: the paired-test table.
- `audit-exploratory/`: deviation D1, post-hoc. See its README.
