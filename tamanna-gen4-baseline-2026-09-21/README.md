# Tamanna Gen 4 baseline — the two canonical 3090 rows on the new platform, 2026-09-21

Phase 0 of the PCIe Gen 4 vs Gen 3 test. RUN AND COMPLETE, 2026-09-21 21:30 to 21:45 PDT.
Results record; facts as measured. The Gen 3 half has not run: it needs Mark at the BIOS.

**Pre-registered framing.** This is a platform change (Ryzen 7 5700X, DDR4-3200 [corrected 2026-10-05: runs at DDR4-2133, memory profile not active], PCIe 4.0,
open frame) and not a build change. Every delta below is reported as "Tamanna vs Miu". Nothing
is attributed to the bus until the Gen 3 half runs on the same box tomorrow.

**Correction, 2026-10-05:** this record said Tamanna has DDR4-3200. Tamanna runs at DDR4-2133 (memory profile not active; a 2026-10-05 attempt to enable it failed training). Resident-model results are unaffected. The sticks are 2 × 16 GB G.Skill F4-3200C16-16GVK (dual rank) in 2 of 4 slots; dmidecode reads Configured Memory Speed 2133 MT/s. Every Tamanna record from 2026-09-21 on was made at DDR4-2133. The harness docstrings in this directory keep their original pre-registered wording unchanged.

## Inventory (step 1)

| | Tamanna | Miu (for reference) |
|---|---|---|
| GPU | RTX 3090, bus 06:00.0, 24576 MiB, driver 580.178.04, CUDA 13.0 runtime | RTX 3090, driver 580.178.04 |
| PCIe | gen max 4 (host and GPU), x16; idles at gen 1–2, **gen 4 x16 in 100% of under-load samples** | gen max 3, x16 |
| CPU | AMD Ryzen 7 5700X, 8c/16t, governor `powersave` (amd-pstate) | Intel i7-8086K, 6c/12t, governor `powersave` |
| RAM | 31 GiB total, 30 available at start, 7 GiB swap | 62 GiB |
| RAM speed | **not readable without root** (`/sys/firmware/dmi` is 0400 root, no sudo). ~~DDR4-3200 per Mark, unverified from the OS~~ **DDR4-2133** (memory profile not active; dmidecode 2026-10-05) | DDR4-2667 |
| Disk | 512 GB Micron 2450 NVMe (MTFDKBA512TFH), 419 GB free before the copy, 375 GB after | |
| OS / kernel | Ubuntu 26.04.1, 7.0.0-31-generic | Ubuntu 24.04, 6.8.0-139-generic |
| Display | headless: no Xorg / Wayland / display-manager process, card at 1 MiB and 0% before the first load | |
| nvcc | 12.4.131 (`nvidia-cuda-toolkit` package, `/usr/bin/nvcc`). **Not too old for the driver**: a 580 driver runs any 12.x toolkit. It is too *new* for the default gcc 15.2 (host_config.h caps at gcc 13), so the build uses gcc-13, which is also installed | 12.8 at `/usr/local/cuda-12.8`, host gcc 13.3 |
| Compilers | gcc/g++ 15.2 default, gcc/g++ 13 present, cmake 4.2.3, git 2.53, no ccache | |
| Power limit | 420 W current / 450 W max | |
| LAN | enp4s0 1000 Mb/s to Miu's eno1 (192.168.x.x); copy ran at 110 MB/s | |

## Build (step 2)

| | |
|---|---|
| Source | `git clone --depth 1 --branch v0.4.0 https://github.com/ggml-org/llama.cpp ~/llama-v0.4.0` |
| Commit | `5266f24da75dc449bd56cbed7addb9c8e4a6a73e` (tag v0.4.0 = b10809), same commit as Miu's `~/llama-v0.4.0` |
| Configure | `cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=86 -DGGML_NATIVE=OFF -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF -DCMAKE_C_COMPILER=gcc-13 -DCMAKE_CXX_COMPILER=g++-13 -DCMAKE_CUDA_HOST_COMPILER=g++-13` |
| Build | `cmake --build build --config Release -j 16`, 21:21:45 to 21:26:39, no errors |
| Resulting cache | `build-flags.txt`: GGML_CUDA ON, arch 86, GGML_NATIVE OFF, GGML_CUDA_FA ON, GGML_CUDA_GRAPHS ON, FORCE_MMQ/FORCE_CUBLAS OFF, AVX2 ON, AVX512 OFF, OPENMP ON, compression mode `size` — identical to Miu's `CMakeCache.txt` on every GGML/LLAMA option |
| Differs from Miu | CUDA toolkit **12.4 vs 12.8** (the only toolkit on Tamanna; no sudo to add another). Host compiler is gcc-13 on both. llama-bench reports `build_commit 5266f24`, `build_number 1` on both (shallow clone) |

The nvcc/gcc pairing was smoke-tested before the build: a trivial sm_86 kernel compiled with
`-ccbin g++-13` and ran. The build log is `build.log`.

## Models (step 3)

Copied over the wired link from Miu's `~/bench-models/` (the staged NVMe copies the 08-28 and
09-07 runs used; `~/LLM_repo` does not exist on Miu and `/mnt/sdb` is empty). rsync, 44.0 GB,
6 min 22 s, 110 MB/s. Hashed on Tamanna after the copy, 1 min 44 s, CPU-bound:

| Model | file | sha256 on Tamanna | matches |
|---|---|---|---|
| Ornith-1.5-35B-A3B Q4_K_M (bartowski) | `~/bench-models/Ornith-1.5-35B-A3B-Q4_K_M.gguf`, 21,864,081,056 B | `12d8d5c01bae7f23ea4822b2f96ba069d531f827d02a57c31002f2f95e72614a` | bartowski LFS oid, as recorded 08-28 |
| Qwen3.6-35B-A3B UD-Q4_K_M (Unsloth) | `~/bench-models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf`, 22,134,528,992 B | `ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61` | Unsloth LFS oid, as recorded 08-28 |

## Protocol (step 4)

| | |
|---|---|
| Harness | `llama-bench -ngl 99 -fa 1 -p 512 -n 128 -d 0,4096,8192 -r 5` — byte-identical to the published rows, the 08-28 A-B-B-A and the 09-07 build A/B. `-o json` for capture, as 09-07 |
| Reps | 3 per model, models alternating within each rep, starting model flipped on rep 2 (the 09-07 pattern): Ornith→Qwen, Qwen→Ornith, Ornith→Qwen |
| Telemetry | `nvidia-smi --query-gpu=… -lms 1000` running from before launch to after exit for every run: PCIe current generation (host and GPU view), link width, temperature, SM clock, memory clock, power draw, utilisation, memory used, active clock-event reasons. "Under load" below means samples with utilisation ≥ 50% |
| Threads | llama-bench default: 8 on Tamanna (8 physical cores), 6 on Miu. Not pinned, because the harness string is the row's identity |
| Not done | the 08-28 page-cache eviction bracket (needs root, none on Tamanna; 09-07 skipped it too). The digests were verified once, after the copy, not per slot |
| Block 1 | the pre-registered run, 21:30:21 to 21:33:14 |
| Block 2 | replication, same design, 21:34:08 to 21:37:06, added after block 1 showed one low prefill rep (the 09-07 precedent). `block2/` |
| Block 3 | **diagnostic, outside the pre-registration**: same design, but every measured run is preceded by a discarded priming run of the identical command, so the measured run always loads warm. 21:38:31 onward. `block3/` |

Runner is `gen4_baseline.py` (block 2 differs only in its output directory; block 3 adds the
priming run). `compare.py` builds `comparison.md` / `comparison.json` from the result files and
the Miu records.

## Result, block 1 (step 5) — the pre-registered run

Mean of 3 reps of llama-bench's own 5-repeat average; brackets are min..max over the 3 reps.
Delta is Tamanna relative to the Miu column. Miu columns are the 09-07 build A/B (`miu-build-ab-2026-09-07`,
block 1, n=3, warm cache, no root) and the 08-28 published A-B-B-A (`miu-ornith-abba-2026-08-28`,
b10088, root bracket). All Tamanna runs are v0.4.0.

| model | metric | Tamanna v0.4.0 (n=3) | Miu v0.4.0 09-07 (n=3) | Δ vs Miu v0.4.0 | Miu b10088 09-07 (n=3) | Δ vs Miu b10088 | Miu b10088 08-28 published | Δ vs 08-28 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Ornith 1.5-35B-A3B | tg128 d=0 | 177.32 [175.24..179.07] | 171.23 [169.42..172.44] | +3.56% | 167.68 [164.59..169.53] | +5.75% | 172.44 | +2.83% |
|  | tg128 d=4096 | 174.78 [173.49..176.14] | 167.90 [162.85..170.72] | +4.10% | 165.44 [162.78..168.73] | +5.65% | 170.69 | +2.40% |
|  | tg128 d=8192 | 171.23 [169.91..172.34] | 165.95 [163.29..167.35] | +3.18% | 163.71 [159.96..165.61] | +4.60% | 166.59 | +2.79% |
|  | pp512 d=0 | 3,419.3 [2,888.4..3,717.4] | 3,543.6 [3,511.9..3,566.0] | -3.51% | 3,464.6 [3,348.6..3,531.7] | -1.31% | 3,602.9 | -5.10% |
|  | pp512 d=4096 | 3,264.6 [2,825.7..3,511.5] | 3,333.9 [3,242.0..3,380.5] | -2.08% | 3,257.3 [3,206.5..3,320.2] | +0.22% | 3,387.4 | -3.63% |
|  | pp512 d=8192 | 3,183.2 [2,830.0..3,373.7] | 3,219.8 [3,126.6..3,271.3] | -1.14% | 3,157.0 [3,094.5..3,197.4] | +0.83% | 3,263.3 | -2.46% |
| Qwen3.6-35B-A3B | tg128 d=0 | 162.73 [162.31..162.98] | 154.11 [145.82..158.55] | +5.59% | 156.54 [156.25..157.02] | +3.95% | 158.18 | +2.87% |
|  | tg128 d=4096 | 160.49 [160.33..160.57] | 152.79 [144.79..156.86] | +5.04% | 155.77 [155.47..156.19] | +3.03% | 157.18 | +2.10% |
|  | tg128 d=8192 | 157.77 [157.74..157.80] | 148.52 [142.15..154.15] | +6.23% | 152.52 [152.35..152.72] | +3.44% | 153.47 | +2.80% |
|  | pp512 d=0 | 3,707.1 [3,667.0..3,771.0] | 3,638.2 [3,572.3..3,675.0] | +1.89% | 3,618.5 [3,606.6..3,639.7] | +2.45% | 3,694.2 | +0.35% |
|  | pp512 d=4096 | 3,574.8 [3,546.1..3,589.6] | 3,432.6 [3,287.9..3,516.4] | +4.14% | 3,440.2 [3,434.5..3,445.6] | +3.92% | 3,493.1 | +2.34% |
|  | pp512 d=8192 | 3,459.1 [3,444.0..3,470.5] | 3,210.7 [3,106.9..3,364.0] | +7.74% | 3,311.9 [3,304.1..3,316.1] | +4.45% | 3,362.5 | +2.87% |

Qwen has a pooled Miu v0.4.0 figure (09-07 blocks 1+2, n=6), which is the better reference for that row:

| metric | Tamanna | Miu v0.4.0 pooled n=6 | Δ |
|---|---:|---:|---:|
| tg128 d=0 | 162.73 | 156.31 [145.82..158.63] | +4.10% |
| tg128 d=4096 | 160.49 | 154.78 [144.79..157.59] | +3.69% |
| tg128 d=8192 | 157.77 | 151.25 [142.15..154.24] | +4.31% |
| pp512 d=0 | 3,707.1 | 3,661.3 [3,572.3..3,696.5] | +1.25% |
| pp512 d=4096 | 3,574.8 | 3,476.3 [3,287.9..3,523.5] | +2.83% |
| pp512 d=8192 | 3,459.1 | 3,293.7 [3,106.9..3,382.2] | +5.02% |

**Decode (tg128), all three depths, both models: Tamanna is 3.2 to 6.2% above Miu v0.4.0 09-07
(3.4 to 4.3% against the pooled Qwen figure) and 2.1 to 2.9% above the 08-28 published rows.**
The decode repeats are tight: Qwen's three reps span 0.06 to 0.67 tok/s per cell, Ornith's 2.4 to
3.8 tok/s. That is a "Tamanna vs Miu" number. Nothing here says which part of the platform it is.

**Prefill (pp512) in block 1 is not a clean number.** Ornith rep 2 (the run after the model swap)
was low on all three depths at once: 2,888 / 2,826 / 2,830 against 3,717 / 3,511 / 3,374 and
3,652 / 3,457 / 3,346 in reps 1 and 3, with all five in-run samples inside the low band. Its
decode was normal (175.24 / 173.49 / 169.91). Per the pre-registration the cell is recorded as it
landed, which is why the Ornith prefill means sit below Miu with a 830 tok/s bracket. What that
rep is, is the subject of blocks 2 and 3.

### Per-rep telemetry, block 1

Samples with GPU utilisation ≥ 50%. `0x4` is SW power cap: the card sits on its 420 W limit
during prefill on every run, with the SM clock at 1,920–1,935 MHz median and never below
1,830 MHz. Memory clock is 9,501 MHz in every under-load sample. PCIe is gen 4 x16 in 100% of
under-load samples in all 18 runs of the night (it idles at gen 1 or 2 between runs). Open frame:
the card started the night at 38 °C, the first run peaked at 62 °C, and every later run started at
55–61 °C and peaked at 67–69 °C.

| rep | model | start → max temp | SM clock median (min..max) | mem clock median | power mean (max) | PCIe gen under load | clock-event reasons | VRAM peak | run time |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Ornith 1.5-35B-A3B | 38 → 62 °C | 1935 (1860..1965) MHz | 9501 MHz | 352 W (418) | gen 4: 100% x[16] | none / SW power cap | 21,184 MiB | 26 s |
| 1 | Qwen3.6-35B-A3B | 55 → 69 °C | 1920 (1845..1950) MHz | 9501 MHz | 353 W (419) | gen 4: 100% x[16] | none / SW power cap | 21,654 MiB | 28 s |
| 2 | Qwen3.6-35B-A3B | 60 → 68 °C | 1920 (1845..1935) MHz | 9501 MHz | 355 W (418) | gen 4: 100% x[16] | none / SW power cap | 21,654 MiB | 23 s |
| 2 | Ornith 1.5-35B-A3B | 59 → 67 °C | 1920 (1845..1935) MHz | 9501 MHz | 381 W (417) | gen 4: 100% x[16] | none / SW power cap | 21,184 MiB | 28 s |
| 3 | Ornith 1.5-35B-A3B | 58 → 68 °C | 1920 (1830..1935) MHz | 9501 MHz | 366 W (418) | gen 4: 100% x[16] | none / SW power cap | 21,184 MiB | 22 s |
| 3 | Qwen3.6-35B-A3B | 59 → 67 °C | 1920 (1830..1950) MHz | 9501 MHz | 366 W (418) | gen 4: 100% x[16] | none / SW power cap | 21,654 MiB | 28 s |

## Block 2 — replication, and the pooled figure

Same design, run immediately after block 1. Decode replicated to within 0.6% on every cell.
Prefill did not: three more low cells, this time confined to d=0 (the first measurement
llama-bench makes after the load): Qwen rep 1 (2,697), Ornith rep 2 (2,979), Qwen rep 3 (2,684).
All three were runs that followed a model swap. Their d=0 samples ramp upward through the five
repeats (e.g. 2190 → 2585 → 2745 → 2909 → 3058) instead of scattering.

| model | metric | block 1 (n=3) | block 2 (n=3) | Δ block 2 vs 1 | Tamanna pooled n=6 | Miu v0.4.0 09-07 (Qwen pooled n=6) | Δ pooled vs Miu v0.4.0 | Miu b10088 08-28 | Δ pooled vs 08-28 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Ornith 1.5-35B-A3B | tg128 d=0 | 177.32 [175.24..179.07] | 177.07 [175.87..177.69] | -0.14% | 177.20 [175.24..179.07] | 171.23 | +3.49% | 172.44 | +2.76% |
|  | tg128 d=4096 | 174.78 [173.49..176.14] | 174.83 [174.58..175.23] | +0.02% | 174.81 [173.49..176.14] | 167.90 | +4.11% | 170.69 | +2.41% |
|  | tg128 d=8192 | 171.23 [169.91..172.34] | 171.43 [171.41..171.46] | +0.11% | 171.33 [169.91..172.34] | 165.95 | +3.24% | 166.59 | +2.85% |
|  | pp512 d=0 | 3,419.3 [2,888.4..3,717.4] | 3,419.1 [2,979.3..3,662.5] | -0.01% | 3,419.2 [2,888.4..3,717.4] | 3,543.6 | -3.51% | 3,602.9 | -5.10% |
|  | pp512 d=4096 | 3,264.6 [2,825.7..3,511.5] | 3,431.0 [3,371.1..3,464.4] | +5.10% | 3,347.8 [2,825.7..3,511.5] | 3,333.9 | +0.42% | 3,387.4 | -1.17% |
|  | pp512 d=8192 | 3,183.2 [2,830.0..3,373.7] | 3,319.0 [3,290.4..3,340.3] | +4.27% | 3,251.1 [2,830.0..3,373.7] | 3,219.8 | +0.97% | 3,263.3 | -0.38% |
| Qwen3.6-35B-A3B | tg128 d=0 | 162.73 [162.31..162.98] | 161.95 [161.29..163.05] | -0.47% | 162.34 [161.29..163.05] | 156.31 | +3.86% | 158.18 | +2.63% |
|  | tg128 d=4096 | 160.49 [160.33..160.57] | 159.52 [159.07..160.39] | -0.60% | 160.01 [159.07..160.57] | 154.78 | +3.38% | 157.18 | +1.80% |
|  | tg128 d=8192 | 157.77 [157.74..157.80] | 157.09 [156.51..157.79] | -0.43% | 157.43 [156.51..157.80] | 151.25 | +4.08% | 153.47 | +2.58% |
|  | pp512 d=0 | 3,707.1 [3,667.0..3,771.0] | 3,050.5 [2,684.0..3,770.3] | -17.71% | 3,378.8 [2,684.0..3,771.0] | 3,661.3 | -7.72% | 3,694.2 | -8.54% |
|  | pp512 d=4096 | 3,574.8 [3,546.1..3,589.6] | 3,459.4 [3,377.6..3,588.9] | -3.23% | 3,517.1 [3,377.6..3,589.6] | 3,476.3 | +1.17% | 3,493.1 | +0.69% |
|  | pp512 d=8192 | 3,459.1 [3,444.0..3,470.5] | 3,400.7 [3,357.5..3,467.3] | -1.69% | 3,429.9 [3,357.5..3,470.5] | 3,293.7 | +4.14% | 3,362.5 | +2.01% |

## Block 3 — what the low prefill runs are (diagnostic, outside the pre-registration)

Tamanna has 31 GiB of RAM and the two models are 22 GB each, so alternating them evicts each
other from the page cache: every run after a swap loads cold from the NVMe (about 10 s at 0%
GPU utilisation before the first test, against 3–4 s warm), and the kernel is still reclaiming the
previous model's pages when the first pp512 test starts. Miu has 62 GiB and both models stayed
warm through the 09-07 run, which its README states.

Block 3 puts a discarded priming run of the identical command in front of every measured run.
Rep 2's first prime and rep 3's first prime are the same model as the run before them, so only
four primes are true cold loads (the ones with a 10 s load phase).

| rep | model | run | load-phase s (util<50 before first ≥50) | pp512 d=0 samples | pp512 d=0 | pp512 d=4096 | pp512 d=8192 | tg128 d=0 | power mean |
|---|---|---|---:|---|---:|---:|---:|---:|---:|
| 1 | Ornith 1.5-35B-A3B | prime (cold) | 10 | 2695 2899 2913 2936 3001 | 2,889 | 2,807 | 2,821 | 175.16 | 368 W |
| 1 | Ornith 1.5-35B-A3B | measured (warm) | 6 | 3388 3734 3719 3724 3696 | 3,652 | 3,457 | 3,339 | 177.67 | 393 W |
| 1 | Qwen3.6-35B-A3B | prime (cold) | 10 | 3405 3860 3882 3850 3803 | 3,760 | 3,558 | 3,459 | 162.79 | 367 W |
| 1 | Qwen3.6-35B-A3B | measured (warm) | 4 | 3490 3840 3875 3837 3811 | 3,771 | 3,594 | 3,464 | 162.96 | 360 W |
| 2 | Qwen3.6-35B-A3B | prime (cold) | 3 | 3520 3830 3867 3825 3803 | 3,769 | 3,578 | 3,456 | 163.00 | 359 W |
| 2 | Qwen3.6-35B-A3B | measured (warm) | 3 | 3480 3830 3860 3831 3802 | 3,761 | 3,581 | 3,455 | 162.83 | 359 W |
| 2 | Ornith 1.5-35B-A3B | prime (cold) | 10 | 3329 3744 3609 3734 3602 | 3,604 | 3,441 | 3,334 | 177.45 | 373 W |
| 2 | Ornith 1.5-35B-A3B | measured (warm) | 4 | 3399 3734 3717 3723 3696 | 3,654 | 3,454 | 3,342 | 177.68 | 370 W |
| 3 | Ornith 1.5-35B-A3B | prime (cold) | 3 | 3406 3735 3713 3729 3696 | 3,656 | 3,452 | 3,337 | 177.56 | 359 W |
| 3 | Ornith 1.5-35B-A3B | measured (warm) | 3 | 3396 3718 3721 3730 3700 | 3,653 | 3,451 | 3,336 | 177.61 | 369 W |
| 3 | Qwen3.6-35B-A3B | prime (cold) | 10 | 2200 2587 2731 2926 3053 | 2,699 | 3,380 | 3,371 | 161.29 | 366 W |
| 3 | Qwen3.6-35B-A3B | measured (warm) | 4 | 3509 3848 3870 3834 3796 | 3,772 | 3,586 | 3,456 | 163.02 | 359 W |

Two of the four true cold loads were low (Ornith rep 1: whole run, all depths, like block 1's
Ornith rep 2; Qwen rep 3: d=0 only, ramping, like block 2's). None of the twelve warm runs across
the night was. Across all three blocks: 12 cold-load runs (load phase ≥ 8 s at 0% GPU), 6 low; 12 warm runs (3–6 s), 0 low. Low = pp512 d=0 more than 5% under the warm figure.

The six warm measured runs are the tightest set of the night, prefill spread ≤ 13 tok/s per
cell, decode ≤ 0.5 tok/s:

| model | metric | block 3 warm (n=3) | block 1 (n=3) | Miu v0.4.0 09-07 (Qwen pooled n=6) | Δ block 3 vs Miu v0.4.0 | Miu b10088 08-28 | Δ block 3 vs 08-28 |
|---|---|---:|---:|---:|---:|---:|---:|
| Ornith 1.5-35B-A3B | tg128 d=0 | 177.65 [177.61..177.68] | 177.32 [175.24..179.07] | 171.23 | +3.75% | 172.44 | +3.02% |
|  | tg128 d=4096 | 174.71 [174.63..174.81] | 174.78 [173.49..176.14] | 167.90 | +4.06% | 170.69 | +2.36% |
|  | tg128 d=8192 | 171.47 [171.36..171.59] | 171.23 [169.91..172.34] | 165.95 | +3.32% | 166.59 | +2.93% |
|  | pp512 d=0 | 3,652.9 [3,651.8..3,653.8] | 3,419.3 [2,888.4..3,717.4] | 3,543.6 | +3.08% | 3,602.9 | +1.39% |
|  | pp512 d=4096 | 3,454.1 [3,450.7..3,457.2] | 3,264.6 [2,825.7..3,511.5] | 3,333.9 | +3.60% | 3,387.4 | +1.97% |
|  | pp512 d=8192 | 3,339.1 [3,336.1..3,342.3] | 3,183.2 [2,830.0..3,373.7] | 3,219.8 | +3.71% | 3,263.3 | +2.32% |
| Qwen3.6-35B-A3B | tg128 d=0 | 162.93 [162.83..163.02] | 162.73 [162.31..162.98] | 156.31 | +4.24% | 158.18 | +3.01% |
|  | tg128 d=4096 | 160.68 [160.49..160.99] | 160.49 [160.33..160.57] | 154.78 | +3.81% | 157.18 | +2.23% |
|  | tg128 d=8192 | 157.72 [157.71..157.73] | 157.77 [157.74..157.80] | 151.25 | +4.27% | 153.47 | +2.77% |
|  | pp512 d=0 | 3,767.7 [3,760.8..3,771.6] | 3,707.1 [3,667.0..3,771.0] | 3,661.3 | +2.91% | 3,694.2 | +1.99% |
|  | pp512 d=4096 | 3,587.1 [3,581.0..3,594.0] | 3,574.8 [3,546.1..3,589.6] | 3,476.3 | +3.19% | 3,493.1 | +2.69% |
|  | pp512 d=8192 | 3,458.2 [3,455.0..3,463.5] | 3,459.1 [3,444.0..3,470.5] | 3,293.7 | +5.00% | 3,362.5 | +2.85% |

**On warm cache, Tamanna is 2.9 to 5.0% above Miu v0.4.0 on prefill and 3.3 to 4.3% on decode,
every cell, both models; 1.4 to 3.0% above the 08-28 published rows.** The block 1 Ornith prefill
deficit is the cold-load state, not the platform.

## What this means for the Gen 3 half

- **Use warm runs for the Gen 3 vs Gen 4 prefill comparison.** Either prime after every swap
  (block 3's design, harness string unchanged, measured runs warm) or group the reps per model.
  Decode is unaffected either way. Comparing cold runs to cold runs would add a ±25% d=0
  prefill coin-flip that has nothing to do with the bus.
- The Gen 4 reference numbers for tomorrow are the **block 3 warm** rows above, with block 1
  standing as the pre-registered record.
- The cold-load state is a **Tamanna property** (31 GiB against 44 GB of models). It is not on
  Miu and is not in the published rows. It would go away with root (`drop_caches` before each
  run makes every run identically cold, which is what the 08-28 bracket did) or with more RAM.

## What differs from Miu besides the pre-registered platform change

| | Tamanna | Miu 09-07 | note |
|---|---|---|---|
| CUDA toolkit | 12.4 | 12.8 | only toolkit on Tamanna, no sudo. Same commit, same host compiler (gcc-13), same cmake options |
| llama-bench threads | 8 | 6 | default = physical cores; not pinned |
| RAM / page cache | 31 GiB, models evict each other | 62 GiB, both warm | the cold-load effect above |
| Kernel / distro | 7.0.0-31, Ubuntu 26.04 | 6.8.0-139, Ubuntu 24.04 | |
| Concurrent load | nothing else running; headless | Brave closed; an 82 GB download was running on 09-07 | |
| RAM speed | ~~DDR4-3200 per Mark, not verified from the OS~~ **DDR4-2133** (memory profile not active; dmidecode 2026-10-05) | DDR4-2667 | the cross-rig DDR4 confound note applies |
| Governor | `powersave` (amd-pstate) | `powersave` (intel_pstate) | symmetric in name; not in behaviour necessarily |

## Files

| path | content |
|---|---|
| `gen4_baseline.py` | the runner (block 1); block 2 is the same file with its output directory changed (`block2/gen4_baseline_block2.py`); block 3 adds the priming run (`block3/gen4_baseline_block3.py`) |
| `compare.py`, `comparison.md`, `comparison.json` | the tables above, computed from the result files and the Miu records |
| `run.log`, `results.json`, `summary.json` | block 1: orchestrator log, all runs with telemetry summaries, the 12-cell summary |
| `raw-<model>-rep<n>.json` | llama-bench JSON output and stderr tail per run |
| `telemetry-<model>-rep<n>.csv` | the 1 s nvidia-smi samples per run (about 25–31 rows each; the sampler drops the odd second under load) |
| `block2/`, `block3/` | the same set for blocks 2 and 3; block 3 also has `raw-prime-*` and `telemetry-prime-*` |
| `build.log`, `build-flags.txt` | the clone-and-build log and the resulting `CMakeCache.txt` options |
| `harness.out` | stdout of the runner, same lines as `run.log` |
