# ESP32-S3 (B, D) and ESP32-P4: board-level energy per token, 2026-10-14: P1–P4 held, P5 failed

Results record for power-01. It measures board-level energy per token for TinyStories greedy generation on three
builds:
- **S3-B:** ESP32-S3 N16R8, variant B libs;
- **S3-D:** the same S3, variant D libs;
- **P4:** ESP32-P4, the insiderllm-p4 IA1 build.

Every figure is **board-level**. The logger sits on each board's USB VBUS, so the figures include the USB bridge,
LEDs, regulators and, on the P4-ETH, the Ethernet PHY. They are not chip power.

**Copied verbatim from the private study repo:** `PREREG.md`, `RESULTS.md`, `NOTES.md`, `score_output.md`,
`scores.json`, `runs.jsonl`, `readings.jsonl`, `run.py` and `score.py`. `RESULTS.md` is the source for every number.
One edit: the S3 board's MAC address is redacted to `10:51:DB:xx:xx:xx` in `NOTES.md` and `run.py`, so those two
copies differ from the originals. `PREREG.md` and `RESULTS.md` are byte-identical (the PREREG hash above checks).

## Pre-registration

- `PREREG.md` sha256 `b75eb427b6a54b39c2fe750aa76b907ffdb0c00007a6ea0f2500d6f3dadc9e04`.
- Locked 2026-10-14 16:56:46 −07:00 in lock commit `63e88013f12ea4c868bf4c64421e86ed6b3ade0e`.
- Pushed to a private GitHub repo before any generate run.
- `score.py` was committed and pushed (`f0c888e`) before it was run.
- **Known before the lock** (PREREG "Disclosures"):
  - the idle powers, so P5's outcome;
  - the step d window figures (S3-B 14.37, S3-D 12.19, P4 7.83 mJ/token), which anticipated P1, P2 and P4.
  - No marginal figure was computed before the lock.

## Hardware

- **S3:** ESP32-S3 N16R8 board. The S3-B and S3-D builds were flashed in turn.
- **P4:** Waveshare ESP32-P4-ETH, silicon v3.2, 400 MHz.
- **Instrument:** a USB power logger: an INA226 (R100 shunt) on a perfboard with a Raspberry Pi Pico (RP2040),
  high side on VBUS between Miu and the board, streaming every sample at ~826 Hz.
  - Energy is integrated on the RP2040 and on the host, and the two must agree within 0.5%.
  - The sync pin (S3 GPIO4, P4 GPIO6) brackets each generation.
- **Calibration:** against an Aneng SZ20 DMM (`calibration/`). The INA226 is a suspected clone: its raw gains were
  −6% (current) and +5% (VBUS), corrected by the fit. The session recheck on 10-14 was −0.01%.

## Firmware

| Build | App sha256 | Sync pin | Source |
|---|---|---|---|
| S3-B | `06abb9ada33896db6f2f07adcbeed03ff45e50473009aab470f35f2af581f8f8` | GPIO4 | 12-patch S3 stack (`dut/s3-stack/`) + `dut/s3-sync-gpio.patch`, libs `B_64B_80M` (see below) |
| S3-D | `cf2ff730cd0392b673fc2d25fa357092586f95e02df9269be24566cfafbf1a9d` | GPIO4 | the same sketch, patch and defines, libs `D_64B_120M`, `FlashMode=qio120` |
| P4 | `38299f178b6e3ff02806a5ba6793fcb02ef4c25ea6074a0d1cb34d25c3bf2b7a` | GPIO6 | [`power-01-sync-gpio` @ `203acd5`](https://github.com/msb-msb/esp32-ai/tree/203acd56e2c7e272306413090f7497f361004bc8), on [`insiderllm-p4` @ `a96ab81`](https://github.com/msb-msb/esp32-ai/tree/a96ab81d9926991ccaeb8f2f5651cb5bf48f6709) |

**S3-B patch stack, confirmed at the source level** (2026-10-15):
- NOTES ("Builds") gives S3-B as the b-libs-interactive-01 final build: `.ino` `ba7d7536…`, libs `B_64B_80M`,
  `-DHEAD_SC16=0 -DLOGITS_SRAM=1 -DCORE_INT4=1 -DINTERACTIVE=1 -DPREFILL_SKIP=1 -DFAST_SAMPLE=1`.
- The stack `no-display+logit-checksum+simd-head+int4-head+simd-core+eot-flag+head-traffic+int4-core+interactive+prefill-skip+sample-profile+fast-sample`
  (the same `.ino` S3-D's build log applies) produces an `.ino` hashing `ba7d7536…`.
- Applying `s3-sync-gpio.patch` (`ea5922bc…`) to it gives `ea055c35…`, the B+sync `.ino` recorded in NOTES.
- The app binary was not rebuilt, so the app hash `06abb9ad…` is as recorded at the flash, not re-derived.
- All twelve patches are in `dut/s3-stack/`: two of them (`sample-profile`, `fast-sample`) are not on a public
  esp32-ai branch.

**Step d:** each sync build matched its non-sync build on greedy output (`b2782783…`), and median ms/token was
within 1%.

## Predictions (verbatim) and verdicts

| | Prediction | Verdict | Interval that decided it |
|---|---|---|---|
| P1 | "S3-B total energy is 10-25 mJ/token." | **held** | 14.5619–15.0104 mJ |
| P2 | "P4 total J/token is lower than S3-B's (its 2.3x speed outweighs its higher board power)." | **held** | P4 − S3-B = −7.1058 to −6.5051 mJ |
| P3 | "P4 marginal J/token is <= 0.6x S3-B's." | **held** | P4 / S3-B = 0.4015–0.5447 |
| P4 | "S3-D total J/token is lower than S3-B's (speed rises more than power)." | **held** | S3-D − S3-B = −2.7219 to −1.9664 mJ |
| P5 | "P4 idle power exceeds S3 idle by >= 0.2 W (Ethernet PHY plus the bigger chip)." | **failed** (outcome observed before the lock) | P4 − S3-B = 0.09055–0.10034 W; P4 − S3-D = 0.08740–0.09767 W |

## Headline: window (gross) J/token, from RESULTS.md

| Board | Window J/token (mean of 3) | Interval | Tokens per joule | ms/token |
|---|---|---|---|---|
| P4 | **7.909 mJ** | 7.8334–7.9850 mJ | 126.4 | 13.572 |
| S3-D | **12.357 mJ** | 12.2148–12.5240 mJ | 80.9 | 26.308 |
| S3-B | **14.709 mJ** | 14.4718–14.9191 mJ | 68.0 | 33.401 |

Total, marginal and idle figures, per-rep data and every attempt are in `RESULTS.md` and `score_output.md`.

## Files

- **This directory:**
  - PREREG, RESULTS, NOTES, the scoring and run scripts and their outputs (verbatim);
  - `calibration/`: `CALIBRATION.md`, `CALIBRATION_NOTES.md`, `calibration.json`, `calibration_points.jsonl`,
    copied from power-logger;
  - `dut/`: the sync-pin patches for the S3 and P4 sketches, with their README, copied from power-logger;
  - `dut/s3-stack/`: the twelve S3 patches behind S3-B and S3-D, in stack order (see above);
  - `SHA256SUMS` for every file here.
- **Raw logs are not mirrored.** They are 252 MB of sample streams in 356 files, kept on Miu under
  `~/Desktop/esp32-llm/evals/power-01/logs/`. `RAW_LOGS_SHA256SUMS` lists every file and its sha256, so a copy can
  be checked against it.
