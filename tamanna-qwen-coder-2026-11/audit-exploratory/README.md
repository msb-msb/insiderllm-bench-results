# HumanEval failure audit: POST-HOC, exploratory (deviation D1, 2026-11-17)

**Decided after seeing the HumanEval results. Not pre-registered, not confirmatory.** The locked scores in
`../humaneval/` and the parent README are the primary result, and nothing here changes them. Mark asked for the
audit on 2026-11-17 after C30 and CN scored below their bands. The confirmatory test of what it found is a separate
pre-registration, `docs/candidates/qwen-coder-mbpp-confirm-2026-11.md`.

## What was checked

1. **Every failed item, classified** for C30 (64), CN (44), and A36 (27, all of them, as the control). A38 and CN3
   were classified the same way for completeness.
2. **Does the harness extract code differently per arm?** No. There's no extraction step: each completion goes to
   the scorer exactly as returned, appended to the prompt (`../humaneval/he_run.py`, `eval/he_<ARM>.jsonl`).
3. **Is a chat template applied, with thinking mode or template stop tokens?** No, for any arm. P5 locks raw
   `/v1/completions` against `llama-server --no-jinja`. Every arm gets the same five lm-eval stops
   (`\nclass \ndef \n# \nif \nprint`), and none of them catches ```.

## Method

- `audit.py`: parses prompt + completion with `ast` and records the finish reason and whether a ``` appears. It
  writes `all.json` and the fence-cut copies `cf/cf_<ARM>.jsonl` (each completion cut at its first ```, the same
  rule for every arm).
- The cut copies were scored in the lock's sandbox, the same image and flags as P5:
  `docker run --rm --network none --cap-drop ALL --security-opt no-new-privileges --memory 4g --pids-limit 256
  -v $PWD/cf:/work he-scorer:b10088 /work/cf_<ARM>.jsonl` → `cf/cf_<ARM>.jsonl_results.jsonl`.
- `audit.py classify` then writes `cls.json` and `final.json`, the class per failed item. The rules are in its
  docstring. **They're rule-based.** The format classes (b) and (c) were confirmed by reading the completions. The
  (a) "wrong logic" class is what's left: syntactically valid code that fails an assertion or raises at runtime.
  Not every (a) item was read by hand.
- `cf_table.py` prints the counterfactual pass@1 and McNemar tables.

## Result

| Failure type | A36 (control) | C30 | CN | A38 | CN3 |
|---|---:|---:|---:|---:|---:|
| (a) wrong logic | 23 | 12 | 26 | 29 | 29 |
| (b1) closing ``` then prose; passes once cut | 0 | 41 | 3 | 0 | 5 |
| (b2) ``` / prose, still fails when cut (mostly `pass` then a new ```python block) | 0 | 7 | 1 | 1 | 0 |
| (b3) non-code tokens after the body (`</file>`, `<reponame>…`, `/`) | 0 | 0 | 4 | 0 | 6 |
| (b4) helper function cut off by the `\ndef` stop (NameError on it) | 0 | 1 | 2 | 0 | 3 |
| (c) truncated at `max_tokens 512` | 0 | 3 | 3 | 2 | 5 |
| (d) missing stdlib import, or timeout | 4 | 0 | 5 | 2 | 3 |
| **Failures** | 27 | 64 | 44 | 34 | 51 |
| **Format (b) share** | **0%** | **77%** | **23%** | 3% | 27% |

**What happens in C30's typical failure:** a correct-looking function body, then a closing ``` it never opened,
then "This function works by: 1. …" in prose. That's a SyntaxError, and the problem fails. Two of C30's three
length-truncated items are prose that ran past 512 tokens.

**Fence-cut counterfactual (post-hoc):**

| Arm | Locked (primary) | Fence-cut (post-hoc) | Change |
|---|---:|---:|---:|
| A36 | 137/164 (83.54%) | 137/164 (83.54%) | +0 |
| A38 | 130/164 (79.27%) | 130/164 (79.27%) | +0 |
| C30 | 100/164 (60.98%) | 142/164 (86.59%) | +42 |
| CN | 120/164 (73.17%) | 123/164 (75.00%) | +3 |
| CN3 | 113/164 (68.90%) | 118/164 (71.95%) | +5 |

| Pair, fence-cut (post-hoc) | only X | only Y | exact McNemar p |
|---|---:|---:|---:|
| C30 vs A36 | 17 | 12 | 0.458 |
| CN vs A36 | 9 | 23 | 0.0201 |
| CN3 vs CN | 13 | 18 | 0.473 |
| A38 vs A36 | 11 | 18 | 0.265 |
| CN vs C30 | 10 | 29 | 0.00338 |

No item that passed under the lock fails after the cut, for any arm.

## Why this is exploratory only

The cut rule was chosen after seeing C30's failures, so the counterfactual is fitted to the very data it explains.
It says the locked protocol measures output format as well as coding for chat-tuned models. It does not show that
C30 codes as well as A36. That claim needs data the rule wasn't fitted to: the MBPP pre-registration.

## Files

- `audit.py`, `cf_table.py`: the method above.
- `all.json`: every item for the 5 arms, with completion, verdict, syntax check, finish reason, fence flag.
- `cf/`: fence-cut inputs and the sandbox's per-problem results.
- `cls.json`, `final.json`: the class per failed item.
