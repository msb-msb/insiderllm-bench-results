# Qwen Coder: MBPP confirmatory test of the HumanEval format finding (pre-registration)

**LOCKED on commit.** Written 2026-11-17 before any MBPP generation. The sha256 of this file is recorded in the
lock commit message and in `qwen-coder-mbpp-confirm-2026-11.md.sha256` next to it. Anything added later is appended
after section M9 as a dated amendment or deviation. Nothing above M9 changes.

Parent: `qwen-coder-article-2026-11.md` (lock 918e33f8, A1, D1). D1 found, post-hoc, that 49 of Coder-30B's 64
HumanEval failures were format failures: a closing ``` and then a prose explanation after a function body. Cutting
every completion at its first ``` took C30 from 100 to 142/164, above A36's 137. The cut rule was chosen after
seeing those failures, so this test checks the finding on data the rule wasn't fitted to.

## M1. Question

Under raw-completion scoring, Coder-30B-A3B lost to both 27B general models on HumanEval. Does it keep losing on a
different benchmark once the trailing-prose effect is removed by a rule fixed in advance? And does the raw score
drop again by the same mechanism?

## M2. Benchmark, prompt, stops

- **MBPP, sanitized, test split: all 257 problems.** `datasets.load_dataset("mbpp", "sanitized", split="test",
  revision="4bb6404fdc6cacfda99d4ac4205087b89d32030c")`. Parquet `sanitized/test-00000-of-00001.parquet` sha256
  `e9e9efa2c0d59ef5e55537a9d126b8f875d5ac010a8d75628d76824884e15850`, cached on Miu. No problem is excluded.
- **Prompt:** bigcode-evaluation-harness's MBPP format with the sanitized field names:
  `'"""\n' + prompt + '\n' + test_list[0] + '\n"""\n'`. The model writes the function, signature included.
- **Stops:** bigcode's MBPP list without `"\n```"`: `\nclass`, `\nassert`, `\n"""`, `\nprint`, `\nif`, `\n<|/`.
  The fence stop is left out on purpose. With it, raw and cut scores would be identical and the test would test
  nothing. These stops differ from HumanEval's five because the benchmark's prompt shape differs. They're the same
  for every arm.
- **Sampling:** identical to P5's `he_gen.py`: temperature 0, top_p 1, top_k 0, min_p 0, typical_p 1, all
  penalties neutral, seed 42, `max_tokens 512`, raw `/v1/completions`.

## M3. Arms, models, builds, servers: as the HumanEval lock (P5)

- **Arms, in order:** A36 (Qwen3.6-27B-UD-Q4_K_XL), A38 (Qwen3.8-27B-UD-Q4_K_XL), C30
  (Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL), CN (Qwen3-Coder-Next Q4_K_M, `-ncmoe 28`), CN3
  (Qwen3-Coder-Next-UD-IQ3_XXS, `-ncmoe 8`), then A36 again as the drift check.
- **Files:** the same working copies on Tamanna (`~/bench-models/qwen-coder/`), with the sha256s in P2 and the
  HumanEval record.
- **CN3's N is fixed at 8.** That's what the HumanEval search found, and there's no new search. If CN3 doesn't load
  at N = 8, the arm is reported as failed and nothing else is tried without Mark.
- **Server:** `llama-server -ngl 99 -fa on -c 4096 --no-jinja --no-mmap --host 192.168.50.18 --port 8099`
  (+ `-ncmoe N`). v0.4.0 `5266f24` at `~/llama-v0.4.0/build/bin` on Tamanna. `llama-server` sha256 `d0b44631…`,
  `libggml-cuda.so.0.23.0` `3b086837…`, as in the HumanEval record. No chat template on any arm.
- **Generator on Miu, scorer on Miu:** the same split as P5.

## M4. Scoring (fixed now)

- **Sandbox:** `he-scorer:b10088` (image `sha256:2f6890e35e0c25f8342568816c2fb49222aa559870c39d308f5534d01d87cfef`).
  Same flags as P5: `--network none --cap-drop ALL --security-opt no-new-privileges --memory 4g --pids-limit 256`.
  `mbpp_score.py` runs inside it, through the official `human_eval.execution.check_correctness` (reliability guard,
  3.0 s per problem).
- **Program per problem:** prompt + completion + the problem's `test_imports` + its 3 `test_list` asserts. A problem
  passes if the program runs to the end with no exception.
- **PRIMARY, "cut":** each completion is cut at its first ``` (`text.split("```", 1)[0]`), the same rule for every
  arm. Nothing else is stripped. If a completion *opens* with a fence, the cut leaves nothing and the problem fails.
  That's part of the rule, not an exception to it.
- **SECONDARY, "raw":** the completion as returned, as in P5.
- **pass@1** over 257, for both.
- **Scorer validation, before the lock (no model involved):**
  - MBPP's own reference solutions score 256/257. Task 123 (amicable numbers to 9,999) times out at 3.0 s even with
    the reference code. It stays in, so it is likely unpassable for every arm.
  - Empty completions score 0/257.
  - A dry run of `mbpp_run.py`'s scoring on reference solutions plus a trailing "```\nprose" gives cut 256 and raw 0.

## M5. Determinism and provenance (as P5)

- **Hashes:** sha256 of each working copy immediately before its server loads it and again after its generation.
  A mismatch before loading stops the run. A pre/post mismatch voids the arm.
- **Drift check:** the final A36 slot's completions must be byte-identical to slot 1. If they aren't, that's
  reported, and every comparison carries the caveat.
- **Engine identity** (binary hashes, version, driver) is written at the start.

## M6. Paired tests

Exact McNemar, two-sided, on the P5 pairs: C30 vs A36, CN vs A36, CN3 vs CN, A38 vs A36, CN vs C30. They're run on
**cut** (primary) and on **raw** (secondary). H3 below also uses exact McNemar on C30 cut vs C30 raw. P6's write-up
rule carries over: p < 0.05 means "measurably beats"; otherwise "a statistical tie".

## M7. Predictions (written before any MBPP generation)

**Hypothesis (from D1):** Coder-30B's HumanEval deficit was mostly output format. With the fence cut it ranks at or
near the top, and with raw scoring it drops.

| | Prediction | Band / criterion |
|---|---|---|
| **H1** | C30 (cut) ranks 1st or 2nd of the 5 arms by passes (a tie shares the rank) | rank ≤ 2 |
| **H2** | A36 does **not** measurably beat C30 on cut | C30 vs A36 (cut): p ≥ 0.05, or C30 ahead |
| **H3** | C30 raw is well below C30 cut | ≥ 10 points lower, and exact McNemar C30 cut vs raw p < 0.05 |
| **H4** | The anchors don't depend on the cut | A36 and A38: raw within 2 points of cut |
| **H5** | Raw scoring repeats the HumanEval verdict | A36 measurably beats C30 on raw (p < 0.05) |
| H6 | CN3 vs CN (cut): a statistical tie | p ≥ 0.05 |

**pass@1 bands, cut (primary):** A36 68–86%; A38 65–85%; C30 68–88%; CN 65–88%; CN3 62–86%.
**pass@1 bands, raw (secondary):** A36 and A38 as their cut bands; C30 30–72%; CN and CN3 0–8 points below their
cut scores.

**How it's judged:**
- **Confirmed** if H1, H2 and H3 all hit. Then the article can say Coder-30B's HumanEval score mostly reflected an
  output-format effect of raw completion, and that on a pre-registered rule it scores level with the 27Bs or above.
- **Disconfirmed** if H2 misses, meaning A36 measurably beats C30 even with the cut. Then the format effect isn't
  the whole story, and the HumanEval verdict stands without qualification.
- **Otherwise partial**, reported as such, hypothesis by hypothesis.

## M8. Run

- Unattended on Tamanna (server) and Miu (generator, scorer), driven by `mbpp_run.py`. It starts after this file is
  committed and pushed.
- Expected: 60–80 min including loads and hashes.
- Doesn't touch the voice environments on Tamanna. Keeps ≥ 20 GB free on Tamanna (47 GB free at the lock, and the
  run writes only logs).

## M9. Harness and record

- **Harness, committed with this file in `docs/bench-results/tamanna-qwen-coder-mbpp-2026-11/harness/`:**

  | File | sha256 |
  |---|---|
  | `mbpp_gen.py` | `9ffe5229615d5c22bfa0008614117b501a1eb6c88ac96e74055b4ea455503911` |
  | `mbpp_score.py` | `a32290178ef6df83570d8d2b25445112e47b265b89ca6ad58a1603a29e390d60` |
  | `mbpp_run.py` | `41c2e584b63fc504ab312168c32f4865e84b47db7c280d4733a20010cfbaf335` |

  `mbpp_run.py` is P5's `he_run.py` with the generator, CN3's N and the two-way scoring changed. Its docstring
  lists the changes.
- **Record:** `docs/bench-results/tamanna-qwen-coder-mbpp-2026-11/`. It holds the completions, the per-problem
  results for both scorings, summaries, `mcnemar.json`, engine identity, the server logs and a README with M7
  filled in, hit or miss. Anything not specified here is labelled exploratory.
