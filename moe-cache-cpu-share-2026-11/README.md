# llama.cpp MoE cache CPU share (PR #30966): Qwen3.6-35B-A3B on Rushuna's RTX 3060, 2026-11-23 UTC

**Record for the pre-registration `docs/candidates/moe-cache-cpu-share-2026-11.md`** (lock commit c22ff41b, sha256
`f047318b9eceb00315e803e94189af1b68484293ab6b187ab0ddc2c07746f6a4`, public copy verified before the run), **with
Amendment A1** (commit 8ea4a796; amended file sha256
`ed172d567d0a17097b853e739a20a0d90fc72821273a2bedfad7001f3cf41e77`, public copy verified before arm (c) ran).

**How the run went.**
1. Arms (a24), (a27) and (b27) ran as locked, and the fit gate passed.
2. The tuner, given the (a24) command as locked, failed on its first server start (out of memory, see below). The run
   stopped there, and this record was committed as 67b4cb3f.
3. Mark then wrote **Amendment A1, after those three arms' results were known**. It changes only arm (c): the tuner
   runs on the (a27) command, and its `recommended:` line is taken verbatim.
4. The tuner ran on (a27), and arm (c) ran under the same harness, guard, A1 conditions and void rules.

**Every (c) figure in this record is the amended arm (A1, post-results).** It is not a pre-registered arm, and every
row and score that uses it says so.

## Results (decode = server `predicted_per_second`; cell = median of 3, min..max)

| arm | `-ncmoe` | cache | len | decode t/s | prompt t/s | prompt_n | cell peak MiB | void |
|---|---:|---|---:|---|---|---|---:|---|
| a24 | 24 | none | 512 | **37.53** (37.48..37.57) | 383.9 (383.0..384.7) | 511, 513, 512 | 10,389 | no |
| a24 | 24 | none | 4,096 | **37.26** (37.19..37.28) | 399.0 (398.0..399.3) | 4097, 4095, 4096 | 10,395 | no |
| a27 | 27 | none | 512 | **34.50** (34.40..34.55) | 355.7 (353.2..357.1) | 512, 512, 512 | 9,017 | no |
| a27 | 27 | none | 4,096 | **34.20** (34.08..34.23) | 362.4 (361.8..362.4) | 4096, 4096, 4097 | 9,017 | no |
| b27 | 27 | 1,866 MiB, share 0 | 512 | **39.37** (39.12..39.37) | 393.0 (389.3..393.4) | 513, 513, 513 | 10,901 | no |
| b27 | 27 | 1,866 MiB, share 0 | 4,096 | **39.03** (38.96..39.10) | 406.7 (404.6..407.8) | 4095, 4094, 4095 | 10,901 | no |
| **c, amended arm (A1, post-results)** | 27 | 2,432 MiB, share 0.8 (tuner) | 512 | **55.67** (55.23..55.74) | 415.9 (413.1..419.4) | 513, 512, 512 | 11,471 | no |
| **c, amended arm (A1, post-results)** | 27 | 2,432 MiB, share 0.8 (tuner) | 4,096 | **55.54** (55.20..55.55) | 424.7 (423.9..424.8) | 4095, 4096, 4097 | 11,471 | no |

Cold requests (excluded from the cells): a24 37.50 t/s, a27 34.42, b27 38.62, c (amended arm, A1, post-results) 52.60.

No cell is void. Every request had cache_n 0, swap-in and swap-out 0 KiB, PCIe gen 3 x16 throughout prefill, and at
most 3.4 MiB of NVMe reads during decode (the flag is at 64 MiB). All 28 answers are coherent summaries of the prompt
code (`answer_head` in the results JSON). MemAvailable never fell below 28,804 MiB, and memwatch never tripped.

## Scoring (M8, with C1 as Amendment A1 defines it)

| comparison | 512 | 4,096 | verdict |
|---|---:|---:|---|
| **C1 (A1)**: c / a24 ≥ 1.5, **c = amended arm (A1, post-results)** | **1.483** | **1.491** | c faster, ranges don't overlap, H0 rejected. **C1 fails at both lengths**, short of 1.5 by 1.1% and 0.6% |
| c / b27, the CPU-share effect (c = amended arm, A1, post-results) | 1.414 | 1.423 | faster, H0 rejected. Cache size also differs: 2,432 vs 1,866 MiB |
| **C2**: b27 / a27 (cache alone, same split) | **1.141** | **1.141** | b27 **faster**, ranges don't overlap. **C2 fails** at both lengths. H0 rejected |
| b27 / a24 | 1.049 | 1.048 | b27 faster, ranges don't overlap. Inside ±5%, so **H0 not rejected** |
| a27 / a24 (3 expert layers moved to the host) | 0.919 | 0.918 | slower, H0 rejected (reported, not scored) |

**Prompt processing** (reported, no claim):
- c/a24 1.083 and 1.064 (c = amended arm, A1, post-results)
- c/b27 1.058 and 1.044 (the 4,096 figure is inside ±5%)
- b27/a27 1.105 and 1.122
- b27/a24 1.024 and 1.019
- a27/a24 0.926 and 0.908

All have non-overlapping ranges.

**Our predictions (M7):**
- **(c)/(a24) at 1.1-1.3x: MISS** at both lengths, at 1.483 and 1.491 (read against the amended arm, A1,
  post-results). The share-0.8 arm landed well above the predicted range.
- **(b27) no faster than (a24): MISS** at both lengths. b27 is 4.9% and 4.8% faster than a24, with non-overlapping
  ranges. The gain is inside the ±5% null band, but M8 scores this prediction on faster / slower, not on H0.

**What it says, within the limits of M9:**
- At `-ncmoe 27`, a 1,866 MiB cache with no CPU share more than recovers the three expert layers it displaces. Moving
  the layers to the host costs 8.1%, and adding the cache gains 14.1% at the same split, for a net +4.9% against the
  best no-cache fit. The small-cache slowdown from the 2080 Ti thread report (C2) did not appear.
- The tuner's pick on the (a27) command (2,432 MiB, 80% of misses on the CPU) is **1.48-1.49x the best no-cache
  fit**. That is just under the thread's 1.5x bar and close to the 2080 Ti owner's 1.53x. Nearly all of the gain over
  b27 comes from the CPU share and the larger cache (1.41-1.42x over b27), not from the cache alone.

## Tuner on the (a27) command (Amendment A1)

- **Command:** `moe-cache-tune.py --out rec/tune-rushuna-a27 -- <M2 base command, -ncmoe 27>`. Ran from 06:08:33 to
  06:15:26 UTC with rc 0. Full stdout is in `rec/out-tuner-A1.txt`; run logs, traces and JSON are in
  `rec/tune-rushuna-a27/`.
- **What it ran:** `-ncmoe 27`, the command it was given. The tuner never changes it.
- **What it found:** "12528 MiB of experts, CUDA0 11797 MiB free, cache up to 2454 MiB". It measured 1,856 and
  2,432 MiB at shares 0, 0.5 and 0.95.
- **Verbatim:** `recommended: --moe-cache-mib 2432 --moe-cache-cpu-share 0.8 (58.2 t/s, 47.0 with share 0)`.
- **Cache allocated in arm (c):** the tuner's run log at 2,432 MiB shows `MoE cache size = 2430.56 MiB for 12528.00
  MiB of host experts`. Arm (c)'s own peak was 11,471 MiB against 11,909, against Mark's projection of about 11,265.

The tuner's own figures, reported beside ours and never mixed in:

| cache MiB | share | tuner t/s | hits |
|---:|---:|---:|---:|
| 1,856 | 0 | 38.4 | 71% |
| 1,856 | 0.5 | 50.2 | 75% |
| 1,856 | 0.95 | 53.0 | 62% |
| 2,432 | 0 | 46.6 | 81% |
| 2,432 | 0.5 | 52.9 | 79% |
| 2,432 | 0.95 | 58.3 | 72% |

Its machine line reads "uploads 8.0 GiB/s, CPU 25.2 GiB/s". It predicted 58.2 t/s at the pick, and we measured 55.7 and
55.5 (-4.4% and -4.6%). Its 1,856 MiB / share 0 run (38.4) agrees with our b27 (39.4 and 39.0).

## Fit gate (M2, M10.4)

(a27) peaked at 8,973 MiB during load and 9,017 MiB over the whole arm. The gate used the larger: 9,017 + 1,866 +
1,024 = **11,907 MiB against 11,909: PASS, by 2 MiB.** The load peak alone gives 11,863. The M2 projection was about
8,800 MiB, and the measured figure came in 173-217 MiB above it. (b27)'s real peak was 10,901 MiB, so the 1,024 MiB
margin left 1,008 MiB unused.

## Why the tuner failed (arm c)

`scripts/moe-cache-tune.py` (sha256 `c3baf2d2…6998b`, byte-identical to b12191 per M3) always runs its first calibration
server at `small = 10% of the expert size` (1,856 MiB here, rounded to 64). It reads the card's free memory from that
run's log and only then applies a cap. `--max-mib` caps only the sizes chosen after that first run. On the (a24)
command, which needs 10,367 MiB at load, 1,856 MiB of cache leaves no room for the 392 MiB compute buffer:

```
CUDA0 MoE cache size =  1856.00 MiB for 11136.00 MiB of host experts, 0% of the misses on the CPU
ggml_backend_cuda_buffer_type_alloc_buffer: allocating 392.00 MiB on device 0: cudaMalloc failed: out of memory
```

The tuner exited with "llama-server exited (1)" (`rec/out-tuner.txt`, `rec/rec/tune-rushuna/run-1856-0.log`).
Wall clock: 06:00:14 to 06:00:36 UTC. The script has no path that would let it run on this command on this card, so
M9's "its Mt may be below 1,866" never got the chance to apply. This is what Amendment A1 addresses.

**Upstream (checked 2026-11-23):** the behaviour was raised during review of PR #30966 by sasa7812 on 2026-10-27, as a
comment on line 569 of `moe-cache-tune.py`
(https://github.com/ggml-org/llama.cpp/pull/30966#discussion_r4385958942). The comment says "the script starts with
10% of experts unconditionally and on drivers with strict allocation it OOMs at the first run". It got no reply in that
thread, and the PR merged with the behaviour unchanged. There is no separate issue and no fix PR. `moe-cache-tune.py` has
had no commit since the merge. The related open issues are #31911 (`device_room()` under-reports free VRAM with a
draft model, plus a comment on 8 GB cards) and #32041 (Windows signal crash).

## Build (M3)

ggml-org/llama.cpp full clone, `v1.0.0` = `b1b770d90d94cad9e9ea5b993bdbc383a522fb28` (build 12359). The flags are as
locked: CUDA 12.8 from user space, arch 86, `GGML_NATIVE=OFF`, `LLAMA_USE_PREBUILT_UI=OFF`, `LLAMA_CURL=OFF`, Release.
The compile ran under `unshare -Un` (network off). `llama-server` sha256 `a6e3fc0a…2e71ac86`, `--version`
"1.0.0-dev (build 12359, commit b1b770d90)". Log: `rec/build.log`.

## Deviations from the lock (none touches a measured value)

1. **Build mechanics.** `cmake` isn't on Rushuna's non-interactive PATH, so the user-space `~/cmake/bin` 3.30.5 was
   used. The Makefile generator failed its compiler check under `unshare -Un` ("gmake: Invalid argument"). The build
   used Ninja (Strata's venv copy) instead, as HotRod's arm H did. The first link failed because libcudart wasn't found
   in user space, and the build was resumed with `LIBRARY_PATH`/`LD_LIBRARY_PATH=~/cuda-12.8/lib64`. The harness sets
   the same `LD_LIBRARY_PATH` at run time.
2. **`/props` `build_commit`** doesn't exist on this build. `/props` `build_info` reads `b12359-b1b770d90`, which
   carries the same check.
3. **Cache allocation line (M5)**: not in the arm server logs, because it prints only at verbose level (it shows in
   the tuner's `-lv 4` log). The cache is visible in (b27)'s load peak, 1,868 MiB above (a27)'s at the same split.
4. **Prompts (M5)**: the 8-hex nonce tokenizes to a variable length. Each prompt was cut so that the median over 16
   sample nonces is exactly 512 and 4,096 (`harness/cut_prompts.out`: spread 509..513 and 4093..4097). The measured
   prompt_n spread was 2 or less in every cell. Hashes under Files.
5. **Tuner `--out`** resolved to `rec/rec/tune-rushuna` (a relative path given after `cd rec`). It was fresh, as
   required.
6. **Machine state "PCIe under load"** is taken from the per-request prefill samples (gen 3 x16 in every request), not
   from a separate block.
7. **Arm (c) is the amended arm (A1, post-results)**, not the locked one. See the amendment in the lock file. It ran
   from `harness/run_amend_a1.sh` with the same functions as `run_all.sh`, and its results file is
   `rec/results-c-A1.json`.

## Files

- `harness/`: `bench_moecache.py` (cut down from HotRod's `bench_hotrod.py`), `run_all.sh`, `run_amend_a1.sh`, `machine_state.sh`,
  `cut_prompts.py` + `.out`, `summarize.py`, `memwatch.py` (v3, unchanged), `stream_read.c` (md5 `33178532…`),
  `corpus.txt`.
- Prompts: `prompt-512.txt` sha256 `fe9c742079133e9575ae502575504a11c9402e4f1834fc5e0a6422931dd399ea`, and
  `prompt-4096.txt` sha256 `7ad80637fc32dc10d399cf2a9ec2d90048992464cfa04d98dcd7ba8ec4a19a82`.
- `rec/`: `machine-state.txt`, `sequence.log`, `run.log`, `results-{a24,a27,b27}.json`, `server-*.log`,
  `card-1s.csv`, `memwatch-*`, `state-*.txt`, `fit-gate.txt`, `out-tuner.txt`, `rec/tune-rushuna/`, `build.log`,
  `chat_template.jinja`, `summary.json`. Amendment A1: `results-c-A1.json`, `server-c-A1.log`, `out-tuner-A1.txt`,
  `tuner-A1-flags.txt`, `tune-rushuna-a27/`, `run-amend-a1.out`, `state-{tuner-A1,c-A1}.txt`.
- `summary.txt`: output of `harness/summarize.py rec`.

**Machine state** (`rec/machine-state.txt`, 2026-11-23 before a24):
- A1 in force: swap 0, all 7 units inactive. Mark ran the sudo steps and I checked them.
- Model re-hash `ac0e2c11…31a61` OK.
- NVMe `dd` 8 GiB direct: 2.1 GB/s.
- `stream_read`, 4 threads: 26.5 GB/s. PCIe 3.0 x16 is about 13 GiB/s pinned (M9).
- Driver 580.173.02.
