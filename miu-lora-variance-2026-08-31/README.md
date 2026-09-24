# LoRA seed-variance — Miu, 2026-08-31 to 2026-09-02

Results record. Facts as measured; no interpretation beyond what the files show.
Every number here is reproducible from a file in this directory.

## 1. Question and design

**Question.** Train the same LoRA adapter ten times on byte-identical data with a
byte-identical configuration, varying only the random seed. How far apart do
the ten adapters land on the frozen test split?

This is the weights-side analogue of the prompt experiment in
`../miu-wikiskill-oneshot-2026-08-30/`, which compiled the same skill ten times
and measured a compiler-noise floor of sigma_c = 4.65 pp.

**Design, fixed before seed 1 ran (2026-08-31 20:27).** There is no separate
pre-registration document. The design is fixed by `train_adapter.py`
(sha256 `fbeb2367…`, mtime 2026-08-31 20:27, unchanged through all ten seeds)
and `splits/manifest.json`.

| item | value |
|---|---|
| base model | Qwen3.6-27B, HF safetensors, loaded NF4 (bitsandbytes, double-quant, bf16 compute) |
| adapter | LoRA r=16, alpha=32, dropout 0.05, bias none |
| target modules | q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj (MLP on all 64 layers; attention on the 16 full-attention layers only; linear-attention projections excluded — see docstring) |
| trainable params | 79,691,776 |
| optimiser | AdamW, lr 1e-4, batch 1, grad accumulation 4, 10 epochs, 60 optimiser steps |
| loss | answer tokens only (prompt masked with -100) |
| training data | `splits/compile.json`, 24 items, fixed order then per-seed shuffle |
| seeds | 1–10; `random`, `numpy`, `torch` and the shuffle RNG all seeded with the same integer |
| corpus | 86 items (`intent_gold.json` 89, sha256 `f2f62653…`; minus 2 regex short-circuits idx 31, 63; minus duplicate idx 81) |
| splits | compile 24 / val 15 / test 47, frozen 2026-08-30, seed 20260830, stratified on the gold triple |
| test split | `splits/test.json`, 47 items, 1 item = 2.13 pp |
| val split | never scored |
| primary metric | exact match: predicted tool, mode and scope all equal gold, after the deployed sanitise/override pipeline (`deployed.py`, solo.py sha256 `32456044…`) |
| secondary metric | effective match — see section 5 |
| scoring path | PEFT + NF4, the configuration the adapters trained in (`score_hf.py`), greedy decoding, max 100 new tokens, thinking off |

## 2. Environment

| item | value |
|---|---|
| machine | Miu: RTX 3090 24 GB (24,576 MiB), i7-8086K, 62 GB RAM, Ubuntu 24.04.4, kernel 6.8.0-138, driver 580.178.04 |
| CUDA toolkit | 12.8 (`/usr/local/cuda-12.8`); torch built against cu128 |
| lora-venv | Python 3.12.3, torch 2.9.1+cu128, transformers 5.16.1, peft 0.20.0, bitsandbytes 0.50.2, accelerate 1.14.0. No site-packages change between the seed 1–2 scoring (2026-08-31 23:26) and the seed 3–10 scoring (2026-09-02 21:37) |
| llama.cpp (sections 7 only) | `/home/minotaur/llama-bench-src/build/bin/llama-server`, version 1 (67b9b0e), built 2026-08-15. Identified by matching the CORS-warning and `--lora` deprecation strings in `logs/server_*.log`; the only build on the machine containing both. Run as `llama-server -ngl 99 -fa on -c 4096 --jinja --no-mmap`, port 8081 |
| HF model dir | `/media/minotaur/Storage_Disk_1/LLM_repo/qwen3.6-27b`, 15 shards, newest file 2026-07-09. Per-file sha256 in `logs/model_sha256.txt`; shard 1 `5f21d4e3…` |
| GGUF (section 7) | `Qwen_Qwen3.6-27B-Q4_K_M.gguf`, sha256 `8739a0cb…` (`logs/gguf_sha256.txt`) |
| scripts | train_adapter.py `fbeb2367…` · train_wrap.py `a0125770…` · score_hf.py `9c84cb29…` · score_lora.py `53093ae1…` · run_arm.py `b0443149…` · deployed.py `1d578e11…` · run_seeds_3_10.sh `e479308a…` · splits/freeze_splits.py `1cb7f204…` |

Adapter weights (`adapters/seedN/adapter_model.safetensors`, 318,835,672 bytes
each) are on disk only, not in git (over GitHub's 100 MB limit). sha256 prefixes,
full values in `logs/adapter_sha256.txt`:

| seed | sha256 | seed | sha256 |
|---|---|---|---|
| 1 | `62724bcf…` | 6 | `c4412d8a…` |
| 2 | `4eaef20a…` | 7 | `2c39bcf7…` |
| 3 | `5cf165b5…` | 8 | `bf82368a…` |
| 4 | `996e575a…` | 9 | `ffbb4e1f…` |
| 5 | `291a06d1…` | 10 | `b873a155…` |

GGUF conversions exist for seeds 1 and 2 only (`seed1-f16.gguf` `609f3e37…`,
`seed2-f16.gguf` `ca13b653…`), used in section 7.

## 3. Results

Test split, 47 items, PEFT + NF4 path. One scoring pass per adapter for seeds
3–10; seeds 1 and 2 were scored 5 and 2 times respectively and every repeat
was byte-identical (section 7), so one pass is reported. Peak memory was
recorded for seeds 3–10 only (`train_wrap.py` for the torch counters,
`logs/vram_seedN.csv` for a 1 s nvidia-smi sampler); the seed 1–2 pilot did
not record it.

"Peak loss" is the highest epoch-mean loss over the 10 epochs; it is epoch 1
for every seed. "Largest rise" is the highest epoch-mean loss that exceeded
the running minimum of earlier epochs, i.e. the biggest rebound, with its
epoch; blank where the loss never rose. Full per-epoch matrix in the appendix.

| seed | exact | effective | raw-valid | final loss | min loss (ep) | peak loss (ep) | largest rise (ep) | peak torch alloc | peak torch reserved | peak nvidia-smi |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| base, no adapter | 21/47 = 44.68% | 25/47 = 53.19% | 46/47 | — | — | — | — | — | — | — |
| 1 | 15/47 = 31.91% | 19/47 = 40.43% | 47/47 | 0.0355 | 0.0003 (8) | 0.1574 (1) | 0.0856 (9) | n/r | n/r | n/r |
| 2 | 20/47 = 42.55% | 25/47 = 53.19% | 47/47 | 0.0016 | 0.0016 (10) | 0.1455 (1) | — | n/r | n/r | n/r |
| 3 | 19/47 = 40.43% | 25/47 = 53.19% | 47/47 | 0.0000 | 0.0000 (10) | 0.1475 (1) | — | 20,797 MiB | 23,412 MiB | 22,898 MiB |
| 4 | 19/47 = 40.43% | 24/47 = 51.06% | 47/47 | 0.0005 | 0.0005 (10) | 0.1494 (1) | — | 20,791 MiB | 23,538 MiB | 23,904 MiB |
| 5 | 19/47 = 40.43% | 25/47 = 53.19% | 47/47 | 0.0019 | 0.0019 (10) | 0.1477 (1) | 0.0175 (6) | 20,789 MiB | 23,320 MiB | 22,976 MiB |
| 6 | 21/47 = 44.68% | 26/47 = 55.32% | 47/47 | 0.0062 | 0.0062 (10) | 0.1760 (1) | — | 20,786 MiB | 23,474 MiB | 23,700 MiB |
| 7 | 19/47 = 40.43% | 25/47 = 53.19% | 47/47 | 0.0021 | 0.0021 (10) | 0.1590 (1) | 0.0247 (7) | 20,788 MiB | 23,652 MiB | 23,308 MiB |
| 8 | 20/47 = 42.55% | 25/47 = 53.19% | 47/47 | 0.0011 | 0.0011 (10) | 0.1492 (1) | — | 20,793 MiB | 23,660 MiB | 23,316 MiB |
| 9 | 20/47 = 42.55% | 26/47 = 55.32% | 47/47 | 0.0019 | 0.0019 (10) | 0.1428 (1) | 0.0334 (6) | 20,802 MiB | 23,426 MiB | 23,754 MiB |
| 10 | 21/47 = 44.68% | 27/47 = 57.45% | 47/47 | 0.0127 | 0.0097 (7) | 0.1415 (1) | 0.0242 (6) | 20,795 MiB | 23,476 MiB | 23,044 MiB |

Seed 3's final loss is 3.5e-6, shown as 0.0000. Train time 981–984 s for every
seed. Sources: `scored_hf/seed{1,2}_rep0.json`, `scored_hf/seed{3..10}.json`,
`scored_hf/base_noadapter.json`, `adapters/seedN/run_meta.json`,
`logs/pilot.log`, `logs/train_seedN.log`.

Spread. Sample SD (n−1), of per-seed percentages — the same formula as sigma_c
in the prompt experiment (`statistics.stdev` in `../miu-wikiskill-oneshot-2026-08-30/make_chart.py`).

| population | n | exact mean | exact SD | effective mean | effective SD |
|---|---:|---:|---:|---:|---:|
| seeds 1–10 | 10 | 41.06% | **3.62 pp** | 52.55% | 4.60 pp |
| seeds 3–10 | 8 | 42.02% | **1.89 pp** | 53.99% | 1.95 pp |
| prompt experiment sigma_c (group 24, n=10), for reference | 10 | 50.85% | 4.65 pp | — | — |

Range: exact 15–21 of 47 (31.91–44.68 pp); effective 19–27 of 47. Base with
no adapter: 21 exact, 25 effective. No seed scored above the base on exact;
seeds 6 and 10 equal it. Summary file: `scored_hf/spread_seeds1-10.json`.

Item-level: 13 of 47 items are exact under all ten seeds, 23 under none, 11
depend on the seed. Any two seeds give identical predictions on 31–44 of 47 items.

## 4. The 11 seed-dependent items

P = exact match, F = not. Base = no adapter, same path.

| idx | gold | base | s1 | s2 | s3 | s4 | s5 | s6 | s7 | s8 | s9 | s10 | pass |
|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---:|
| 6 | answer/chat/all | P | F | P | P | F | P | P | F | P | P | P | 7/10 |
| 15 | answer/chat/all | F | F | P | P | F | P | P | P | P | P | P | 8/10 |
| 18 | rag/recall/session | F | P | F | F | P | F | P | P | P | P | F | 6/10 |
| 33 | answer/chat/all | P | F | F | P | F | F | F | F | F | F | F | 1/10 |
| 35 | answer/chat/all | P | F | P | P | P | P | P | P | P | P | P | 9/10 |
| 37 | answer/chat/all | F | F | P | P | P | P | P | P | P | P | P | 9/10 |
| 40 | answer/chat/all | P | F | P | F | P | P | F | F | F | F | P | 4/10 |
| 58 | rag/recall/session | P | F | F | F | F | F | P | F | F | F | F | 1/10 |
| 61 | rag/explore/session | F | P | P | P | P | F | P | P | F | P | P | 8/10 |
| 62 | rag/recall/session | P | P | F | F | F | F | P | F | P | P | P | 5/10 |
| 73 | answer/chat/session | F | F | F | F | P | P | F | P | P | F | P | 5/10 |

Seed 1 fails 8 of the 11. Items 33 and 58 pass under the base and under one
seed each. Items 15 and 37 fail under the base and pass under 8 and 9 seeds.

## 5. Metric provenance

- **Exact match** is the metric of the 2026-08-07 intent eval and of the
  2026-08-30 pre-committed verdict. Primary here.
- **Effective match** was defined in
  `../miu-wikiskill-oneshot-2026-08-30/run_arm.py` lines 59–64 (file mtime
  2026-08-30 15:29, commit 26cbdf8e), after the baseline arm of that
  experiment had been scored (10:34 the same day) and before the compiled-skill
  arms (first at 15:37). Rule: if gold tool is `rag` or `web_and_rag`,
  effective = exact; otherwise scope is ignored and tool + mode must match.
  It was not pre-registered, appears in that README's tables without a prose
  definition, and the verdict conditions there are stated on exact match only.
  `score_hf.py` and `score_lora.py` copy the six lines verbatim. **Secondary
  metric only; do not quote it as a verdict.**

## 6. Incidents

**2026-08-31, pilot.** The first seed 1 run quantised `lm_head` along with
the rest of the model; a rerun of seed 2 on that configuration loaded at
15.00 GiB and OOMed on a 2.37 GiB dequantisation allocation with 21.50 GiB
in use (`logs/train_seed2.log`, adapter kept in
`adapters/_discarded_seed1_lmhead_quantised/`, not scored). `train_adapter.py`
was changed to leave `lm_head` unquantised and seeds 1 and 2 were rerun on the
final configuration at 20:27 and 20:43 (`logs/pilot.log`). All ten adapters in
section 3 are from the final configuration.

**2026-09-01, seeds 3–10 attempt, all failed** (`logs/seeds.log`,
`run_seeds.sh`). Desktop (lightdm) was up and the memfault soak timer was
running. Seeds 3–9 each OOMed in the first forward pass: the training process
held 18.65–19.04 GiB, the card reported 398–638 MiB free of 23.56 GiB, and the
failing allocation was 614–682 MiB. About 4.1 GiB was held outside the
training process. Model load took 247–352 s per seed (page cache evicted by the
soak's 18 GB GGUF reads) versus 9 s in the pilot. Seed 10 ended after 86 s
with no line passing the runner's output filter; no adapter was written.

**2026-09-02, seeds 3–10, clean** (`logs/seeds_3_10.log`, `run_seeds_3_10.sh`).
lightdm stopped, card at 33 MiB used, soak paused via `~/.soak-pause` for the
duration (the timer had still been active; the soak logged the paused cycles as
blind and uncredited). Gate: free VRAM ≥ 21,864 MiB checked before every seed
and before scoring; every check read 24,091 MiB. All eight seeds trained
without error. Highest nvidia-smi peak 23,904 MiB (seed 4), leaving 672 MiB of
the 24,576 MiB card; highest torch-reserved peak 23,660 MiB (seed 8). Seed 3
loaded in 336 s (cache evicted by the last soak cycle before the pause);
seeds 4–10 loaded in 9 s each. Scoring: base loaded once, eight adapters
attached and unloaded in sequence, 169–171 s per pass, done 21:57. Soak
resumed 21:58; its 22:11 cycle re-read the GGUF and resumed crediting from the
next cycle.

## 7. Executor noise floor and runtime LoRA scale

**Noise floor, llama.cpp path** (`scored/noisefloor_noadapter.json`,
`logs/server_noisefloor.log`, 2026-08-31 11:44). No adapter, test split,
5 repetitions: 23/47 exact, 27 effective, 46/47 raw-valid on every rep;
0 prediction differences and 0 raw-string differences across all 10 rep pairs.
Score-level sigma_e = 0 on this sample. (The 2026-08-30 README, same model and
server flags, saw 2 items flip predictions across its 5 reps with the score
unchanged; this 08-31 run saw none.)

**Noise floor, PEFT + NF4 path** (`scored_hf/seed1_rep{0..4}.json`,
`scored_hf/seed2_rep{0,1}.json`, `logs/hf_main.log`). Seed 1 scored 5 times,
seed 2 twice, greedy decoding: every repeat byte-identical in predictions.
sigma_e = 0 on this path as well.

**Runtime LoRA scale, llama.cpp path** (`scored/control_*.json`,
`scored/seed1_id0*.json`, `scored/seed2_id1.json`, `logs/server_scoring.log`,
2026-08-31 22:00–22:05; `scored/sep_resident_rep{0,1,2}.json`,
`logs/server_sep.log`, 2026-09-01 10:42). Server loaded with the seed 1 and
seed 2 f16 GGUF adapters. Prediction differences are counted against the
no-adapter noise-floor run.

| run | request `lora` field | exact | effective | raw-valid | preds differing from no-adapter |
|---|---|---:|---:|---:|---:|
| control_alloff | `[]` (all adapters explicitly off) | 20/47 | 25 | 47 | 16 |
| control_nofield | omitted | 20/47 | — | — | (records only) |
| control_scales_zeroed | omitted, server scales 0.0 | 22/47 | 26 | 47 | 8 |
| control_scales_zeroed_rep2 | same, repeated | 22/47 | 27 | 47 | 9 |
| seed1_id0 | `[{id:0, scale:1.0}]` | 22/47 | 27 | 47 | 16 |
| seed1_id0_recheck | same, repeated | 22/47 | 27 | 47 | 16 (0 vs first run) |
| seed2_id1 | `[{id:1, scale:1.0}]` | 21/47 | 26 | 47 | 11 |
| sep_resident_rep0/1/2 | omitted, separate server | 23/47 | 27 | 46 | 0, 0, 0 |

The two scales-zeroed runs differ from each other on 9 of 47 predictions
while totalling the same 22/47. All-off differs from scales-zeroed on 18.
The three `sep_resident` runs (2026-09-01) reproduce the no-adapter baseline
on all 47 predictions and on the 46/47 raw-valid count; the server flags used
for that separation run were not captured in `logs/server_sep.log`. Through
llama.cpp, seed 1 scored 22/47 and seed 2 21/47; through PEFT + NF4 the same
weights scored 15/47 and 20/47. The `score_hf.py` docstring records why the
PEFT path was adopted for section 3.

**v0.4.0 re-run (2026-09-09, `scored_v040/`, `logs/v040_repro.log`, `run_v040_repro.sh`,
`run_v040_extra.sh`, `repro_v040_score.py`, `compare_preds.py`).** Same harness on
llama-server 0.4.0 (5266f24), every launch line and `/lora-adapters` call logged.
Against a fresh no-adapter baseline (23/47, 0 differing across 2 reps): `--lora-scaled
A:0.0,B:0.0` at launch 0/47 differing (2 reps); `--lora A,B --lora-init-without-apply`
with no `lora` field 16/47 differing and `GET /lora-adapters` reporting both at scale
1.0; `"lora": []` byte-identical to no-field; runtime `POST /lora-adapters` both 0 then
6/47 differing at default `cache_prompt` (identical across 2 reps) and 0/47 with
`cache_prompt: false` against a no-adapter run made with the same setting. So the
08-31 runtime-zeroed deviation is prompt-cache reuse (ggml-org/llama.cpp#26207, numbers
posted there), the b10088 9/47 instability did not reproduce, and the two zero states
that never reach zero are filed as ggml-org/llama.cpp#28674. The section-3 choice of
the PEFT + NF4 path stands: the b10088 behaviour was real when it was made.

## Files

| path | content |
|---|---|
| `train_adapter.py`, `train_wrap.py` | trainer (unchanged across seeds) and the peak-memory wrapper used for seeds 3–10 |
| `run_pilot.sh`, `run_seeds.sh`, `run_seeds_3_10.sh` | seed 1–2 pilot; 09-01 failed batch; 09-02 batch with VRAM gate |
| `score_hf.py` | PEFT + NF4 scorer (section 3) |
| `score_lora.py`, `run_arm.py`, `deployed.py` | llama.cpp scorer, prompt-arm scorer, deployed-literal extractor (section 7) |
| `splits/` | frozen splits, manifest, freeze script |
| `adapters/seedN/` | adapter_config.json, run_meta.json (loss, steps, peaks), README; weights on disk only |
| `scored_hf/` | per-seed and base results, `spread_seeds1-10.json` |
| `scored/` | llama.cpp-path runs (section 7) |
| `logs/` | pilot, 09-01 and 09-02 batch logs, per-seed train logs, `vram_seedN.csv`, server logs, sha256 lists |

## Appendix: per-epoch mean loss

| seed | e1 | e2 | e3 | e4 | e5 | e6 | e7 | e8 | e9 | e10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.1574 | 0.0566 | 0.0442 | 0.0304 | 0.0201 | 0.0113 | 0.0034 | 0.0003 | 0.0856 | 0.0355 |
| 2 | 0.1455 | 0.0617 | 0.0419 | 0.0351 | 0.0299 | 0.0239 | 0.0120 | 0.0054 | 0.0028 | 0.0016 |
| 3 | 0.1475 | 0.0653 | 0.0428 | 0.0224 | 0.0212 | 0.0074 | 0.0059 | 0.0027 | 0.0013 | 0.0000 |
| 4 | 0.1494 | 0.0713 | 0.0437 | 0.0341 | 0.0225 | 0.0142 | 0.0095 | 0.0021 | 0.0019 | 0.0005 |
| 5 | 0.1477 | 0.0682 | 0.0428 | 0.0265 | 0.0132 | 0.0175 | 0.0072 | 0.0040 | 0.0068 | 0.0019 |
| 6 | 0.1760 | 0.0682 | 0.0488 | 0.0275 | 0.0171 | 0.0170 | 0.0163 | 0.0116 | 0.0099 | 0.0062 |
| 7 | 0.1590 | 0.0577 | 0.0403 | 0.0202 | 0.0067 | 0.0056 | 0.0247 | 0.0056 | 0.0048 | 0.0021 |
| 8 | 0.1492 | 0.0616 | 0.0471 | 0.0270 | 0.0177 | 0.0137 | 0.0057 | 0.0033 | 0.0020 | 0.0011 |
| 9 | 0.1428 | 0.0628 | 0.0424 | 0.0368 | 0.0175 | 0.0334 | 0.0164 | 0.0055 | 0.0035 | 0.0019 |
| 10 | 0.1415 | 0.0628 | 0.0361 | 0.0152 | 0.0200 | 0.0242 | 0.0097 | 0.0129 | 0.0137 | 0.0127 |
