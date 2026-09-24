# Tamanna Gen 3 half — the two canonical 3090 rows with the slot forced to PCIe 3.0, 2026-09-21

RUN AND COMPLETE, 2026-09-21 22:32:48 to 22:38:17 PDT, 55 minutes after the Gen 4 block 3 on the same
box. Results record; facts as measured. Companion to `../tamanna-gen4-baseline-2026-09-21/`, which
has the inventory, the build record, the model digests and the cold-load finding.

## What changed between the halves

Mark set the PCIe slot to Gen 3 in the BIOS. That is a reboot (22:28:43), so the driver and page cache
were fresh; nothing else on the box changed. Confirmed before launch:

| | Gen 4 half (block 3) | Gen 3 half |
|---|---|---|
| `pcie.link.gen.max` / `hostmax` / `gpumax` | 4 / 4 / 4 | **3 / 3 / 4** (the card still advertises 4; the host caps it) |
| Under load, every sample, every run | gen 4 x16, 100% | **gen 3 x16 in all 252 under-load samples across the 12 runs** (primes included), host view and GPU view both |
| Card before first load | 1 MiB, 49 °C | 7 MiB, 46 °C |
| Page cache at start | warm from block 2 | empty (fresh boot) — every first load cold, absorbed by the priming run |
| Build, models, harness, threads | v0.4.0 `5266f24`, CUDA 12.4, sm_86; same two files, same digests; `llama-bench -ngl 99 -fa 1 -p 512 -n 128 -d 0,4096,8192 -r 5`; 8 threads | identical |

## Design

Block 3's priming design: three reps per model, models alternating within each rep with the starting
model flipped on rep 2, and a **discarded priming run of the identical command before every measured
run** so each measured run loads warm. 12 llama-bench invocations, 6 measured. 1 s nvidia-smi telemetry
from before launch to after exit on all 12. Runner is `gen3_baseline.py` (block 3's runner with the
output directory changed). `compare3.py` builds `comparison.md` / `comparison.json`.

## The three-way

Miu columns are the 08-28 published A-B-B-A (b10088, root bracket) and the 09-07 build A/B b10088
block (n=3, warm, no root). Tamanna columns are the warm measured runs, n=3 each, mean of llama-bench's
5-repeat average, min..max over reps in brackets. Miu is a different platform (i7-8086K, DDR4-2667,
PCIe 3.0, 62 GiB, CUDA 12.8 toolkit, b10088 not v0.4.0), so its deltas are "Tamanna vs Miu" and carry
every one of those differences. The gen 3 vs gen 4 column is the same box, same build, same files,
same night, one reboot apart.

| model | metric | Miu b10088 08-28 published | Miu b10088 09-07 (n=3) | Tamanna gen 3 (n=3) | Tamanna gen 4 (n=3) | gen 3 vs 4, same box | gen 3 vs Miu 08-28 | gen 4 vs Miu 08-28 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Ornith 1.5-35B-A3B | tg128 d=0 | 172.44 | 167.68 [164.59..169.53] | 176.12 [176.05..176.18] | 177.65 [177.61..177.68] | **-0.86%** (resolvable) | +2.13% | +3.02% |
|  | tg128 d=4096 | 170.69 | 165.44 [162.78..168.73] | 173.11 [173.11..173.11] | 174.71 [174.63..174.81] | **-0.92%** (resolvable) | +1.42% | +2.36% |
|  | tg128 d=8192 | 166.59 | 163.71 [159.96..165.61] | 170.07 [170.05..170.09] | 171.47 [171.36..171.59] | **-0.82%** (resolvable) | +2.09% | +2.93% |
|  | pp512 d=0 | 3,602.9 | 3,464.6 [3,348.6..3,531.7] | 3,653.7 [3,653.1..3,654.3] | 3,652.9 [3,651.8..3,653.8] | **+0.02%** (inside spread) | +1.41% | +1.39% |
|  | pp512 d=4096 | 3,387.4 | 3,257.3 [3,206.5..3,320.2] | 3,444.8 [3,439.4..3,451.8] | 3,454.1 [3,450.7..3,457.2] | **-0.27%** (inside spread) | +1.69% | +1.97% |
|  | pp512 d=8192 | 3,263.3 | 3,157.0 [3,094.5..3,197.4] | 3,332.0 [3,328.0..3,334.8] | 3,339.1 [3,336.1..3,342.3] | **-0.21%** (resolvable) | +2.10% | +2.32% |
| Qwen3.6-35B-A3B | tg128 d=0 | 158.18 | 156.54 [156.25..157.02] | 161.75 [161.70..161.78] | 162.93 [162.83..163.02] | **-0.73%** (resolvable) | +2.26% | +3.01% |
|  | tg128 d=4096 | 157.18 | 155.77 [155.47..156.19] | 159.84 [159.48..160.06] | 160.68 [160.49..160.99] | **-0.52%** (resolvable) | +1.69% | +2.23% |
|  | tg128 d=8192 | 153.47 | 152.52 [152.35..152.72] | 156.63 [156.56..156.69] | 157.72 [157.71..157.73] | **-0.69%** (resolvable) | +2.06% | +2.77% |
|  | pp512 d=0 | 3,694.2 | 3,618.5 [3,606.6..3,639.7] | 3,750.9 [3,726.9..3,767.4] | 3,767.7 [3,760.8..3,771.6] | **-0.45%** (inside spread) | +1.53% | +1.99% |
|  | pp512 d=4096 | 3,493.1 | 3,440.2 [3,434.5..3,445.6] | 3,593.8 [3,589.7..3,595.9] | 3,587.1 [3,581.0..3,594.0] | **+0.19%** (inside spread) | +2.88% | +2.69% |
|  | pp512 d=8192 | 3,362.5 | 3,311.9 [3,304.1..3,316.1] | 3,447.5 [3,447.2..3,447.6] | 3,458.2 [3,455.0..3,463.5] | **-0.31%** (resolvable) | +2.53% | +2.85% |

## Gen 3 to gen 4 on the same box

Resolvability by the 08-28 rule: a gap counts only if it exceeds the larger of the two same-config
repeat spreads.

| model | metric | gen 3 − gen 4 (tok/s) | gen 3 spread | gen 4 spread | verdict |
|---|---|---:|---:|---:|---|
| Ornith 1.5-35B-A3B | tg128 d=0 | -1.54 | 0.14 | 0.07 | RESOLVABLE |
|  | tg128 d=4096 | -1.60 | 0.01 | 0.18 | RESOLVABLE |
|  | tg128 d=8192 | -1.40 | 0.03 | 0.23 | RESOLVABLE |
|  | pp512 d=0 | +0.79 | 1.22 | 2.02 | UNRESOLVABLE |
|  | pp512 d=4096 | -9.29 | 12.37 | 6.45 | UNRESOLVABLE |
|  | pp512 d=8192 | -7.07 | 6.89 | 6.21 | RESOLVABLE |
| Qwen3.6-35B-A3B | tg128 d=0 | -1.18 | 0.08 | 0.19 | RESOLVABLE |
|  | tg128 d=4096 | -0.84 | 0.58 | 0.49 | RESOLVABLE |
|  | tg128 d=8192 | -1.08 | 0.13 | 0.02 | RESOLVABLE |
|  | pp512 d=0 | -16.82 | 40.50 | 10.81 | UNRESOLVABLE |
|  | pp512 d=4096 | +6.70 | 6.24 | 12.99 | UNRESOLVABLE |
|  | pp512 d=8192 | -10.75 | 0.36 | 8.55 | RESOLVABLE |

**Decode: gen 3 is 0.5 to 0.9% slower than gen 4 on every cell of both models, and every one of the
six cells resolves**, because the repeat spreads are 0.01 to 0.58 tok/s against gaps of 0.8 to 1.6
tok/s. The effect is the same size at d=0, 4096 and 8192, which is what a per-token fixed cost looks
like rather than a bandwidth-scaling one.

**Prefill: no bus effect at this size.** The six cells sit between −0.45% and +0.19%; two of them land
above zero, four resolve as "unresolvable" and the two that clear the spread (Ornith and Qwen at
d=8192, both about −0.2 to −0.3%) are 7 and 11 tok/s on 3,300 to 3,450. With `-ngl 99` the prefill
never crosses the bus except for the prompt tokens and the logits, and 512 tokens is not enough to
notice. Nothing here is a ±3% story.

**Against Miu.** Tamanna at gen 3 is still 1.4 to 2.9% above the 08-28 published rows on every cell
and 2.1 to 6.1% above the 09-07 b10088 block. So of the +2 to +3% "Tamanna vs Miu" decode gap the
Gen 4 half reported, the bus accounts for well under one point (0.5 to 0.9), and the rest is the
platform (5700X, DDR4-3200, RAM, kernel, toolkit 12.4 vs 12.8, b10088 vs v0.4.0 in the 08-28 column).
This is a measured split, not the pre-registered attribution: the pre-registration said "no
attribution to the bus until the gen 3 half runs", and this is that half.

## Telemetry, gen 3 half

Under-load samples (utilisation ≥ 50%). SM clock 1,920 to 1,935 MHz median, never under 1,800;
memory clock 9,501 in every sample; card on the 420 W cap during prefill as before. Peaks 67 to 69 °C
from starts of 56 to 60 °C after the first run, the same envelope as the Gen 4 half. Two samples
(the last sample of the rep 3 Qwen prime and of the rep 3 Qwen measured run) carry `0x24`, which
adds the SW thermal-slowdown bit to the power-cap bit; both are at 61 to 62 °C with the SM clock at
1,920 and 1,935 MHz, so the flag was raised without a clock change and does not touch the numbers.

| run | model | PCIe gen (host view / GPU view) x width | under-load samples | SM clock median (min..max) | mem clock | power mean (max) | temp start → max | reasons |
|---|---|---|---:|---|---|---|---|---|
| prime rep 1 | Ornith 1.5-35B-A3B | 3/3 x[16] | 21 | 1920 (1830..1950) | 9501 | 359 W (419) | 46 → 68 °C | none / SW power cap |
| measured rep 1 | Ornith 1.5-35B-A3B | 3/3 x[16] | 21 | 1920 (1845..1935) | 9501 | 357 W (419) | 60 → 69 °C | none / SW power cap |
| prime rep 1 | Qwen3.6-35B-A3B | 3/3 x[16] | 19 | 1935 (1830..1950) | 9501 | 352 W (418) | 60 → 67 °C | none / SW power cap |
| measured rep 1 | Qwen3.6-35B-A3B | 3/3 x[16] | 20 | 1928 (1845..1950) | 9501 | 353 W (418) | 56 → 67 °C | none / SW power cap |
| prime rep 2 | Qwen3.6-35B-A3B | 3/3 x[16] | 22 | 1920 (1800..1950) | 9501 | 348 W (417) | 59 → 68 °C | none / SW power cap |
| measured rep 2 | Qwen3.6-35B-A3B | 3/3 x[16] | 22 | 1920 (1830..1950) | 9501 | 350 W (416) | 60 → 68 °C | none / SW power cap |
| prime rep 2 | Ornith 1.5-35B-A3B | 3/3 x[16] | 20 | 1928 (1830..1950) | 9501 | 371 W (416) | 58 → 68 °C | none / SW power cap |
| measured rep 2 | Ornith 1.5-35B-A3B | 3/3 x[16] | 20 | 1920 (1800..1950) | 9501 | 367 W (418) | 59 → 68 °C | none / SW power cap |
| prime rep 3 | Ornith 1.5-35B-A3B | 3/3 x[16] | 21 | 1920 (1800..1950) | 9501 | 359 W (418) | 60 → 69 °C | none / SW power cap |
| measured rep 3 | Ornith 1.5-35B-A3B | 3/3 x[16] | 21 | 1920 (1800..1950) | 9501 | 358 W (417) | 60 → 69 °C | none / SW power cap |
| prime rep 3 | Qwen3.6-35B-A3B | 3/3 x[16] | 23 | 1920 (1845..1935) | 9501 | 343 W (418) | 60 → 68 °C | none / SW power cap / +SW thermal flag (1 sample) |
| measured rep 3 | Qwen3.6-35B-A3B | 3/3 x[16] | 22 | 1928 (1830..1935) | 9501 | 352 W (417) | 57 → 68 °C | none / SW power cap / +SW thermal flag (1 sample) |

## Caveats

- One reboot separates the halves. Fresh driver state is a possible confound in principle; the
  clocks, power, temperatures and repeat spreads are the same on both sides, so there is nothing to
  hang it on.
- The primes on this half show one whole-run-low cold run (Qwen rep 3 prime: 2,752 / 2,713 / 2,695 pp,
  159.16 tg) and one d=8192-only low (Qwen rep 1 prime: 3,061), the cold-load state the Gen 4 README
  describes. Both were discarded by design; the measured runs behind them are in line with the rest.
- n=3 per side. The decode gaps clear the spreads by 3x to 100x, but this is one night on one box.

## Files

| path | content |
|---|---|
| `gen3_baseline.py` | the runner |
| `compare3.py`, `comparison.md`, `comparison.json` | the three-way and resolvability tables, computed from the result files |
| `run.log`, `harness.out`, `results.json`, `summary.json` | orchestrator log, all 12 runs (`results` measured, `primes` discarded) with telemetry summaries, the 12-cell summary over measured runs |
| `raw-<model>-rep<n>.json`, `raw-prime-<model>-rep<n>.json` | llama-bench JSON and stderr tail per run |
| `telemetry-<model>-rep<n>.csv`, `telemetry-prime-…` | the 1 s nvidia-smi samples per run |
