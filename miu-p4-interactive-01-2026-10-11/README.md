# ESP32-P4 (v3.2): S3 interactive protocol, prefill skip, EOT flag and FAST_SAMPLE on the cross-chip baseline, 2026-10-11: P1–P4 held

Results record for `~/Desktop/esp32-llm/p4/evals/p4-interactive-01/PREREG.md`. It is part of the insiderllm-p4 series and builds on esp32-ai PR #24 (Barkın Sarıkartal).

## Pre-registration

- PREREG.md sha256 `82d9da63d1693dce1db1eb30238f8f24493342909b20cea7b256d3f7e2181721`.
- Written 2026-10-11T21:22:44-07:00, before the first flash (21:23:18). Unchanged after the runs.

## Hardware

Waveshare ESP32-P4-ETH, silicon v3.2, 400 MHz, CH343 `usb-1a86_…5C93015982`. The S3 was not touched.

## Firmware

- `insiderllm-p4` commit `a96ab81`.
- **Public source, pinned:** [https://github.com/msb-msb/esp32-ai/tree/a96ab81d9926991ccaeb8f2f5651cb5bf48f6709](https://github.com/msb-msb/esp32-ai/tree/a96ab81d9926991ccaeb8f2f5651cb5bf48f6709) (branch `insiderllm-p4` on `msb-msb/esp32-ai`, built on esp32-ai PR #24 by Barkın Sarıkartal).
- Base: step-3 final (`-DP4_ATTN2=1 -DP4_LOGITS_SRAM=1 -DP4_CORE_INT4=1`, `-DPR24_KV_QUANT=0 -ffp-contract=off`, core 3.3.10, ChipVariant=postv3).
- **Change:** `ia_s3_port.h`, generated **verbatim** from our S3 board sketch (sha256 `ba7d7536…`): the chat.py line protocol, PREFILL_SKIP, splitmix64, `ia_sample`, FAST_SAMPLE.
- **Plus:** `STOP_AT_EOT` on `VOCAB_EOT_ID`. All new flags default to 0.

## Model

Release model.bin, `fp=a9bdd778`.

## Predictions (verbatim) and verdicts

| | prediction (verbatim, abridged) | verdict | measured |
|---|---|---|---|
| P1 | "with all new flags off, the benchmark gate is unchanged (57e5119adcfba1c4, text b9abf55b...) and ms/token 13.7 +/- 0.2." | **held** | gate PASS; 13.7 ×3 |
| P2 | "interactive greedy with ids 433 447 259 405, n=200, eot=0 reproduces 57e5119adcfba1c4 and the text, with PREFILL_SKIP off and on." | **held** | both: 57e5119adcfba1c4, 20/20, b9abf55b…, via unchanged chat.py |
| P3 | "seeded sampling (t=0.8, p=0.9, seeds 1/2/3, the 50 decode-01 prompts, n=200, eot=0) produces the same token sequence as the S3's FAST_SAMPLE build compiled with contraction off, in >= 98% of runs." | **held** | **150/150** identical to a host emulation (verbatim S3 sampler + llm.h exact path + the device's newlib fdlibm, contraction off; validated on the gate first) |
| P4 | "PREFILL_SKIP saves 5.5-7.0 ms per prompt token except the last." | **held** | 6.49 ms/token (slope over L = 4/16/64/128) |

## Other results

- **TTFT, skip off → on:**

  | prompt tokens | skip off | skip on |
  |---:|---:|---:|
  | 4 | 41.1 ms | 21.6 ms |
  | 16 | 163.8 ms | 66.6 ms |
  | 64 | 707.6 ms | 297.3 ms |
  | 128 | 1562.5 ms | 738.5 ms |

- **Demo** ("Once upon a time, a little dog found a red ball", seed 42, eot 1):
  - greedy 72.9 tok/s at the host, 12.79 ms/token forward, 140 tokens (same out_ids as the S3 demo);
  - sampled 55.2 tok/s, 11.54 ms/token, 73 tokens.
  - Sampling costs ~6.6 ms/token on the P4, so the S3's fused-softmax patch is the next port.

**Board state:** IA1 (INTERACTIVE=1, PREFILL_SKIP=1, FAST_SAMPLE=1), app `f6f9caf7f98c74c3`.

## Files

Paths are local on Miu, under `~/Desktop/esp32-llm/`: `p4/evals/p4-interactive-01/` (RESULTS.md sha256 `b71f4291527c14c8cc4df5ee5a612e25ae082341781b1cc145f29d48a7008719`), `logs/`, `host/`.
