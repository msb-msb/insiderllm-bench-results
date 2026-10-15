# ESP32-P4 (v3.2) and ESP32-S3: FMA contraction explains the cross-chip logit difference, 2026-10-11: P1, P2, P3 failed; contraction off on both chips gives bit-identical logits

Results record for `~/Desktop/esp32-llm/p4/evals/fma-01/PREREG.md`.

**Hypothesis under test:** the P4's exact-mode logits (PR #24 harness, fp32 KV: `eac9915b0114d2e7`) differ from the S3 gate's (`4400a1cbf4a5137d`) because GCC contracts a*b+c into fused multiply-add differently on RISC-V and Xtensa.

## Pre-registration

- PREREG.md sha256 `26b2099fda9f52ee1011f7348a082d421b55b1d5a03b5161e862171fc1e4e44c`.
- Written 2026-10-11T20:25:52-07:00, before any build or flash. Unchanged after the runs.

## Hardware

- P4: Waveshare ESP32-P4-ETH, silicon v3.2, 400 MHz, CH343 `usb-1a86_…5C93015982`.
- S3: ESP32-S3 N16R8 rev 2, 240 MHz, native USB `usb-Espressif_…10:51:DB:xx:xx:xx`.
  - Used 20:31–20:34, after another session had logged `done 20:28:20` and released the port.
  - The board was restored byte-exact.

## Firmware

**P4 B4c**
- PR #24 `2906bde` + `bench-harness.patch` (e446eb73…), core 3.3.10 `esp32p4-libs` (ChipVariant=postv3), `-O3`.
- **Public source, pinned:** [https://github.com/msb-msb/esp32-ai/tree/2906bde9c4387381a2962a3c123e51b675bf7d46](https://github.com/msb-msb/esp32-ai/tree/2906bde9c4387381a2962a3c123e51b675bf7d46). This is the PR #24 head (Barkın Sarıkartal), mirrored on `msb-msb/esp32-ai` as the base of branch `insiderllm-p4`. Upstream PR: https://github.com/slvDev/esp32-ai/pull/24.
- `-DPR24_BENCH=1 -DPR24_KV_QUANT=0 -DLOGIT_CHECKSUM=1 -ffp-contract=off`. App `6a68886c20d8eb2b`.

**S3**
- `tools/build_variant.sh no-display+logit-checksum+simd-head+int4-head+simd-core+eot-flag+head-traffic+int4-core CPUFreq=240`, `VOCAB_REGEN=1`.
- `-DHEAD_SC16=0 -DLOGITS_SRAM=1 -DLOGIT_CHECKSUM=1 -ffp-contract=off`. App `352767d3db7b9f35`.

**Fused-instruction counts in the sketch object**
- P4: 27 → 0.
- S3: 25 (23 madd.s, 2 msub.s) → 0.

## Model

Release model.bin `1d8326c0…477e`; every boot printed `fp=a9bdd778`.

## Predictions (verbatim) and verdicts

| | prediction (verbatim) | verdict | measured |
|---|---|---|---|
| P1 | "P1: building the PR #24 exact-mode harness with -ffp-contract=off makes its 20-token logit hash equal to the S3's 4400a1cbf4a5137d." | **failed** | `57e5119adcfba1c4` ×3 |
| P2 | "P2: if P1 fails, the first divergent token moves later than token 2." | **failed** | First divergence at token 0; 3/20 match (9/20 with contraction on) |
| P3 | "P3: the S3 benchmark build with -ffp-contract=off still gives 4400a1cbf4a5137d (i.e. the S3 build doesn't currently rely on contraction)." | **failed** | `57e5119adcfba1c4` |

## Key result

| build | contraction | logit_hash_all |
|---|---|---|
| S3 gate | on | 4400a1cbf4a5137d |
| P4 exact | on | eac9915b0114d2e7 |
| P4 exact | **off** | **57e5119adcfba1c4** |
| S3 gate | **off** | **57e5119adcfba1c4** (20/20 per-token hashes = P4) |

- The text is `b9abf55b…` (763 B) in all four.
- **With contraction off on both chips, the logits are bit-identical.** libm, software against hardware division and sqrt, and conversions don't contribute.

**Cause found in the disassembly**
- Both compilers fuse the same statements with the same counts.
- But in RoPE's `q1*c − q2*sn`, the S3 (`mul.s` + `msub.s`, i.e. acc − a·b) fuses `q2*sn`, while the P4 (`fmul.s` + `fmsub.s`, i.e. a·b − c) fuses `q1*c`.
- That RoPE line is the only structural difference found. Whether it is the only contributor is untested.

**Cost of contraction off:** P4 16.3 → 17.0 ms/token (attention 6.8 → 7.3, n = 3); S3 43.2 → 44.6 (one checksum-build run).

## Board states

- **P4:** back on PR #24 as shipped + postv3 (`c2a4e67579b9607a`).
- **S3:**
  - 0x0–0x110000 backed up (two identical reads, sha256 `2d684989…192f`).
  - Restored, and read back identical.
  - Boots with the other session's `R ready … fast_sample=1` line.

## Files

Paths are local on Miu, under `~/Desktop/esp32-llm/`.

- `p4/evals/fma-01/`:
  - PREREG.md, RESULTS.md (sha256 `bca575732bd2f2703ed78af7585d7498f00feb1ccdf15e097842d8fbbf585428`);
  - `logs/`;
  - `s3_backup_0x0_0x110000.bin`.
