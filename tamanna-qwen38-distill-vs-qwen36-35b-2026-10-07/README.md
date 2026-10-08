# Qwen3.8-35B-A3B-Distill (empero-ai) vs Qwen3.6-35B-A3B, both Q4_K_M, Tamanna, 2026-10-07

Pre-registration: `docs/candidates/qwen38-35b-distill-vs-qwen36-35b-2026-10.md`. Run as pre-registered, approved by Mark
2026-10-07, with the published Q4_K_M files and the thinking-on pass kept. Both models ran on the **v0.4.0 pin**
(`5266f24`). No fork was involved.

## Verdict, stated first

**Primary gate: NO DIFFERENCE.** The distill scored **22/47** and the base Qwen3.6-35B-A3B **23/47**, one item apart. The
gate counts ±1 as no difference. Both passes were identical for both models: 47 of 47 predictions and 47 of 47 raw
strings.

**The pre-registered format rule also fired, but not for the reason it anticipated.**

- **The rule:** "≥ 5 items with a `<think>` leak or no parseable answer on pass 1". It anticipated reasoning running
  past the 100-token budget.
- **What tripped it:** the distill had **6 unparseable answers, and none of them is reasoning.** Zero `<think>` spans
  and an empty `reasoning_content` on every item. On items 26, 28, 29, 40, 41 and 72 the distill ignored the
  classifier system prompt and **answered the user conversationally** ("That's a genuinely good question, and I think
  the honest answer is: I don't know…") until it hit the 100-token cap.
- **The base:** 0 unparseable, 47/47 schema-valid.
- **Reading:** the trigger counts as pre-registered. The headline the rule prescribed, "the distill doesn't honour
  thinking-off at this budget", doesn't describe what happened. What happened is "the distill drops the JSON
  instruction and chats on 6 of 47 conversational messages".
- **The rule's other consequence applies:** the thinking-on pass carries the quality comparison. It lands one item
  apart as well: **22 vs 23**.
- **Decided (Mark, 2026-10-07):** the write-up says the distill **"sometimes chats instead of classifying" (6/47)**.

**Deviation note (recorded 2026-10-07).** The format rule fired as pre-registered, but for a different reason than the
one it was written for. It was written for reasoning that leaks past a 100-token budget with thinking off, and its
prescribed headline was "the distill doesn't honour thinking-off at this budget". No reasoning leaked. The six items are
replies addressed to the user, all on messages that speak to the assistant directly about its memory or identity. The
trigger and its consequence (the thinking-on pass carries the quality comparison) stand as pre-registered. Only the
headline wording departs from the pre-registration, and Mark chose it after seeing the outputs.

**Score sensitivity, not a re-gate.** The parser mirrors the deployed app: an unparseable answer falls back to
`answer/chat/all`, with a keyword scan for the tool. On two of the six items (40 and 41) that default happens to be the
gold answer, so the distill's 22 includes **2 fallback hits**. On parsed answers only, it gets **20 right** against the
base's **23**, 3 below. The base needs no fallback. The gate was pre-registered on the deployed scoring, and its verdict
stands.

**Secondary results:**

- **Speed:** equal, as expected. Decode is within 0.2% at every depth.
- **Reasoning length:** the card's "shorter" claim holds. With thinking on, the distill's **median is 94 reasoning
  tokens per item against the base's 483**, 5.1x fewer.
  - The base hit the 8,192-token cap on 4 items, deliberating in circles.
  - The distill hit it on 1 item: a degenerate "- Null" repetition loop.
  - Thinking-on wall time for all 47 items: 91.7 s for the distill, 346.1 s for the base.

So on this task (routing, short output, thinking off): **the same score, the same speed, much shorter reasoning, and a
new failure the base doesn't have** (chatting instead of classifying). The verdict covers this task. It doesn't test
the card's maths and code claims.

## Tamanna, as run

| | |
|---|---|
| board / BIOS | ASRock B550 Phantom Gaming 4/ac, **BIOS P3.90** (2025-09-30), read from `/sys/class/dmi/id` |
| CPU / RAM | Ryzen 7 5700X; 2 x 16 GB G.Skill F4-3200C16 at **DDR4-2133** (the memory profile is not active; see `tamanna-docp-verify-2026-10-05`). 31 GiB visible, 8 GiB swap file, `vm.swappiness` 60 |
| GPU | RTX 3090 24 GB, driver 580.178.04, PCIe gen 4 x16 in every under-load sample, 420 W cap |
| OS | Ubuntu 26.04.1, kernel 7.0.0-34 (the 09-24 rows say -31) |
| state | headless (7 MiB on the card before each phase, no login sessions), Ollama inactive |
| timing | 2026-10-07 17:45–18:07 PDT. **This is the last run before the RAM/BIOS work (new sticks due 10-08..13).** |

Snapshots before each phase and at the end are in `conditions.txt`.

## Files and hashes

| | Qwen3.6-35B-A3B (base) | Qwen3.8-35B-A3B-Distill |
|---|---|---|
| file | `qwen3.6-35b-a3b-Q4_K_M.gguf` (store `LLM_repo/qwen3.6-35b-a3b-gguf/`) | `Qwen3.8-35B-A3B-Q4_K_M.gguf` from `empero-ai/Qwen3.8-35B-A3B-Distill-GGUF` at rev `b1f9d1dc` |
| bytes | 21,166,757,920 | 21,713,462,944 |
| sha256 | `203c3a7c3becd6ebd7ba1af7d82e5363b1a5d6f84e608d3214c3fb1269230511` | `196103269085bc54c9b8f49ed21e9f53e1b56b465e8b796c6d8e31e06f63cfa5` |
| hash checked against | **nothing: provenance unknown** (see Limits). Recorded today; the Tamanna copy matches the store copy. | the HF LFS oid. The Tamanna download and the store copy both match. |
| llama-bench reads | qwen35moe 35B.A3B Q4_K - Medium, 19.70 GiB, 34.66 B params | the same type, 20.21 GiB, 35.51 B params |

**Correction to the pre-registration.** The pre-registration said v0.4.0 would load the distill's MTP head and that it
would "cost VRAM, not speed". **v0.4.0 doesn't load it at all** without speculative flags. The server log lists 20
`blk.40.nextn.*` tensors (521 MiB) as "unused tensor … ignoring". Peak VRAM was **20,980 MiB for both models** in every
measured run.

## 1. Primary: quality on the 47-item split (thinking off)

The method is the Bonsai 2 run's (`../tamanna-bonsai-2-vs-qwen38-27b-2026-09-24/quality/run_quality.py`):

- The request is byte-identical: system = `solo.py` intent prompt (sha256 `32456044…`, asserted), temperature 0,
  `max_tokens` 100, `enable_thinking: false`.
- Scoring: `parse_and_sanitise()`, exact match on tool/mode/scope.
- Server: v0.4.0 `llama-server -ngl 99 -fa on -c 4096 --jinja`. The scorer ran from Miu. Two passes per model.
- Two additions to the record only: `reasoning_content` is saved, and a non-empty one counts as a leak.

| | Qwen3.6-35B-A3B Q4_K_M | Distill Q4_K_M |
|---|---:|---:|
| **exact (all three fields)** | **23 / 47** | **22 / 47** |
| tool · mode · scope correct | 29 · 27 · 28 | 31 · 29 · 27 |
| "effective" (tool+mode only where gold is not a rag tool) | 27 | 29 |
| schema-valid JSON · unparseable · `<think>` leaks | 47 · 0 · 0 | **41 · 6 · 0** |
| exact on parsed answers only (sensitivity) | 23 | 20 (+2 fallback hits = 22) |
| pass 2 identical predictions / raw text | 47 / 47 | 47 / 47 |
| mean wall per item | 0.273 s | 0.303 s |

Agreement on pass 1: **both right 21**, base only 2, distill only 1, neither 23.

- **Per field, the distill is ahead on tool (+2) and mode (+2) and one behind on scope.** The six chat replies cost it
  structure, not routing judgement. Four of them sit on items where both models are wrong anyway.
- **References:**
  - Qwen3.6-27B Q4_K_M at 23/47 (v0.4.0, ten-seeds).
  - Qwen3.8-27B UD-Q4_K_XL at 19/47 (PrismML fork, 09-24).
  - No 35B-A3B had been scored on this split before today.

Per-item table: `quality/per-item.md`. Counts: `quality/agreement.json`.

## 2. Secondary: speed

The Bonsai 2 `speed_cmp.py` with paths and names changed:

- `llama-bench -ngl 99 -fa 1 -p 512 -n 128 -d 0,4096,8192 -r 5` on v0.4.0.
- The block 3 priming design: three reps, models alternating, starting model flipped on rep 2, a discarded priming run
  before every measured run.
- Telemetry every 1 s.

Figures are the mean of three measured reps, with min..max over the reps in brackets. 17:45–17:50 PDT.

| metric | Qwen3.6-35B-A3B Q4_K_M | Distill Q4_K_M | distill vs base |
|---|---:|---:|---:|
| tg128 d=0 | 183.94 [183.78..184.05] | 183.62 [183.46..183.94] | −0.2% |
| tg128 d=4096 | 181.08 [180.88..181.39] | 181.03 [180.89..181.27] | −0.0% |
| tg128 d=8192 | 177.58 [177.39..177.84] | 177.44 [177.43..177.47] | −0.1% |
| pp512 d=0 | 3,661.1 [3,654.0..3,671.2] | 3,657.4 [3,651.2..3,663.4] | −0.1% |
| pp512 d=4096 | 3,484.3 [3,479.3..3,490.6] | 3,463.9 [3,453.4..3,479.3] | −0.6% |
| pp512 d=8192 | 3,365.8 [3,354.8..3,380.3] | 3,342.0 [3,335.9..3,348.8] | −0.7% |

Pre-registered expectation: decode equal within 3%. **Met at every depth.**

| | Qwen3.6-35B-A3B | Distill |
|---|---|---|
| peak VRAM | 20,980 MiB | 20,980 MiB |
| board power under load (mean / max) | 358–362 W / 417 W | 360–365 W / 418 W |
| SM clock (median) | 1920 MHz | 1920 MHz |
| peak temperature | 70 °C | 70 °C |

One priming run is visibly cold: base rep 2 prime, pp512 2,882 against ~3,650 warm. That is the known alternating-load
effect on Tamanna's 31 GiB, and it's why the priming runs exist. No measured run shows it.

**Not comparable to the article's 157.66 tok/s.** That figure came from Miu on the Unsloth UD-Q4_K_M at July's build.
This is Tamanna, plain Q4_K_M, v0.4.0. The difference is not analysed here.

## 3. Secondary: thinking on (no gate)

`quality/run_thinking.py`:

- The same 47 items, system prompt, parser and scorer, with `enable_thinking: true`, `max_tokens` 8,192, temperature 0
  and one pass.
- Server at `-c 16384`.
- Reasoning tokens are a `/tokenize` count of `reasoning_content`.

| | Qwen3.6-35B-A3B | Distill |
|---|---:|---:|
| exact | 23 / 47 | 22 / 47 |
| tool · mode · scope | 31 · 29 · 29 | 30 · 29 · 27 |
| **reasoning tokens per item, median** | **483** | **94** |
| reasoning tokens per item, mean | 1,209.8 | 292.1 |
| median / mean / max, excluding cap hits | 388 / 560.3 / 3,431 (n=43) | 92 / 120.3 / 374 (n=46) |
| total reasoning · total completion tokens | 56,862 · 57,768 | 13,728 · 14,758 |
| items hitting the 8,192 cap | **4** (13, 41, 58, 60) | **1** (68) |
| unparseable | 4 (the four cap hits) | 2 (68 cap hit; 73 answered off-format) |
| wall time, all 47 items | 346.1 s | 91.7 s |

Agreement: both right 22, base only 1, distill only 0, neither 24.

**What the caps were:**

- **Base:** all four cap hits are over-long deliberation that circles back on the same choice. Item 58's reasoning ends
  `Final Answer: {"tool": "rag",` at the cap.
- **Distill:** its cap hit is a degenerate loop (`- Null` repeated to the cap). The card warns about greedy decoding;
  the pre-registration kept temperature 0, recorded loops as an outcome, and didn't retry.

The card's "noticeably shorter outputs" claim holds on this task. Turning thinking on doesn't change either score
by more than the noise.

## Watchdog and stop rules

- **The Bonsai 2 run's stop conditions applied:**
  - stop if a model fails to load or a run fails;
  - decode outside 3% is reported, not acted on (the secondary here);
  - PCIe gen 4 in every under-load sample.
- **None fired.** Neither record writes down any memory rule, so the watchdog is the current one, `memwatch.py
  --count-swap` (v3, Mark 2026-10-05): only MemAvailable < 2 GiB stops a run, and swap is counted and published.
- It ran on the speed harness and on each of the four servers. It never tripped. The lowest MemAvailable was 25,130 MiB.

| phase | swap-out during load · during measurement | swap-in during load · during measurement |
|---|---|---|
| speed (12 runs) | 194,420 KiB · 0 | 37,136 KiB · 63,796 KiB |
| primary, base | 816 KiB · 0 | 0 · 0 |
| primary, distill | 7,420 KiB · 0 | 328 KiB · 124 KiB |
| thinking on, distill | 0 · 0 | 0 · 0 |
| thinking on, base | 0 · **1,009,140 KiB** | 0 · 91,128 KiB |

**The base's thinking-on pass swapped about 1 GB out while measuring**, with MemAvailable at 25 GB or more throughout.
That's page-cache pressure from two 21 GB files on a 31 GiB box. It can only affect wall time, not tokens or scores,
and the base's 346 s figure should be read with it in mind. Swap-in during the speed runs came to 64 MB over 12 runs,
with decode spreads of 0.05–0.51 tok/s.

## Limits

- **The base Q4_K_M's provenance is unknown.** No download or quantize record exists for
  `LLM_repo/qwen3.6-35b-a3b-gguf/qwen3.6-35b-a3b-Q4_K_M.gguf`. It's dated 07-21 beside our F16 and was probably
  quantized locally from it, but that isn't confirmed.
  - Its sha256 (`203c3a7c…`) was recorded 2026-10-07 in the store's `SHA256SUMS` and `README.md`. It is a hash of the
    file as found, not a check against a source.
  - Header: Q4_K_M (`file_type` 15), no imatrix keys, 40 blocks.
  - The distill's file comes from a different, unknown llama.cpp version, also without an imatrix. The quantizer is
    therefore a small uncontrolled variable. Mark chose the published files over re-quantizing both.
- **One task.** A routing split with short output, at temperature 0. It says nothing about the card's maths, code or
  tool-use claims, or about long-form generation, which the card flags as the distill's weak spot.
- **One quant, one build, one box.** Q4_K_M, v0.4.0, Tamanna.
- **Thinking-on is a single pass at temperature 0,** against the card's recommended temperature 0.6.
- **"Effective" and "parsed-only" are descriptive.** The gate is exact match on the deployed scoring.

## Files

| path | content |
|---|---|
| `speed_cmp.py`, `speed/` | runner; `run.log`, `results.json`, `summary.json`, raw llama-bench JSON and telemetry per run (measured and priming), `memwatch.log` / `memwatch-summary.json` |
| `quality/run_quality.py` | the primary scorer (from the Bonsai 2 run; the request is unchanged) |
| `quality/run_thinking.py` | the thinking-on pass |
| `quality/raw-*.json`, `quality/thinking-*.json` | every completion, parsed prediction, gold, per-field, usage and wall time; reasoning text for the thinking-on pass |
| `quality/per-item.md`, `quality/agreement.json` | from `analyze.py` |
| `quality/server-*.log`, `quality/watch-*/` | `llama-server` logs and the watchdog per server |
| `serve.sh`, `serve_watch.sh`, `run_speed.sh`, `conditions.sh`, `memwatch.py` | launchers, state snapshot, watchdog |
| `conditions.txt` | Tamanna's state before each phase and at the end |
| `benchmarks-rows-staged.json` | the six speed rows as staged on 10-07; **merged 2026-10-08 into benchmarks.json v1.14.0** when the article shipped (`qwen-3-8-35b-a3b-distill-vs-qwen-3-6-35b`) |
