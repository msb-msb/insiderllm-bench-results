# Candidate: a measured "Qwen Coder" article — 2026-11-07

**2026-11-08: Mark chose the measured piece, with our own HumanEval. The pre-registration is at the end of this
file, LOCKED 2026-11-08.** The scope below is the 11-07 survey it was built from.

**Scope only. Nothing has been written, downloaded or benchmarked.** This comes from the 11-07 Bing AI
export (`docs/candidates/ai-grounding-demand-2026-10.md`, "July vs November, disjoint windows").

## The demand

Bing AI's grounding query **"qwen coder"** gets 3,256 citations in the 11-07 export (08-07..11-04, 90
days). That's **36 a day, #2 in the file, and we hold 7.3% of them.** No page of ours is about Qwen
Coder. The query is absent from the July file, which covers 04-19..07-09. It had 1,782 citations at
8.5% in the 10-07 file, which covers 04-19..10-04. So it arrived after July and is still growing.

The whole Coder cluster in the 11-07 file is 13 queries, 3,475 citations, 38.6 a day. In July it was 8
queries and 2.5 a day. The bare query is nearly all of it, and the rest are small:

| Query | Citations | Share |
|---|---:|---:|
| qwen coder | 3,256 | 7.3% |
| qwen3 coder next | 48 | 4.8% |
| qwen coder models | 45 | 24.2% |
| newest qwen coder model | 23 | 24.7% |
| qwen 3 coder vs qwen 3.6 | 21 | 31.8% |
| best qwen coder model | 16 | 20.3% |
| qwen2.5-coder:32b review | 15 | 11.1% |
| qwen3-coder-next vs qwen3.6-27b | 12 | 31.6% |
| ollama qwen coder models | 10 | 52.6% |
| qwen3-coder-next vs qwen3.8-27b | 10 | 26.3% |

These questions are "which Qwen Coder is current, and which one fits my machine", plus Coder against the
general Qwen models. A bare two-word query at 7.3% is likely dominated by Qwen's own pages and Hugging
Face, as "qwen" (1.7%) and "nvfp4" are. So a page could win the long-tail queries, which already give
us 20-50%, more surely than it could move the head query.

## Which Coder models exist (Hugging Face, checked 2026-11-07)

Searched `huggingface.co/api/models`, author `Qwen`, "Coder": 44 repos. **There is no official Qwen
Coder after Qwen3-Coder-Next.** Qwen hasn't released a 3.5, 3.6 or 3.8 Coder.

| Model | Released | Type | Licence | Official GGUF | Main third-party GGUF |
|---|---|---|---|---|---|
| Qwen2.5-Coder 0.5B / 1.5B / 7B / 14B / 32B (base + Instruct) | 2024-09/11 | dense | Apache-2.0 | yes (Instruct) | many; Ollama `qwen2.5-coder` |
| Qwen2.5-Coder-3B | 2024-11 | dense | **other** (Qwen research licence, not Apache) | yes | — |
| Qwen3-Coder-30B-A3B-Instruct | 2025-07-31 | MoE, 3B active | Apache-2.0 | no | unsloth (485K downloads), lmstudio-community, ggml-org (re-uploaded 2026-10-22) |
| Qwen3-Coder-480B-A35B-Instruct | 2025-07-22 | MoE, 35B active | Apache-2.0 | no | not a local model at our sizes |
| Qwen3-Coder-Next (+ Base, FP8) | 2026-01-30 | MoE 80B, 3B active, 256K | Apache-2.0 | yes (`Qwen/Qwen3-Coder-Next-GGUF`) | unsloth (177K), lmstudio-community |

**GGUF sizes** (repo file sizes, decimal GB):

- **Qwen3-Coder-30B-A3B** (unsloth):

  | UD-Q2_K_XL | UD-IQ3_XXS | Q3_K_M | IQ4_XS | UD-Q4_K_XL | Q4_K_M | Q5_K_M | Q8_0 |
  |---:|---:|---:|---:|---:|---:|---:|---:|
  | 11.8 | 12.8 | 14.7 | 16.4 | 17.7 | 18.6 | 21.7 | 32.5 |

- **Qwen3-Coder-Next** (unsloth):

  | UD-Q2_K_XL | UD-IQ3_XXS | UD-Q3_K_M | IQ4_XS | Q4_K_M | UD-Q4_K_XL | Q5_K_M | Q8_0 |
  |---:|---:|---:|---:|---:|---:|---:|---:|
  | 26.8 | 28.5 | 35.9 | 42.7 | 48.5 | 49.6 | 56.8 | 84.8 |

- **Qwen2.5-Coder-14B-Instruct** (Qwen's own): Q4_K_M 9.0, Q8_0 15.7.

**What "Qwen Coder" also means now: community cuts and fine-tunes**, none of them from Qwen:

- **The Flash-Next Coder cut.** `ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF` is a code-specialised
  cut of Qwen3.8-Flash-Next with half the experts. It's Apache-2.0, has 745K downloads (the most of
  any Coder GGUF found) and was updated upstream 10-19. Derivatives include Gyro-Coder (agentionai),
  abliterated and Strata repacks, and cut240.
- **Fine-tunes named "Qwen3.8-27B … Coder"**, e.g. DavidAU's "NEO-CODER-MAX" (1.5M downloads) and
  nerkyor's "Coder390" (0.9M). Their names are model-merge soup, and their provenance is unchecked.
- **Fine-tunes named "Qwen3.6 … Coder" and "Qwen3.5 … Coder"**, e.g. ManniX-ITA's
  Qwen3.6-27B-A3B-Coder-MTP and Qwen3.5-9B-Coder. The same caveat applies.

Some searchers will think one of these is an official "Qwen 3.8 Coder", the way "qwen 3.8 35b a3b" turned out to be a
community distill (`ai-grounding-demand-2026-10.md`). "There is no official Qwen Coder after Coder-Next" is a
checkable, useful sentence for the page.

## What we've already measured

**One Coder model: the ISTA Flash-Next Coder cut, IQ1_M** (`ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF`,
revision `5348543e`, both shards sha256-checked). It's measured for speed only, in 36 rows of
`benchmarks.json` (`rushuna-coder-iq1m-*`, `tamanna-coder-iq1m-*`). The 3060 page covers it in full, and
the 3090 page's bridge section repeats it:

| 4K / 16K / 32K prompt | RTX 3060 12 GB (Rushuna, 32 GB DDR4-2133) | RTX 3090 24 GB (Tamanna, 64 GB DDR4-3000) |
|---|---|---|
| Strata prompt processing, tok/s | 933 / 1,025 / 1,094 | 2,418 / 2,751 / 2,907 |
| Strata decode as shipped, tok/s | 30.2 / 30.9 / 30.6 | 109.2 / 111.3 / 109.2 |
| llama.cpp decode, `-b/-ub 4096`, tok/s | 9.1 / 8.5 / 7.9 | 32.9 / 30.4 / 28.6 |

Sources: `strata-vs-llama-cpp-rtx-3060`, `strata-vs-llama-cpp-rtx-3090`, and the bench records
`rushuna-strata-coder-2026-10-05/` and `tamanna-strata-2026-10-09/`.

- **No quality numbers.** The 3060 page quotes ISTA's own: 91.3% of the full model's SWE-bench
  Verified and 98.7% of its LiveCodeBench v6.
- **Agent safety.** The 3060 page carries the 10-27 Cohere update about Flash-Next's unrequested
  outbound upload while running as an agent. Any Coder page that recommends this cut for agent use
  must carry it too.
- **The Strata comparison flatters this model.** Strata runs only the Flash-Next family, so the
  Strata numbers can't stand in for "Qwen Coder" generally.

**Nothing measured on Qwen2.5-Coder, Qwen3-Coder-30B-A3B or Qwen3-Coder-Next.** LLM_repo holds only the
Flash-Next Coder (`qwen3.8-flash-next-gsq-rco-coder-gguf/`), and Tamanna and Rushuna have working
copies of the same. What our pages say about the official Coders is all model-card and community
figures:
- **codellama-vs-deepseek-coder-vs-qwen-coder** (lastmod 10-15) has a Qwen3-Coder-Next paragraph.
- **qwen-models-guide** has a Coder-Next row and pick. It's a frozen hub.
- **best-local-coding-models-2026** has the Qwen 2.5-Coder FIM picks and Coder-Next at 48 GB+. It's
  frozen. Its 16 GB table (L217) says **"Qwen 3.5 Coder Next"**, which matches no model on Hugging
  Face; it's probably Qwen3-Coder-Next. Fix it after the freeze lifts on 12-15.

## What a measured 3090 / 3060 piece would need

**Models and what fits.** Same `llama-bench` method as our other records; RAM figures are for the
offload arms:

| Model | Quant (size) | 3090 24 GB, Tamanna 64 GB | 3060 12 GB, Rushuna 32 GB |
|---|---|---|---|
| Qwen3-Coder-30B-A3B | Q4_K_M (18.6) | fully on GPU | `-ncmoe` offload |
| Qwen3-Coder-30B-A3B | UD-Q2_K_XL / IQ3_XXS (11.8-12.8) | — | near-fully on GPU, a quality trade |
| Qwen3-Coder-Next | Q4_K_M (48.5) | `-ncmoe` offload, about 25-30 GB in RAM | doesn't fit 32 GB with headroom |
| Qwen3-Coder-Next | UD-IQ3_XXS (28.5) | offload | offload, tight, like the Flash-Next IQ1_M at 29.6 GB |
| Qwen2.5-Coder 14B | Q4_K_M (9.0) | — | fully on GPU |
| Qwen2.5-Coder 32B | Q4_K_M (~20) | fully on GPU | — |
| Flash-Next Coder IQ1_M | — | already measured | already measured |

- **Comparators:** Qwen3.6-27B and Qwen3.8-27B. Both are already in benchmarks.json on the 3090. They
  answer the "Coder vs 3.6/3.8-27B" queries.
- **Downloads:** to LLM_repo with sha256 (invariant ae), pulled on Tamanna (12-13 MiB/s).
  - Coder-30B-A3B Q4_K_M plus a low quant: ~31 GB.
  - Coder-Next Q4_K_M plus UD-IQ3_XXS: ~77 GB.
  - Qwen2.5-Coder 14B and 32B Q4_K_M: ~29 GB.
  - **About 137 GB in all.** Tamanna had 168 GB free on 11-06, and Rushuna 53 GB on 10-05; working
    copies on Rushuna would need room cleared first.
- **What to measure:**
  - **Decode and prefill at 4K/16K/32K**, matching the Strata records so the Flash-Next Coder rows
    compare directly.
  - **`-ncmoe` sweeps** for the MoE files on each card.
  - **FIM latency** for the 2.5-Coders, which are still the autocomplete picks. A short llama-server
    `/infill` test, not just llama-bench.
- **Quality, an open question for Mark:**
  - Speed alone answers "what fits and how fast", not "which is better at code". Model-card scores
    (SWE-bench, LiveCodeBench) can be cited as theirs.
  - A small own eval, a fixed set of repo tasks graded pass/fail, is a different kind of article and
    much more work.
- **Internal links:** the article can't link to the frozen hubs (qwen-models-guide,
  best-local-coding-models-2026) before 12-15. It can link codellama-vs-deepseek-coder-vs-qwen-coder
  and the two Strata pages.
- **Rig time:** about a day of Tamanna and a day of Rushuna, unattended. Check against the hub
  experiment's post-window, which starts 11-18. Bench work doesn't touch the site, so it doesn't
  conflict.

## Open for Mark

1. Measured piece, or a cheaper first step? The first step would be a dated section on
   codellama-vs-deepseek-coder-vs-qwen-coder (not frozen) saying what's current and that there's no
   3.x Coder after Coder-Next. It could ship before the freeze lifts.
2. Speed only with cited quality figures, or an own pass/fail eval?
3. Include the community "Coder" fine-tunes, or name only the ISTA cut, whose provenance we checked?

---

# Pre-registration (LOCKED 2026-11-08): Qwen3-Coder-30B-A3B and Qwen3-Coder-Next on the 3090 and 3060 — 2026-11-08

**Status: LOCKED 2026-11-08 (Mark's decisions of the same day, P10).** The sha256 of this file as locked is in the
lock commit's message; nothing below this heading changes after it. Later facts go in the records (P9) or in dated
amendments appended after P10, never as edits. Nothing was downloaded, copied or run before the lock. The only
earlier change on any rig is P7's Rushuna deletion, which isn't a run.

Repo facts below were read on 2026-11-08 from `huggingface.co/api/models/<repo>?blobs=true`. The downloads are
checked against these exact sha256s.

## P1. Question

Which of the two current official Qwen Coders fits a 24 GB RTX 3090 and a 12 GB RTX 3060, how fast does each run at
4K / 16K / 32K of context, and how does each score on HumanEval against the two 27B general models we've already
scored on the same card (Qwen3.6-27B 82.32%, Qwen3.8-27B 80.49%)?

Qwen2.5-Coder is out (Mark, 11-08), and with it the FIM latency test planned in the scope above. The ISTA Flash-Next
Coder cut isn't re-measured; its 36 rows stay as they are.

## P2. Models (exact files)

| Model | Repo @ revision | File / quant | Bytes | sha256 (LFS oid) | Licence | Used on |
|---|---|---|---:|---|---|---|
| Qwen3-Coder-30B-A3B-Instruct | `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` @ `b17cb02d` | `Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf` | 17,665,334,432 | `2841aa31…ff2533` | Apache-2.0 | both rigs |
| Qwen3-Coder-Next | `Qwen/Qwen3-Coder-Next-GGUF` @ `b82fb738` (official) | `Qwen3-Coder-Next-Q4_K_M/…-0000{1..4}-of-00004.gguf` | 48,411,092,032 | `6bcfc9f9…09534da`, `817def06…f01d3`, `23aa634d…c99883f`, `249c768c…bdb2b` | Apache-2.0 | Tamanna |
| Qwen3-Coder-Next | `unsloth/Qwen3-Coder-Next-GGUF` @ `ce09c67b` | `Qwen3-Coder-Next-UD-IQ3_XXS.gguf` | 28,482,506,752 | `00a9bf4f…ac0ade4` | Apache-2.0 | Rushuna (speed); Tamanna (HumanEval arm CN3) |

- **Coder-30B-A3B: no official GGUF.** `Qwen/Qwen3-Coder-30B-A3B-Instruct-GGUF` doesn't exist (the API returns
  "Invalid username or password", its answer for a missing repo). So unsloth, per Mark's rule, and **UD-Q4_K_XL**
  because it's the quant both 27B comparators were scored at. That's the closest quant parity the HumanEval
  comparison can get.
- **Coder-Next: official GGUF exists**, so Qwen's own Q4_K_M on Tamanna. Its smallest quant is Q4_K_M. At 48.4 GB it
  can't run on Rushuna, which has 32 GB of RAM and a 12 GB card: 44 GB in all, less the OS. So Rushuna gets
  unsloth's UD-IQ3_XXS (28.5 GB). That's the size class the Flash-Next IQ1_M already ran at on that box (29.6 GB).
  **Why the departure from "official first" (Mark, 11-08):** Qwen's official repo has nothing below Q4_K_M. At 48.4 GB
  that doesn't fit Rushuna's 32 GB of RAM plus its 12 GB card.
- **Quant parity on the HumanEval side isn't exact for Coder-Next.** It runs at Qwen's official Q4_K_M; the 27B
  anchors are unsloth's UD-Q4_K_XL. Both are ~4.5-4.8 bits, but they're different recipes from different publishers.
  Mark (11-08): keep the official Q4_K_M; the article states that the anchors are UD-Q4_K_XL.
- **Comparators (already in LLM_repo, nothing to download):**
  - `LLM_repo/from-miu/Desktop/lucebox-hub/dflash/models/unsloth/Qwen3.6-27B-UD-Q4_K_XL.gguf`, 17,612,564,704 B.
    This is the event #1 file, re-hashed and restored 2026-09-24.
  - `LLM_repo/qwen3.8-27b-gguf/Qwen3.8-27B-UD-Q4_K_XL.gguf`, 17,923,394,624 B. This is the event #3 file, repaired
    2026-09-23. **Not** the `.CORRUPT-event3` file beside it.
  - Both get hashed against their upstream digests before use (memory: fault-window copies).

## P3. Rigs and the pinned build

| | Tamanna | Rushuna |
|---|---|---|
| Card | RTX 3090 24 GB, PCIe 4.0 x16 | RTX 3060 12 GB, PCIe 3.0 x16 |
| CPU / RAM | Ryzen 7 5700X, 64 GB DDR4-3000, `-t 8` | i7-7700, 32 GB DDR4-2133, `-t 4` |
| Driver (11-08) | 580.178.04 | 580.173.02 |
| llama.cpp | `~/llama-v0.4.0/build/bin`, v0.4.0 `5266f24` (source build, sm_86) | `~/llama-v0.4.0`, v0.4.0 `5266f24` (CUDA 12.8 bundle, sm_86) |
| Coder-30B-A3B | fully on the card (`-ncmoe 0`) | expert offload |
| Coder-Next | expert offload (Q4_K_M) | expert offload (UD-IQ3_XXS) |

**Why v0.4.0 `5266f24`:**
- **The Strata records are on it.** It's the llama.cpp in both Strata records (the L1/L2 arms on both rigs) and in
  the 3060 `-ncmoe` record of 09-11. "Matching the Strata records" means the same build, flags and prompt lengths.
  Then the new rows sit directly beside the Flash-Next Coder's llama.cpp rows.
- **It's already on both rigs.** Nothing needs building, and neither build needs sudo.
- **v0.7.0 is on Tamanna only.** It's the voice run's build, and Rushuna doesn't have it. Using it would mean building
  it on Rushuna and losing the match with the Strata rows. On Tamanna, v0.4.0 and v0.7.0 decode the same (162.9 vs
  162.2 tok/s, Qwen3.6-35B-A3B, 11-03). But v0.7.0 prefills about 16% faster (4,362 vs 3,768 tok/s at d=0). The
  article says so: prefill on a current build will likely be higher than ours.
- **Cost: the 27B HumanEval scores ran on a different build.** They ran on b10088 (`67b9b0e`), on Miu, with this same
  3090 card before it moved to Tamanna. So both 27Bs are re-run as anchors on v0.4.0 on Tamanna (P5). That's needed
  anyway: Qwen3.6-27B's raw-path per-problem vector was lost in the 08-15 `/tmp` clean, and a paired McNemar test
  needs it.
- **Day-0 load check.** Before any measured cell, check that v0.4.0 loads both Coder-Next files (qwen3next
  architecture). If either fails, STOP and ask. Don't switch builds mid-registration.

## P4. Speed

**Harness:** `bench_coder.py` from `rushuna-strata-coder-2026-10-05/`, llama.cpp arms only, with the Tamanna Strata
record's changes (llama.cpp path, `-t`, model by run directory, stage search 48 → 0). Plus `memwatch.py`, unchanged.
- **Measurement:** temperature 0, `max_tokens 256`. Per cell, (priming request, measured request) × 3. Report the
  mean of the 3 measured requests (min..max).
- **Arms:**
  - **L1:** `llama-server -ngl 99 -ncmoe N -fa on -c 34816 -np 1 --lazy-mode on -t T`.
  - **L2:** the same plus `-b 4096 -ub 4096`.
  - **No L3.** Its pinned-host variant is a no-op on v0.4.0 (`GGML_CUDA_REGISTER_HOST`, dated note 2026-10-10), so
    it would repeat L2.
- **Prompts: re-cut, not copied.** The Strata prompt files are exact token counts for the Flash-Next tokenizer, and
  the Coders use Qwen3's tokenizer. So prompts are re-cut from the same `corpus.txt` (sha256 `09a0975d…`) to exactly
  4,096 / 16,384 / 32,512 tokens with each Coder's tokenizer via `/tokenize`, as Rushuna's first prep did. Their
  sha256s go in the record.
  - The new rows compare with the Flash-Next Coder rows at equal token counts and the same source text, but not as
    identical byte strings. The article says so.
- **Stage search, for N:** Tamanna's method. At L2, `-c 34816`, step N down by 2 from 48 (Coder-Next) or up by 2 from
  0 (Coder-30B on Tamanna). N = the lowest value that serves a 32,512-token request. The same N is used for L1.
- **3060 offload sweep** (Rushuna, both models): `ncmoe_sweep.py` from `rushuna-3060-qwen36-ncmoe-2026-09-11/`.
  - Command: `llama-bench -ngl 99 -ncmoe N -fa 1 -p 0 -n 128 -d 0,4096 -r 3 -t 4 -lm mmap`.
  - N = 48, then down by 4 to the lowest that loads, plus that lowest even N. Peak VRAM is sampled for each.
  - The sweep's lowest N (at d=4096) and the server's N (at 34,816 context) will differ. Both are recorded.
  - The sweep stays on Rushuna, as Mark asked. On Tamanna the server stage search already finds Coder-Next's N.
- **Void rules,** as in the Strata records:
  - prompt_n within ±3 tokens of the cell's other requests; cache_n 0; swap-out 0;
  - PCIe link gen 4 x16 (Tamanna) or gen 3 x16 (Rushuna) during every prefill.
  - **NVMe reads during a measured decode:** flag over 64 MiB, and void the cell over 1 GiB. That's the
    page-cache-pressure risk for Coder-Next on Rushuna's 32 GB.
  - A void cell is re-run once. Void twice and it's reported as void.
- **Rushuna's Coder-30B rows have context.** Tamanna's Coder-30B arms are resident, but the Rushuna 30B-A3B rows sit
  beside Qwen3.6-35B-A3B's 3060 rows (`-ncmoe 24`, 38.5 tok/s) for context. They're different models, and the
  article says so.

## P5. Quality: HumanEval, the 3.8-vs-3.6 27B protocol

The same as `miu-memory-retest-humaneval-2026-08-16/humaneval-3.8-bracket/`:
- **Benchmark and scoring:** all 164 problems; pass@1. Scored by the official OpenAI `human-eval` in the
  `he-scorer:b10088` image on Miu, with `--network none --cap-drop ALL --security-opt no-new-privileges --memory 4g
  --pids-limit 256` (image present on Miu, 11-08).
- **Generation:** `he_gen.py`, raw prompts to `/v1/completions`. Sampling pinned: temperature 0, top_p 1, top_k 0,
  min_p 0, typical_p 1, repeat/presence/frequency penalty neutral, seed 42, `max_tokens 512`. Stops are lm-eval's
  five: `\nclass \ndef \n# \nif \nprint`.
- **Server:** `llama-server -ngl 99 -fa on -c 4096 --no-jinja --no-mmap`, plus `-ncmoe N` for the offloaded
  Coder-Next. So no chat template, and both Coders run as plain code completers, exactly as the 27Bs did.
- **One change to `he_gen.py`: the URL.** It runs on Miu, as before, against Tamanna's llama-server on the LAN,
  bound to Tamanna's LAN address on port 8099. So the generator, its `datasets` copy of `openai_humaneval` and the
  scorer stay byte-identical to the 08-16 run. The diff goes in the record.
- **Provenance:** sha256 of the working copy immediately before the server loads it and again after the eval. Plus
  `llama-server` and `libggml-cuda.so` sha256s. A pre/post mismatch voids the arm.
- **Arms, all on Tamanna, in this order:**
  1. **A36:** the Qwen3.6-27B anchor;
  2. **A38:** the Qwen3.8-27B anchor;
  3. **C30:** Coder-30B-A3B, resident;
  4. **CN:** Coder-Next Q4_K_M, at the speed run's N;
  5. **CN3:** Coder-Next UD-IQ3_XXS, the 3060's file, run on Tamanna (Mark, 11-08). N = the lowest even N, stepping
     up from 0, at which the server loads and answers at `-c 4096`;
  6. A36 again, as a drift check. Its completions must be byte-identical to slot 1.
- **The CPU/GPU split can change floating-point results.** CN and CN3 score the file at Tamanna's split. A different
  `-ncmoe` on another card could flip a problem or two. The record states each arm's N.
- **The anchors are what the Coders are compared against.** The published 82.32 / 80.49 stay as the article's
  reference figures. Paired tests (exact McNemar, two-sided) use the anchors' fresh vectors, because the comparison has
  to be on the same build and host.
- **Not run on Rushuna.** Rushuna's Coder-30B is the same file as Tamanna's, and its Coder-Next file is scored on
  Tamanna as CN3.

## P6. Predictions (set before any download)

**Fit (N):**

| | Predicted N | Band |
|---|---|---|
| Tamanna Coder-30B-A3B, L2, `-c 34816` | 0 (fully on the card, ~22 GiB) | N ≤ 2 |
| Tamanna Coder-Next Q4_K_M | ~30 of 48 | 26–34 |
| Rushuna Coder-30B-A3B | ~31 of 48 | 26–36 |
| Rushuna Coder-Next UD-IQ3_XXS | ~32 of 48 | 28–40 |

**Speed, tok/s** (the server arms at N; bands, not points):

| | Decode 4K / 16K / 32K | L2 prefill 4K / 32K | L1 prefill 4K / 32K |
|---|---|---|---|
| Tamanna Coder-30B-A3B | 120–175 / 90–150 / 65–125 | 2,500–4,500 / 1,400–3,300 | 2,000–4,000 / 1,000–2,800 |
| Tamanna Coder-Next Q4_K_M | 22–40 / 20–38 / 18–36 | 700–1,600 / 700–1,700 | 250–520 / 250–520 |
| Rushuna Coder-30B-A3B | 28–45 / 22–40 / 17–35 | 800–1,800 / 600–1,600 | 200–450 / 200–450 |
| Rushuna Coder-Next UD-IQ3_XXS | 7–15 / 7–14 / 6–14 | 300–900 / 300–900 | 80–250 / 80–250 |

**Structural predictions** (these are the ones worth being wrong about):
- **S-a: Coder-Next decode stays nearly flat with depth.** 32K decode ≥ 85% of 4K, on both rigs. Most of its
  layers are linear-attention (Gated DeltaNet), so KV traffic barely grows.
- **S-b: Coder-30B-A3B decode falls with depth.** It uses full attention in every layer, so 32K decode ≤ 80% of 4K
  on Tamanna.
- **S-c: L2 beats L1 for prefill** for every offloaded config, by ≥ 1.5×. It did on the Flash-Next Coder (2.6×
  Tamanna).
- **S-d: the 3060 sweep is monotonic** for both models, with decode rising as N falls. At N = 48 (all experts in
  RAM), tg128 d=0 is 22–32 for Coder-30B and 6–12 for Coder-Next.

**HumanEval pass@1:**
- **Anchors reproduce within ±3 problems.** A36 at 132–138 of 164 (published 135). A38 at 129–135 (published 132).
  Outside that, the build/host change moved greedy output. The article then says so, and the paired comparison stands
  on the anchors alone.
- **C30 (Coder-30B-A3B): 75–88% (123–144 / 164).** It's no better than Qwen3.6-27B in any way the test can detect:
  exact McNemar against A36, p ≥ 0.05. A 3B-active coder against a 27B dense general model is predicted to be a tie,
  not a win.
- **CN (Coder-Next): 80–93% (131–153 / 164).** Its point estimate is above A36, A38 and C30. Against A36 it's
  predicted **not** significant (p ≥ 0.05).
- **CN3 (Coder-Next UD-IQ3_XXS): 75–91% (123–149 / 164).** It's at or below CN, within 6 points. Against CN it's
  predicted **not** significant (p ≥ 0.05): on HumanEval a 3060 owner gives up nothing the test can detect.
- **How it's written up:** if CN's gap over A36 does reach p < 0.05, the article says Coder-Next measurably beats
  Qwen3.6-27B on HumanEval. If it doesn't, the result is "a statistical tie", in the 3.8-vs-3.6 page's wording. The
  same rule applies to every pair.

## P7. Downloads, disk and copies

**Downloads: on Miu, the night of 2026-11-08 (Mark).** Into LLM_repo, invariant ae. Each goes into its own
directory, with a README (repo, revision, date, licence) and `SHA256SUMS`:

| LLM_repo directory | Content | GB |
|---|---|---:|
| `qwen3-coder-30b-a3b-instruct-gguf/` | UD-Q4_K_XL | 17.67 |
| `qwen3-coder-next-gguf/` | official Q4_K_M, 4 shards | 48.41 |
| `qwen3-coder-next-gguf-unsloth/` | UD-IQ3_XXS | 28.48 |
| **Total** | | **94.56** |

- **How:** 8 ranged curl segments per file, pinned to the P2 revisions (`/resolve/<revision>/<file>`). At Miu's
  ~2 MiB/s that's about 12.5 h.
- **Verified** when every file's sha256 matches its P2 LFS oid. That means all 6 files, re-hashed on Miu after the
  download finishes. **No file is copied to a rig and no run starts until all 6 match.** A mismatch means
  re-downloading that file; it is never used.
- LLM_repo had 2.6 TB free on 11-08.

**Disk on the rigs:**
- **Rushuna, done 2026-11-08 (Mark's go): the Flash-Next Coder working copy was deleted** after it matched.
  - That was `~/bench-models/qwen3.8-flash-next-coder/IQ1_M/`, both shards, 58.4 GB.
  - Its sha256s matched `SHA256SUMS.hub`, and the LLM_repo copy re-checked OK against the same file the same day.
  - df went from 7.0 GB free (97%) to **62 GB free (71% used)**.
  - The run needs 46.15 GB (Coder-30B 17.67 + Coder-Next UD-IQ3_XXS 28.48), leaving ~16 GB.
- **Tamanna: 168 GB free on 11-08.**
  - The working copies need 130.1 GB: Coder-30B 17.67, Coder-Next Q4_K_M 48.41, Coder-Next UD-IQ3_XXS 28.48 (CN3),
    and the two 27B anchors 17.61 and 17.92. That leaves ~38 GB.
  - **Rule (Mark): at least 20 GB free on Tamanna at all times**, for the voice models. Before each copy, `df`. If
    the copy would leave less than 20 GB, don't copy. Instead, delete a Coder-run working copy whose arms are done
    (the LLM_repo copy is canonical), then re-check.
- **Copies:** rsync from LLM_repo to each rig. sha256 on arrival against the store's `SHA256SUMS`, and again just
  before load. Working copies go in `~/bench-models/qwen-coder/`.

**Tamanna: the voice environments are off limits (Mark).** The voice run is 2026-11-24 and its installs are done.
- **Not touched, opened for writing, upgraded or run:**
  - `~/voice-pipeline/` (its venvs, TLS, keys and binaries);
  - `~/voice-01/`;
  - `~/llama-v0.7.0/`;
  - uv's managed Python and caches (`~/.local/share/uv`, `~/.cache/uv`);
  - `~/.cache/huggingface`.
- **Nothing installed with pip or uv.** These runs need only `~/llama-v0.4.0` and the system `python3` (stdlib) for
  the harness.
- Work files go in `~/tamanna-qwen-coder-2026-11/`.
- **Port 8099,** which isn't a voice port. No server stays up after its arm.

## P8. Schedule and run time

**Mark (11-08): the Tamanna runs happen this week, not after the voice run. Finish every Coder run by 2026-11-20.**
Nothing starts on any rig until P7's downloads are verified.

| Day (PST) | Rig | What | Estimate |
|---|---|---|---|
| Sun 11-08 night → Mon 11-09 | Miu | downloads (12.5 h unattended), then sha256 of all 6 files against P2 | done ~11-09 midday; hashing ~15 min |
| Mon 11-09 | Rushuna | copy + hash (LAN, ~46 GB); day-0 load check (v0.4.0 loads both files); prompt re-cut | ~1 h |
| Mon 11-09 → Tue 11-10 | Rushuna | sweep + server matrix (L1, L2): Coder-30B, then Coder-Next UD-IQ3_XXS | ~4.5 h unattended |
| Tue 11-10 | Tamanna | copy + hash (~130 GB, with the 20 GB check); day-0 load check; prompt re-cut | ~1.5 h |
| Tue 11-10 → Wed 11-11 | Tamanna | speed: Coder-30B resident (N=0 check) + matrix; Coder-Next Q4_K_M stage search + matrix | ~3 h unattended |
| Wed 11-11 → Thu 11-12 | Tamanna + Miu | HumanEval, in order: A36 → A38 → C30 → CN → CN3 → A36. Generation client and scorer on Miu | ~2 h with loads and hashes |
| 11-13 → 11-20 | either | buffer: re-runs of void cells, any day-0 failure (STOP and ask), the records | must end by 11-20 |

- **Rushuna and Tamanna don't depend on each other.** Each starts once the downloads are verified.
- **11-11 is the hub experiment's ship day.** That's site work only, and nothing here deploys. If Mark wants that day
  quiet, HumanEval moves to 11-12.
- **Nothing here deploys.** The article ships after the runs, outside the 08/12/16/20 PT Bluesky slots.
- **The freeze:** the article can't link qwen-models-guide or best-local-coding-models-2026 before 12-15. So it ships
  linking codellama-vs-deepseek-coder-vs-qwen-coder and the two Strata pages, and the hub links get added on or after
  12-16.

## P9. What gets written down

- **Record directories:** `docs/bench-results/rushuna-qwen-coder-2026-11-XX/` and
  `docs/bench-results/tamanna-qwen-coder-2026-11-XX/`. They hold:
  - the lock hash;
  - every command line and the build sha256s;
  - the prompt-file hashes;
  - per-request JSON and the memwatch logs;
  - the HumanEval generations, per-problem results and summaries (pass@1, vector, hashes), plus the McNemar tables;
  - a README with P6 filled in, hit or miss.
- **benchmarks.json rows:** one per speed cell and sweep point, with full provenance (repo, revision, sha256
  verified against the upstream LFS oid) and `display_attached false`.
- **Notes on every Tamanna row:** the DDR4-3000 note.
- **Notes on every row where the rigs sit side by side:** the 3000-vs-2133 confound, stated each time.

## P10. Mark's decisions (2026-11-08), applied before the lock

1. **Rushuna disk:** hash the Flash-Next Coder working copy against LLM_repo, and delete it if it matches. Done: it
   matched and was deleted. Rushuna has 62 GB free (P7).
2. **Rushuna's Coder-Next file:** unsloth UD-IQ3_XXS. The reason is in P2.
3. **HumanEval on the 3060's UD-IQ3_XXS:** yes, run on Tamanna as arm CN3 (P5, P6).
4. **3090 Coder-Next:** the official Q4_K_M. The article notes that the 27B anchors are UD-Q4_K_XL (P2).
5. **Downloads:** on Miu the night of 11-08, into LLM_repo, with the sha256s checked against upstream (P7).
6. **Schedule:** the Tamanna runs happen this week and finish by 11-20. Don't touch the voice environments, and keep
   at least 20 GB free on Tamanna (P7, P8).
7. **Gate:** no run starts until the downloads are verified.

## A1. Clarification (2026-11-17, Mark): the prompt_n void rule uses the stricter reading

P4's "prompt_n within ±3 tokens of the cell's other requests" means **every pair of requests in the cell is within 3
tokens**: max − min ≤ 3 across all 6 requests (3 primes, 3 measured). It does **not** mean ±3 around the cell's
centre, which `rushuna-qwen-coder-2026-11/summarize.py` applied and the Tamanna Strata record used.

- **Why it came up:** the per-request nonce line tokenizes to a slightly different length each time, so some cells
  span 4 tokens (cache_n was 0 everywhere). The Rushuna record flagged the two readings for Mark on 2026-11-10.
- **Applies to:** every cell of this registration, on both rigs, from this date, including cells already measured.
  Records re-state their verdicts under it. Records outside this registration (the Strata ones) are not re-judged.
- **Re-runs:** P4 is unchanged. A void cell is re-run once, and void twice is reported as void. Mark (2026-11-17): the
  Rushuna Coder-Next L1-16K re-run, void under this reading, is reported as void with no further re-run.
- **Not a change to the lock text above.** The lock commit is 918e33f8; this section is appended after P10 as the
  lock header requires.

## D1. Deviation (2026-11-17, Mark): post-hoc failure audit of the HumanEval result

**POST-HOC. Decided after seeing the HumanEval results. Exploratory, not confirmatory.** The locked P5 scores stay
the primary result, unchanged: A36 137, A38 130, C30 100, CN 120, CN3 113 of 164
(`tamanna-qwen-coder-2026-11/`, "HumanEval (P5)").

- **Why:** all three Coder arms scored below their P6 bands, C30 by 23 problems. Mark asked for every failure to be
  classified before anything was written up, with A36 as the control, and for the harness and template to be
  checked.
- **What the audit checked:** the harness has no code-extraction step, so every arm's completion is scored exactly
  as returned. No arm gets a chat template or thinking mode, because P5 locks raw `/v1/completions` with
  `--no-jinja`. All arms get the same five stops, and none of them catches ```.
- **Finding:** **49 of C30's 64 failures are format failures.** The model writes a function body, then a closing
  ``` it never opened, then a prose explanation. That's a SyntaxError, so the problem fails. CN has 10 of 44 format
  failures, A36 has 0 of 27. Per class (wrong logic / fence + prose, passes once cut / fence + prose, still fails /
  junk tokens / helper cut by `\ndef` / truncation / other):
  - C30: 12 / 41 / 7 / 0 / 1 / 3 / 0;
  - CN: 26 / 3 / 1 / 4 / 2 / 3 / 5;
  - A36: 23 / 0 / 0 / 0 / 0 / 0 / 4.
- **Fence-cut counterfactual (post-hoc):** cut every completion at its first ```, the same rule for every arm, and
  re-score in the same sandbox with P5's flags:

  | Arm | Locked (primary) | Fence-cut (post-hoc) |
  |---|---:|---:|
  | A36 | 137/164 (83.54%) | 137/164 (83.54%) |
  | A38 | 130/164 (79.27%) | 130/164 (79.27%) |
  | C30 | 100/164 (60.98%) | 142/164 (86.59%) |
  | CN | 120/164 (73.17%) | 123/164 (75.00%) |
  | CN3 | 113/164 (68.90%) | 118/164 (71.95%) |

  Under the cut, C30 vs A36 becomes a tie (exact McNemar p = 0.458), and C30 beats CN (p = 0.0034).
- **Status:** the cut rule was chosen after looking at C30's failures, so the table can't support a claim. It's
  evidence for a hypothesis, and the separate pre-registration `qwen-coder-mbpp-confirm-2026-11.md` tests that
  hypothesis on MBPP with the rule fixed in advance.
- **Files:** `tamanna-qwen-coder-2026-11/audit-exploratory/` (method, per-item classes, cut inputs and sandbox
  results, scripts).
- **Not a change to the lock text above.** Appended after P10 and A1, as the lock header requires.
