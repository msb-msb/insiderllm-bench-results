# llama.cpp MoE cache CPU share (PR #30966): Qwen3.6-35B-A3B on Rushuna's RTX 3060, 2026-11-23 UTC

**Record for the pre-registration `docs/candidates/moe-cache-cpu-share-2026-11.md`** (lock commit c22ff41b, sha256
`f047318b9eceb00315e803e94189af1b68484293ab6b187ab0ddc2c07746f6a4`, public copy verified before the run).

**Status: STOPPED after arm (b27).** Arms (a24), (a27) and (b27) ran as locked, and the fit gate passed. The tuner
then failed on its first server start (out of memory), so arm (c) has no `recommended:` line and was not run. The lock
doesn't say what to do if the tuner fails. Per Mark's instruction, the run stopped here with no amendment. C1 and our
prediction 1 both need (c) and can't be scored as locked. C2, the cache effect, H0 and prediction 2 are scored below.

## Results (decode = server `predicted_per_second`; cell = median of 3, min..max)

| arm | `-ncmoe` | cache | len | decode t/s | prompt t/s | prompt_n | cell peak MiB | void |
|---|---:|---|---:|---|---|---|---:|---|
| a24 | 24 | none | 512 | **37.53** (37.48..37.57) | 383.9 (383.0..384.7) | 511, 513, 512 | 10,389 | no |
| a24 | 24 | none | 4,096 | **37.26** (37.19..37.28) | 399.0 (398.0..399.3) | 4097, 4095, 4096 | 10,395 | no |
| a27 | 27 | none | 512 | **34.50** (34.40..34.55) | 355.7 (353.2..357.1) | 512, 512, 512 | 9,017 | no |
| a27 | 27 | none | 4,096 | **34.20** (34.08..34.23) | 362.4 (361.8..362.4) | 4096, 4096, 4097 | 9,017 | no |
| b27 | 27 | 1,866 MiB, share 0 | 512 | **39.37** (39.12..39.37) | 393.0 (389.3..393.4) | 513, 513, 513 | 10,901 | no |
| b27 | 27 | 1,866 MiB, share 0 | 4,096 | **39.03** (38.96..39.10) | 406.7 (404.6..407.8) | 4095, 4094, 4095 | 10,901 | no |
| c | 24 | tuner's pick | — | **not run**: tuner failed | | | | |

Cold requests (excluded from the cells): a24 37.50 t/s, a27 34.42, b27 38.62.

No cell is void. Every request had cache_n 0, swap-in and swap-out 0 KiB, PCIe gen 3 x16 throughout prefill, and at
most 3.4 MiB of NVMe reads during decode (the flag is at 64 MiB). All 21 answers are coherent summaries of the prompt
code (`answer_head` in the results JSON). MemAvailable never fell below 28,804 MiB, and memwatch never tripped.

## Scoring (M8)

| comparison | 512 | 4,096 | verdict |
|---|---:|---:|---|
| **C2**: b27 / a27 (cache alone, same split) | **1.141** | **1.141** | b27 **faster**, ranges don't overlap. **C2 fails** at both lengths. H0 rejected |
| b27 / a24 | 1.049 | 1.048 | b27 faster, ranges don't overlap. Inside ±5%, so **H0 not rejected** |
| a27 / a24 (3 expert layers moved to the host) | 0.919 | 0.918 | slower, H0 rejected (reported, not scored) |
| **C1**: max(b27, c) / a24 ≥ 1.5 | — | — | **can't be scored as locked** (no c). b27 alone reaches 1.05x, a third of the way to 1.5x |
| c / b27 | — | — | not run |

**Prompt processing** (reported, no claim): b27/a27 1.105 and 1.122, b27/a24 1.024 and 1.019, a27/a24 0.926 and 0.908.
All have non-overlapping ranges.

**Our predictions (M7):**
- **(c)/(a24) at 1.1-1.3x:** can't be scored (no c).
- **(b27) no faster than (a24): MISS** at both lengths. b27 is 4.9% and 4.8% faster than a24, with non-overlapping
  ranges. The gain is inside the ±5% null band, but M8 scores this prediction on faster / slower, not on H0.

**What it says, within the limits of M9:** on this card a 1,866 MiB cache, with no CPU share, more than recovers the
three expert layers it displaces. Moving the layers to the host costs 8.1%, and adding the cache gains 14.1% at the
same split. The net against the best no-cache fit is +4.9%. The small-cache slowdown from the 2080 Ti thread report
(C2) did not appear here.

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
M9's "its Mt may be below 1,866" never got the chance to apply. Any way to get an arm (c) changes the locked design,
for example giving the tuner a different `-ncmoe`. That is Mark's decision, as an amendment.

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

## Files

- `harness/`: `bench_moecache.py` (cut down from HotRod's `bench_hotrod.py`), `run_all.sh`, `machine_state.sh`,
  `cut_prompts.py` + `.out`, `summarize.py`, `memwatch.py` (v3, unchanged), `stream_read.c` (md5 `33178532…`),
  `corpus.txt`.
- Prompts: `prompt-512.txt` sha256 `fe9c742079133e9575ae502575504a11c9402e4f1834fc5e0a6422931dd399ea`, and
  `prompt-4096.txt` sha256 `7ad80637fc32dc10d399cf2a9ec2d90048992464cfa04d98dcd7ba8ec4a19a82`.
- `rec/`: `machine-state.txt`, `sequence.log`, `run.log`, `results-{a24,a27,b27}.json`, `server-*.log`,
  `card-1s.csv`, `memwatch-*`, `state-*.txt`, `fit-gate.txt`, `out-tuner.txt`, `rec/tune-rushuna/`, `build.log`,
  `chat_template.jinja`, `summary.json`.
- `summary.txt`: output of `harness/summarize.py rec`.

**Machine state** (`rec/machine-state.txt`, 2026-11-23 before a24):
- A1 in force: swap 0, all 7 units inactive. Mark ran the sudo steps and I checked them.
- Model re-hash `ac0e2c11…31a61` OK.
- NVMe `dd` 8 GiB direct: 2.1 GB/s.
- `stream_read`, 4 threads: 26.5 GB/s. PCIe 3.0 x16 is about 13 GiB/s pinned (M9).
- Driver 580.173.02.
