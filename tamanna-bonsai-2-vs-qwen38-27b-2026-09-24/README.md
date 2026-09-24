# Ternary Bonsai 2 27B vs Qwen3.8-27B UD-Q4_K_XL — the pre-registered comparison, Tamanna, 2026-09-24

## Gate verdict, stated first: REFUTED

Pre-registration (`docs/candidates/bonsai-2-27b-2026-09-23.md`, A5): *confirm* if Bonsai 2 is within one item of
Qwen3.8-27B Q4_K_XL on the 47-item split **and** decodes at least as fast; *refute* if it is three or more items below,
regardless of speed; *inconclusive* at a two-item gap. **Bonsai 2 scored 12 of 47 against Qwen3.8-27B's 19 of 47, seven
items below, so the refute condition fired.** It did decode 1.8x faster, which the gate says cannot rescue a quality
miss. On this task, under this fork, the "98% of Qwen3.8" claim does not hold; the pre-registration also says this
task is a routing split with thinking off, so it speaks to that task and not to PrismML's 14-benchmark thinking-mode
aggregate.

Both models ran under the **PrismML fork** `prism-b10709-9a9394a` (`~/llama-prismml`, upstream base b10709), because
Bonsai 2's PQ2_0 type does not load on mainline; the v0.4.0 pin was not used or touched. Fork-vs-pin on this box and
this Qwen3.8 file the day before (`../tamanna-bonsai-2-staging-2026-09-23/`): decode within 1%, **prefill −2.2 to −2.4%**.

## 1. Speed

`llama-bench -ngl 99 -fa 1 -p 512 -n 128 -d 0,4096,8192 -r 5`, block 3 priming design (three reps, models alternating,
starting model flipped on rep 2, a discarded priming run before every measured run), 1 s telemetry. Mean of the three
measured reps of llama-bench's 5-repeat average; brackets are min..max over reps. 12:34–12:46 PDT.

| metric | Qwen3.8-27B UD-Q4_K_XL (n=3) | Bonsai 2 27B PQ2_0 (n=3) | Bonsai / Qwen |
|---|---:|---:|---:|
| tg128 d=0 | 42.13 [42.11..42.15] | 77.62 [77.57..77.67] | **1.84x** |
| tg128 d=4096 | 41.60 [41.59..41.62] | 75.93 [75.90..75.96] | **1.83x** |
| tg128 d=8192 | 41.11 [41.11..41.11] | 74.38 [74.36..74.40] | **1.81x** |
| pp512 d=0 | 1,415.2 [1,412.3..1,419.2] | 1,475.9 [1,474.3..1,477.5] | **1.04x** |
| pp512 d=4096 | 1,358.5 [1,356.9..1,361.2] | 1,413.5 [1,412.1..1,414.7] | **1.04x** |
| pp512 d=8192 | 1,299.6 [1,299.3..1,300.2] | 1,350.6 [1,350.1..1,351.3] | **1.04x** |

Prefill carries the fork's offset: on this box v0.4.0 read Qwen3.8's pp512 at 1,445 / 1,388 / 1,332 against the fork's
1,415 / 1,358 / 1,300 (−2.2 to −2.4%), so both prefill columns above are about 2.3% under what the pin would give; the
ratio between them is unaffected.

| | Qwen3.8-27B UD-Q4_K_XL | Bonsai 2 27B PQ2_0 |
|---|---|---|
| peak VRAM · board power (under load) · SM clock median · peak temp | 17,666 MiB | 402 W mean, 420 W max | 1770 MHz | 73 °C | 8,118 MiB | 400 W mean, 421 W max | 1815 MHz | 72 °C |

Both on the 420 W cap during prefill; PCIe gen 4 x16 in every under-load sample; repeat spreads 0.01–0.10 tok/s on
decode, 0.9–7 tok/s on prefill. Rows added to `benchmarks.json` v1.8.0 as `tamanna-prismfork-*`, engine tagged
`prism-b10709-9a9394a`.

## 2. Quality: the 47-item intent split

Write path, byte-identical to the Jev-mode work's `run_decision.write()`: `POST /v1/chat/completions`, system = the
deployed intent prompt (`solo.py`, sha256 `32456044…` asserted), user = the message, temperature 0,
`max_tokens` 100, thinking off via `chat_template_kwargs`. Parsed with the ten-seeds `parse_and_sanitise()`, scored
exact-match on tool/mode/scope. Server: the fork's `llama-server -ngl 99 -fa on -c 4096 --jinja`, one model at a time,
scorer run from Miu. Two passes per model.

| | Qwen3.8-27B UD-Q4_K_XL | Bonsai 2 27B PQ2_0 |
|---|---:|---:|
| **exact (all three fields)** | **19 / 47** | **12 / 47** |
| tool · mode · scope correct | 28 · 24 · 28 | 28 · 27 · 18 |
| "effective" (tool+mode only where gold is not a rag tool) | 23 | 26 |
| schema-valid JSON · unparseable · `<think>` leaks | 47 · 0 · 0 | 47 · 0 · 0 |
| pass 2 identical predictions / raw text | 47 / 47 | 47 / 47 |
| mean wall per item | 0.739 s | 0.53 s |

Agreement: both right on **10**, Qwen only **9**, Bonsai only **2**, neither **26**; the two models disagree on
27 of 47 items. **The seven-item gap is entirely scope.** On tool the two tie at 28; on mode Bonsai is
*ahead* (27 vs 24, right where Qwen is wrong on 5 items against 2 the other way); on scope Bonsai collapses from 28 to
18, and its errors are one confusion: it answers `facts` where gold is `session` (12 items) or `all` (11). Qwen3.8's
scope errors are the family's usual `session`→`all` (9). So the ternary model kept the routing judgement and lost the
field that depends on reading whether a message refers back to earlier conversation — the same field the Jev-mode work
found hardest, now failing in a new direction. That is what the "effective" metric shows going the other way (26 vs 23):
on tool and mode alone Bonsai is at least as good.

For scale: the ten-seeds base on this split is Qwen3.6-27B Q4_K_M at 23/47 via llama.cpp; Qwen3.8-27B UD-Q4_K_XL under
this fork lands at 19. One item is 2.1 points.

### Per-item table

Wrong field values in **bold**. Pass 1 of 2; pass 2 was identical on every item for both models.

| item | gold tool/mode/scope | Qwen3.8-27B Q4_K_XL | Bonsai 2 PQ2_0 | correct | fields that differ |
|---:|---|---|---|---|---|
| 1 | answer/chat/all | answer/chat/all | answer/chat/**facts** | qwen only | scope |
| 2 | answer/chat/all | **rag**/**recall**/**session** | **rag**/**recall**/**session** | neither | — |
| 4 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |
| 6 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |
| 7 | answer/chat/all | answer/chat/all | answer/chat/**facts** | qwen only | scope |
| 10 | answer/chat/session | answer/chat/**all** | answer/chat/**facts** | neither | scope |
| 12 | answer/chat/session | answer/chat/**all** | answer/chat/**all** | neither | — |
| 13 | rag/recall/docs | **answer**/**chat**/**all** | **answer**/**chat**/**facts** | neither | scope |
| 15 | answer/chat/all | **rag**/**recall**/**session** | **rag**/**recall**/**session** | neither | — |
| 16 | answer/chat/all | answer/chat/**facts** | answer/chat/**facts** | neither | — |
| 18 | rag/recall/session | **answer**/**chat**/**facts** | **answer**/**chat**/**facts** | neither | — |
| 22 | rag/recall/session | **answer**/**chat**/**facts** | **answer**/**chat**/**facts** | neither | — |
| 24 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**facts** | neither | scope |
| 25 | rag/recall/session | rag/recall/session | rag/recall/session | both | — |
| 26 | rag/recall/session | rag/**explore**/session | **answer**/**chat**/session | neither | tool, mode |
| 28 | rag/explore/session | **answer**/**chat**/**all** | **answer**/**chat**/**facts** | neither | scope |
| 29 | rag/explore/session | **answer**/**chat**/session | **answer**/**chat**/session | neither | — |
| 30 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**facts** | neither | scope |
| 33 | answer/chat/all | answer/chat/all | answer/chat/**facts** | qwen only | scope |
| 34 | answer/chat/all | answer/chat/all | **rag**/**recall**/**session** | qwen only | tool, mode, scope |
| 35 | answer/chat/all | answer/chat/**facts** | answer/chat/**facts** | neither | — |
| 36 | answer/chat/all | answer/chat/all | answer/chat/**facts** | qwen only | scope |
| 37 | answer/chat/all | **rag**/**recall**/all | answer/chat/**facts** | neither | tool, mode, scope |
| 38 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |
| 39 | answer/chat/all | answer/chat/all | answer/chat/**facts** | qwen only | scope |
| 40 | answer/chat/all | **rag**/**recall**/**session** | **rag**/chat/**session** | neither | mode |
| 41 | answer/chat/all | answer/chat/all | answer/chat/**facts** | qwen only | scope |
| 44 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |
| 48 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |
| 49 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |
| 50 | answer/chat/all | answer/chat/all | answer/chat/**facts** | qwen only | scope |
| 51 | answer/chat/all | answer/chat/all | answer/chat/**facts** | qwen only | scope |
| 53 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**facts** | neither | scope |
| 58 | rag/recall/session | rag/**explore**/session | rag/**explore**/session | neither | — |
| 60 | answer/chat/session | **rag**/**recall**/**docs** | answer/chat/**facts** | neither | tool, mode, scope |
| 61 | rag/explore/session | rag/explore/session | rag/explore/session | both | — |
| 62 | rag/recall/session | rag/recall/session | rag/recall/session | both | — |
| 65 | answer/chat/facts | **rag**/**recall**/**session** | answer/chat/facts | bonsai only | tool, mode, scope |
| 68 | rag/recall/session | rag/**execute**/session | **answer**/**execute**/**facts** | neither | tool, scope |
| 69 | rag/explore/all | **answer**/explore/all | **answer**/**chat**/all | neither | mode |
| 71 | answer/chat/facts | answer/chat/facts | answer/chat/facts | both | — |
| 72 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**facts** | neither | scope |
| 73 | answer/chat/session | **rag**/**recall**/session | answer/chat/session | bonsai only | tool, mode |
| 74 | rag/explore/session | **answer**/**chat**/**all** | **answer**/**chat**/**facts** | neither | scope |
| 77 | rag/explore/session | rag/**recall**/session | **answer**/**chat**/session | neither | tool, mode |
| 78 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**facts** | neither | scope |
| 82 | rag/explore/docs | rag/**recall**/docs | rag/**recall**/docs | neither | — |


## 3. Bits per weight: which figure is honest

| figure | source | arithmetic |
|---|---|---|
| **1.76 bpw, 5.9 GB** | PrismML's headline | the **PTQ1_0** file: 5,946,648,928 B × 8 / 26,895,998,464 params = **1.77 bpw** |
| **2.13 bpw** | llama-bench's `model_type` line for the file we ran | the **PQ2_0** file: 7,206,168,928 B × 8 / 26,895,998,464 = **2.14 bpw** (llama-bench: 2.140 on its own byte count) |

There is no discrepancy in the arithmetic; the two numbers describe two files. PrismML's 1.76 is the dense-trit
PTQ1_0 packing; PQ2_0, the "2-bit slot packing" the card recommends for GPUs and the one every figure in this record was
taken on, spends a quarter more bytes for kernel-friendly layout. **For a reader sizing VRAM the honest figure is the
file they will load: 7.2 GB / 2.14 bpw for PQ2_0 (8,118 MiB peak here with the 8k sweep), 5.9 GB / 1.77 bpw only if
they run PTQ1_0, which was not measured.** "A 27B in 5.9 GB" is true of one packing and not of the one you are told to use.

## Files

| path | content |
|---|---|
| `speed_cmp.py`, `speed/` | runner; `run.log`, `results.json`, `summary.json`, raw llama-bench JSON and 1 s telemetry per run (measured and priming) |
| `quality/run_quality.py` | the scorer, run from Miu against Tamanna; imports the ten-seeds `deployed.py` / `score_lora.py` and the frozen `splits/test.json` |
| `quality/raw-*.json` | both passes per model: raw completion, parsed prediction, gold, per-field, usage, wall |
| `quality/per-item.md`, `quality/agreement.json` | the table above and its counts |
| `quality/server-*.log` | the fork `llama-server` logs |
| `serve_fork.sh` | the server launch line |
