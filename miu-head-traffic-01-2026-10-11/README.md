# ESP32-S3 N16R8, esp32-ai TinyStories output head side traffic (fp16 scales, logits in SRAM), bit-exact, 2026-10-11: P1–P3 held

Results record for `~/Desktop/esp32-llm/evals/head-traffic-01/PREREG.md`. It is stacked on the simd-core and eot-flag
builds, with STOP_AT_EOT=0. Two changes remove PSRAM traffic around the int4 head without changing a value:
- **(a)** the row scales stay fp16, as in the file;
- **(b)** the 101 KB logits buffer moves to internal SRAM.

## Pre-registration

- **PREREG.md** sha256 `72ddc332bf393aa839521ad12d1295d4daac75704b4d4f5f1c0370c4308f66c4`.
- **Written 2026-10-11T09:22:16-07:00**, after compile-only checks and before anything was flashed.
- **19 s before** the first hardware run (gate capture at 09:22:35). The first timing run is at 09:23:15.
- Unchanged after the runs.

## Hardware

ESP32-S3 rev 2, 16 MB quad flash at 80 MHz, 8 MB octal PSRAM at 80 MHz, native USB. **No display attached.** Host: Miu.

## Firmware

- esp32-ai @ `52ebcbb`, core 3.3.10 (IDF v5.5.4), `-O3`, `CPUFreq=240`.
- **Patch stack** `no-display+logit-checksum+simd-head+int4-head+simd-core+eot-flag+head-traffic`:
  - as `../miu-eot-flag-01-2026-10-11/`;
  - plus `head-traffic.patch` `e31a4625f5dd72daa187d7841d78e2ad86514a67d93aee1900699bcd025d2638`.
- vocab.h regenerated as in the eot-flag record.
- **(a) `HEAD_SC16`:**
  - The int4 head's scales are kept as fp16 in PSRAM: 50,706 B against 101,412 B fp32.
  - Each is widened per row by a branch-free exponent rebias, which is bit-equal to `half2float` on normal halves.
  - Boot self-test, all 25,353 rows: each scale equals the file's, is normal, and widens bit-identically.
- **(b) `LOGITS_SRAM`:** logits are allocated in internal SRAM, strictly (boot stops if it fails).
- **Defines:**
  - gate: `-DLOGIT_CHECKSUM=1`;
  - timing: defaults (both 1). Control: `-DHEAD_SC16=0 -DLOGITS_SRAM=0`.

## Model

Release model.bin `1d8326c05c383ccfa615f5455575802817cb453dbc7ab28875d41a9dbb45477e`; every boot printed `fp=a9bdd778`.

## Predictions (verbatim) and verdicts

| | prediction (verbatim) | verdict | measured |
|---|---|---|---|
| P1 | "P1: bit-identical." | **held** | `4400a1cbf4a5137d`, 20/20 hashes; text identical |
| P2 | "P2: head drops from 24.1 to between 21.0 and 23.5 ms at 240 MHz." | **held** | 21.7 |
| P3 | "P3: non-head unchanged ±1.0 ms." | **held** | 26.3 → 26.3 |

## Correctness gate (240 MHz, `-DLOGIT_CHECKSUM=1`)

- **logit_hash_all:** `4400a1cbf4a5137d`, with 20/20 per-token hashes equal to the simd-core gate.
- **Text:** sha256 `b9abf55bdd1c…`, identical.
- **Self-tests:** `head fp16 scale selftest: 25353/25353 rows ok`, int4 head 25,353/25,353, and core 4,632 / 576 / 576.

**SRAM (b): the logits buffer fits.** Internal heap immediately before → after the logits allocation:

| build | free | largest free block |
|---|---|---|
| control (logits in PSRAM) | 309,056 → 309,056 B | 262,132 → 262,132 B |
| LOGITS_SRAM=1 | 309,056 → 206,652 B | 262,132 → 163,828 B |

End-of-setup free SRAM is 289 KB for the control and 189 KB with (b).

## Result (ms/token, 240 MHz, n = 3 per configuration, range 0.0 everywhere)

| stage | control | (a)+(b) | exploratory: (a) only, n = 1 | exploratory: (b) only, n = 3 |
|---|---:|---:|---:|---:|
| input | 1.5 | 1.6 | 1.6 | 1.6 |
| attn | 17.9 | 17.8 | 17.9 | 17.8 |
| ffn | 3.2 | 3.2 | 3.2 | 3.2 |
| ple | 3.7 | 3.7 | 3.7 | 3.7 |
| **non-head sum** | **26.3** | **26.3** | 26.4 | 26.3 |
| **head** | **24.1** | **21.7** | 23.9 | **21.2** |
| **ms/token** | **50.4** | **48.0** | 50.3 | **47.5** |
| end-to-end tok/s | 19.06 | 20.40 | 19.10 | 20.62 |
| 200 tokens wall | 10.49 s | 9.81 s | 10.47 s | 9.70 s |

Text sha256 `b9abf55b…` in every run.

**Exploratory, not pre-registered:**
- **(b) carries the whole gain.** (a) alone saves 0.2 ms with the logits in PSRAM, and costs 0.5 ms on top of (b).
- **Reading, not tested:** once the logits writes leave PSRAM, the per-row fp16 widening is no longer hidden under
  memory stalls.
- **(b) only is exact:** `4400a1cbf4a5137d`, 20/20 hashes, identical text, head 21.2.
- **It is the faster configuration.** The next record (`../miu-int4-core-01-2026-10-11/`) stacks on it
  (`-DHEAD_SC16=0 -DLOGITS_SRAM=1`).

## Files

Paths are local, not in this repo: bare `tools/` and `logs/` paths are under Miu `~/Desktop/esp32-llm/`.

- `~/Desktop/esp32-llm/evals/head-traffic-01/` PREREG.md and RESULTS.md (sha256
  `ec078b9abbfd0a0e1d9915f4181161ecfb7eb26dbefaa047b1b5af2a2b5cc2e3`).
- `~/Desktop/esp32-llm/logs/head-traffic-01/`:
  - `gate_ht1.txt`, `gate_b_only.txt`;
  - `run_{ctrl,ht}_240MHz_{1,2,3}.txt`, `explore_a_only_240MHz.txt`, `explore_b_only_240MHz{,_2,_3}.txt`;
  - `build_*.txt`, `sweep_console.txt`.
- Sweep: `tools/sweep_head_traffic.sh`. Build info:
  `~/Desktop/esp32-llm/builds/no-display+logit-checksum+simd-head+int4-head+simd-core+eot-flag+head-traffic/build/*/BUILDINFO.txt`.
