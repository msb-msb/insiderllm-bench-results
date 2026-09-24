# WikiSkill one-shot replication — hour 0 + Gate 0, Miu, 2026-08-30

> ## ⚠️ READ THIS BEFORE QUOTING ANY NUMBER
>
> This file records TWO states. Figures were amended mid-run when idx 81 was
> found to duplicate idx 80 byte-for-byte.
>
> | | at Gate 0 (superseded) | **canonical** |
> |---|---:|---:|
> | corpus | 87 | **86** |
> | test split | 48 | **47** |
> | baseline exact | 50.00% | **48.94% (23/47)** |
> | 1 test item | 2.08 pp | **2.13 pp** |
> | baseline bootstrap CI | [35.4, 64.6] | **[34.0, 63.8]** |
>
> **Quote only the right-hand column.** The superseded figures are kept because
> the Gate 0 go/no-go decision was actually taken on them, and deleting them
> would erase the audit trail for that decision. They are marked *(stale)*
> wherever they appear. Everything in "Compilation + scoring" is canonical.
>
> Splits: compile 24 + val 15 + test 47 = 86. Chain: 89 gold − 2 regex
> short-circuits (idx 31, 63) = 87 at Gate 0, − 1 duplicate (idx 81) = 86.

Not a replication of arXiv 2608.27454. This measures the four things that paper
leaves open: token cost, run-to-run variance, corpus-size sensitivity, and
separating the compiling model from the executing model.

**Status: COMPLETE. Result is a clean negative — see "Verdict".**

## Task

mycoSwarm intent classification. 89 hand-corrected gold pairs mined from Monica
chat logs (`LLM_repo/intent_gold.json`, sha256 `f2f6265…`), verified on load to
reproduce every published figure of `intent-eval-2026-08-07.md`: n=89, tool
{answer 53, rag 36}, mode {chat 53, recall 25, explore 11}, scope {all 43,
session 38, docs 4, facts 4}, 9 corrections, constant baseline 47.2% / 59.6%.

**Corpus drift found and handled.** `classify_fast()` did not exist when the gold
set was built — the `small_talk` and `web_search` rules were added *as a result*
of that eval. Today 2 of 89 items (idx 31, 63) short-circuit before the model,
both correctly. They are deterministic and no skill can move them, so the
experimental corpus is **n=87** at this point. It becomes **86** after the
idx 80/81 duplicate is dropped later the same day — see the banner above.

## Splits — frozen, seed 20260830

Stratified on the full gold triple, largest-remainder per stratum.
`splits/freeze_splits.py` is deterministic and re-runnable.

| split | n | note |
|---|---:|---|
| compile | 24 | traces the frontier model will read |
| val | 15 | **frozen, never scored** — reserved for a later gated loop |
| test | **47** | 1 item = 2.13 pp |

All 8 gold triples are represented in test. **These are the post-amendment
figures.** The split was cut 24/15/48 and idx 81 was dropped from test later the
same day when it turned out to duplicate compile-split idx 80 byte-for-byte —
see "Amendment" below. Corpus n=86, not 87.

## Configuration

- `Qwen_Qwen3.6-27B-Q4_K_M.gguf` (16.75 GiB, sha256 `8739a0cb…`), llama.cpp
  `llama-server -ngl 99 -fa on -c 4096 --jinja --no-mmap`, port 8081.
- Prompt + validators + past-reference regex extracted from `solo.py` by AST
  (`deployed.py`), so the deployed literal is used verbatim and drift is
  detectable. `_INTENT_SYSTEM_PROMPT` = 2,304 chars, matching the eval.
  solo.py sha256 `324560443ab55e3a`.
- `run_arm.py` mirrors `intent_classify()` from the raw string onward: fence
  strip, per-field sanitise to `answer/chat/all`, then both overrides
  (past-reference → `scope=session`; `docs`+`web_and_rag` → `rag`).
- **Thinking suppressed via `chat_template_kwargs={"enable_thinking":false}`.**
  `/no_think` in the user message does NOT work on this build — it still emits
  ~1 KB of reasoning. Verified by probe before any arm was run.

## Results

> **STALE ROW WARNING.** The n=48 figures below are the pre-amendment values,
> kept for the record of what was run at Gate 0. **Do not quote them.** The
> canonical baseline after dropping the idx 80/81 duplicate is **48.94% (23/47)**,
> and every number in the "Compilation + scoring" section is on that basis.

| arm | split | n | exact | effective | raw-valid | reps | SD |
|---|---|---:|---:|---:|---:|---:|---:|
| baseline, think **off** (deployed) | test | 48 *(stale)* | 50.00% | 58.33% | 47/48 | 5 | 0.00 |
| baseline, think **off** | all | 87 *(stale)* | 48.28% | 55.17% | 86/87 | 5 | 0.00 |
| baseline, think **on** | test | 48 *(stale)* | 45.83% | 50.00% | 48/48 | 3 | 0.00 |

**Amended, canonical (n=47 test / n=86 corpus):**

| arm | split | n | exact | effective | raw-valid | reps | SD |
|---|---|---:|---:|---:|---:|---:|---:|
| baseline, think **off** (deployed) | test | 47 | **48.94%** | 57.45% | 46/47 | 5 | 0.00 |
| baseline, think **on** | test | 47 | 44.68% | 48.94% | 47/47 | 3 | 0.00 |

Per-field on test (n=48, stale): tool 64.58%, mode 66.67%, scope 64.58%.
Only schema violation: `{"mode": "creative"}` — not in the enum.

Amended baseline test exact 48.94%, bootstrap 95% CI **[34.0, 63.8]**.
Constant classifier on the amended test split scores 44.68%, so the margin is
+4.26 pp (the pre-amendment read was +6.25 pp, CI [-4.2, +16.7], at n=48).

Like-for-like with the 2026-08-07 eval (n=89, adding back the 2 now-short-circuited
items, both correct): **49.44% exact / 56.18% effective**.

## Findings

1. **Gate 0 passes.** 50.00% at the time (48.94% after the amendment) against
   an 85% stop threshold. Either way, ~50 points of headroom. Not the Monica cell.
2. **Thinking on is worse and far more expensive**: 45.83% vs 50.00%, with
   22.7× the completion tokens and 15.1× the wall time. The deployed config
   (thinking off, `num_predict 100`) is both the faithful and the better arm.
   Thinking does buy 100% schema compliance, but pays 4.2 pp of accuracy for it.
3. **Score-level executor noise is zero; generation-level noise is not.**
   Across 5 reps the score never moved, but 2/87 items (idx 2, 68 — both in
   test) flip predictions between reps and 7/87 emit different raw strings. Both
   flipping items are wrong under every variant, so the instability lands
   entirely inside the "wrong" bucket. σ_e = 0 is a property of this sample, not
   a guarantee: the latent instability is worth ~2.08 pp of test score.
4. **The 27B is the first model to beat the constant on exact match** (49.44%
   vs 47.2% like-for-like, computed pre-amendment at n=89-equivalent) — but it is still *below* the constant on effective
   (56.18% vs 59.6%), and the margin over the constant does not clear zero.

## Cost so far — all local, no API

| item | value |
|---|---|
| think-off pass, 87 items | 69 s, 56,866 prompt + ~1,740 completion tokens |
| think-off pass, 48 test items | 38 s, 31,258 prompt + 947 completion tokens |
| think-on pass, 48 test items | 578 s, 31,162 prompt + 21,512 completion tokens |
| model load (`--no-mmap`) | ~130 s |
| total GPU | ~40 min |

## Files

`splits/` frozen splits + manifest · `deployed.py` AST extraction of the
deployed prompt · `run_arm.py` arm runner · `baseline/*.json` full per-item
records (prediction, raw string, tokens, latency) · `logs/`


---

# Compilation + scoring — 2026-08-30

20 skills compiled by `claude-opus-5` (effort high, adaptive thinking, cache ttl
1h) from our own logs, scored on the 47-item test split. Server config verified
identical to the baseline by re-running the baseline arm: reproduced 23/47 =
48.94% exactly, same effective, same raw-valid.

## Verdict — both pre-committed conditions FAIL

| quantity | value |
|---|---|
| b (baseline test exact) | 48.94% (23/47) |
| sigma_c (group 24, n=10, sample SD) | **4.65 pp**, 95% CI [3.21, 8.50] |
| mean(s) group 24 | 50.85% |
| **Delta** | **+1.91 pp** |
| 2 x sigma_c | 9.29 pp — Delta does NOT clear it |
| paired bootstrap 95% CI on Delta | **[-4.26, +8.30]** — includes 0 |

**THE SKILL WORKED: NO.** **LOOP WORTH BUILDING: NO** (fails condition 1;
conditions 2 and 3 pass).

Delta is +1.91 pp against a compiler-noise floor of 4.65 pp. The effect is
roughly 0.4 sigma_c. Every sensitivity check agrees: minus the borderline
correction (+1.96), minus the 2 rep-unstable items (+1.56), minus both (+1.59).
Effective match moves +2.77 pp against its own 2SD of 8.04 — also inside noise.

## The finding that matters

g24_07 scored **59.57%, +10.6 pp over baseline** — and it is a draw from the
noise distribution, 1.9 sigma_c above the compiler mean, not a better skill.
A gate on our 15-item val split (1 item = 6.7 pp) would have selected it and
declared success. **Gating on a small validation split systematically mistakes
compiler noise for improvement.** That is a direct, measured critique of the
method, and it is only visible because we compiled 10 times instead of once.

## Does artifact diversity produce score diversity? No.

The 20 skills are textually near-disjoint (5-gram Jaccard 0.001-0.017) but
converge on the same diagnosis. Across the 45 group-24 pairs, textual distance
vs score distance: **Pearson r = +0.118, permutation p = 0.440**. No
relationship. Twenty different documents encoding the same strategy score the
same, within noise.

## Corpus-size ablation

| traces | n | mean exact | SD | Delta vs b |
|---:|---:|---:|---:|---:|
| 24 | 10 | 50.85% | 4.65 | +1.91 pp |
| 16 | 5 | 49.79% | 3.23 | +0.85 pp |
| 8 | 5 | 46.38% | 3.81 | **-2.55 pp** |

Monotone in trace count, but the whole range is inside one sigma_c. The 8-trace
condition — the paper's own default diet — scores *below* the no-skill baseline.

## The one consistent, real effect

**20/20 skills reached 47/47 raw-valid, vs 46/47 for baseline.** Every skill
eliminated the `{"mode": "creative"}` enum violation. Schema compliance is the
only thing compilation reliably fixed — and it is worth 0 accuracy points,
because the sanitiser already rewrote that field to the correct default.

## Prompt tax and break-even

- Baseline 651.7 prompt tokens/inference; skilled mean 2,035.6. **Tax = 1,383.9
  tokens per inference, forever.** Range 1,112-1,573; correlation with skill
  length r = 0.922, so it scales with the artifact as expected.
- Compilation cost 259,743 frontier tokens ($4.97) for 20 skills.
- **Break-even N = 259,743 / 1,383.9 = 188 local inferences.** Per single skill:
  12,987 frontier tokens -> 9 inferences.

The two currencies are not the same and must not be summed: compilation is paid
once in frontier tokens at frontier prices; the tax is paid forever in local
tokens at GPU-seconds. Break-even is a token-for-token statement only.

## Four token buckets

| bucket | where | input | output | wall_s |
|---|---|---:|---:|---:|
| B1 baseline rollout (5x87 + recheck) | local | 314,960 | 9,622 | 389 |
| B1b thinking-on probe (3x47) | local | 93,486 | 64,347 | 1,674 |
| B2 compilation (20 calls) | FRONTIER | 66,495 | 193,248 | 2,678 |
| B3 skilled rollout (20x47) | local | 1,913,419 | 17,975 | 823 |
| B4 gating / validation | - | 0 | 0 | 0 |

Frontier cache split: 8,647 write / 53,028 read / 4,820 uncached — **79.7% of
frontier input was cache reads**. One creation event per group, on call 0, no
re-writes; the 1h TTL held across a 45-minute run.

Note the shape B3 exposes: the skilled rollout consumed **1.91M local input
tokens, 7.4x the entire compilation**. The paper's optimizer-API-call metric
counts none of it.
