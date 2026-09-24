# Jev-mode test, phase 2: is the scope deficit field independence, and does the speedup track answer length?

**2026-09-21, same setup as phase 1**: Miu, RTX 3090 with the desktop up, Qwen3.6-27B Q4_K_M fully
resident, fork `parallel-decision` @ `14d04e755`, the same server line (`../launch_server.sh`,
`-kvu --decision-seqs 3`), the ten-seeds 47-item split and scorer. One server process for every run
in this directory. Every number is in `analysis_phase2.json` (`analyze_phase2.py` over `raw/`);
`a1_scope_disagreement.json` is the phase-1 item table for A1.

## A. The scope deficit is not the field-independence problem

### A1. Where choose and write disagree on scope

They disagree on scope on **2 of 47 items**, and on both the tool and mode matched:

| idx | gold | choose | p(scope) | write |
|---|---|---|---:|---|
| 40 | answer/chat/all | answer/chat/**session** | 0.494 | answer/chat/all |
| 68 | rag/recall/session | answer/execute/**all** | 0.636 | answer/execute/session |

Choose's scope errors: **19 of 47** (write: 17). Of the 19, **5** are on items where choose's tool
or mode also differed from write (13, 22, 28, 37, 60) and **14** are on items where tool and mode
matched write. Of those 14, write is also wrong on scope on **12**; the two where write is right
are the two rows above. So the whole scope gap between the paths is two items, and both are
items where choose already agreed with write on the other two fields. The confusion is the same
shape on both paths: gold `session` predicted `all` (choose 11, write 10) dominates.

### A2. Two-pass choose

Pass 1: schema `tool` + `mode`. Pass 2: schema `scope` only, with `tool: X, mode: Y` (pass 1's
answers) appended to the item context. Three passes each, all deterministic within the session.

| | exact | tool | mode | scope | wall mean | p95 | vs single pass |
|---|---:|---:|---:|---:|---:|---:|---:|
| single pass, this session (`choose_ref`) | 21/47 | 30 | 30 | 28 | 0.298 s | 0.345 s | 1.00× |
| two-pass, alternating per item (`twopass`) | 21/47 | 31 | 29 | 28 | 1.340 s | 1.407 s | 4.50× |
| two-pass, batched by pass (`twopass_seq`) | 21/47 | 30 | 30 | 28 | 0.328 s | 0.383 s | **1.10×** |
| two-pass, line in instructions (`twopass_instr`, 1 rep) | 22/47 | 31 | 29 | 29 | 1.360 s | 1.417 s | 4.57× |

Against the pre-registration: **scope did not recover** (28 → 28, not 30); overall stayed at
21/47, outside 23 ± 1; latency, measured properly, rose by **10 percent**, well under 2× — pass 2
costs 38 ms of scoring plus a 79 ms prefill of the ~54-token context (message + line), on top of
pass 1's 128 ms scoring.

In the raw decision, scope changed on four items between single pass and batched two-pass (29, 30,
40, 77), every one of them from one wrong value to another. After the sanitise pipeline the
past-reference override forces 29 and 77 to `session` on both paths, so at the scored level two
items moved (30: `facts` → `all`, gold `session`; 40: `session` → `facts`, gold `all`) and
**neither went to gold**. Telling the scope question what tool and mode were chosen does not help it; the
`session`-vs-`all` confusion is in the model's reading of the message, not in the field seeing its
neighbours.

**The 4.5× row is a harness artefact, kept because it is the trap.** Alternating two schemas per
item means two different cached prefixes (instructions + tool/mode catalogue, instructions + scope
catalogue), and the server holds one: `cached_tokens` was 0 on every pass-2 call and every pass-1
call after the first, so each request re-prefilled ~700 tokens (578 ms). Batched by pass, both
prefixes stay warm (`cached_tokens` 672 / 656) and the cost is what the pre-registration expected.
Anyone building a two-pass pipeline on this endpoint has to group calls by schema.

**Two side findings from A2, both about determinism, both recorded rather than chased:**

1. *The catalogue is part of the prompt.* Pass 1 with a two-field schema gives different tool/mode
   answers from the three-field single pass on **5 items** (28, 58, 62, 68, 69), both warm. The
   fields cannot see each other's answers, but every field sees the schema catalogue in the prefix,
   so removing `scope` from it moves `tool` and `mode`.
2. *Cache state moves answers.* The same pass-1 request differs between the alternating run
   (prefix re-prefilled) and the batched run (prefix from cache) on **2 items** (69: mode
   `chat` ↔ `explore` at p 0.50 / 0.48; 77: tool `rag` ↔ `answer` at 0.506 / 0.512), and
   single-pass choose differs between the phase-1 and phase-2 server sessions on 2 items (30, 69),
   with field probabilities moving up to 0.108. Within one session and one cache state every
   run is byte-identical. This is the prompt-cache-reuse family (llama.cpp #26207) showing up on the
   decision path too; the items that flip are the ones sitting at p ≈ 0.5.

## B. The speedup tracks answer length, above a fixed floor

Same 47 items, `/v1/chat/completions` at temperature 0, four output formats. `write_json` is the
phase-1 request re-run in this session; the other three append an output-format override to the
system prompt (`FORMAT_SUFFIX` in `run_phase2.py`). The scorer parses the JSON (or the slash
string) and ignores `reason`. Three passes each, all deterministic, 141 samples per row.

| format | tokens (mean / p95) | exact | wall mean | p95 | vs choose (0.298 s) | prompt ms | generate ms | ms/token |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| bare `tool/mode/scope` | 4.5 / 5 | 23/47 | 0.392 s | 0.475 s | **1.32×** | 289 | 98 | 21.8 |
| compact JSON (phase 1) | 19.7 / 25 | 23/47 | 0.782 s | 0.908 s | **2.63×** | 288 | 489 | 24.8 |
| pretty JSON, one field per line | 28.1 / 29 | 24/47 | 0.997 s | 1.050 s | **3.35×** | 288 | 704 | 25.1 |
| JSON + one-sentence `reason` | 52.8 / 71 | 23/47 | 1.637 s | 2.089 s | **5.50×** | 292 | 1,340 | 25.4 |

Pre-registration held: the ratio rises in proportion to tokens. A line through the four formats
is **wall = 0.275 s + 25.8 ms × tokens** (fit in `analysis_phase2.json`). Where the time goes:

- **Fixed ~290 ms per request is prompt processing** of the ~50 uncached tokens (the user message
  plus template; the system prompt is cached, `cache_n` 600–640 of ~650). It is the same on all
  four formats and it is essentially the whole of the bare-values format's cost. It is also what
  single-pass choose costs in total (0.298 s this session: 124 ms prefill + 169 ms scoring), which
  is why choose is only 1.3× faster than writing four tokens: the batched score of 21 rows costs
  about the same as the decode it replaces at that length.
- **Generation is 22–25 ms per token and linear.** Sampling overhead is not visible: client
  overhead (wall minus server prompt and generate time) is 5 ms on every format.
- The 5× line the phase-1 pre-registration set is crossed at about 50 generated tokens. The
  video's 300 ms vs 3.5 s on Gemma 4 12B is consistent with a long JSON answer, not with a
  three-field one.

Accuracy moved a little with the format (pretty 24/47, bare values lose one on mode) because the
override changes the system prompt; that is not what this section measures and none of it is
outside the executor noise the series already carries.

## Files

| path | content |
|---|---|
| `run_phase2.py` | modes `choose`, `twopass`, `twopass_seq`, `twopass_instr`, `write_short/json/pretty/reason` |
| `analyze_phase2.py`, `analysis_phase2.json`, `logs/analysis_stdout.txt` | every number above |
| `a1_scope_disagreement.json` | A1 per-item table from the phase-1 records |
| `raw/*.json` | per-item records for all 20 runs (per-pass usage and timings for the two-pass modes) |
| `logs/server.log`, `logs/runs.log` | the one launch, and every run summary in order |
