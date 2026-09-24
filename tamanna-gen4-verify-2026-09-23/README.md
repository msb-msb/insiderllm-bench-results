# Tamanna Gen 4 restored — verification run, 2026-09-23

RUN AND COMPLETE, 2026-09-23 13:17:29 to 13:23:00 PDT. Results record; facts as measured.

## Purpose

Verify that Tamanna's PCIe slot is back at Gen 4 and that the box reproduces its own 09-21 Gen 4 figures.
The slot was set to Gen 3 in the BIOS on 2026-09-21 for the gen 3 half of the baseline
(`../tamanna-gen3-baseline-2026-09-21/`), stayed there through the 09-22 DFlash run, and was set back to
Gen 4 on 2026-09-23. This run is the check that the restore took and nothing else drifted.

## Setup

| | |
|---|---|
| Box | Tamanna, RTX 3090 24 GB, Ryzen 7 5700X, 31 GiB DDR4, headless, open frame; rebooted 13:15 after the BIOS change |
| PCIe before launch | `pcie.link.gen.max / hostmax / gpumax` = 4 / 4 / 4; under load **gen 4 x16 in every sample of all 12 runs** (primes included) |
| Build | llama.cpp v0.4.0, commit `5266f24da75dc449bd56cbed7addb9c8e4a6a73e`, `~/llama-v0.4.0`, CUDA 12.4 / gcc-13, sm_86, GGML_NATIVE=OFF — the pinned build, confirmed by `git rev-parse HEAD` before the run |
| Models | `~/bench-models/Ornith-1.5-35B-A3B-Q4_K_M.gguf` and `Qwen3.6-35B-A3B-UD-Q4_K_M.gguf`, the files hashed on 09-21 |
| Harness | `llama-bench -ngl 99 -fa 1 -p 512 -n 128 -d 0,4096,8192 -r 5`, byte-identical to the baseline |
| Design | **Block 3 priming design**: three reps per model, models alternating, starting model flipped on rep 2, and a discarded priming run of the identical command before every measured run so each measured run loads warm. 12 invocations, 6 measured. 1 s nvidia-smi telemetry on every run |
| Runner | `gen4_verify.py` (the 09-21 block 3 runner with only its output directory changed) |
| Reference | `../tamanna-gen4-baseline-2026-09-21/block3/summary.json`, the warm measured rows the 09-21 README names as the Gen 4 reference |
| Pass criterion | pre-set: **every cell within 1%** of the 09-21 figure, else stop and report |

## Result: PASS, worst cell 0.58%

Mean of 3 reps of llama-bench's 5-repeat average; brackets are min..max over reps; delta is 09-23 relative
to 09-21.

| model | metric | 09-21 gen 4 (block 3 warm, n=3) | 09-23 gen 4 (n=3) | delta | within 1% |
|---|---|---:|---:|---:|---|
| Ornith 1.5-35B-A3B | tg128 d=0 | 177.65 [177.61..177.68] | 177.44 [177.37..177.52] | -0.12% | PASS |
|  | tg128 d=4096 | 174.71 [174.63..174.81] | 174.48 [174.46..174.50] | -0.13% | PASS |
|  | tg128 d=8192 | 171.47 [171.36..171.59] | 171.35 [171.23..171.46] | -0.07% | PASS |
|  | pp512 d=0 | 3,652.9 [3,651.8..3,653.8] | 3,658.7 [3,656.9..3,662.1] | +0.16% | PASS |
|  | pp512 d=4096 | 3,454.1 [3,450.7..3,457.2] | 3,445.2 [3,436.7..3,452.3] | -0.26% | PASS |
|  | pp512 d=8192 | 3,339.1 [3,336.1..3,342.3] | 3,335.5 [3,324.3..3,342.2] | -0.11% | PASS |
| Qwen3.6-35B-A3B | tg128 d=0 | 162.93 [162.83..163.02] | 162.88 [162.83..162.96] | -0.03% | PASS |
|  | tg128 d=4096 | 160.68 [160.49..160.99] | 160.73 [160.55..161.08] | +0.03% | PASS |
|  | tg128 d=8192 | 157.72 [157.71..157.73] | 157.73 [157.66..157.78] | +0.01% | PASS |
|  | pp512 d=0 | 3,767.7 [3,760.8..3,771.6] | 3,745.8 [3,717.3..3,761.3] | -0.58% | PASS |
|  | pp512 d=4096 | 3,587.1 [3,581.0..3,594.0] | 3,584.5 [3,568.7..3,597.4] | -0.07% | PASS |
|  | pp512 d=8192 | 3,458.2 [3,455.0..3,463.5] | 3,451.6 [3,449.0..3,453.1] | -0.19% | PASS |

All 12 cells are inside 1%. Eleven are inside 0.3%. The worst is Qwen3.6 pp512 at d=0 at −0.58%, where one
of the three 09-23 reps read 3,717 against 3,759 and 3,761; the other two reps sit on the 09-21 figure.
Decode agrees to 0.13% or better on every cell.

Card idle at 7 MiB and 44 °C before the first load, 58 °C after the last. SM clock 1,920 MHz median under load,
memory clock 9,501, on the 420 W cap during prefill, the same envelope as 09-21.

## What this settles

Gen 4 is restored and Tamanna reproduces itself across a BIOS change and a reboot two days apart. The Gen 4
reference rows for the box remain the 09-21 block 3 figures; this run is a check on them, not a replacement.
The 09-22 DFlash record (`../tamanna-dflash-35b-a3b-2026-09-22/`) carries a dated note that it was made at
Gen 3, bounded by the 09-21 halves at 0.5–0.9% on decode and ~0 on prefill for a resident model.

## Files

| path | content |
|---|---|
| `gen4_verify.py` | the runner, as run on Tamanna |
| `compare.py` | builds the table above from `summary.json` and the 09-21 block 3 summary |
| `run.log`, `harness.out` | orchestrator log |
| `results.json`, `summary.json` | all 12 runs with telemetry summaries (`results` measured, `primes` discarded); the 12-cell summary over measured runs |
| `raw-<model>-rep<n>.json`, `raw-prime-…` | llama-bench JSON and stderr tail per run |
| `telemetry-<model>-rep<n>.csv`, `telemetry-prime-…` | the 1 s nvidia-smi samples per run |
