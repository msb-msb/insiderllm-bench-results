# HumanEval on the CHAT path — Qwen 3.6-27B and 3.8-27B, 2026-08-17

A NEW ARM, not a correction. The published raw-completion result
(3.6 82.32%, 3.8 80.49%) stands and is unaffected: different protocol,
different question. Analysis lives in the article; this directory is the raw
evidence.

Four independent runs, two seeds per model, 12.87 h of GPU time on one RTX 3090.

## Result

| Run | pass@1 (scoreable) | trunc = fail | truncations |
|---|---:|---:|---:|
| 3.8 / s42 | 95.09% (155/163) | 94.51% | 1 |
| 3.8 / s43 | 95.06% (154/162) | 93.90% | 2 |
| 3.6 / s42 | 95.12% (156/164) | 95.12% | 0 |
| 3.6 / s43 | 95.73% (157/164) | 95.73% | 0 |

Between-model gap +0.35 pp to 3.6; within-model seed spread 0.61 pp for 3.6.
The gap between models is smaller than the gap between two runs of one model,
so the comparison is UNRESOLVABLE at n=2. Paired McNemar on commonly-scored
problems gives p = 1.0000 on both seeds.

## Configuration

Chat path, both models treated identically:

- endpoint `/v1/chat/completions`, `--jinja`
- reasoning effort NOT set. 3.8's GGUF chat_template resolves it to `xhigh`
  (`reasoning_effort|default('xhigh')`, template line 59); 3.6 has no such
  parameter. That asymmetry is the thing under test, not a bug normalised away.
- temp 1.0, top_p 0.95, top_k 20 (3.8's card recommendation)
- `-c 32768`, `max_tokens 32000`, NO stop sequences, seeds 42 and 43
- `-ngl 99 -fa on --no-mmap`, `--reasoning-format deepseek-legacy`
- llama.cpp b10088 `67b9b0e`; scorer `he-scorer:b10088`, sandboxed
  (`--network none --cap-drop ALL --security-opt no-new-privileges
  --memory 4g --pids-limit 256`), timeout 10.0

`max_tokens` was raised from 16384 to 32000 after a 20-problem pilot found one
response at 14,953 tokens, 91.3% of the old ceiling. The pilot generation is
kept in `generations/` for the record.

Sampling is stochastic at temp 1.0, so the two seeds per model measure real
run-to-run variance. The "reproducible by hash" licence from the raw arm does
not apply here and was not claimed.

## Memory-fault bracket

Every run bracketed against the unresolved bit-6 page-cache fault
(see `docs/memory-fault-2026-08-15.md`): evict, confirm 0% residency via
mincore, buffered read + sha256 vs upstream, launch immediately, re-hash after.
All eight hashes matched; step2->3 gaps 0.000-0.001 s. 3.8 evicted to
0/4,375,829 pages, 3.6 to 0/4,299,943 — the differing page counts are the two
file sizes and are the expected signature.

## Contents

| path | what |
|---|---|
| `generations/` | raw per-problem responses: content, reasoning_content, finish_reason, token counts, elapsed. The irreplaceable artifact — 12.87 h of GPU time. |
| `scored/*.jsonl` | extracted completions as fed to the scorer |
| `scored/*_vec.json` | per-problem pass/fail vectors |
| `scored/*_status.json` | extraction status per problem (OK / TRUNCATED_EMPTY) |
| `scripts/` | orchestrator, generator, extractor as run |
| `server-logs/` | llama-server stdout per run, incl. n_ctx_slot and per-slot timings |
| `run.log` | orchestrator stdout: brackets, milestones, summaries |

## Truncations

Three, all on 3.8, none on 3.6, no overlap between seeds: `HumanEval/108`
(s42), `HumanEval/32` and `HumanEval/99` (s43). Each consumed the full 32,000
token budget on reasoning and emitted zero answer characters. These are
UNSCOREABLE, not failures, and are excluded from the scoreable-only denominator
and counted separately. The `trunc = fail` column is the sensitivity check.

3.6 never once failed to terminate, while spending more total tokens
(911k vs 840k).

## Token cost

| run | total | mean | median | p95 | thinking | answer median |
|---|---:|---:|---:|---:|---:|---:|
| 3.8/s42 | 444,556 | 2,711 | 993 | 8,607 | 92.8% | 173 |
| 3.8/s43 | 395,746 | 2,413 | 887 | 8,529 | 91.8% | 180 |
| 3.6/s42 | 449,579 | 2,741 | 2,574 | 5,121 | 88.1% | 330 |
| 3.6/s43 | 461,418 | 2,814 | 2,667 | 4,942 | 88.3% | 313 |

Same total spend, opposite shape. 3.8 is bimodal — mean ~3x median, cheap on
most problems and occasionally catastrophic. 3.6 is uniform — mean and median
nearly coincide, tighter tail, never runs away.
