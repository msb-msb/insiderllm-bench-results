# ESP32-P4 (v3.2): logits buffer in internal SRAM, 2026-10-11: P1–P3 held

Results record for `~/Desktop/esp32-llm/p4/evals/p4-logits-01/PREREG.md`. Step 2 of the insiderllm-p4 series (builds on esp32-ai PR #24).

## Pre-registration

- PREREG.md sha256 `b857fc5c7690f403b7feb4e37545f72c5728bc2506fef278022c1aa8169f51ea`.
- Written 2026-10-11T20:59:27-07:00, before the first flash (20:59:51). Unchanged after the runs.

## Hardware

As `../miu-p4-attn2-01-2026-10-11/`.

## Firmware

- `insiderllm-p4` commit `271a77a`.
- **Public source, pinned:** [https://github.com/msb-msb/esp32-ai/tree/271a77ac5beec6423d795adb24728c6fd779a7e7](https://github.com/msb-msb/esp32-ai/tree/271a77ac5beec6423d795adb24728c6fd779a7e7) (branch `insiderllm-p4` on `msb-msb/esp32-ai`, built on esp32-ai PR #24 by Barkın Sarıkartal).
- Cross-chip baseline flags + `-DP4_ATTN2=1 -DP4_LOGITS_SRAM=1`.
- **Change:** `s.logits` (101,412 B) is allocated in internal SRAM instead of PSRAM.

## Model

Release model.bin, `fp=a9bdd778`.

## Predictions (verbatim) and verdicts

| | prediction (verbatim) | verdict | measured |
|---|---|---|---|
| P1 | "P1: gate holds." | **held** | 57e5119adcfba1c4, 20/20, text b9abf55b… |
| P2 | "P2: head stage drops by 0.2-0.8 ms." | **held** | 6.7 → 6.3 |
| P3 | "P3: non-head stages unchanged within +/-0.2 ms." | **held** | 0.7 / 5.3 / 1.0 / 1.2 unchanged |

## Result (n = 3)

- **15.0 → 14.5 ms/token**, 62.9 → 65.7 tok/s.
- **Internal RAM:**
  - Free 383,012 → 280,608 B around the allocation; largest block 335,860 → 237,556.
  - End of setup: 164,328 free / 122,868 largest, against 266,732 / 225,268 with logits in PSRAM.

## Files

Paths are local on Miu, under `~/Desktop/esp32-llm/`: `p4/evals/p4-logits-01/` (RESULTS.md sha256 `6764f09a97bc89c45218c8ab282c56d48734c454af3d78431733d68c56ab9464`).
