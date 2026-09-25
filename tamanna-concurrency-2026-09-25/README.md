# Multi-user serving on Tamanna's RTX 3090 — concurrency sweep, 2026-09-25

RUN AND COMPLETE, 2026-09-25. Record only; no article, nothing to `content/`. Both models on the
**v0.4.0 pin** (`5266f24da75dc449bd56cbed7addb9c8e4a6a73e`), one at a time, `-ngl 99 -fa on --jinja`,
`-np` at 1 / 4 / 8 / 16 with `-c` scaled so every slot gets 4,096 tokens of context.

## Headline

**Every level loaded on both models. Nothing had to be stopped for VRAM, and per-user decode never
fell below 10 tok/s** — the level the brief marks as the edge of interactive. The dense 27B comes
closest at 13.7 tok/s with 16 users, and by then the thing that has actually broken is not decode
but **time to first token: 7.1 s at p95**, which is where a student decides the tutor is broken.

The MoE serves roughly **twice the aggregate throughput of the dense model at every level** and
does it in less VRAM growth, because its KV cache is 80 KiB per token against the dense model's
260 KiB. That is the whole story of this sweep: 40 layers x 2 KV heads against 65 x 4.

## Qwen3.6-35B-A3B UD-Q4_K_M (MoE, ~3B active)

| -np | -c | VRAM after load | VRAM peak | decode mean | decode worst | TTFT mean | TTFT p95 | aggregate | power |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 4,096 | 21,150 MiB | 21,172 MiB | **156.8** | 156.8 | 0.16 s | 0.17 s | 143 tok/s | 364 W |
| 4 | 16,384 | 21,578 MiB | 21,604 MiB | **82.1** | 81.6 | 0.62 s | 0.67 s | 273 tok/s | 372 W |
| 8 | 32,768 | 22,150 MiB | 22,182 MiB | **47.8** | 43.0 | 1.18 s | 1.31 s | 295 tok/s | 377 W |
| 16 | 65,536 | 23,308 MiB | 23,342 MiB | **27.0** | 25.3 | 2.43 s | 2.63 s | 336 tok/s | 360 W |

Per-user decode vs one user: np1 1.00x, np4 0.52x, np8 0.30x, np16 0.17x.
Aggregate vs one user: np1 1.00x, np4 1.91x, np8 2.06x, np16 2.35x.

## Qwen3.8-27B UD-Q4_K_XL (dense)

| -np | -c | VRAM after load | VRAM peak | decode mean | decode worst | TTFT mean | TTFT p95 | aggregate | power |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 4,096 | 16,984 MiB | 16,994 MiB | **41.4** | 41.4 | 0.40 s | 0.42 s | 39 tok/s | 406 W |
| 4 | 16,384 | 18,202 MiB | 18,214 MiB | **24.9** | 24.9 | 1.47 s | 1.59 s | 87 tok/s | 408 W |
| 8 | 32,768 | 19,824 MiB | 19,836 MiB | **14.4** | 14.4 | 2.96 s | 3.28 s | 99 tok/s | 414 W |
| 16 | 65,536 | 23,116 MiB | 23,130 MiB | **13.7** | 13.7 | 6.37 s | 7.09 s | 164 tok/s | 401 W |

Per-user decode vs one user: np1 1.00x, np4 0.60x, np8 0.35x, np16 0.33x.
Aggregate vs one user: np1 1.00x, np4 2.24x, np8 2.54x, np16 4.20x.

## Reading these numbers

**Per-user decode excludes prefill.** It is `(tokens - 1) / (last chunk - first chunk)`, measured in
the worker thread. Aggregate is every token the round produced over the round's wall clock, so it
includes prefill and the tail where early finishers have left. That is why aggregate at one user
(143 tok/s MoE) is below per-user decode (157): a 198-token prompt and 256 tokens of output means
prefill is a real fraction of a short request.

**Where each model stops being worth it, by the 10 tok/s line: neither, within 16 users.** But the
two get there differently. The MoE degrades smoothly and predictably — 0.52x, 0.30x, 0.17x of
single-user decode at 4, 8 and 16 — and it is still at 27 tok/s with sixteen students attached. The
dense model degrades hard to 8 users (0.35x) and then **barely moves from 8 to 16** (14.4 to 13.7
tok/s) while aggregate jumps 99 to 164 tok/s. Doubling the users there costs almost no per-user
speed, which says the 8-user config was leaving the batch underfed rather than saturating the card.

**TTFT is the real limit, not decode.** It is linear in concurrency on both models and it is the
number a user feels first. At 16 users the MoE makes you wait 2.6 s before anything appears; the
dense model makes you wait 7.1 s. If this were a classroom the dense model would feel broken at 16
long before its 13.7 tok/s did.

**VRAM.** The MoE went 21.1 to 23.3 GiB across the whole sweep, 2.2 GiB for sixteen slots and 64k of
total context. The dense model went 17.0 to 23.1 GiB, 6.1 GiB for the same, and it started 4.2 GiB
lower. Both ended within about 1.2 GiB of the card. A 17th slot fits neither.

**Power** sat at 360-380 W for the MoE and 400-415 W for the dense model on a 420 W cap, so the
dense model runs closer to the limit while producing half the tokens.

## Method

| | |
|---|---|
| Box | Tamanna: RTX 3090 24 GB, Ryzen 7 5700X, 31 GiB DDR4, PCIe 4.0, headless, driver 580.178.04 |
| Engine | llama.cpp v0.4.0 `5266f24`, CUDA sm_86, the site pin. Not the PrismML fork |
| Server | `llama-server -ngl 99 -fa on --jinja -np N -c (N x 4096) --host 127.0.0.1 --port 8081` |
| Client | `concurrency_client.py`, threads over urllib, no third-party dependency. Runs ON the box, so LAN latency is not in TTFT |
| Load | N concurrent `/v1/chat/completions`, all released by a barrier so the level is genuinely simultaneous. One 198-token student question, `max_tokens` 256, `temperature` 0.7 |
| Rounds | 1 warm-up discarded, then 3 measured. Every figure is pooled over all requests of the 3 rounds |
| Telemetry | 1 s `nvidia-smi` during each round; power is the mean over samples at >=20% utilisation |

**Thinking is off, and the first run of this bench is why.** Both models are hybrid thinking models.
With `--jinja` and thinking left on, llama.cpp streams the chain of thought as
`delta.reasoning_content` rather than `delta.content`, and the entire 256-token budget is spent
before any answer appears. The first attempt recorded zero successful requests at every level for
exactly that reason. Requests now send `chat_template_kwargs: {"enable_thinking": false}`, matching
the convention the intent-split work on this site already uses, and the client counts **either**
field so a future template change reports a problem instead of reporting zero.

## Limits

One card, one prompt shape, one output length. Every user sends the same 198-token question, so
prompt-cache reuse across slots is more favourable than a real classroom would be — `cached_tokens`
was non-zero on repeat rounds. Nothing here tests mixed prompt lengths, long conversations that grow
past 4k, or users arriving at staggered times. `-c` was scaled to give each slot exactly 4k; a
shared smaller context with `-kvu` would trade differently and was not tried.

## Files

| path | content |
|---|---|
| `concurrency_client.py` | the client, as run |
| `run_levels.sh` | the driver: start server, wait for health, record VRAM, run client, stop |
| `<model>-np<N>.json` | per level: every request's TTFT, tokens, decode rate, wall, plus the 1 s GPU samples and the round summaries |
| `server-<model>-np<N>.log` | llama-server log per level |
| `driver.log` | the live run log |
| `summary.json` | the tables above, machine-readable |
