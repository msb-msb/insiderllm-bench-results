# ESP32-S3 N16R8, esp32-ai TinyStories output head on the PIE int8 MAC, bit-exact, 2026-10-10: P1–P4 held

Results record for `~/Desktop/esp32-llm/evals/simd-head-01/PREREG.md`. The int8 head matvec is moved from a scalar
loop to a hand-written PIE kernel (`ee.vmulas.s8.accx`), with an exact integer result, and timed at three CPU clocks.

## Pre-registration

- **PREREG.md** sha256 `476aca53f9b83873192a96c87d996e175f3dadda0f4f75061cca2555097fa271`.
- **Written 2026-10-10T21:29:28-07:00:**
  - before any build of the SIMD firmware. The earliest surviving build record is 21:31:47
    (`logs/simd-head-01/build_gate_simd0.txt`). ⚠ An earlier compile-only check left no surviving record, because its
    BUILDINFO was overwritten;
  - **2 min 32 s before** the first hardware run (gate capture at 21:32:00);
  - before the timing runs.
- Unchanged after the runs. An addendum in RESULTS.md (the audit-01 cross-check) was added after the runs and changes
  no verdict.

## Hardware

ESP32-S3 rev 2, 16 MB quad flash at 80 MHz, 8 MB octal PSRAM at 80 MHz, native USB. **No display attached.** Host: Miu.

## Firmware

- esp32-ai @ `52ebcbb`, core 3.3.10 (IDF v5.5.4), `-O3`.
- FQBN as `../miu-cpu-clock-01-2026-10-10/` with `CPUFreq=<240|160|80>`.
- **Patch stack** (`tools/build_variant.sh no-display+logit-checksum+simd-head`):
  - `no-display.patch` `da49829dc9e2b66c57f309db39791c2972ddb8ad983d8657ded4a6fce5d2db7a`
  - `logit-checksum.patch` `c434877c50999077fd78ac8f784f6e97f5dc3ae622a527842f8db3747784540b`
  - `simd-head.patch` `d72d482d28436cb0eba1c194b8d097b758cbc94318d9d48306d78d7f3062a5c0` (adds `head_dot96_s8.S`)
- **Defines:**
  - gate: `-DLOGIT_CHECKSUM=1 -DHEAD_SIMD=0|1`;
  - timing runs: `-DHEAD_SIMD=1`, with the scalar control at `-DHEAD_SIMD=0`. `LOGIT_CHECKSUM` defaults to 0.

## Model

Release model.bin `1d8326c05c383ccfa615f5455575802817cb453dbc7ab28875d41a9dbb45477e`. Every boot printed `fp=a9bdd778`.

## Predictions (verbatim) and verdicts

| | prediction (verbatim) | verdict | measured |
|---|---|---|---|
| P1 | "P1: SIMD and scalar outputs are bit-identical (logit hashes, text)." | **held** | 20/20 logit hashes equal, `logit_hash_all 4400a1cbf4a5137d`; text identical |
| P2 | "P2: at 240 MHz, head ms drops from 59.1 to between 15 and 45 ms." | **held** | 43.6 |
| P3 | "P3: non-head stages unchanged within ±1.0 ms." | **held** | Δ 0.0 for every stage |
| P4 | "P4 (decider): at 240 vs 80 MHz, the SIMD head’s clock-independent share (fit a/f+b) is larger than the scalar head’s ~14 ms. If the SIMD head lands near 15–25 ms, the effective memory floor is low and int4/DMA are next. If it lands near 40 ms, upstream’s bandwidth floor is real and DMA overlap is next." | **held** | b = 41.3 ms, so it lands "near 40" |

The decider's next step ("DMA overlap") was later weakened by the audit-01 cross-check in RESULTS.md. Only about
2.4 ms of compute was left to hide, and forum DMA throughput (~53 MB/s) is below the ~61–64 MB/s that cached PIE
loads reach.

## Correctness gate (240 MHz, `-DLOGIT_CHECKSUM=1`)

| | scalar (`HEAD_SIMD=0`) | SIMD (`HEAD_SIMD=1`) |
|---|---|---|
| logit_hash_all (20 tokens) | `4400a1cbf4a5137d` | `4400a1cbf4a5137d` |
| text sha256 (200 tokens) | `b9abf55bdd1c3ba2883d3b05709c375ec0395ee691b758f7647ecce34a0cc467` | same |

The text sha256 is computed by `tools/parse_run.py` from the captured text between `>>> ` and `--- N tokens`. It is not a
firmware line, and it recomputes identically from the raw logs.
| boot self-test | – | `simd head selftest: 25353/25353 rows ok` |

## Result (ms/token, n = 3 per configuration, range 0.0 everywhere)

| stage | scalar 240 (control) | SIMD 240 | SIMD 160 | SIMD 80 |
|---|---:|---:|---:|---:|
| input / attn / ffn / ple | 2.1 / 20.7 / 6.4 / 6.3 | 2.1 / 20.7 / 6.4 / 6.3 | 2.9 / 27.1 / 9.1 / 8.9 | 5.4 / 47.3 / 17.1 / 16.9 |
| non-head sum | 35.5 | 35.5 | 48.0 | 86.7 |
| **head** | **59.1** | **43.6** | **44.7** | **48.3** |
| **ms/token** | **94.7** | **79.1** | **92.8** | **135.1** |
| end-to-end tok/s | 10.34 | 12.31 | 10.49 | 7.18 |
| 200 tokens wall | 19.34 s | 16.24 s | 19.07 s | 27.85 s |

- **Fit for the SIMD head:** a = 564 ms·MHz, b = 41.3 ms. The prediction for 160 MHz is 44.8; it measured 44.7.
- **Calculation:** the head reads 2,535,300 B per token (weights 2,433,888 + scales 101,412) and writes 101,412 B of
  logits. That is about 61 MB/s of reads over b, or about 64 MB/s counting the writes.

## Files

Paths are local, not in this repo: bare `tools/` and `logs/` paths are under Miu `~/Desktop/esp32-llm/`.

- `~/Desktop/esp32-llm/evals/simd-head-01/`: OPTIONS.md, PREREG.md, RESULTS.md (sha256
  `3bcd9b1847612238463f571b662a19002ec199e8f41b8203b6afb48fcd8793f9`).
- `~/Desktop/esp32-llm/logs/simd-head-01/`:
  - `gate_simd{0,1}.txt`;
  - `run_{scalar_240,simd_240,simd_160,simd_80}MHz_{1,2,3}.txt`, `build_*.txt`, `sweep_console.txt`;
  - `final_reflash_simd_240MHz.txt`, `final_check_simd_240MHz.txt`.
- Build info: `~/Desktop/esp32-llm/builds/no-display+logit-checksum+simd-head/build/*/BUILDINFO.txt`.
