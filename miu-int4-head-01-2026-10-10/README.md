# ESP32-S3 N16R8, esp32-ai TinyStories output head streamed as packed int4 with PIE unpack, bit-exact, 2026-10-10: P1–P4 held

Results record for `~/Desktop/esp32-llm/evals/int4-head-01/PREREG.md`. At boot the head is restaged into PSRAM as
packed int4 (1,216,944 B of weights) instead of int8 (2,433,888 B), and unpacked in the PIE kernel.

## Pre-registration

- **PREREG.md** sha256 `2caf28eeb0b769805e17e257744d113527e052f3ef83ce70979387d0ba6c02f0`.
- **Written 2026-10-10T22:11:05-07:00**, before any build of the int4 firmware.
- **2 min 40 s before** the first hardware run (gate capture at 22:13:45).
- Unchanged after the runs.

## Hardware

ESP32-S3 rev 2, 16 MB quad flash at 80 MHz, 8 MB octal PSRAM at 80 MHz, native USB. **No display attached.** Host: Miu.

## Firmware

- esp32-ai @ `52ebcbb`, core 3.3.10 (IDF v5.5.4), `-O3`.
- FQBN as `../miu-cpu-clock-01-2026-10-10/` with `CPUFreq=<240|160|80>`.
- **Patch stack** (`no-display+logit-checksum+simd-head+int4-head`):
  - `no-display.patch` `da49829dc9e2b66c57f309db39791c2972ddb8ad983d8657ded4a6fce5d2db7a`
  - `logit-checksum.patch` `c434877c50999077fd78ac8f784f6e97f5dc3ae622a527842f8db3747784540b`
  - `simd-head.patch` `d72d482d28436cb0eba1c194b8d097b758cbc94318d9d48306d78d7f3062a5c0`
  - `int4-head.patch` `1e7524889cb0da9817aa17da832697d35451469b010f4001cf98f70d65286543` (adds `llm_head_dot96_s4`)
- **Defines:**
  - gate: `-DLOGIT_CHECKSUM=1 -DHEAD_INT4=1|0`;
  - timing runs: `-DHEAD_INT4=1`, with the int8-SIMD control at `-DHEAD_INT4=0`. `HEAD_SIMD` defaults to 1.

## Model

- Release model.bin `1d8326c05c383ccfa615f5455575802817cb453dbc7ab28875d41a9dbb45477e`; every boot printed `fp=a9bdd778`.
- **Head storage in the file:**
  - tied, the first 25,353 rows of `tok_emb`;
  - offset-8 unsigned nibbles, with element 2k in the low nibble;
  - one per-tensor group of 128, so one group per 96-column row;
  - **fp16** scales.
- **Staged in PSRAM by this patch:**
  - 48 B per row, with lo = element 32c+k and hi = element 32c+16+k, both two's complement;
  - **fp32** scales, 101,412 B. Not changed; fp16 would save 50,706 B per token.

## Predictions (verbatim) and verdicts

| | prediction (verbatim) | verdict | measured |
|---|---|---|---|
| P1 | "P1: int4-head output is bit-identical to scalar/int8 (hash 4400a1cbf4a5137d, text)." | **held** | 20/20 hashes, `4400a1cbf4a5137d`; text identical |
| P2 | "P2: at 240 MHz, head drops from 43.6 to between 20 and 30 ms." | **held** | 24.1 |
| P3 | "P3: non-head unchanged within ±1.0 ms." | **held** | Δ 0.0 for every stage |
| P4 | "P4: the a/f+b fit (240 vs 80 MHz, checked at 160) gives a clock-independent head part of 17–25 ms (about half of 41.3). If the clock-dependent part grows past 8 ms, the unpack has made the head partly compute-bound again." | **held** | b = 22.6 ms; clock-dependent part 1.6 ms at 240 MHz |

## Correctness gate (240 MHz, `-DLOGIT_CHECKSUM=1`)

| | int4 (`HEAD_INT4=1`) | int8 SIMD (`HEAD_INT4=0`) |
|---|---|---|
| logit_hash_all (20 tokens) | `4400a1cbf4a5137d` | `4400a1cbf4a5137d` |
| per-token hashes vs scalar (`../miu-simd-head-01-2026-10-10/` gate) | 20/20 equal | 20/20 equal |
| text sha256 | `b9abf55bdd1c…` | same |
| boot self-test | `simd head selftest: 25353/25353 rows ok` (vs scalar `(code−8)·x` on the file codes) | 25353/25353 ok |
| head in PSRAM | `head   -> PSRAM  packed int4, 1318356 B` | – |
| free PSRAM at boot | 4.93 MB | 3.77 MB (simd-head-01) |

## Result (ms/token, n = 3 per configuration)

Profile ranges are 0.0 everywhere. The int8 control's tok/s ranged 12.31–12.32, and the int4 80 MHz wall time
23.61–23.62 s.

| stage | int8 SIMD 240 (control) | int4 240 | int4 160 | int4 80 |
|---|---:|---:|---:|---:|
| input / attn / ffn / ple | 2.1 / 20.7 / 6.4 / 6.3 | 2.1 / 20.7 / 6.4 / 6.3 | 2.9 / 27.1 / 9.1 / 8.9 | 5.4 / 47.3 / 17.1 / 16.9 |
| non-head sum | 35.5 | 35.5 | 48.0 | 86.7 |
| **head** | **43.6** | **24.1** | **24.8** | **27.2** |
| **ms/token** | **79.1** | **59.6** | **72.8** | **113.9** |
| end-to-end tok/s | 12.31–12.32 | 16.21 | 13.27 | 8.47 |
| 200 tokens wall | 16.24 s | 12.33 s | 15.08 s | 23.61–23.62 s |

- **Fit:** a = 372 ms·MHz, b = 22.6 ms. The prediction for 160 MHz is 24.9; it measured 24.8.

**PSRAM traffic per token (head; calculated from the shapes):**

| | bytes read | logit writes | MB/s over head time, reads / all | MB/s over b, reads / all |
|---|---:|---:|---:|---:|
| int8 SIMD | 2,535,300 | 101,412 | 58.1 / 60.5 | 61.5 / 63.9 |
| int4 SIMD | 1,318,356 | 101,412 | 54.7 / 58.9 | 58.5 / 63.0 |

## Files

- `~/Desktop/esp32-llm/evals/int4-head-01/` PREREG.md and RESULTS.md (sha256
  `d6d673d65d9adb4ced3a25639ad3eca8ab772f065f87d9854693a6f0ad58d098`).
- `~/Desktop/esp32-llm/logs/int4-head-01/`:
  - `gate_int4_{1,0}.txt`;
  - `run_{int8_240,int4_240,int4_160,int4_80}MHz_{1,2,3}.txt`, `build_*.txt`, `sweep_console.txt`;
  - `final_reflash_int4_240MHz.txt`, `final_check_int4_240MHz.txt`.
- Build info: `~/Desktop/esp32-llm/builds/no-display+logit-checksum+simd-head+int4-head/build/*/BUILDINFO.txt`.
