# ESP32-P4 (v3.2): int4 core weights with PIE unpack on the cross-chip baseline, 2026-10-11: P1 held, P2 held at the bound, P3 held

Results record for `~/Desktop/esp32-llm/p4/evals/p4-int4core-01/PREREG.md`. Step 3 of the insiderllm-p4 series. It builds on esp32-ai PR #24 and ports the idea of our S3 int4-core patch.

## Pre-registration

- PREREG.md sha256 `61d45172feabd111bd9b64bd3cdbcbb76a04ef8a39fac6789f7d077e1998d90e`.
- Written 2026-10-11T21:03:50-07:00, before the first flash (21:04:15). Unchanged after the runs.

## Hardware

As `../miu-p4-attn2-01-2026-10-11/`.

## Firmware

- `insiderllm-p4` commit `c279282`.
- **Public source, pinned:** [https://github.com/msb-msb/esp32-ai/tree/c279282db9838878b03b5ee100922e397b484268](https://github.com/msb-msb/esp32-ai/tree/c279282db9838878b03b5ee100922e397b484268) (branch `insiderllm-p4` on `msb-msb/esp32-ai`, built on esp32-ai PR #24 by Barkın Sarıkartal).
- Cross-chip baseline flags + `-DP4_ATTN2=1 -DP4_LOGITS_SRAM=1 -DP4_CORE_INT4=1`.
- **Change:** all 43 core tensors are int4 in PSRAM through the PR's `llm_pie4` kernel. `down` is padded 66 → 96 with zero-weight codes; the kernel width comes from `stride4`.
- **Self-test:** every row of every core tensor, two patterns, bitwise against `matvec_q8_range`: 11568/11568 ok.

## Model

Release model.bin, `fp=a9bdd778`.

## Predictions (verbatim) and verdicts

| | prediction (verbatim) | verdict | measured |
|---|---|---|---|
| P1 | "P1: gate holds." | **held** | 57e5119adcfba1c4, 20/20, text b9abf55b…; self-test ok |
| P2 | "P2: non-head stages drop by 0.8-2.0 ms in total." | **held, at the bound** | Stage sum 8.2 → 7.4 (±0.2 print precision; ms/token − head gives −0.7) |
| P3 | "P3: head stage unchanged within +/-0.3 ms." | **held** | 6.3 → 6.2 |

## Result (n = 3)

- **14.5 → 13.7 ms/token**, 65.7 → 69.6 tok/s.
- Stages: input 0.6, attn 4.9, ffn 0.9, ple 1.0, head 6.2.
- Internal RAM at the end of setup: 137,928 free / 98,292 largest. The −26 KB is the self-test's static buffers.

**The board was left on this build** (S3t, app `4d2c88d9f4f1ee52`): the fastest build that passed its gate.

## Files

Paths are local on Miu, under `~/Desktop/esp32-llm/`: `p4/evals/p4-int4core-01/` (RESULTS.md sha256 `9807fe4a641eca7f409252ed922ece1fdda0ba6890dad09bd8a36c76be699112`).
