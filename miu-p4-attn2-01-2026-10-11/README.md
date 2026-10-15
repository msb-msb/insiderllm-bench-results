# ESP32-P4 (v3.2): exact dual-core attention on the cross-chip baseline, 2026-10-11: P1 held, P2 failed, P3 held at the bound

Results record for `~/Desktop/esp32-llm/p4/evals/p4-attn2-01/PREREG.md`. Step 1 of the insiderllm-p4 series, which builds on esp32-ai PR #24 (Barkın Sarıkartal).

## Pre-registration

- PREREG.md sha256 `e49e4cf6affff6b3db893cd166d27bba8d9a2d2598edbf051a4b2702dcfbb228`.
- Written 2026-10-11T20:56:32-07:00, before the first flash (20:56:57). Unchanged after the runs.

## Hardware

Waveshare ESP32-P4-ETH, silicon v3.2, 400 MHz, PSRAM hex 200 MHz, L2 256 KB / 128 B. CH343 `usb-1a86_…5C93015982`. S3 not touched.

## Firmware

- `p4/pr24` branch `insiderllm-p4` commit `3991a51`: PR `2906bde` + harness `9914179` + this step.
- **Public source, pinned:** [https://github.com/msb-msb/esp32-ai/tree/3991a51eda911774d3659e8b1e2e083b9a10bf0c](https://github.com/msb-msb/esp32-ai/tree/3991a51eda911774d3659e8b1e2e083b9a10bf0c) (branch `insiderllm-p4` on `msb-msb/esp32-ai`, built on esp32-ai PR #24 by Barkın Sarıkartal).
- Core 3.3.10 `esp32p4-libs` (ChipVariant=postv3), `-O3`.
- Cross-chip baseline flags `-DPR24_BENCH=1 -DPR24_KV_QUANT=0 -ffp-contract=off`, plus `-DP4_ATTN2=1`.
- **Change:** the fp32 attention loop is moved verbatim into `llm_attend_heads_f32`. Heads 0–1 run on core 0 (own scores buffer), heads 2–3 on core 1, joined before `attn_proj`.

## Model

Release model.bin `1d8326c0…477e`, `fp=a9bdd778`.

## Predictions (verbatim) and verdicts

| | prediction (verbatim) | verdict | measured |
|---|---|---|---|
| P1 | "P1: gate holds (57e5119adcfba1c4, text b9abf55b...)." | **held** | 57e5119adcfba1c4, 20/20, text b9abf55b… |
| P2 | "P2: attention stage time drops by 35-50%." | **failed** | 7.3 → 5.3 ms (−27%). The stage also contains the qkv/attn_proj matvecs, RoPE and KV writes |
| P3 | "P3: total ms/token drops from the step-0 control by 2.0-4.0 ms." | **held, at the bound** | 17.0 → 15.0 (0.1 ms print precision; stage sum 14.9) |

## Result (n = 3, ms/token)

| build | ms/token | tok/s | input | attn | ffn | ple | head |
|---|---:|---:|---:|---:|---:|---:|---:|
| step-0 control | 17.0 | 55.7 | 0.7 | 7.3 | 1.0 | 1.2 | 6.7 |
| attn2 | **15.0** | 62.9 | 0.7 | 5.3 | 1.0 | 1.2 | 6.7 |

## Files

Paths are local on Miu, under `~/Desktop/esp32-llm/`.

- `p4/evals/p4-attn2-01/`: PREREG.md, RESULTS.md (sha256 `93f8d17fb1fb6062fdb56ff9fd9cbae254ecca66af44b0c6e5eb34e6dcf58c15`), `logs/`.
- `p4/evals/p4-baseline-00/logs/` (control).
