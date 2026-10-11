# ESP32-S3 N16R8, esp32-ai TinyStories per-stage time vs CPU clock (240/160/80 MHz), 2026-10-10: P1, P2, P3 all failed

Results record for `~/Desktop/esp32-llm/evals/cpu-clock-01/PREREG.md`. Only the CPU clock is varied, through the FQBN,
to test whether the output head is PSRAM-bound and the other stages compute-bound.

**Later reading:** this record's interpretation of the head was reversed by `../miu-simd-head-01-2026-10-10/`. The
measurements stand. See CORRECTIONS.md.

## Pre-registration

- **PREREG.md** sha256 `04ebd42657374496bee693ffdb044bc4ae11955741ea5ffa7ce4acf13a9dc23e`.
- **Written 2026-10-10T20:35:04-07:00.** The first sweep run started at 20:36:36 (`run_240MHz_1.txt` header), so the
  PREREG came **1 min 32 s before** it.
- **Not blind** to the 240 MHz profile: the dry run (`../miu-esp32-s3-repro-2026-10-10/`) had been seen.
- Unchanged after the runs.

## Hardware

- ESP32-S3 rev 2, 16 MB quad flash at 80 MHz, 8 MB octal PSRAM at 80 MHz (`../miu-esp32-s3-board-check-2026-10-10/`).
- Native USB, `/dev/ttyACM0`. **No display attached.** Host: Miu.

## Firmware

- esp32-ai @ `52ebcbb`, core 3.3.10 (IDF v5.5.4), `-O3`.
- **FQBN:** `esp32:esp32:esp32s3:UploadSpeed=921600,USBMode=hwcdc,CDCOnBoot=cdc,UploadMode=default,CPUFreq=<240|160|80>,FlashMode=qio,FlashSize=16M,PartitionScheme=custom,PSRAM=opi,DebugLevel=info`.
  Only `CPUFreq` changes, giving `-DF_CPU=160000000L` etc. The firmware does not print its runtime CPU frequency.
- **Patch stack:** `no-display.patch` (`USE_DISPLAY 1 → 0`), sha256
  `da49829dc9e2b66c57f309db39791c2972ddb8ad983d8657ded4a6fce5d2db7a`. Defines: none.
- Built and flashed with `tools/build_variant.sh no-display CPUFreq=<f>`, firmware only.

## Model

Release model.bin sha256 `1d8326c05c383ccfa615f5455575802817cb453dbc7ab28875d41a9dbb45477e`. Every boot printed
`build: bytes=14912348 fp=a9bdd778`.

## Method

- Per run: RTS reset, fixed compiled prompt (433 447 259 405), 200 greedy tokens.
- The firmware prints `throughput:` and `profile ms/token:` lines, captured with `tools/capture_serial.py`.
- 3 runs per clock, 9 in all. None failed or was excluded. There were 0 I2C errors.
- The 200-token text is byte-identical across all 9 runs.

## Predictions (verbatim) and verdicts

| | prediction (verbatim) | verdict | measured |
|---|---|---|---|
| H | "Hypothesis: the output head is PSRAM-bound; the other stages are compute-bound." | not supported | see below |
| P1 | "Prediction 1: non-head stages (input+attn+ffn+ple, 35.6 ms at 240 MHz) scale within ±15% of 1/f: ~53 ms at 160, ~107 ms at 80." | **failed** | 48.0 at 160 (within band, held); **86.7 at 80 (band 90.8–122.8)** |
| P2 | "Prediction 2: head ms changes by less than 30% of the CPU-proportional change (at 160 MHz: under 59.4→~68 ms; at 80 MHz: under ~95 ms)." | **failed** | 80.3 at 160, 149.9 at 80. The change is 72% and 77% of the proportional change |
| P3 | "Prediction 3: total ms/token at 160 MHz falls in 110–125 ms." | **failed** | 128.3 |
| C | "If the head scales near 1/f, the head is compute- or cache-latency-bound, not bandwidth-bound, and the PSRAM-clock experiment drops in priority." | not ruled on | "near" is undefined. The head scaled at 72–77% of 1/f |

## Result (ms/token, n = 3 per clock; every cell's range is 0.0 at the firmware's 0.1 ms print precision)

| stage | 240 MHz | 160 MHz | 80 MHz |
|---|---:|---:|---:|
| input | 2.1 | 2.9 | 5.4 |
| attn | 20.7 | 27.1 | 47.3 |
| ffn | 6.4 | 9.1 | 17.1 |
| ple | 6.3 | 8.9 | 16.9 |
| non-head sum | 35.5 | 48.0 | 86.7 |
| head | 59.1 | 80.3 | 149.9 |
| **ms/token** | **94.7** | **128.3** | **236.7** |
| end-to-end tok/s | 10.34 | 7.64 | 4.15 |
| 200 tokens wall | 19.34 s | 26.18 s | 48.16 s |

**Exploratory fit** (t = a/f + b on 240 and 80 MHz, checked at 160; not pre-registered):

| part | clock-scaled at 240 (a/240) | clock-independent (b) | fit at 160 | measured at 160 |
|---|---:|---:|---:|---:|
| head | 45.4 | 13.7 | 81.8 | 80.3 |
| non-head | 25.6 | 9.9 | 48.3 | 48.0 |

## Files

Paths are local, not in this repo: bare `tools/` and `patches/` paths are under Miu `~/Desktop/esp32-llm/`.

- `~/Desktop/esp32-llm/evals/cpu-clock-01/` PREREG.md and RESULTS.md (sha256
  `22bc77d67f370fa78f7e25a9b4a422692fd60e66230b6684235a2632c91a31bc`).
- `~/Desktop/esp32-llm/logs/cpu-clock-01/`:
  - `run_{240,160,80}MHz_{1,2,3}.txt`, `build_*MHz.txt`, `sweep_console.txt`;
  - `final_reflash_240MHz.txt`, `final_check_240MHz.txt`.
- Tools: `tools/build_variant.sh`, `tools/capture_serial.py`, `tools/sweep_cpu_clock.sh`, `patches/no-display.patch`.
