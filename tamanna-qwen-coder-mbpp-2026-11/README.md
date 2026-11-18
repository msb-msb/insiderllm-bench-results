# Tamanna (RTX 3090): MBPP confirmatory test of the HumanEval fence finding, 2026-11-17

Pre-registration: `docs/candidates/qwen-coder-mbpp-confirm-2026-11.md`. Lock commit `c4860c1a`, file sha256
`62c5e120a054b9e392909a48a69dda74a1bd91b7458c89ec2c3845ed5f19d4b6`. It tests deviation D1 of
`qwen-coder-article-2026-11.md`. This record is section M9 of the lock.

**Verdict under the pre-registered rule (M7): PARTIAL.** H1 and H2 hit and H3 missed, so it is neither "confirmed"
nor "disconfirmed". **No arm wrote a ``` in any of its 257 completions**, so cut and raw scores are identical for
every arm and the fence-cut rule went untested (below).

## Timeline (PST; the logs are Miu's clock, PST)

| Event | Time |
|---|---|
| Lock committed (`c4860c1a`) and pushed to the main repo | 14:03:52 commit time, then pushed |
| MBPP run start | 14:04:28 |
| A36, A38, C30 results written | 14:11:57, 14:19:15, 14:22:33 |
| **Lock public on the bench-results mirror** (commit `e839ebb`) | **14:24:22** |
| CN, CN3, A36-drift results; run done | 14:32:27, 14:38:23, 14:45:56 |

The lock text was fixed before the run started: it was committed and pushed to the main repo at 14:03:52. **The
public copy went live after three arms' results were already written**, so the public timestamp proves only that
this exact text, sha256 `62c5e120…`, existed by 14:24:22. Public copy:
`https://github.com/msb-msb/insiderllm-bench-results/blob/main/candidates/qwen-coder-mbpp-confirm-2026-11.md`.
It hashes to the lock sha256.

## Setup (as locked, M2–M5)

- **Benchmark:** MBPP sanitized, test split, all 257 problems. Dataset revision `4bb6404f…`, parquet sha256
  `e9e9efa2…`.
- **Prompt:** bigcode's MBPP format, `"""\n{prompt}\n{test_list[0]}\n"""\n`.
- **Stops:** `\nclass \nassert \n""" \nprint \nif \n<|/`, the same for every arm.
- **Sampling:** temperature 0, seed 42, `max_tokens 512`, as P5.
- **Server:** on tamanna, `llama-server -ngl 99 -fa on -c 4096 --no-jinja --no-mmap` bound to tamanna's LAN address,
  port 8099 (+ `-ncmoe 28` for CN, `-ncmoe 8` for CN3). v0.4.0 `5266f24`: `llama-server` `d0b44631…`,
  `libggml-cuda.so.0.23.0` `3b086837…` (`engine-identity.txt`).
- **Generator and scorer on miu.**
- **Scoring:** `he-scorer:b10088` with P5's sandbox flags. `mbpp_score.py` runs through the official
  `human_eval.execution.check_correctness` with a 3.0 s timeout. The program is prompt + completion + test imports
  + the 3 asserts.
  - **Primary, "cut":** each completion cut at its first ```.
  - **Secondary, "raw":** the completion as returned.
- **Harness:** `harness/` holds the files committed with the lock (sha256s in M9). The working copies on miu that
  ran matched them before the start. **The public mirror redacts the LAN address** inside `mbpp_gen.py` and
  `mbpp_run.py`, so the mirror's copies of those two don't hash to M9's figures. The main repo's copies do.
- **Scorer validation before the lock** (`scorer-validation/`): MBPP's reference solutions pass 256/257, and the
  miss, task 123, times out at 3.0 s. Empty completions score 0/257.

## Results

| Slot | Arm | -ncmoe | Cut (primary) | Raw (secondary) | Cut band | Raw band | Gen tok/s |
|---|---|---:|---:|---:|---|---|---:|
| 1 | A36: Qwen3.6-27B-UD-Q4_K_XL | — | **217/257 (84.44%)** | 217 (84.44%) | 68–86% hit | 68–86% hit | 31.4 |
| 2 | A38: Qwen3.8-27B-UD-Q4_K_XL | — | **204 (79.38%)** | 204 (79.38%) | 65–85% hit | 65–85% hit | 31.0 |
| 3 | C30: Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL | — | **205 (79.77%)** | 205 (79.77%) | 68–88% hit | 30–72% **MISS: above** | 162.7 |
| 4 | CN: Qwen3-Coder-Next Q4_K_M | 28 | **198 (77.04%)** | 198 (77.04%) | 65–88% hit | 0–8 pts below cut: hit (0) | 35.3 |
| 5 | CN3: Qwen3-Coder-Next-UD-IQ3_XXS | 8 | **190 (73.93%)** | 190 (73.93%) | 62–86% hit | 0–8 pts below cut: hit (0) | 64.6 |
| 6 | A36 again | — | 217, byte-identical to slot 1 | 217 | must be identical | | 31.4 |

- **Provenance:** every arm's working copy hashed the same before its load and after its generation
  (`summary-*.json`). No arm is void.
- **Determinism:** slot 6's completions are byte-identical to slot 1's for all 257 problems (`drift-check.json`,
  out_sha16 `fdf81a5b2437a4a9` both times).
- **CN3 loaded at the fixed N = 8,** as M3 required.
- Gen tok/s is the generator's whole-run rate (generated tokens over wall time), not a speed measurement.

### Paired tests (exact McNemar, two-sided; `mcnemar.json`)

| Pair (X vs Y) | X | Y | only X | only Y | p | P6 wording |
|---|---:|---:|---:|---:|---:|---|
| C30 vs A36 | 205 | 217 | 12 | 24 | 0.0652 | statistical tie |
| CN vs A36 | 198 | 217 | 12 | 31 | 0.0054 | A36 measurably beats CN |
| CN3 vs CN | 190 | 198 | 22 | 30 | 0.332 | statistical tie |
| A38 vs A36 | 204 | 217 | 8 | 21 | 0.0241 | A36 measurably beats A38 (exploratory, see below) |
| CN vs C30 | 198 | 205 | 19 | 26 | 0.371 | statistical tie |

The cut and raw tables are identical, since the two scorings saw the same text.

### M7 predictions, hit or miss

| | Prediction | Result | |
|---|---|---|---|
| H1 | C30 (cut) ranks 1st or 2nd of 5 | 2nd: A36 217, C30 205, A38 204, CN 198, CN3 190 | **hit** |
| H2 | A36 does not measurably beat C30 (cut) | p = 0.0652 (12 vs 24) | **hit**, close to the line |
| H3 | C30 raw ≥ 10 points below cut, McNemar p < 0.05 | 0 points: no completion contained ``` | **MISS** |
| H4 | A36, A38 raw within 2 points of cut | 0 points | hit |
| H5 | A36 measurably beats C30 on raw | p = 0.0652 | **MISS** |
| H6 | CN3 vs CN (cut) a statistical tie | p = 0.332 | hit |

**Rule (M7):** "confirmed" needs H1, H2 and H3. "Disconfirmed" means H2 misses. Otherwise partial. **H3 missed and
H2 hit, so PARTIAL.**

## Why it's partial: the fence behaviour didn't appear

- **No completion from any arm contains ```** (0 of 257, every arm). The cut changed nothing, so the comparison M4
  was built for never happened.
- **The finding does carry over in part.** Under the same raw-completion protocol as HumanEval, C30 doesn't lose to
  A36 on MBPP. It's second of five and a statistical tie with A36, where on HumanEval A36 beat it at p = 2.0e-6.
  That's consistent with D1's explanation. It isn't a test of the cut rule.
- **Observation (exploratory, not predicted):** 136 of C30's 257 completions end on a comment line, typically
  `# Test the function`. A36 has 11 like that. It looks as if the model was about to write test code or prose, and
  the MBPP stops (`\nassert`, `\nprint`, `\nif`) ended generation first. HumanEval's stops include `\nprint` and
  `\nif` but not `\nassert`, and none catches ```. This is an explanation of what happened, not a measured result.

## Exploratory (not predicted): A36 beats A38

A36 (Qwen3.6-27B) measurably beats A38 (Qwen3.8-27B) on MBPP: 217 against 204, 21 against 8 discordant, p = 0.024.
M7 made no prediction for this pair. On HumanEval (P5) the same pair was a tie (137 against 130, p = 0.265). It's
one benchmark, unpredicted, so treat it as a lead.

## Files

- `harness/`: `mbpp_gen.py`, `mbpp_score.py`, `mbpp_run.py`, committed with the lock.
- `sequence.log`, `mbpp_run.out`: the run log. `engine-identity.txt`, `drift-check.json`, `mcnemar.json`.
- `gen-<ARM>.json` / `.log`: completions with finish reason, token count, prompt and test per problem.
- `eval/`: the `mbpp_<ARM>_{cut,raw}.jsonl` scorer inputs and their `_results.jsonl`, plus the copy of
  `mbpp_score.py` the container ran.
- `summary-<ARM>.json`: passes, pass@1, per-problem vectors (cut and raw), pre/post sha256.
  `scorer-<ARM>-{cut,raw}.txt`: scorer output.
- `server-logs/`: tamanna's llama-server log per arm.
- `scorer-validation/`: the reference-solution and empty-completion checks run before the lock.
