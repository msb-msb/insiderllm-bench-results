# ESP32-S3 N16R8, esp32-ai TinyStories core matvec weights streamed as packed int4 with PIE unpack, bit-exact, 2026-10-11: P1–P4 held

Results record for `~/Desktop/esp32-llm/evals/int4-core-01/PREREG.md`. The 43 core int8 matvec tensors are restaged as
packed int4 in PSRAM, as was done for the head (`../miu-int4-head-01-2026-10-10/`). The PIE kernels unpack exactly.
It is stacked on head-traffic in its (b)-only configuration, with STOP_AT_EOT=0.

## Pre-registration

- **PREREG.md** sha256 `c5ba1695b88f7d05b7a85ee93a70baad25bcc9766ee10a2d58bb4a20fdbb4d73`.
- **Written 2026-10-11T09:30:47-07:00**, after compile-only checks and before anything was flashed.
- **21 s before** the first hardware run (gate capture at 09:31:08). The first timing run is at 09:31:48.
- Unchanged after the runs.

## Hardware

ESP32-S3 rev 2, 16 MB quad flash at 80 MHz, 8 MB octal PSRAM at 80 MHz, native USB. **No display attached.** Host: Miu.

## Firmware

- esp32-ai @ `52ebcbb`, core 3.3.10 (IDF v5.5.4), `-O3`.
- FQBN as `../miu-cpu-clock-01-2026-10-10/` with `CPUFreq=<240|160|80>`.
- **Patch stack** `no-display+logit-checksum+simd-head+int4-head+simd-core+eot-flag+head-traffic+int4-core`:
  - as `../miu-head-traffic-01-2026-10-11/`;
  - plus `int4-core.patch` `59c6fa858759e9560507e2404097bd4be733052289598128dbf4468222953bf1`.
- **`CORE_INT4` (default 1):** every core tensor is restaged at boot from the file's codes into the int4 head kernel
  layout, 286,848 B in total.
  - The 96-column tensors use the int4 head kernel `llm_head_dot96_s4`, unchanged.
  - `ple_proj` (128 columns) uses a new `llm_dot128_s4`.
  - `down` (66 columns) stays padded with zero weights, now to 96 columns, so its int4 rows stay 16-byte aligned. It
    uses `llm_head_dot96_s4`.
  - fp32 row scales, the float tail and the dual-core split are unchanged.
  - CORE_INT4=0 is the int8 simd-core path.
  - Per-kernel boot self-tests compare every row against `(code − 8) · x` from the file.
- **Defines:**
  - gate: `-DHEAD_SC16=0 -DLOGITS_SRAM=1 -DLOGIT_CHECKSUM=1`;
  - timing: `-DHEAD_SC16=0 -DLOGITS_SRAM=1 -DCORE_INT4=1`. Control: `-DCORE_INT4=0`.

## Model

Release model.bin `1d8326c05c383ccfa615f5455575802817cb453dbc7ab28875d41a9dbb45477e`; every boot printed `fp=a9bdd778`.

## Predictions (verbatim) and verdicts

| | prediction (verbatim) | verdict | measured |
|---|---|---|---|
| P1 | "P1: bit-identical." | **held** | `4400a1cbf4a5137d`, 20/20 hashes; text identical |
| P2 | "P2: non-head drops from 26.4 to between 22.0 and 25.0 ms at 240 MHz." | **held, at the lower bound** | 22.0 (sum of four stages at 0.1 ms print precision: ±0.2; ms/token − head = 22.1) |
| P3 | "P3: head unchanged ±1.0 ms (vs the head-traffic-01 result)." | **held** | 21.2: 0.0 against the (b)-only base, −0.5 against the pre-registered (a)+(b) 21.7 |
| P4 | "P4: a/f+b fit (240/80, checked at 160) shows the non-head clock-independent part falling from 14.95 ms by 2–4.5 ms." | **held** | b 14.95 → 10.50 (−4.45); a/240 11.45 → 11.50; fit predicts 27.75 at 160, measured 27.5 |

## Correctness gate (240 MHz, `-DLOGIT_CHECKSUM=1`)

- **logit_hash_all:** `4400a1cbf4a5137d`, with 20/20 per-token hashes equal to the simd-core gate.
- **Text:** sha256 `b9abf55bdd1c…`, identical.
- **Kernel self-tests:**
  - `simd core int4 selftest: dot96_s4 4632/4632 rows ok`
  - `dot128_s4 576/576 rows ok`
  - `down96_s4 576/576 rows ok`
- **Memory:** PSRAM allocated 3.25 MB against 2.98 MB; the int8 staging is kept for its scales. Free SRAM at boot is
  187 KB.

## Result (ms/token, n = 3 per configuration, range 0.0 everywhere)

| stage | control 240 | int4-core 240 | int4-core 160 | int4-core 80 |
|---|---:|---:|---:|---:|
| input | 1.6 | 1.0 | 1.1 | 1.6 |
| attn | 17.8 | 16.1 | 20.1 | 32.8 |
| ffn | 3.2 | 2.4 | 3.1 | 5.2 |
| ple | 3.7 | 2.5 | 3.2 | 5.4 |
| **non-head sum** | **26.3** | **22.0** | **27.5** | **45.0** |
| head | 21.2 | 21.2 | 21.9 | 24.4 |
| **ms/token** | **47.5** | **43.3** | **49.5** | **69.5** |
| end-to-end tok/s | 20.62 | 22.59 | 19.62 | 13.82 |
| 200 tokens wall | 9.70 s | 8.85 s | 10.19 s | 14.47 s |

Text sha256 `b9abf55b…` in all 12 runs.

**Exploratory per-stage fit** (240/80 MHz, checked at 160; "before" is simd-core-01):

| stage | before a/240 / b | int4-core a/240 / b | bytes saved per token | saved / Δb |
|---|---|---|---:|---:|
| input | 0.30 / 1.30 | 0.30 / 0.70 | 36,864 | 61 MB/s |
| attn | 8.35 / 9.55 | 8.35 / 7.75 | 110,592 | 61 MB/s |
| ffn | 1.40 / 1.80 | 1.40 / 1.00 | 56,448 | 71 MB/s |
| ple | 1.40 / 2.30 | 1.45 / 1.05 | 73,728 | 59 MB/s |
| non-head | 11.45 / 14.95 | 11.50 / 10.50 | 277,632 | 62 MB/s |

The whole gain is in the clock-independent part, at the same ~62 MB/s PSRAM rate as the int4 head. The int4 unpack
adds no clock-dependent time at this precision. Attention (16.1 ms) is still the largest non-head stage: 8.35 ms is
clock-scaled float compute, and 7.75 ms is clock-independent, mostly the fp32 KV cache.

The board was left on this build at 240 MHz, with checksum off and STOP_AT_EOT=0
(`final_check_i4_240MHz.txt`: 43.3 ms/token, 22.59 tok/s).

## Files

Paths are local, not in this repo: bare `tools/` and `logs/` paths are under Miu `~/Desktop/esp32-llm/`.

- `~/Desktop/esp32-llm/evals/int4-core-01/` PREREG.md and RESULTS.md (sha256
  `eef1f1a6ef5e7624b34b1431418a142f158f5dca7c4cd4e0f2872fac53259254`).
- `~/Desktop/esp32-llm/logs/int4-core-01/`:
  - `gate_i4.txt`;
  - `run_{ctrl_240,i4_240,i4_160,i4_80}MHz_{1,2,3}.txt`, `build_*.txt`, `sweep_console.txt`;
  - `final_reflash_i4_240MHz.txt`, `final_check_i4_240MHz.txt`.
- Sweep: `tools/sweep_int4_core.sh`. Build info:
  `~/Desktop/esp32-llm/builds/no-display+logit-checksum+simd-head+int4-head+simd-core+eot-flag+head-traffic+int4-core/build/*/BUILDINFO.txt`.
