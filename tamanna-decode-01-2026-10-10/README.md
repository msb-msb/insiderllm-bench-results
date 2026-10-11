# Tamanna (RTX 3090), TinyStories PLE story-boundary behaviour under four decoding settings, 2026-10-10: P1 failed, P2 held, P3 held, P4 failed

Results record for `~/esp32-llm/esp32-ai/evals/decode-01/PREREG.md` on Tamanna. It tests what happens at
`<|endoftext|>` (id 0), which the device firmware prints as zero bytes and never stops on.

Tamanna shared with: none.

## Pre-registration

- **PREREG.md** sha256 `f02b27d541858876bd90e27fedf3f94c5984298af88458eba15abee41758071e`.
- **prompts.txt** sha256 `f29b68e10fd434457bf3cbcf046a03313722d1abcb5dfc960fa08e7da8ec1fd6`.
- **Locked 2026-10-10T20:32:21-07:00:** the Tamanna NOTES.md entry, and the PREREG.md / prompts.txt mtimes.
- **First generation: about 20:33:32**, roughly 1 min after the lock. ⚠ Derived: generate.log carries no start
  timestamp. The figure is its mtime, 20:44:26, minus the logged total of 654 s.
- PREREG.md is unchanged after the results; Tamanna NOTES.md says "sha still f02b27d5…".

## Setup

- **Models:**
  - ts-repro-01: `runs/ple-ts-repro-01-s0.pt`, sha256 `cd6709b8…5265`, seed 0.
  - ts-repro-02: `runs/ple-ts-repro-02-s1.pt`, sha256 `87dcf713…2173`, seed 1.
  - Both are fp32 PyTorch checkpoints; see `../tamanna-ts-repro-2026-10-10/`.
- **Stack:** torch 2.13.0+cu130 on an RTX 3090. Harness `tools/decode_eval.py`, sha256
  `0367a545e6ea74988846834bdf5f66dd45823d2117fca6a1ec6897a9c06391d0`.
- **Prompts:** 50 fixed, 25 in-domain and 25 off-domain. None mentions Lily, girl or "little girl".
- **Generation:** logits over the first 25,353 ids, 200 new tokens.
- **Settings:**
  - (a) greedy;
  - (b) greedy, stopping on id 0;
  - (c) T = 0.8 with top-p 0.9;
  - (d) as (c), with repetition penalty 1.1.
  - (c) and (d) use seeds 0, 1 and 2, with generator seed = seed × 1000 + prompt index.
- **Volume:** 900 generations (`generations.jsonl`, sha256
  `bd1eb7b46356099486234a3588eb1323538be9ee4e87937726707e57833f2f3c`), 654 s in all.
- **Unscored:** an exploratory int4-dequantized greedy setting.
- **Hardware:** no ESP32 involved. This is host-side PyTorch.

## Predictions (verbatim from PREREG.md) and verdicts

| | prediction (verbatim) | verdict | evidence (RESULTS.md) |
|---|---|---|---|
| P1 | "Greedy decoding: ≥80% of generations restart into a new story after the first boundary, and most restarts open with the same default story (Lily/"little girl")." | **failed** | restart 76.0% on both checkpoints (< 80%); restart→default 100.0% on both |
| P2 | "Stopping at the boundary: 0 restarts by construction." | **held** | 0.0% on both |
| P3 | "Off-domain prompts (space, robots, machines): keyword retention <50% under every decoding setting." | **held** | 8 cells, 1.3%–16.0% |
| P4 | "T=0.8 / top-p 0.9: default-story collapse rate drops to at most half the greedy rate." | **failed** | ts-repro-01: a 80.0% → c 58.0% (limit 40.0%). ts-repro-02: a 78.0% → c 55.3% (limit 39.0%) |

## Results (all 50 prompts; from RESULTS.md)

n = 50 per checkpoint for (a) and (b), and n = 150 for (c) and (d), pooled over 3 seeds. Greedy is deterministic, so
it has no spread. RESULTS.md gives no per-seed range for (c) or (d).

| checkpoint | setting | boundaries/gen | restart | restart→default | collapse | retention | distinct-2 |
|---|---|---:|---:|---:|---:|---:|---:|
| ts-repro-01 | a greedy | 0.86 | 76.0% | 100.0% | 80.0% | 44.0% | 0.583 |
| ts-repro-01 | b greedy+stop | 0.00 | 0.0% | n/a | 32.0% | 44.0% | 0.605 |
| ts-repro-01 | c T0.8 p0.9 | 1.01 | 83.3% | 56.0% | 58.0% | 34.0% | 0.856 |
| ts-repro-01 | d + rep 1.1 | 1.03 | 91.3% | 51.8% | 74.0% | 31.3% | 0.938 |
| ts-repro-02 | a greedy | 0.82 | 76.0% | 100.0% | 78.0% | 24.0% | 0.649 |
| ts-repro-02 | b greedy+stop | 0.00 | 0.0% | n/a | 20.0% | 24.0% | 0.641 |
| ts-repro-02 | c T0.8 p0.9 | 0.87 | 83.3% | 50.4% | 55.3% | 34.0% | 0.875 |
| ts-repro-02 | d + rep 1.1 | 0.91 | 86.0% | 50.4% | 64.0% | 30.0% | 0.941 |

**Off-domain keyword retention (P3 cells):**

| checkpoint | a | b | c | d |
|---|---:|---:|---:|---:|
| ts-repro-01 | 16.0% | 16.0% | 5.3% | 6.7% |
| ts-repro-02 | 4.0% | 4.0% | 6.7% | 1.3% |

**Exploratory, unscored:** fp32 and int4 greedy give 0/50 identical 200-token outputs on each checkpoint, with mean
first divergence at 5.4 / 5.6 tokens. On int4 greedy, 93.8% / 100.0% of restarts open with the default story.

**Post-hoc, from RESULTS.md, not verdicts:**
- Sampling cuts collapse only about 0.7× (80 → 58%, 78 → 55.3%). Repetition penalty 1.1 makes it worse.
- The attractor is "Once upon a time, there was a little girl named X", with X usually Lily or Lucy.
- The device additionally uses int8 activations, which this harness does not model.

## Training-data base rate (corpus-openers-01, added after the results; not a verdict)

These are counts over the exact slice the two checkpoints trained on: `data/tinystories/raw/tinystories-train-first-300MiB.txt`,
sha256 `2fa7ae4d…0bdd`, 344,375 non-empty stories, split on `<|endoftext|>` as `prepare.py` does. CPU only.

| measure | training data | model restarts (this record) |
|---|---:|---:|
| decode-01's "default story" metric (Lily or "little girl" in the first 60 tokens) | **34.00%** | 100% greedy; 50.4–56.0% sampled (c) |
| opens with exactly "Once upon a time, there was a little girl named" | 12.60% | – |
| opens with "Once upon a time" + "little girl" in the first sentence | 18.48% | – |
| contains "Lily" anywhere | 22.04% | – |
| top name after "named" | Lily, 43,503 (12.63% of stories); next Timmy, 16,697 | Lily, then Lucy |

The default opener is the data's most common opener, so it is a prior. The model produces it about 1.5–3× more often
than the data does after a boundary.

- Files: `~/esp32-llm/evals/corpus-openers-01/` on Tamanna, copied to Miu `~/Desktop/esp32-llm/evals/corpus-openers-01/`.
- `count_openers.py` with `output.txt` (sha256 `4ce24752f90524959e156244d8b3006b8078cd0341859572f2cf604015af2856`).
- `count_openers_tok60.py` with `output_tok60.txt` (sha256 `08b017045c33ef2ae8af83db3b138772e138513655ab30068abb522535612b8b`).

## Files (on Tamanna, `~/esp32-llm/esp32-ai/evals/decode-01/`)

Paths are local, not in this repo: bare `data/`, `runs/` and `tools/` paths are under Tamanna `~/esp32-llm/esp32-ai/`.

- PREREG.md, prompts.txt, RESULTS.md (sha256 `73914cbd0ac9ef714c5bee46067b4cc89fc0fead66eb57ac7cc0e04996cd58d1`)
- generations.jsonl, generate.log (sha256 `c300993dc857636a662e870e01595004e4e6eae504c699364fc273990951b68b`)
- Harness: `~/esp32-llm/esp32-ai/tools/decode_eval.py`
