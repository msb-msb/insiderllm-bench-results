# Tamanna (RTX 3090 24 GB), retraining the esp32-ai TinyStories PLE model from the release recipe, seeds 0 and 1, 2026-10-10

Reproduces the upstream `ple` arm (`research/tinystories/scripts/run_deploy_ablation.sh`, the source of the release
model) at seeds 0 and 1, and checks the exported model against its own PyTorch golden. **No pre-registration**: the
expected value is upstream's published two-seed ppl.

Tamanna shared with: none.

## Setup

- **Machine:** Tamanna, NVIDIA GeForce RTX 3090 24 GB, driver 580.178.04. Python 3.12.15, torch 2.13.0+cu130,
  CUDA 13.0, uv 0.13.0.
- **Code:** slvDev/esp32-ai @ `52ebcbbd905270592c1d415efd1128d04d0fa365`. Recipe unchanged except `--tag`
  (`ts-repro-01`, `ts-repro-02`) and `--seed 1` for the second run.
- **Data:** `prepare --vocab 32768` on `data/tinystories/raw/tinystories-train-first-300MiB.txt` (314,572,800 B,
  sha256 `2fa7ae4d539bed8eea4f3aeaf27122a5db12c1c7da225d68adbaf24b37440bdd`; 344,375 non-empty stories per
  `evals/corpus-openers-01/output.txt`), 54.51 s (`prepare.log`: `Elapsed (wall clock) time … 0:54.51`). Tokenizer
  sha256 `4e28163669f2249af31a528a54fc25064dcbd0a34edbfa7bedb16d2d600ec7ae`, equal to the release tokenizer.
- **Not deterministic:** train.py sets no cuDNN/deterministic flags.

## Result

| run | seed | final val loss | final val ppl | train loop | wrapper wall | peak alloc / reserved | host verify |
|---|---:|---:|---:|---:|---:|---:|---|
| ts-repro-01 | 0 | 2.4310 | 11.37 | 118 s | 124.1 s | 2,637.9 / 2,962.0 MiB | PASS, max abs diff 0.00001 |
| ts-repro-02 | 1 | 2.4328 | 11.39 | 118 s | 122.7 s | 2,637.9 / 2,962.0 MiB | PASS, max abs diff 0.00001 |
| two-seed mean | | 2.4319 | 11.38 | | | | |
| upstream RESULTS.md (`ple`, two seeds) | | | 11.41 | | | | |

- **Source lines** (train.log): `ple-ts-repro-01-s0 DONE core=558,368 table=25,165,824 val=2.4310 ppl=11.37` and
  `ple-ts-repro-02-s1 DONE core=558,368 table=25,165,824 val=2.4328 ppl=11.39`. Step 4999 lines show 118 s for both.
- **Wrapper and VRAM:** `WRAP wall_seconds=124.1` / `122.7`, `WRAP peak_allocated_MiB=2637.9`,
  `WRAP peak_reserved_MiB=2962.0`. nvidia-smi.csv peak 3,294 MiB in both runs.
- **verify.log:** `max abs diff = 0.00001`, `PASS: C matches PyTorch golden`. The top-1 id agrees: 1 for seed 0,
  438 for seed 1.
- **Calculation:** the two-seed mean ppl of 11.38 is the mean of the two lines, computed here. It is 0.03 below
  upstream's 11.41, and inside the spread that two seeds can show.

**Core count, explained:** the core parameter count is **558,368** in both runs, against **556,416** in the release
`metadata.json` (`"core": 556416`, `"total": 28867968`).
- The 1,952 difference is exactly the 20 RMSNorm weight vectors (6 × 3 × 96 + 96 + 128). The model shapes are the
  same.
- train.py's counter, `src/model.py:276-292` `param_budget()` (used at `research/tinystories/train.py:122` and
  printed at `:201`), counts all parameters except the table and the head, so it includes the norms.
- Built on CPU with the release config, the model's core holds 556,416 2-D matrix parameters (equal to metadata's
  "core") plus 1,952 1-D norm parameters, and nothing else.
- The code that wrote the release metadata.json is not in the repo at `52ebcbb`, so its convention is inferred from
  the counts.
- Evidence: Miu `~/Desktop/esp32-llm/evals/param-gap-01/` (`count_params.py`, `output.txt` sha256
  `c9ed844cd4f8bf704b4c7ac19cb24bac1fb4f52a9e07d29de09a6683c6105ff3`).

## Model hashes (SHA-256, `runs/*/SHA256SUMS` on Tamanna)

| file | ts-repro-01 (seed 0) | ts-repro-02 (seed 1) |
|---|---|---|
| checkpoint | `ple-ts-repro-01-s0.pt` `cd6709b8fb8d2737eb8061751b5dbfec4f02a53832f99621bd5f3b4dd0855265` | `ple-ts-repro-02-s1.pt` `87dcf713722f845d166f4404180db1c2e5bc455cfa7ab3b5b61156c95de82173` |
| model.bin | `a7f1ce96291a6bfc3ab5cefd8c5b0e27af68759d7123d5112456ab0d5526b3a5` | `52a330ac18e5f612e0e0234c09dcb4e99eaa58566da54b7a595b6e46591f3e4e` |
| golden.txt | `4f9d8cced28db30859757484840cc95c70d4c1a4fdaaaf4f67eaeb2511c6d14a` | `1cc49b0f6bd8f8d622b34d8eedec4c01b7dab84d4afeb3a14457f329fbc63abb` |
| golden.npz | `8668325cc5bf493168f2fe276ef682b03dbb804517ad0521ddc7bbd9f9e77652` | `5727a3fbc440f3c4c7fe082039ab0d8a0a8657affc5e6e31948c3eae16c2dd1e` |

- Release for comparison: model.bin `1d8326c05c383ccfa615f5455575802817cb453dbc7ab28875d41a9dbb45477e`, the same
  size (14,912,348 B) with different bytes.
- ts-repro-01's model.bin, golden.txt and RUN.md were copied to Miu (`~/Desktop/esp32-llm/models/ts-repro-01/`) with
  matching hashes. verify.c on Miu: PASS, max abs diff 0.00001 (NOTES.md). Neither retrain has been flashed.

## Files (on Tamanna, `~/esp32-llm/esp32-ai/runs/`)

Paths are local, not in this repo: bare `data/`, `runs/`, `research/` and `src/` paths are under Tamanna `~/esp32-llm/esp32-ai/` (the last two are slvDev/esp32-ai @ `52ebcbb`); `evals/` is under Miu `~/Desktop/esp32-llm/` and Tamanna `~/esp32-llm/`.

- `ts-repro-01/`: RUN.md, train.sh, train_wrap.py, train.log, prepare.log, nvidia-smi.csv, export.log, model.bin,
  golden.txt, golden.npz, verify.log, staging_verify.log, SHA256SUMS.
- `ts-repro-02/`: the same set minus RUN.md, prepare.log and staging_verify.log.
- Tamanna `~/esp32-llm/NOTES.md`.
