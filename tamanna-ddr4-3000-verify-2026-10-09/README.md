# Tamanna at DDR4-3000, 64 GB: the gen 4 verify bench, 2026-10-09

The verify bench pre-registered in `../tamanna-docp-verify-2026-10-05/README.md` ("Method" and "Comparison,
decided now"), run now that the memory change took. That record's run was aborted on 10-05 (DOCP had not
trained) and never produced a figure. This is its first run.

## What changed since the reference (09-23)

| | 09-23 (reference, `../tamanna-gen4-verify-2026-09-23/`) | 10-09 (this run) |
|---|---|---|
| RAM | 2 × 16 GB F4-3200C16-16GVK, 31 GiB, **DDR4-2133**, 1.2 V | 4 × 16 GB F4-3200C16-16GVK, 62 GiB, **DDR4-3000, 1.35 V manual** |
| Read bandwidth (`stream_read.c`, 4 threads) | 32.36 GB/s (measured 10-05, same kernel) | 41.95 GB/s (10-09 12:42) |
| BIOS | P3.90 | P4.00 |
| memtest86+ | — | 1 full pass at DDR4-3000, 0 errors (Mark, 13:40) |
| Everything else | llama.cpp v0.4.0 `5266f24`, CUDA 12.4 / gcc-13 build, PCIe gen 4 x16, the same two files | same |

So this run changes RAM speed, RAM capacity and the BIOS at once. For fully resident models that should not
matter, which is what the bench checks.

## Method: byte-identical to 09-23

- `verify.py` is `../tamanna-docp-verify-2026-10-05/docp_verify.py` with only the output directory changed, and
  that file is `../tamanna-gen4-verify-2026-09-23/gen4_verify.py` with only the output directory changed (`diff`:
  one line each).
- `llama-bench -ngl 99 -fa 1 -p 512 -n 128 -d 0,4096,8192 -r 5`, Ornith-1.5-35B-A3B Q4_K_M and Qwen3.6-35B-A3B
  UD-Q4_K_M, Block 3 priming, 3 reps, models alternating.
- Both files re-hashed on Tamanna today, 2026-10-09, matching the 09-21 record:
  Ornith `12d8d5c01bae7f23ea4822b2f96ba069d531f827d02a57c31002f2f95e72614a`,
  Qwen3.6 `ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61`.
- **Expected, set on 10-05: every cell within 1% of 09-23.** If any cell moves more than 1%, it is reported and
  nothing is attributed until Mark decides.

## Conditions on the day

- The ISTA IQ3_XXS download (`~/bench-models/qwen3.8-flash-next-ista-iq3xxs/dl.sh`, 8 curl segments over Tamanna's
  WiFi) is **paused with SIGSTOP by PID for the whole measured run** and resumed after. The LAN copies (Flash-Next
  UD-IQ3_XXS and the Coder IQ1_M, for the next two benches) finish before the run starts.
- Before the run (14:16): `stream_read.c` (same source, md5 `331785328ca94900143b5c062c101bcd`, gcc-13 -O3 -fopenmp)
  read **42.44 GB/s** at 4 threads (repeats 42.07, 42.21), so the box came back from memtest at 3000. Uptime 29 min.
  All 8 download curls in state T (stopped) at 15.6 of 47.0 GB. The Rushuna → Miu-store copy of the Coder ran during
  the bench; it does not touch Tamanna.

## Result: PASS, every cell within 1% (run 14:16–14:21 PDT)

`python3 compare.py` (`compare.txt`): 09-23 is the reference, n = 3 each, mean [min..max] of llama-bench's 5-repeat
average.

| model | metric | 09-23 gen 4, DDR4-2133, 31 GiB (n=3) | 10-09 gen 4, DDR4-3000, 64 GB (n=3) | delta | within 1% |
|---|---|---:|---:|---:|---|
| Ornith 1.5-35B-A3B | tg128 d=0 | 177.44 [177.37..177.52] | 177.16 [176.95..177.39] | -0.16% | PASS |
|  | tg128 d=4096 | 174.48 [174.46..174.50] | 174.60 [174.41..174.79] | +0.07% | PASS |
|  | tg128 d=8192 | 171.35 [171.23..171.46] | 171.23 [170.79..171.61] | -0.07% | PASS |
|  | pp512 d=0 | 3,658.7 [3,656.9..3,662.1] | 3,652.7 [3,641.4..3,662.7] | -0.17% | PASS |
|  | pp512 d=4096 | 3,445.2 [3,436.7..3,452.3] | 3,448.3 [3,435.5..3,460.2] | +0.09% | PASS |
|  | pp512 d=8192 | 3,335.5 [3,324.3..3,342.2] | 3,335.8 [3,326.8..3,353.2] | +0.01% | PASS |
| Qwen3.6-35B-A3B | tg128 d=0 | 162.88 [162.83..162.96] | 162.76 [162.63..162.94] | -0.07% | PASS |
|  | tg128 d=4096 | 160.73 [160.55..161.08] | 160.86 [160.60..161.22] | +0.08% | PASS |
|  | tg128 d=8192 | 157.73 [157.66..157.78] | 157.79 [157.76..157.82] | +0.04% | PASS |
|  | pp512 d=0 | 3,745.8 [3,717.3..3,761.3] | 3,763.6 [3,751.8..3,773.8] | +0.48% | PASS |
|  | pp512 d=4096 | 3,584.5 [3,568.7..3,597.4] | 3,602.8 [3,594.9..3,608.3] | +0.51% | PASS |
|  | pp512 d=8192 | 3,451.6 [3,449.0..3,453.1] | 3,456.4 [3,453.0..3,461.5] | +0.14% | PASS |

worst |delta| = 0.51%  ->  PASS
PCIe gen under load across all 12 runs: [4]

**The correction line holds.** Resident-model results are unaffected by the RAM change: largest move 0.51% (Qwen3.6
pp512 d=4096), every decode cell within 0.16%. PCIe gen 4 under load on all 12 runs. Card 41 → 65 °C, power mean
~363 W, as on 09-23 (`run.log` has the per-run telemetry).

**The cold-load prefill dip is gone at 64 GB.** At 31 GiB, alternating the two 22 GB models cost 10–27% on d=0
prefill in 6 of 12 cold runs. Here every priming run (each one right after a model swap) is within 1.1% of the
measured run that follows it on pp512 d=0 (+1.1, 0.0, +0.2, +0.3, −0.2, −0.2%). Both files now stay in page cache
together. Priming stays in the method so later runs compare with earlier ones; it no longer changes the number.

## Files

`verify.py` (harness), `compare.py`, `compare.txt`, `run.log`, `harness.out`, `results.json`, `summary.json`,
`raw-*.json` and `telemetry-*.csv` per run (priming runs as `raw-prime-*` / `telemetry-prime-*`).
