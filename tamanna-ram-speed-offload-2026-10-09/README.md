# Tamanna RAM speed (DDR4-3000 vs 2133) on offloaded decode, 2026-10-09

Results record for `docs/candidates/tamanna-ram-speed-offload-2026-10.md` (pre-registered and approved by Mark
2026-10-09, including the BIOS switch protocol). Same box, same files, same build, same flags at both speeds; only
the RAM speed changes, by Mark in the BIOS. Order: 3000 → Auto/2133 → back to 3000 at 1.35 V, with `dmidecode`
(Mark) and `stream_read.c` checked after each switch.

## Setup

- **Machine:** Tamanna, RTX 3090 24 GB at PCIe gen 4 x16, Ryzen 7 5700X 8c, 64 GB (4 × 16 GB F4-3200C16-16GVK),
  BIOS P4.00, Ubuntu 26.04. llama.cpp v0.4.0 `5266f24` at `~/llama-v0.4.0` (CUDA 12.4 / gcc-13, sm_86).
- **Harness:** `ramspeed.py <speed>`.
  - Arm A: `llama-bench -m Qwen3.6-35B-A3B-UD-Q4_K_M.gguf -ngl 99 -ncmoe N -fa 1 -p 512 -n 128 -d 0,4096 -r 5 -t 8
    -lm mmap`, N = 40 (every expert layer on the CPU), 20, 0 (fully resident control); 3 reps, each running
    40, 20, 0 as (discarded priming, measured).
  - Arm B: `llama-bench -m Qwen3.8-Flash-Next-UD-IQ3_XXS-00001-of-00003.gguf -ngl 99 -ncmoe 29 -fa 1 -p 0 -n 128
    -d 0,4096 -r 3 -t 6 -lm mmap` (the Miu 09-08 sweep's flags), one priming run, then 3 measured.
- **Files, hashed on Tamanna 2026-10-09:** Qwen3.6-35B-A3B UD-Q4_K_M `ac0e2c11…53e31a61` (matches 09-21); Flash-Next
  UD-IQ3_XXS three shards `268f81fd…`, `cfe600b2…`, `f1912ba3…` (match the store's SHA256SUMS and the 09-07 record).
- **Conditions:** the ISTA IQ3_XXS download on Tamanna was paused (SIGSTOP on all 8 curls, by PID) for every
  measured run and resumed between arms. Per invocation: NVMe read bytes, MemAvailable, CPU Tctl, nvidia-smi.
- `-ncmoe 29` fits on this card (peak 23,390 MiB; Miu's was 23,652), so no change from the Miu flags.

## Arm at DDR4-3000 (14:22–14:36 PDT)

Bandwidth before the run (14:16, after memtest): **42.44 GB/s** at 4 threads (`stream_read.c`; repeats 42.07,
42.21). Mark reported dmidecode at 3000 MT/s on all four slots before memtest; the memtest pass and reboot
didn't change BIOS settings, and the bandwidth confirms the speed.

Mean of 3 measured invocations of llama-bench's own average, [min..max], tok/s:

| arm | -ncmoe | tg128 d=0 | tg128 d=4096 | pp512 d=0 | pp512 d=4096 |
|---|---:|---|---|---|---|
| A, 35B-A3B | 40 (all experts on CPU) | 46.46 [46.43..46.48] | 46.32 [46.30..46.34] | 484.5 [484.2..485.1] | 465.9 [465.3..466.9] |
| A | 20 | 73.43 [73.34..73.53] | 72.97 [72.92..73.04] | 811.7 [811.2..812.0] | 777.2 [776.6..777.8] |
| A | 0 (resident) | 162.90 [162.63..163.04] | 160.69 [160.61..160.79] | 3,768.8 [3,765.8..3,771.8] | 3,605.0 [3,598.2..3,608.6] |
| B, Flash-Next UD-IQ3_XXS | 29 | 32.57 [32.53..32.62] | 32.38 [32.35..32.40] | — | — |

- NVMe reads during measured runs: 0.0–0.1 MiB on every arm A run; arm B 55.2 / 1.6 / 0.7 MiB (rep 1 after the
  priming run's cold load of 47.9 GB). Not expert-sized against an 82 GB file, so no cell is flagged.
- MemAvailable stayed 62,450–62,801 MiB throughout: llama-bench's mmapped weights count as reclaimable page cache.
- PCIe gen 4 x16 under load on every run. CPU Tctl max 55–65 °C.
- **Cross-rig reference only (different CPU, board and RAM):** Miu's 09-08 figure for arm B's exact flags was 22.60
  tok/s at d=0 and 24.48 at d=4096 (i7-8086K 6c, DDR4-2667). Tamanna at 3000 is 32.57 / 32.38. Not attributed to
  any one difference.

## Arm at DDR4-2133 (15:01–15:17 PDT)

Mark set the BIOS memory to Auto and rebooted (up 14:59). `sudo dmidecode -t memory` (Mark): **2133 MT/s, 1.2 V on all
four slots**. `stream_read.c` at 15:00: **31.52 GB/s** at 4 threads (repeats 31.61, 31.56). No machine-check lines in
the boot's kernel log. The download was not running (the reboot ended it; restarted after this arm). PCIe gen 4 x16
under load on every run.

**Same-day bandwidth ratio: 31.52 → 42.44 GB/s, +34.6%.** The pre-registered ranges were set on 32.36 → 41.95
(+29.6%, two different days). The ranges are not revised; the ratio is stated so the gains can be read against it.

## 3000 against 2133

`python3 compare.py` (`compare.txt`). Mean of 3 measured invocations, [min..max], tok/s; "predicted" is the
pre-registered range, not revised.

| arm | -ncmoe | metric | DDR4-2133 | DDR4-3000 | gain | ranges overlap? | predicted | inside? |
|---|---:|---|---|---|---:|---|---|---|
| A | 40 | tg128 d=0 | 36.84 [36.82..36.87] | 46.46 [46.43..46.48] | +26.1% | no | +15% to +30% | inside |
| A | 40 | tg128 d=4096 | 36.76 [36.71..36.78] | 46.32 [46.30..46.34] | +26.0% | no | +15% to +30% | inside |
| A | 40 | pp512 d=0 | 375.2 [374.6..375.9] | 484.5 [484.2..485.1] | +29.1% | no | -5% to +5% | OUTSIDE |
| A | 40 | pp512 d=4096 | 359.8 [359.4..360.1] | 465.9 [465.3..466.9] | +29.5% | no | -5% to +5% | OUTSIDE |
| A | 20 | tg128 d=0 | 60.40 [60.37..60.45] | 73.43 [73.34..73.53] | +21.6% | no | +5% to +20% | OUTSIDE |
| A | 20 | tg128 d=4096 | 60.07 [60.03..60.10] | 72.97 [72.92..73.04] | +21.5% | no | +5% to +20% | OUTSIDE |
| A | 20 | pp512 d=0 | 640.3 [640.1..640.4] | 811.7 [811.2..812.0] | +26.8% | no | -5% to +5% | OUTSIDE |
| A | 20 | pp512 d=4096 | 609.8 [609.5..610.1] | 777.2 [776.6..777.8] | +27.4% | no | -5% to +5% | OUTSIDE |
| A | 0 | tg128 d=0 | 162.57 [162.46..162.68] | 162.90 [162.63..163.04] | +0.2% | yes, within noise | -1% to +1% | inside |
| A | 0 | tg128 d=4096 | 160.56 [160.49..160.69] | 160.69 [160.61..160.79] | +0.1% | yes, within noise | -1% to +1% | inside |
| A | 0 | pp512 d=0 | 3,755.0 [3,753.4..3,756.9] | 3,768.8 [3,765.8..3,771.8] | +0.4% | no | -1% to +1% | inside |
| A | 0 | pp512 d=4096 | 3,586.1 [3,575.1..3,604.6] | 3,605.0 [3,598.2..3,608.6] | +0.5% | yes, within noise | -1% to +1% | inside |
| B | 29 | tg128 d=0 | 28.40 [27.52..28.85] | 32.57 [32.53..32.62] | +14.7% | no | +5% to +25% | inside |
| B | 29 | tg128 d=4096 | 28.76 [28.30..29.00] | 32.38 [32.35..32.40] | +12.6% | no | +5% to +25% | inside |

### Arm B, rep 1 at 2133 touched the NVMe

The first measured Flash-Next run at 2133 read **2,039 MiB** from the NVMe (reps 2 and 3: 10.4 and 2.6 MiB; at 3000:
55.2 / 1.6 / 0.7 MiB). That is expert-sized, so per the pre-registration that run is flagged and left out of the
verdict. Its decode (27.52 d=0) is also the low outlier. **Arm B on reps 2–3 only:** 2133 d=0 28.85 [28.84..28.85],
d=4096 28.65 [28.30..28.99]; against 3000, **+12.9% at d=0 and +13.0% at d=4096**, inside the +5 to +25% range either
way. The page cache at 2133 was evidently not fully warm after one priming run; why it differed from the 3000 arm
isn't known.

## Verdict, against the pre-registration

- **Resident control (`-ncmoe 0`): unaffected.** Decode +0.2 / +0.1%, ranges overlapping. pp512 +0.4 / +0.5%, inside
  ±1% (the d=0 ranges don't quite overlap, by 9 tok/s). The control holds, so the other cells can be attributed to
  RAM speed.
- **Decode with experts on the CPU: RAM speed moved it, as predicted in kind.** All experts on the CPU: **+26.1%**
  (36.84 → 46.46), inside +15 to +30%. Half: **+21.6%** (60.40 → 73.43), **just outside** the +5 to +20% range. I
  set that range assuming the CPU half was a smaller share of per-token time than it is; by the pre-registered
  formula, +26% at `-ncmoe 40` implies about 80% of per-token time is RAM-bound CPU work there (against the +34.6%
  same-day bandwidth ratio), and +21.6% at `-ncmoe 20` implies about 70%. Flash-Next at `-ncmoe 29`: +12.9 / +13.0%
  (reps 2–3), inside.
- **Prompt processing with experts on the CPU: WRONG prediction.** I predicted about 0% (±5%), on the reasoning that
  llama.cpp copies offloaded experts to the GPU for large batches, so prefill would ride on PCIe. It moved
  **+27 to +30%**, about as much as decode. **Candidate explanation, not tested:** the experts are mmapped, so they
  sit in pageable memory, and a copy to the GPU from pageable memory goes through a CPU memcpy into a pinned staging
  buffer first. That memcpy is a RAM read and write, so it scales with RAM speed. Consistent with Rushuna's 08-24
  finding that `GGML_CUDA_REGISTER_HOST=1` (registering the host memory, so no staging copy) gave +28% pp512. The
  test that would settle it: the same pp512 cells with `GGML_CUDA_REGISTER_HOST=1` at both speeds; if the gap
  closes, the staging copy was it. Not run; it is not in this pre-registration.
- **Nothing exceeded +30% on decode** against the pre-registered ratio, and nothing exceeded the +34.6% same-day
  bandwidth ratio anywhere.

**What this means for published figures:** no published Tamanna row is offloaded, so nothing needs correcting.
From here on every Tamanna offload figure states DDR4-3000. Offloaded-MoE decode and prefill on this box move with RAM
speed by roughly a quarter between 2133 and 3000; the Miu/Rushuna cross-rig comparisons already carry their RAM
speeds (DDR4 confound note) and this measures how much that matters: a lot.

## Restore to 3000

Mark restored DDR4-3000 in the BIOS and rebooted (up 15:44). `sudo dmidecode -t memory` (Mark): **Configured Memory
Speed 3000 MT/s on all four slots.** `stream_read.c` at 15:46: **42.30 GB/s** at 4 threads (repeats 42.03, 41.87),
matching the 3000 arm's 42.44. No machine-check lines in the boot's kernel log.

**Open: voltage.** dmidecode reads "Configured Voltage: 1.2 V" (min and max 1.2 V too) on every slot. It read the
same at 2133/Auto. On this board that field may report the stick's JEDEC SPD value rather than the voltage set in
the BIOS, and it was not read during the first 3000 boot, so there is nothing to compare it with. Linux can't read
the DRAM rail without root tools. **Confirmed by Mark in the BIOS (15:5x): DRAM Voltage 1.350 V.** So dmidecode's 1.2 V is the SPD value, not the
set voltage, on this board. The memtest pass covers this setting.


**Dated note 2026-10-10:** `GGML_CUDA_REGISTER_HOST=1` is a no-op for model weights on llama.cpp v0.4.0 (nothing calls
the registration function; `../tamanna-register-host-2026-10-10/`). The test proposed in the verdict could not run on this engine; the staging-copy explanation for the +27–30% pp512 gain is still untested.
