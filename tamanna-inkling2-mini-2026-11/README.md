# Tamanna (RTX 3090 24 GB): Inkling 2 Mini, lock amendment A1 (bandwidth test), 2026-11-25

**Pre-registration.** The lock is `docs/candidates/inkling-2-mini-3060-2026-11.md` with A1 appended, LOCKED
2026-11-25 in `9c2a7dee`.
- sha256 `312c4fdb4b4da9d5d8d401ba48250807e3f8279cabdf6352b8aea1ab7afd86c4`.
- Mirror `d946fb3`; the public copy hashed equal before the first Tamanna step.
- The bands were recomputed from the day's bandwidth and committed before any measured request: `bands-A1.md`,
  commit `c4b35824`.

**The Rushuna half.** It is `../rushuna-inkling2-mini-2026-11/`. That record's discussion is where the hypothesis
under test comes from: with every expert in system RAM, Inkling decode is bound by RAM read bandwidth.

**Clock.** The arm logs (`rec/run_everything.out`, `rec/arms/run.log`) show **Tamanna's local time, PST**. The
machine state header shows UTC.
- Gates: after the 12:33 PST bandwidth run, finished before 13:02 PST.
- Arms: 13:02:30 to 13:49:48 PST, which is 21:02 to 21:49 UTC.

**Arms run: the main arms only.** That means U and L at 8K, 32K and 256K, then S10d at 8K and 16K.
**The optional arm T-2133 was not run on 11-25.** Go condition 6 was not met then. It ran on 2026-11-27: see the addendum of that date. A1-P8 and A1-P9 both fail, above the band.

## Setup

- **Rig:** Tamanna. RTX 3090 24 GB on PCIe 4.0 x16 (gen 4 x16 read during every prefill). The CPU is a Ryzen 7 5700X
  (8 cores / 16 threads, 32 MiB L3). The board is a B550 Phantom Gaming 4/ac on BIOS P4.00. RAM is 64 GB DDR4-3000 at
  1.35 V (4 × 16).
- **Software:** driver 580.178.04, kernel 7.0.0-43, nvidia-persistenced active.
- **Swap:** an 8 GiB swap file was on. No cell had a swap-out.
- **Bandwidth (A1.4)** was measured on the day, before the gates: **42.30 GB/s read** with `stream_read.c` at 4
  threads, median of 42.17, 42.45 and 42.30. The STREAM triad was 26.69 GB/s. Full details are in `bands-A1.md` and
  `bandwidth/`.
- **Files:** working copies under `~/inkling2-2026-11/model/`, rsynced from the Miu LLM_repo canonical copies. Their
  hashes were checked in `rec/machine-state.txt` against lock I3:
  - UD-Q4_K_M: `78fcedcf…`
  - DSpark: `3da00cf7…` (copied but not used: A1 has no DSpark arms)
  - SQ-10: `ac4d452a…`
- **Builds (A1.2): the Rushuna binaries, copied by sha256.**
  - **L**, mainline `33aeb17f`: `llama-server` `bfbbfe4a…`, `llama-perplexity` `390cc60c…`, `llama-tokenize`
    `48eb8517…`, with the shared libraries from Rushuna's `build/bin/`.
  - **CUDA libraries:** the 12.8 runtime libraries `libcudart`, `libcublas` and `libcublasLt`, copied from Rushuna's
    `~/cuda-12.8/lib64` into `~/inkling2-2026-11/cuda12-lib`. Their hashes are in `rec/machine-state.txt`.
  - **U:** the asset `c9745b61…`, extracted fresh: `llama-server` `2132fdf5…`, `llama-perplexity` `f3362a14…`.
  - **S:** the pinned v0.2.21 installer (`install.sh` `d67f9fb2…`, the same as on Rushuna), run into an isolated HOME.
    It installed **terminal 0.2.21.1 (build 0.1.68)**. The first launch, a setup step not used for any figure, fetched
    **engine 0.1.67, `a0105917…`, identical to Rushuna's**. The setup log is `rec/strata-engine-check-setup.log`.
- **Flags, sampling and requests:** as lock I5 and A1.3.
  - Common flags: `-ngl 99 -np 1 -ctk q8_0 -ctv q8_0 -fa auto -t 4 --cache-ram 0 --fit off -lm mmap --jinja --port
    8081 -lv 4`, plus `-cmoe` and `-c`.
  - Sampling: temperature 1.0, top-p 1, top-k 0, min-p 0, seed 1234.
  - Prompts: the Rushuna prompt files, byte for byte.
- **Harness changes from the Rushuna record:** `diff -r` against `../rushuna-inkling2-mini-2026-11/harness/`.
  - `env.sh`: the header comment, and `LD_LIBRARY_PATH` pointed at `$W/cuda12-lib`.
  - `summarize.py`: the PCIe void rule reads `PCIE_GEN`, set to 4 on Tamanna (A1.5).
  - New scripts for the A1 arms and checks only: `machine_state_a1.sh`, `gates_a1.sh`, `run_a1.sh` and
    `run_everything_a1.sh`. `run_a1.sh` keeps the same `arm()` and `sarm()` functions. Its f16-KV fallback now
    triggers only on an error-level refusal line, which fixes Rushuna deviation 2; it never fired here.
  - `bench_inkling.py`, `memwatch.py`, `run_arm.sh`, `gate.sh` and `smoke.py` are unchanged.

## Gates (A1.5)

| gate | PPL | vs Rushuna CPU reference 5.8308 | result |
|---|---|---|---|
| CPU reference on Tamanna | 5.8243 | −0.11%, which is under 0.5%, so Rushuna's reference stands | – |
| U (`-ngl 99 -cmoe`, q8_0, `-fa auto`) | 5.8241 | −0.11% | pass (±2%) |
| L (same) | 5.8278 | −0.05% | pass |

**Load logs.**
- Flash attention was enabled in every llama.cpp arm.
- The CUDA0 model buffer was 1,266.34 MiB, the same as Rushuna.

CUDA0 compute buffers:

| build | 8K | 32K | 256K |
|---|---|---|---|
| U | 669.95 MiB | 693.95 MiB | 918.95 MiB |
| L | 7,567.85 MiB | 9,943.85 MiB | OOM on a 32,119.85 MiB request |

The U and L figures are identical to Rushuna's; that is the same binary.

## Results

Each cell is the median [min..max] of 3 requests, except 256K deep, which is ×1. Units are tok/s.
- **No cell was void.**
- No cell had a swap-out.
- Every prefill read gen 4 x16.
- The full table is in `rec/summary.txt`.

| arm | ctx | decode short | decode deep | prefill deep | VRAM peak |
|---|---|---|---|---|---|
| U | 8K | **16.40** [16.39..16.42] | 16.19 [16.15..16.23] | 237.9 | 2,584 MiB |
| U | 32K | 16.39 [16.33..16.41] | 15.90 [15.89..15.90] | 243.6 | 3,016 MiB |
| U | 256K | 16.35 [16.34..16.41] | 13.36 (×1, 235,931 tokens, TTFT 1,055 s) | 223.6 (×1) | 7,050 MiB |
| L | 8K | 15.30 [15.26..15.32] | 15.10 [15.08..15.12] | 295.3 | 9,494 MiB |
| L | 32K | 15.26 [15.25..15.32] | 14.74 [14.68..14.76] | 269.3 | 12,278 MiB |
| L | 256K | does not load: `allocating 32119.85 MiB on device 0: cudaMalloc failed: out of memory` | – | – | – |
| S10d | 8K | **103.0** [102.3..110.8], 36% of drafts accepted | 96.3 [90.5..96.3], 37% | 2,860 | 14,212 MiB |
| S10d | 16K | 98.1 [93.8..106.5], 34% | 85.0 [83.5..91.6], 36% | 2,701 | 14,500 MiB |

Short prefill (512 tokens) ran at about 183 tok/s on U and 229 on L.

**Strata's drafting probe chose "on" again.** On this card it measured 1.47x (code 1.94x, chat 1.11x), with plain
decoding at 84 tok/s. The runconfig is in `rec/strata-install-and-runconfig.txt`.

## Predictions (A1.6), scored with the bands from `bands-A1.md` (r = 42.30 / 26.94 = 1.5702)

| # | prediction | band | measured | verdict |
|---|---|---|---|---|
| **A1-P1** | U-8k short = 10.41 × r ±15% | [13.89..18.80] | **16.40** (16.35 predicted, +0.3%) | **inside** |
| A1-P2 | L-8k short = 9.92 × r | [13.24..17.91] | 15.30 (−1.8%) | **inside** |
| A1-P3 | U-32k short = 10.37 × r | [13.84..18.72] | 16.39 | **inside** |
| A1-P3 | U-256k short = 10.36 × r | [13.83..18.71] | 16.35 | **inside** |
| A1-P4 | U-256k short within ±10% of U-8k short | – | −0.3% | **holds** |
| A1-P5 | U loads at 8K, 32K and 256K; L loads at 8K and 32K and fails at 256K | – | as predicted | **inside** |
| A1-P6 | U-8k deep prefill above Rushuna's 154.4, ranges not overlapping | – | 237.9 [237.8..238.1] | **inside** |
| A1-P7 | S10d-8k short at 1.5-2.6x Rushuna's 39.9 | 60-104 | 103.0 (2.58x) | **inside**, at the top of the band |
| A1-P8 / P9 | T-2133 decode ratio = bandwidth ratio ±10% | – | not run (go condition 6) | **pending** |

**Tamanna/Rushuna decode ratios, beside r = 1.570** (reported as A1.6 requires):

| cell | Tamanna | Rushuna | ratio |
|---|---|---|---|
| U-8k short | 16.40 | 10.41 | **1.575** |
| U-32k short | 16.39 | 10.37 | 1.581 |
| U-256k short | 16.35 | 10.36 | 1.578 |
| L-8k short | 15.30 | 9.92 | 1.542 |

**Both explanations stay open.**
- **(a) Bandwidth:** the ratios sit within 0.7% of r on U.
- **(b) CPU, or CPU plus GPU:** the 5700X differs in cores, cache, memory controller and latency.

The lock (A1.6) is explicit that a ratio inside the band doesn't rule out (b). Only T-2133, which changes the RAM
clock with the same CPU, can separate the two. Cross-rig comparisons are directional, apart from the bandwidth
question itself.

## Discussion

**Observation.** Short-context decode moved by the bandwidth ratio almost exactly: 1.575-1.581 on U against r of
1.570. Routed-expert traffic at 16.40 tok/s, at 1.784 GB per token, is 29.3 GB/s. That is **69.2% of 42.30**, against
69% on Rushuna. The same share of measured read bandwidth on two different CPU and RAM platforms is what the
bandwidth-bound hypothesis predicts.

**It is still not attribution.**
- A faster CPU on a bandwidth-bound workload would also show near-r ratios if the CPU part scaled by coincidence.
- The 3090's faster GPU share would push the ratio above r. The near-exact match says that share is small at short
  context on both cards.
- T-2133 is the test that settles it.

**Deep context separates the GPU share.**
- At 236K fill, U decodes 13.36 on Tamanna against 7.32 on Rushuna, a ratio of 1.83, above r. Attention over a long
  KV runs on the GPU, so its share grows with depth, and the 3090 is faster there.
- At 32K deep the ratio is 1.61 (15.90 / 9.88), close to r.
- This is consistent with decode being RAM-bound at short context and increasingly GPU-bound at depth. It is
  directional only.

**Codacus's 18 tok/s (K5)** is within ±15% of Tamanna's 16.40 (−8.9%). His setup is unknown, so this says only that
his figure is plausible on a box with ~40+ GB/s of read bandwidth. It does not say what his box was.

**Strata on the 3090** decodes 103 tok/s with drafting at 8K short, 2.58x the 3060. That is close to the 2.6x
VRAM-bandwidth ratio, as expected for a pack held entirely in VRAM. Strata is 6.3x U's decode on this card, against
3.8x on Rushuna.

## Limits (A1.9)

- One quant and one day's builds.
- The main arms change RAM, CPU and GPU together.
- 256K deep is one request per arm.
- Strata's drafting probe decided on its own, and chose on again.
- The NVMe sequential read in the machine state (1.4 GB/s with `dd`) is context only. Decode NVMe reads were under
  the 1 GiB rule in every cell.

## Deviations

None from A1 in the arms run. To record:
1. **The CUDA 12.8 runtime libraries were copied from Rushuna**, so the copied L and U binaries load on Tamanna,
   which has no CUDA 12.8 toolkit. The binaries are unchanged by sha256, and the libraries' hashes are in
   `rec/machine-state.txt`.
2. **The Unsloth asset unpacks into `./`, not into `app/`.** The first extraction landed in `uns/`, and those files
   were removed. It was then re-extracted into `uns/app/`, and the hashes matched.
3. **A1 has no smoke test**, as A1.3 states, and no Qwen arm.

## Addendum, 2026-11-26: pre-T-2133 bandwidth reading at DDR4-3000 (not a scored cell)

T-2133 was scheduled for 2026-11-26 and is **on hold**. Mark paused it before any BIOS change: Tamanna was not
rebooted, its RAM stayed at DDR4-3000 at 1.35 V, and no T-2133 request was run.

Before the planned reboot, `stream_read` was run once more at DDR4-3000. It was the same binary (source sha256
`09858c7f…`, binary `0ff077fb…`), with 4 threads and each run best of 8, at 2026-11-26 21:27 UTC on an idle card (1 MiB,
no compute process, load 0.00):

| | runs | median |
|---|---|---|
| Tamanna, read, 4 threads, DDR4-3000 (pre-T-2133) | 42.17, 42.21, 42.30 GB/s | **42.21 GB/s** |

- **Not a scored cell, and not an input to any band.** It is labelled context only: it shows the box's bandwidth at
  DDR4-3000 the day after A1.4 (42.30 GB/s), within 0.2%.
- When T-2133 does run, the lock's procedure (A1 T-2133 step 2 and A1.6) applies as written. BW(2133) and the
  restore reading are measured then, and the A1-P8/P9 bands are recomputed and committed before any measured 2133
  request.
- Raw output: `bandwidth/stream-read-tamanna-2026-11-26-pre3000.txt`.

## Post-results observation, 2026-11-27 (not a re-score)

The Inkling bandwidth model (expert bytes per token × tok/s ≈ 69% of `stream_read` bandwidth) over-predicts the
October Flash-Next record (`../tamanna-ram-speed-offload-2026-10-09/`, old UD-IQ3_XXS at `-ncmoe 29`): 50.9 tok/s
predicted against 32.57 measured, and +15% decode for +35% bandwidth. That is consistent with a fixed per-token
overhead the model leaves out. T-2133 is the test that bears on it. Nothing in this record is re-scored. The working
is in `docs/candidates/qwen3-8-flash-ram-offload-2026-11.md` section 4 (draft, parked).

## Addendum, 2026-11-27: optional arm T-2133 run (A1-P8 and A1-P9 scored)

**Go condition 6 was met:** Mark made both BIOS changes. The bands were committed before any 2133 request: `bands-T2133.md`, commit
`8c7911e7`. This addendum scores A1-P8 and A1-P9. The table row above that reads "pending" is superseded by this
section. Nothing else in the record is re-scored.

**Sequence (UTC, 2026-11-27).**
1. 21:54: Tamanna idle (card 7 MiB, no compute process, no transfers, load 0.00). Pre-reboot `stream_read` at
   DDR4-3000: 42.05, 42.21, 42.26, median 42.21 GB/s (context only).
2. Mark set DDR4-2133. `dmidecode` reads 4 × 16 GB at 2133 MT/s configured, 1.2 V (`t2133/dmidecode-2133.txt`).
   BIOS P4.00, persistence mode enabled after the reboot.
3. 22:09: **BW(2133) = 31.54 GB/s** (31.40, 31.54, 31.61). Same source (`09858c7f…`) and binary (`0ff077fb…`),
   4 threads, each run best of 8. Bands computed and committed (`8c7911e7`).
4. 22:10-22:14: U-8k short, then U-32k short. Each had a fresh server, a model pre-read, a cold request excluded,
   and 3 × 512 tokens. The server command is byte-identical to the main arm's `results-U-8k.json` and
   `results-U-32k.json` `cmd`. Run by `harness/run_t2133.sh`, which is `run_a1.sh`'s `arm()` with short cells only
   (A1.3 T-2133 step 3). On Tamanna the main `rec/arms` was moved aside during the run and put back unchanged
   afterwards, so the T-2133 logs did not append to it.
5. Mark restored DDR4-3000. `dmidecode` reads 3000 MT/s configured (`t2133/dmidecode-3000-restore.txt`).
   **Voltage: 1.35 V, as set.** Mark read it on the BIOS screen during an extra reboot at about 22:45. dmidecode's 1.2 V
   is the SPD value, as in the 10-09 record.
6. 22:25: **restore check: 42.08 GB/s** (42.18, 42.07, 42.08). That is ≥ 40.5, so Tamanna counts as **restored**.
7. After the voltage-check reboot:
   - 22:47, under a minute after boot at load 1.47: 41.23, 41.63, 41.38 GB/s (boot load, context only).
   - 22:49, at load 0.18: 41.77, 42.15, 42.17 GB/s, median **42.15 GB/s**.

   Tamanna is back at DDR4-3000 / 1.35 V and can be used by other sessions.

**Void rules (A1.5): no cell is void.**
- No swap-out (pswpout +0).
- Every prefill read gen 4 x16.
- prompt_n was 512-514, and cache_n was 0.
- NVMe reads during decode were 0.0 MiB.
- Every answer was non-empty and not looping.
- memwatch did not trip: min MemAvailable was 61,897 MiB.

### Results (tok/s, median [min..max] of 3)

| cell | decode at DDR4-3000 (main arm, 2026-11-25) | decode at DDR4-2133 (2026-11-27) | decode ratio | bandwidth ratio | band (±10%) | verdict |
|---|---|---|---|---|---|---|
| **A1-P8: U-8k short** | 16.40 [16.39..16.42] | **13.83** [13.83..13.83] | **0.843** | 0.746 | [0.671..0.820] | **fails, above the band** |
| **A1-P9: U-32k short** | 16.39 [16.33..16.41] | **13.82** [13.80..13.83] | **0.843** | 0.746 | [0.671..0.820] | **fails, above the band** |

- The ranges don't overlap. Short prefill fell from about 183 to 148 tok/s.
- **Robustness:** with today's pre-reboot 42.21 or the restore reading of 42.08 as BW(3000), the top of the band
  moves to 0.822 or 0.825. Both cells still fail.
- **Deviation (written into `bands-T2133.md` before the run):** A1 asks for the 3000 inputs "from the same day". The
  main arms ran on 11-25, and T-2133 was deferred to 11-27. The scored inputs are the ones the lock names. Bandwidth at
  3000 read 42.30, 42.21, 42.21 and 42.08 GB/s across the three days.

### What it says (A1.6, "How A1-P8 reads")

**The ratio is above the band, so part of decode is not bandwidth-bound.**
- Read bandwidth fell 25.4%; decode fell 15.7%.
- Equivalently, 2133 → 3000 is +34.1% bandwidth for +18.6% decode.
- This is with the CPU, GPU, binary, file, flags and prompts held fixed. Only the RAM clock changed, plus whatever
  timings the board chose with it, which aren't controlled (A1.9).

**Consequence for A1-P1, as the lock says:** the CPU explanation, (b), carries more weight.
- The Tamanna/Rushuna decode ratio of 1.575 against r = 1.570 was not pure bandwidth scaling. Within one box, decode
  doesn't scale with bandwidth one-for-one.
- The near-exact cross-rig match combined a bandwidth part with a part that differs between the rigs by CPU or GPU.
- The "69% of read bandwidth on both rigs" in the Discussion was a coincidence of that mix. It is not a constant.

**Fixed per-token overhead (unscored analysis, fixed in `bands-T2133.md` before the run).** Fit t = a + k / BW to the
two U-8k points:

| | Inkling U-8k short, `-cmoe` (this arm) | Flash-Next old UD-IQ3_XXS, `-ncmoe 29` (10-09 record) |
|---|---|---|
| decode 2133 → 3000 | 13.83 → 16.40 (+18.6%) | 28.40 → 32.57 (+14.7%) |
| bandwidth 2133 → 3000 | 31.54 → 42.30 (+34.1%) | 31.52 → 42.44 (+34.6%) |
| per-token time at 3000 | 60.98 ms | 30.70 ms |
| **fixed part a** | **27.8 ms (45.5%)** | 17.7 ms (57.6%) |
| bandwidth part at 3000 | 33.2 ms (k = 1.405 GB) | 13.0 ms (k = 0.552 GB) |

U-32k gives the same fit: a = 27.8 ms, 45.5%.

**So the fixed per-token overhead seen in the Flash-Next record shows up here too.** It is about 45% of an Inkling
token at DDR4-3000.

What a two-point fit can't tell:
- **What the fixed part is.** It could be CPU compute on the experts, memory latency, or the on-card share (the GPU
  plus launches). T-2133 holds all of those fixed, so it can't separate them.
- **Whether t = a + k / BW is the right shape at all.** Two points can't show it.

These are directional readings:
- **k = 1.405 GB is below the 1.784 GB of three-pass routed-expert bytes,** and above the 0.924 GB of one pass. The
  variable part streams less than every pass reading its experts afresh. One possible reason is passes re-picking
  experts already in cache. This was not tested.
- **Cross-rig (directional, DDR4 confound):** with Tamanna's a and k, Rushuna at 26.94 GB/s would decode 12.5 tok/s.
  It measured 10.41, which puts its fixed part near 44 ms, against Tamanna's 28. That fits a slower CPU, or a slower
  GPU share, on the 3060 box. Same caveats.

Raw files:
- `t2133/arms/`: results JSON, server logs, card CSVs, memwatch and `summary.txt` (`PCIE_GEN=4`).
- `t2133/run_t2133.out`.
- `t2133/dmidecode-*.txt`.
- `bandwidth/stream-read-tamanna-2026-11-27-{pre2133,2133,restore3000,post-voltage-check,post-voltage-check-settled}.txt`.

## Files

- `bands-A1.md`: the day's bandwidth and the recomputed bands, committed before the measured requests.
- `bandwidth/`: the raw `stream_read` and STREAM output, the 2026-11-26 pre-T-2133 reading (context only), and the
  2026-11-27 T-2133 readings.
- `bands-T2133.md`, `t2133/`, `harness/run_t2133.sh`: the T-2133 arm (2026-11-27).
- `rec/machine-state.txt`: hashes and state before arm U.
- `rec/gate/`, `rec/gates_a1.out`: the PPL gates.
- `rec/run_everything.out`, `rec/arms/`: per-arm results JSON, server and engine logs, card CSVs and memwatch.
- `rec/summary.txt`: `summarize.py` with `PCIE_GEN=4`.
- `rec/strata-engine-check-setup.log`, `rec/strata-install-and-runconfig.txt`: Strata setup and the installer hash.
- `harness/`: the A1 harness.
