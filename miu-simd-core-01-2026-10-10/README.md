# ESP32-S3 N16R8, esp32-ai TinyStories core (non-head) int8 matvecs on PIE, bit-exact, 2026-10-10: P1–P5 held

Results record for `~/Desktop/esp32-llm/evals/simd-core-01/PREREG.md`. It is stacked on the int4 head. Every
integer-accumulate core matvec moves to PIE kernels, and every float op (attention QK/softmax/AV, norms, RoPE,
activations) is left as it was. The audit and plan are in `evals/simd-core-01/AUDIT.md`.

## Pre-registration

- **PREREG.md** sha256 `9822bdb011e639f84e975479203c15be2e562cff81a82b38869940b846c2be70`.
- **Written 2026-10-10T22:33:25-07:00**, before any build of the simd-core firmware.
- **1 min 43 s before** the first hardware run (gate capture at 22:35:08). The first timing run is at 22:35:54.
- Unchanged after the runs.

## Hardware

ESP32-S3 rev 2, 16 MB quad flash at 80 MHz, 8 MB octal PSRAM at 80 MHz, native USB. **No display attached.** Host: Miu.

## Firmware

- esp32-ai @ `52ebcbb`, core 3.3.10 (IDF v5.5.4), `-O3`.
- FQBN as `../miu-cpu-clock-01-2026-10-10/` with `CPUFreq=<240|160|80>`.
- **Patch stack** (`no-display+logit-checksum+simd-head+int4-head+simd-core`):
  - `no-display.patch` `da49829dc9e2b66c57f309db39791c2972ddb8ad983d8657ded4a6fce5d2db7a`
  - `logit-checksum.patch` `c434877c50999077fd78ac8f784f6e97f5dc3ae622a527842f8db3747784540b`
  - `simd-head.patch` `d72d482d28436cb0eba1c194b8d097b758cbc94318d9d48306d78d7f3062a5c0`
  - `int4-head.patch` `1e7524889cb0da9817aa17da832697d35451469b010f4001cf98f70d65286543`
  - `simd-core.patch` `a40b0ffade8687f487de3d53d7cd6aa4d2555e0a3fbf8b616e8615f257755251` (adds `llm_dot128_s8`,
    `llm_dot80_s8`, and a zero-padded `down` copy)
- **Defines:**
  - gate: `-DLOGIT_CHECKSUM=1 -DCORE_SIMD=1`;
  - timing runs: `-DCORE_SIMD=1`, with the int4-head control at `-DCORE_SIMD=0`. `HEAD_SIMD` and `HEAD_INT4` default
    to 1.

## Model

Release model.bin `1d8326c05c383ccfa615f5455575802817cb453dbc7ab28875d41a9dbb45477e`; every boot printed `fp=a9bdd778`.

## Predictions (verbatim) and verdicts

| | prediction (verbatim) | verdict | measured |
|---|---|---|---|
| P1 | "P1: output bit-identical (hash 4400a1cbf4a5137d, text)." | **held** | 20/20 hashes, `4400a1cbf4a5137d`; text identical |
| P2 | "P2: at 240 MHz, non-head total drops from 35.5 to between 15 and 28 ms." | **held** | 26.4 |
| P3 | "P3: head unchanged within ±1.0 ms (24.1)." | **held** | 24.1 |
| P4 | "P4: a/f+b fit (240 vs 80, checked at 160) shows the non-head clock-dependent part falling from ~25.6 ms to under 14 ms." | **held** | 11.45 ms |
| P5 | "P5: attention remains the largest non-head stage." | **held** | attn 17.9 of 26.4 |

## Correctness gate (240 MHz, `-DLOGIT_CHECKSUM=1`)

- **logit_hash_all:** `4400a1cbf4a5137d`, with 20/20 per-token hashes equal to the scalar gate.
- **Text:** sha256 `b9abf55bdd1c…`, identical.
- **Kernel self-tests** (every row vs `llm_dot_i8`):
  - `simd core selftest: dot96 4632/4632 rows ok`
  - `dot128 576/576 rows ok`
  - `dot80 576/576 rows ok`
- **SRAM:** free SRAM at boot is 289 KB, against 294 KB before.

## Result (ms/token, n = 3 per configuration, range 0.0 everywhere)

| stage | int4-head control 240 | simd-core 240 | simd-core 160 | simd-core 80 |
|---|---:|---:|---:|---:|
| input | 2.1 | 1.6 | 1.7 | 2.2 |
| attn | 20.7 | 17.9 | 21.9 | 34.6 |
| ffn | 6.4 | 3.2 | 3.9 | 6.0 |
| ple | 6.3 | 3.7 | 4.4 | 6.5 |
| **non-head sum** | **35.5** | **26.4** | **31.9** | **49.3** |
| head | 24.1 | 24.1 | 24.8 | 27.2 |
| **ms/token** | **59.6** | **50.4** | **56.7** | **76.5** |
| end-to-end tok/s | 16.21 | 19.05 | 16.85 | 12.40 |
| 200 tokens wall | 12.33 s | 10.50 s | 11.87 s | 16.13 s |

**Exploratory per-stage fit** (240/80 MHz, checked at 160; "before" is cpu-clock-01's non-head data, which matches this
control at 240 MHz exactly):

| stage | before a/240 / b | simd-core a/240 / b | fit vs measured at 160 |
|---|---|---|---|
| input | 1.65 / 0.45 | 0.30 / 1.30 | 1.75 vs 1.7 |
| attn | 13.30 / 7.40 | 8.35 / 9.55 | 22.07 vs 21.9 |
| ffn | 5.35 / 1.05 | 1.40 / 1.80 | 3.90 vs 3.9 |
| ple | 5.30 / 1.00 | 1.40 / 2.30 | 4.40 vs 4.4 |
| non-head | 25.60 / 9.90 | 11.45 / 14.95 | 32.12 vs 31.9 |

Clock-dependent work fell by 14.2 ms, but non-head time fell by only 9.1 ms, because b rose by 5.0 ms. The memory
traffic of the core weights is now exposed. AUDIT.md's estimate of about 21 ms of integer-accumulate time was too high.

## Files

Paths are local, not in this repo: bare `evals/` paths are under Miu `~/Desktop/esp32-llm/`.

- `~/Desktop/esp32-llm/evals/simd-core-01/`: AUDIT.md, PREREG.md, RESULTS.md (sha256
  `969c91da5b057d4b8105436cb8c634ba114b219369f849ccecc24bd3b22a956f`).
- `~/Desktop/esp32-llm/logs/simd-core-01/`:
  - `gate_core1.txt`;
  - `run_{ctrl_240,core_240,core_160,core_80}MHz_{1,2,3}.txt`, `build_*.txt`, `sweep_console.txt`;
  - `final_reflash_core_240MHz.txt`, `final_check_core_240MHz.txt`.
- Build info: `~/Desktop/esp32-llm/builds/no-display+logit-checksum+simd-head+int4-head+simd-core/build/*/BUILDINFO.txt`.
