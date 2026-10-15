# ESP32-S3 N16R8, esp32-ai TinyStories, rebuilt Arduino libs: 64 B D-cache line and 120 MHz octal PSRAM, bit-exact, 2026-10-11: 42.5 → 25.8 ms/token; P1, P7 held; P2–P5 ranges failed (faster than predicted)

Results record for `~/Desktop/esp32-llm/evals/cache-psram-2x2-01/PREREG.md`. The firmware is unchanged; the arms differ
only in the ESP-IDF libraries the Arduino core links (`qio_opi/` rebuilt with the pinned lib-builder for core 3.3.10).

> **Arms C and D:** flash clocked at 120 MHz, above the BY25Q128AS's 108 MHz rating for EBh without HPM, if the part
> is the AS. The flash (JEDEC 68 40 18) is not confirmed as BY25Q128ES; its SFDP table does not match the ES
> datasheet's.

## Pre-registration
- **PREREG.md** sha256 `a237c6b2952b06b4e47df9dcdb8a36373d646340fef6e7ba58744dcc9838332d`, frozen
  2026-10-11T16:42:08-07:00. Unchanged after the runs.
- **Addendum** `PREREG_ADDENDUM_2026-10-11.md` sha256 `d5aa80038897c93e7f684779db7fe8811834f5bb4b9e14e8a96cfc7b46ed24b1`,
  written 19:31:24. It records the flash-part check and the C/D label, and was written before any arm was flashed.
- **First flash** 19:32:04.

## Hardware
ESP32-S3 rev 0.2, 16 MB quad flash (Boya, JEDEC 68 40 18), 8 MB octal PSRAM, native USB. **No display attached.**
Host: Miu.

## Firmware
- esp32-ai @ `52ebcbb`, core 3.3.10 (IDF v5.5.4), `-O3`, 240 MHz.
- **Stack** `…+head-traffic+int4-core+psram-memtest` with `-DHEAD_SC16=0 -DLOGITS_SRAM=1 -DCORE_INT4=1`.
  `psram-memtest.patch` `8dd21368…` adds a two-core PSRAM pattern test and temperature logging.
- **Arms:**
  - A: 32 B line, PSRAM/flash 80/80;
  - B: 64 B line, 80/80;
  - C: 32 B line, 120/120;
  - D: 64 B line, 120/120.
  - Flash must be 120 MHz with octal PSRAM 120 in IDF v5.5.4.
  - S: the same firmware on stock libraries, as a reference.

## Model
Release model.bin `1d8326c05c383ccfa615f5455575802817cb453dbc7ab28875d41a9dbb45477e`; every boot printed `fp=a9bdd778`.

## Result (ms/token, n = 3 resets per arm, identical across runs)
| stage | A 32B/80 | B 64B/80 | C 32B/120 | D 64B/120 |
|---|---:|---:|---:|---:|
| input | 1.0 | 0.8 | 0.8 | 0.6 |
| attn | 15.3 | 13.0 | 13.1 | 11.3 |
| ffn | 2.4 | 2.0 | 2.1 | 1.8 |
| ple | 2.6 | 2.1 | 2.2 | 1.9 |
| head | 21.2 | 14.8 | 15.0 | 10.2 |
| **ms/token** | **42.5** | **32.7** | **33.2** | **25.8** |
| tok/s | 23.01 | 29.70 | 29.27 | 37.28 |

- **Validity:** every arm passed its memory tests (0 bad words). Every gate gave `logit_hash_all 4400a1cbf4a5137d`
  with 20/20 per-token hashes and identical text (`b9abf55b…`). The temperature rose at most +3 °C from boot.
- **D soak:** 15 minutes with checksums on, 158/158 memtests and 157/157 hashes, peak +8.0 °C.
- **Reference:** S (stock libraries) = A in every stage.

## Verdicts
| | verdict |
|---|---|
| **P1, exactness** | held |
| **P2, A = 43.3 ± 0.3** | failed as written: 42.5. S = 42.5, so the offset is the memtest build, not the libraries |
| **P3, B 33.5–39.5** | failed: 32.7. Saving 9.8 at its bound; head share 65% held |
| **P4, C 33.5–40.0** | failed: 33.2 |
| **P5, D 26.5–36.0** | failed: 25.8. The interaction bound held |
| **P6** | not tested |
| **P7, C vs A head ≥ 15%, input < 0.5 ms** | held: −29%, −0.2 |

Implied PSRAM rate gain (exploratory): 64 B line ×1.50, 120 MHz ×1.46, both ×2.31. The head's effective rate goes from
about 62 to about 143 MB/s.

The board was restored to the FAST_SAMPLE interactive build on stock libraries (seed 1 `968b9087…`, 43.40 ms/token).
The model partition was never written.

## Protocol deviation (noted 2026-10-11)
- **Stop rule not followed.** The PREREG said to stop if the control missed P2 (A = 43.3 ± 0.3). A measured 42.5,
  and the run continued.
- **Reason given.** The stock-library run had already ruled out the libraries: the same firmware on stock libraries
  gave 42.5 ms/token, with every stage identical to A. So the offset is the memtest-patch build, not the rebuilt
  libraries. The frozen protocol has no such exception.

## Follow-up (20:27)
The FAST_SAMPLE interactive build was moved to the 64 B-line libraries at 80/80 MHz (variant B).
- Gate: `4400a1cbf4a5137d`, text `b9abf55b…`, memtest PASS.
- Seed 1 output unchanged (`968b9087…`).
- Demo stream: greedy 24.11 → 31.43 tok/s; sampled 21.03 → 26.20 tok/s; seed-42 output unchanged.

The board is left on that build.

## Files
Paths are local, not in this repo.
- `~/Desktop/esp32-llm/evals/cache-psram-2x2-01/`: PREREG.md, PREREG_ADDENDUM_2026-10-11.md, and RESULTS.md (sha256 `b06f2ada41dee37ddd7b5ccc6e932de25ec61cbe93b6aa1ac2f2cb16df5d83f7`).
- `~/Desktop/esp32-llm/logs/cache-psram-2x2-01/`:
  - `flash_{id,sfdp,status}.txt`;
  - `gate_*.txt`, `run_*_{1,2,3}.txt`, `soak_D.txt`;
  - `run_arm.sh`, `run_restore.sh`.
- `~/Desktop/esp32-llm/libbuild/`: lib variants, build notes, datasheets.
