# Jev-mode test, phase 1: choose vs write on the ten-seeds 47-item split

**2026-09-21, Miu (RTX 3090), Qwen3.6-27B Q4_K_M fully resident, one server, one session.**
Fork: thecodacus/llama.cpp `parallel-decision` @ `14d04e755` (2026-09-20). Full environment in
`environment.txt`; every number below is in `analysis.json`, computed by `analyze.py` from `raw/`.

## Result against the pre-registration

| | pre-registered | measured | verdict |
|---|---|---|---|
| accuracy | choose within ±2 items of write | write **23/47**, choose **21/47** (−2) | inside, at the edge |
| latency | choose at least 5× lower | **3.4×** mean (0.795 s → 0.235 s), 3.5× at p95 | **outside — the finding** |

Both paths are deterministic: three full passes each, predictions byte-identical across reps, and
choose's per-field probabilities identical to 1e-9 across reps.

## The control, and the 21/47 expectation

The brief expected write to reproduce 21/47 (44.68%). It reproduced **23/47** on all three passes.
The ten-seeds README records why: 21/47 was scored through **PEFT + NF4 on the HF safetensors**
(section 3), and on **this GGUF through llama.cpp** the recorded no-adapter baseline is 23/47
(section 7: 5 reps on b10088; `scored_v040/baseline_rep{0,1}`: 2 reps on v0.4.0). Against
`scored_v040/baseline_rep0.json` today's control matches on score, on every per-field count
(30/30/30), on raw-valid (46/47), and on **46 of 47 predictions**. The one flip is item 28
(mode `explore` → `chat`, wrong both times) across a build change (v0.4.0 `5266f24` → fork
`b9891`); the 08-30 record logged two flips between reps on one build, so one across builds is
inside the executor noise the series already carries. The other five raw-string differences are
newline formatting with identical predictions. The gate I had scripted asked for zero flips, so
the choose runs were started by hand after reading the diff; the 21-vs-23 question is Mark's to
rule on, and nothing downstream changes if the answer is "discard".

So on this file, **writing the answer gets 23/47 = 48.94%**, and the newsletter's "44.68% writing
the answer" is the NF4 figure. Choose landing on exactly 21/47 = 44.68% is a coincidence.

## Accuracy

| | exact | tool | mode | scope | raw-valid |
|---|---:|---:|---:|---:|---:|
| write (`/v1/chat/completions`, temp 0) | 23/47 | 30 | 30 | 30 | 46/47 |
| choose (`/v1/decision`, tree) | 21/47 | 30 | 31 | 28 | 47/47 |

Item level: both right on 20, write-only on 3 (idx 40, 58, 73), choose-only on 1 (idx 61),
neither on 23. The two paths give the same three-field prediction on 36 of 47 items. Field
disagreements: tool 2 (61, 73), mode 7 (13, 22, 28, 37, 58, 60, 69), scope 2 (40, 68). Choose
never emits an invalid value (47/47 raw-valid, by construction); write produced one unparseable
answer, as it did in every recorded run.

The 23 items neither path gets are the same shape as the ten-seeds "34 items score the same
with or without an adapter": mostly `rag/recall/session` gold that both paths call
`answer/chat/all`.

## Latency

Client wall-clock per item, 141 samples per path (3 × 47), both paths warm (the system prompt is
cached on both: write `cache_n` 605 of ~652 prompt tokens, choose `cached_tokens` 723 of ~769).

| | mean | median | p95 | min | max |
|---|---:|---:|---:|---:|---:|
| write | 0.795 s | 0.767 s | 0.927 s | 0.731 s | 1.134 s |
| choose | 0.235 s | 0.233 s | 0.264 s | 0.207 s | 0.365 s |
| ratio | 3.38× | | 3.52× | | |

Where the time goes (server-reported means): write = 295 ms prompt for the ~47 uncached user
tokens + **494 ms generating 19.85 tokens** at ~25 ms/token. Choose = 64 ms prefill of the same
context + **166 ms scoring 21 rows** in one `llama_decode` (`rounds` = 1 on every request at
3 decision slots; the 12 leaves plus 9 divergence nodes fit one batch). So choose replaces a
20-token decode with one batched forward of 21 rows, and on a 27B dense model at Q4 that batched
forward costs about a third of what the decode did, not a fifth. The video's 300 ms vs 3.5 s
(11.7×) was Gemma 4 12B writing a longer JSON; this schema's answer is 19 tokens, so write's
ceiling was already low.

Cold first call (page cache warm, prompt cache empty): choose 2.05 s (1.78 s prefill of the
769-token prefix), write 1.24 s. Not in the table; every tabled request is warm.

## Is confidence lower on the wrong ones?

Yes, on average, with a lot of overlap. Choose was wrong on 26 items, right on 21.

| | right (21) | wrong (26) |
|---|---:|---:|
| min field probability, mean / median | 0.797 / 0.832 | 0.622 / 0.564 |
| product of the three, mean / median | 0.720 / 0.791 | 0.455 / 0.429 |

Per field, the chosen value's probability when that field is right vs wrong: tool 0.877 vs 0.804,
mode 0.886 vs 0.798, scope 0.801 vs 0.678. Scope is both the weakest field (28/47) and the least
confident.

A refusal threshold on the minimum field probability:

| refuse below | wrong caught | right lost |
|---:|---:|---:|
| 0.5 | 9 of 26 | 1 of 21 |
| 0.6 | 14 | 3 |
| 0.7 | 18 | 5 |
| 0.8 | 21 | 8 |

At 0.5 it catches a third of the errors for one lost correct answer; past 0.7 it starts eating
the right answers. The tail is the problem: six wrong items sit above 0.77 (idx 53, 18, 24, 10,
78, 82), and idx 82 is wrong at tool 1.00 / mode 0.995 / scope 0.98 (gold `explore`, chose
`recall`, write made the same call). Confident-and-wrong exists; the score is informative, not
a guarantee. The full ranked list is in `analysis.json` → `confidence.wrong_items`.

## What was run, exactly

- Server (`launch_server.sh`): the ten-seeds section-7 flags `-ngl 99 -fa on -c 4096 --jinja`,
  plus `-kvu --decision-seqs 3`, `--load-mode mmap`. Model at 22.0 GB on the card beside the
  desktop's 4.2–4.4 GB.
- Choose (`run_decision.py choose`): `instructions` = the deployed intent system prompt
  (`deployed.py`, solo.py sha256 `32456044…`), unchanged; `schema` = the three enum fields with
  their deployed label sets in the order the prompt lists them; one context per request;
  `mode: tree`. The endpoint **requires a description per field** (HTTP 400 without one), so each
  field carries the prompt's own header phrase verbatim ("what tools are needed", "what kind of
  thinking", "where to search (only matters when tool is rag or web_and_rag)") — asserted present
  in the prompt at import, so the catalogue adds nothing the write path did not see. The decision
  object is JSON-dumped and pushed through the same `parse_and_sanitise()` as the written answer
  (past-reference override, docs/web_and_rag override), then `score()` exact.
- Write (`run_decision.py write`): byte-for-byte the `score_lora.py` request — temperature 0,
  max_tokens 100, thinking off, stock system prompt.
- Order: write ×3 then choose ×3, same server process, no restart between.

## Things that did not work, recorded so nobody repeats them

1. `--no-mmap` is gone from the fork's argument parser (b9891 > v0.4.0). Its equivalent
   `--load-mode none` then failed twice with `CUDA error: out of memory` 2 s into load, before
   any weights were on the card. Swap was 8/8 GB used and the box had ~17 GB free, so the 17 GB
   host read plus pinned staging is what ran out. `--load-mode mmap` (the default) loads the same
   weights to the same card; only the host path differs for a fully resident model.
2. `--decision-seqs 16` (the README's example size) then failed for real: `cudaMalloc` refused
   202 MiB at ~22 GB used. The fork's minimum is 3, and at 3 this schema still scores in one round.
   A bigger schema or a bigger context would need the desktop down.
3. The fork's log does not print the model / KV / compute buffer sizes at its default verbosity;
   the 22.0 GB figure is `nvidia-smi` after load minus nothing (the desktop is inside it).

## Not done, deliberately

Nothing on the soak; nothing to content/. No `greedy` mode run, no `contexts` batching (one
request per item so each has its own wall-clock), no thread or ubatch sweep. The desktop stayed up
throughout, as instructed, which is what set the 3-slot ceiling.

## Files

| path | content |
|---|---|
| `run_decision.py` | harness, both paths, imports the ten-seeds `deployed.py` / `score_lora.py` |
| `analyze.py`, `analysis.json` | everything in this README, plus the ranked wrong-item list |
| `launch_server.sh` | the server line that served every run |
| `environment.txt` | fork commit, build flags, model sha256, GPU state, scorer hash |
| `raw/write_rep{0,1,2}.json`, `raw/choose_rep{0,1,2}.json` | per-item records: preds, raw / decision, probabilities, usage, server timings, wall |
| `logs/server.log` | all six launches including the four failures; `logs/runs.log` the run summaries |
