# llama.cpp MoE cache CPU share (PR #30966) on an RTX 3060 with 32 GB (pre-registration)

**LOCKED on commit.** Written 2026-11-22 before any engine build and any measured request (the model working copy
was placed and hashed beforehand, M10.2). The sha256 of this file is in the lock commit message and in
`moe-cache-cpu-share-2026-11.md.sha256` next to it, and the file is published byte-exact to the public mirror
(`candidates/`) before the first measurement. Anything added later is appended after section M10 as a dated amendment
or deviation. Nothing above M10 changes.

Machines are named, never addressed: **Rushuna** (RTX 3060 12 GB, i7-7700 4C/8T, 32 GB DDR4-2133, PCIe 3.0 x16) and
**Miu** (the model store). Prior records this builds on: `rushuna-3060-qwen36-ncmoe-2026-09-11/` and
`rushuna-july-rows-remeasure-2026-09-28/` (the 35B file on this card, `-ncmoe 24`, 4 threads),
`llamacpp-v0.7-nemotron-bolt-2026-10/` (arm B, the `--moe-cache-mib` size rule), `strata-hotrod-2026-11/` (harness,
memory guard, void rules, A1).

## M1. Scope, question and claims under test

**Scope: Rushuna only.** The cache keeps host-memory experts in spare VRAM. On a 24 GB RTX 3090 this 22 GB file fits
entirely on the card (`-ngl 99` with no expert offload), so no experts sit in host memory and the cache has nothing to
act on. A 3090 arm would only measure the cache switched off. Tamanna is not part of this test.

**Question.** On a 12 GB card with part of the experts in system RAM, does `--moe-cache-cpu-share` (computing a share of
the cache misses on the CPU from the host experts instead of uploading them over PCIe), at the value the bundled tuner
picks, change decode speed against no cache and against the cache with no CPU share?

**The feature.** ggml-org/llama.cpp PR #29887 ("llama : add a GPU cache for MoE experts kept in host memory", am17an,
merged 2026-10-07) added `--moe-cache-mib`. PR #30966 ("llama_moe_cache: run missed experts on CPU, add tuning script",
am17an, merged 2026-11-07, first in build b12191) added `--moe-cache-cpu-share F` and `scripts/moe-cache-tune.py`.

**Claim C1 (PR #30966 thread): up to ~2x decode on 8-12 GB cards.** The PR description shows one machine (92 GB free on
the card) and makes no small-card claim. The small-card figures are owner reports in its comment thread, on pre-merge
commits, all with every expert on the CPU (`-cmoe`):

| reporter's card | model | no cache | cache only (share 0) | best fixed share tried | best / no cache |
|---|---|---:|---:|---:|---:|
| RTX 3070 8 GB | Cyber-Tiel-Coder-35B-A3B UD-Q4_K_S | ~35 | 41.0 (3,136 MiB) | 62.4 (3,136 MiB, 0.95) | 1.78x |
| RTX 2080 Ti 11 GB | Qwen3.6-35B-A3B UD-Q6_K_XL | 42.11 | 23.5 (2,752 MiB) / 50.2 (6,784 MiB) | 64.5 (6,784 MiB, 0.95) | 1.53x |
| RTX 5060 Ti 16 GB | Qwen3.6-35B-A3B UD-Q6_K_XL | 44.23 | 18.7 (2,752 MiB) / 38.8 (8,320 MiB) | 61.1 (8,320 MiB, 0.95) | 1.38x |

The "2x" in the YouTube coverage (SimplyExplain, KernelBrief) is a rounding of these. **Stated as tested here: the
better of (b27) and (c) decodes ≥1.5x faster than (a24)**, the best fit with no cache. That is the reader's real
trade: on this card a cache costs expert layers that would otherwise sit on the GPU.

**Claim C2 (Cloud Codes, "llama.cpp MoE Cache Slower Than No Cache?", from the 2080 Ti report above): a small cache is
slower than no cache on an ~11 GB card** (42.11 → 23.5 tok/s, -44%). **Stated as tested here: (b27) decodes slower than
(a27)**, at the same layer split, so the cache is the only difference.

**Cache effect alone:** (b27) / (a27), reported at both lengths.

**Null (H0), for each comparison above:** the ratio falls within ±5%, i.e. 0.95 < ratio < 1.05.

## M2. Arms (same model, build and flags; only `-ncmoe` and the cache flags differ)

| arm | `-ncmoe` | cache flags | role |
|---|---:|---|---|
| **a24** no cache | 24 | none (`--moe-cache-mib` defaults to 0 = disabled) | best fit without a cache; the C1 baseline |
| **a27** no cache | 27 | none | reference cell: same split as (b27), isolates the cache from the layer change |
| **b27** cache, share 0 | 27 | `--moe-cache-mib 1866` (share left at its default, 0.00) | the Nemotron size rule, below |
| **c** tuner's pick | 24 (the tuner's input command, below) | `--moe-cache-mib Mt --moe-cache-cpu-share Ft` | `scripts/moe-cache-tune.py`'s `recommended:` line, verbatim |

**Base command, every arm, with N from the table:** `llama-server -m Qwen3.6-35B-A3B-UD-Q4_K_M.gguf -ngl 99 -ncmoe N
-fa on -c 16384 -np 1 --fit off -lm mmap -t 4 --port 8081`.
- **`-ncmoe 24`**: the setting the earlier Rushuna records settled on for this file and card.
  `rushuna-3060-qwen36-ncmoe-2026-09-11/` measured it as the best fit (16 expert layers on the GPU, 10,259 MiB peak).
  `rushuna-july-rows-remeasure-2026-09-28/` confirmed that `-ncmoe 24 -c 16384` loads and serves a 16,128-token prompt
  (peak 10,267 MiB), and that `-ncmoe 20` does not load.
- **`-ncmoe 27`**: three expert layers moved back to the host to make room for the 1,866 MiB cache. Mark's choice.
  Projected from the 09-28 record (6,481 MiB at `-ncmoe 32`, 10,351 at `-ncmoe 24`, about 484 MiB per layer): (a27)
  peaks near 8,800 MiB, and 8,800 + 1,866 + 1,024 = 11,690 MiB, under 11,909. At `-ncmoe 26` the same sum was about
  12,190 MiB and would fail the gate. This is a projection; the gate uses the measured peak.
- **`-t 4`**: recorded in both records. The 09-11 result table is headed "mmap, 4 threads", and the 09-28 harness ran at
  "v0.4.0 defaults (4 threads, auto)", resolved to 4 in its JSON. Four is also this CPU's physical core count.
- `--fit off`, `-lm mmap` and `--port 8081` as in the Nemotron record. The defaults differ (M3).

**Cache size for (b27): 1,866 MiB**, the Nemotron arm B rule unchanged: 10% of this file's 18,662 MiB of expert weights
(the PR #29887 author's "10% of the total expert size is good").

**Fit gate (M10.4):** before any (b27) request, arm (a27)'s measured load peak on this build is read. If that peak +
1,866 + 1,024 MiB margin exceeds 11,909 MiB (the usable total from the 09-28 record's out-of-memory line), the run stops
and Mark is told. No N or cache size is chosen on the fly.

**Tuner (c).** The tuner does not choose `-ncmoe`: it tunes `--moe-cache-mib` and `--moe-cache-cpu-share` for the
command it is given, and its `recommended:` line holds only those two flags. It is given the (a24) command, the one a
reader with this card would already be running: `python3 scripts/moe-cache-tune.py --out tune-rushuna -- <base
command, N = 24>`. It is run once, after (b27), in a fresh `--out` directory (the script reuses a run directory for the
same command). It runs the server at 2 cache sizes × 3 shares (0, 0.5, 0.95), 2,048 tokens on the first run and 512 on
the others. It caps the cache at the card's free memory minus the model's use minus 512 MiB, and predicts a size × share
grid. Recorded: full stdout, the run directory, its wall-clock runtime (start and end UTC), the `-ncmoe` it ran with
and the cache size it picked, and its `recommended:` line, which is appended unchanged to the (a24) command to make arm
(c). The tuner's own t/s figures are reported beside our cells, never mixed in.

**Order: a24, a27, fit gate, b27, tuner, c.** One server resident at a time; card at 0 MiB between arms.

## M3. Build, pinned

**Pinned: ggml-org/llama.cpp v1.0.0 = build b12359, commit `b1b770d90d94cad9e9ea5b993bdbc383a522fb28`** (the annotated
tag v1.0.0 points at it; it's the same pin as the v1 MTP lock). It includes #31888, "moe-cache : ensure CPU part does
not wait for the cached experts" (merged 2026-11-08). The other moe-cache changes after b12191 that it includes are
#31497, which keeps the cache off a draft model (11-08), and #32157, a code move (11-13). Not included: #32636 (11-20).
The auto share controller (#31286) was closed unmerged, so no build has an auto mode. `scripts/moe-cache-tune.py` at
this commit is byte-identical to b12191's.

Full clone, built on Rushuna with the user-space CUDA 12.8: `-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=86
-DGGML_NATIVE=OFF -DLLAMA_USE_PREBUILT_UI=OFF -DLLAMA_CURL=OFF`, Release, network off for the compile (HotRod H3).
The record gets the binary's sha256 and `--version`; `/props` `build_commit` must read `b1b770d`.

**Default flags on this build**, read from `common/common.h` and `common/arg.cpp` at `b1b770d9`:

| flag | default | effect on this test |
|---|---|---|
| `--moe-cache-mib` | 0, disabled | arms (a24) and (a27) need no flag |
| `--moe-cache-cpu-share` | 0.00 | arm (b27) is share 0 without passing it |
| `--fit` | on: "adjust unset arguments to fit in device memory" | set `--fit off` so nothing is moved behind our back. `common/fit.cpp` has no reference to the MoE cache: fit neither sizes nor accounts for it |
| `-fa` | auto | set `-fa on` |
| `-lm` / `--load-mode` | auto = mmap unless a device can't | set `-lm mmap`. A thread report crashed with the cache plus `--load-mode dio`; dio is not used |
| `-t` | -1 (auto) | set `-t 4` |
| `--port` | 9931 | set 8081 |

## M4. Model and storage

`Qwen3.6-35B-A3B-UD-Q4_K_M.gguf` (Unsloth), 22,134,528,992 bytes, sha256
**`ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61`**. This is the Unsloth LFS oid, and it equals the
entry in Miu LLM_repo `from-miu/bench-models/SHA256SUMS` and the sidecar on Rushuna. Canonical copy: Miu LLM_repo
`from-miu/bench-models/`. Working copy: Rushuna NVMe `~/moecache-2026-11/model/`, copied from Rushuna's HDD-parked
copy and re-hashed (M10.2). It is re-hashed again on the day of the run; a mismatch stops it. `~/hotrod-2026-11` was
moved to the HDD to make room, after its contents were checked against the committed HotRod record.

## M5. Measurements

**Per arm:** start the server and wait for `/health`. Then one **cold request** (the 512-token prompt with its own
nonce), **reported separately and excluded from every cell value**. Then **3 measured requests at 512 tokens, then 3 at
4,096**, on the same resident server. **Cell value = median of the 3 (min..max).**

Each request is a chat completion, streamed, with a fresh 8-hex nonce line first. Settings: thinking off, temperature 0,
`cache_prompt false`, `ignore_eos`, `max_tokens 256`.

- **Prompts:** `prompt-512.txt` and `prompt-4096.txt`, cut from the HotRod harness corpus so that each request's
  prompt_n (template plus nonce plus text) is 512 and 4,096 on this file's tokenizer. Counted with this build's
  `llama-tokenize` after the build and before arm (a24); the files and their sha256 go in the record.
- **Decode** = the server's `predicted_per_second`. **Prompt processing** = `prompt_per_second`, with client TTFT
  beside it.
- **Memory:** card memory.used sampled at 1 s, with peak per cell and per arm, plus the cache allocation line from the
  server log. RAM: minimum MemAvailable over the arm, and server VmRSS split into RssAnon and RssFile (mmap'd model
  pages count as file RSS).
- **Per request, as in HotRod H5:** prompt_n, cache_n, swap-in/out KiB, NVMe read bytes during prefill and during
  decode, PCIe gen/width during prefill, first 200 characters of each answer. The PR thread saw garbled output with a
  CPU share on Vulkan. This run is CUDA, but an empty, looping or garbled answer still voids its cell (M6).
- **Machine state,** once before arm (a24): free RAM, swap and the A1 units, NVMe sequential read (`dd` of the model,
  `iflag=direct`, 8 GiB), DDR read bandwidth (`stream_read`), PCIe link at idle and under load, driver version.

**Memory guard:** `memwatch.py` v3 from the Strata records, unchanged. It trips if MemAvailable falls under 2 GiB at
any time. On a trip it SIGTERMs the harness and every process named exactly `llama-server` or `llama-bench`, and writes
`TRIPPED`. A trip ends the arm and is reported. The tuner launches `llama-server` itself, so the guard covers it too.
HotRod's two fixes come with the harness: the arm script kills its whole process tree on STOP, and no background loop
outlives it.

**A1 conditions (HotRod lock, amendment A1) apply from before arm (a24) until after arm (c):** swap off (`swapoff -a`),
and `mycoswarm`, `ollama`, `fwupd`, `ModemManager` and the `apt-daily`, `apt-daily-upgrade` and `fwupd-refresh` timers
stopped. Storage, thermal and SMART services keep running. The harness refuses to start if swap is on or any of those
units is active, and records their state at the start of every arm. After (c), Mark restores swap and the units.

## M6. Void rules (HotRod H6, Rushuna, with the decode-read rule applied)

A cell is void if any of its 3 measured requests has:
- prompt_n spread over 3 tokens across the 3;
- cache_n above the template header (≈0);
- swap-out above 0 KiB (0 by construction with swap off);
- the PCIe link below gen 3 x16 during any prefill;
- NVMe reads over 1 GiB during the decode (flag over 64 MiB). The 22 GB file fits in RAM, so decode reads mean
  page-cache pressure, which is not the mechanism under test;
- an empty, looping or garbled answer.

A void cell is re-run once (a fresh server, its own cold request, then the cell's 3); void twice is reported as void.

## M7. Predictions (ours, written 2026-11-22, before any build or measurement)

- **(c) / (a24), decode: 1.1-1.3x** at both lengths. **So C1 is expected to fail.**
- **(b27) no faster than (a24), decode:** (b27) slower than (a24), or no difference shown. **So C2 is expected to hold
  or tie.** (Mark's predictions as first written, against arms (a) and (b), read against (a24) under the four-arm design.)

## M8. Scoring

- **Faster / slower** only when the medians differ and the min..max ranges don't overlap (HotRod H7). Otherwise "no
  difference shown".
- **C1 holds** at a length if max((b27), (c)) / (a24) ≥ 1.5 with non-overlapping ranges. It is scored at 512 and 4,096
  separately; which arm was the better one is reported.
- **C2 holds** at a length if (b27) is slower than (a27).
- **Cache effect alone:** (b27) / (a27) with its ranges, at both lengths. Also reported, not scored: (a27) / (a24), the
  cost of the three layers moved to the host, and (c) / (b27).
- **H0 is rejected** for a comparison at a length if its ratio falls outside 0.95-1.05 with non-overlapping ranges.
- **Our predictions** are scored against the same medians: the (c) / (a24) ratio inside or outside 1.1-1.3; (b27) vs
  (a24) as slower / no difference (hit) or faster (miss).
- Prompt processing is reported per arm and length by the same rule. No claim is made about it in advance (the
  Nemotron record saw the cache cost 5.6% of prompt speed).

## M9. Limits stated in advance

- One model, one quant, one card. The thread's best results are on other 35B-A3B files and with `-cmoe`. Here 24 or 27
  of 40 layers' experts are on the host, so the cache and the CPU share act on part of the experts, not all.
- This tests the small-cache case. At `-ncmoe 24` the VRAM left for a cache is about 1 GiB, and the tuner caps its
  sizes at what fits, so its Mt may be below 1,866: (c) vs (b27) differs in size, share and split, not share alone.
- Rushuna's CPU is 4 cores on DDR4-2133. The mechanism depends on the CPU reading experts faster than PCIe uploads them
  (thread example: 48.7 vs 9.6 GiB/s). Rushuna's ratio will be smaller, and the machine state records both figures.
- 256-token decodes with 3 runs per cell: the tuner's prediction is for a warm cache over 512-2,048 tokens. The cold
  request warms each server before the measured ones.
- One build. Earlier or later builds may behave differently (M3).

## M10. Gates

1. Mark approves this text; it is locked on commit, its sha256 recorded, pushed, and mirrored byte-exact through the
   leak gate. The public file's hash is checked against the lock before any measurement.
2. Model working copy on the Rushuna NVMe, sha256 equal to `ac0e2c11…31a61`.
3. Build at `b1b770d9` done, binary hashed, prompts counted and hashed, after Mark's go. These are not measurements.
4. Arm (a27)'s load peak read; the M2 fit gate passes, or the run stops and Mark is told.
5. A1 in force (Mark's sudo steps), and Mark says go.

## Amendment A1 (2026-11-22, Mark): arm (c) runs the tuner on the (a27) command

**Written AFTER the results of (a24), (a27) and (b27) were known.** This is not a pre-registered change. Those three
arms ran as locked on 2026-11-23 UTC (record `docs/bench-results/moe-cache-cpu-share-2026-11/`, commit 67b4cb3f), the
fit gate passed, and the run stopped at the tuner. **Why:** `scripts/moe-cache-tune.py` as written can't run on the
(a24) command on a 12 GB card. Its first calibration server always allocates a cache of 10% of the expert bytes
(1,856 MiB here) before it reads how much room the card has, and `--max-mib` doesn't apply to that first run. On the
(a24) command (10,367 MiB at load) the server ran out of memory allocating its 392 MiB compute buffer. The lock didn't
cover a tuner failure, so no arm (c) existed.

(This amendment is A1 of this lock. "A1 conditions" in M5, meaning swap off and the units stopped, refer to the HotRod
lock's amendment A1 and are unchanged.)

**Change, arm (c) only.** The tuner is run on the **(a27) command**: the M2 base command with `-ncmoe 27`, everything
else identical: `python3 scripts/moe-cache-tune.py --out <fresh dir> -- <base command, N = 27>`. Its `recommended:`
line is taken verbatim and appended to the (a27) command to make arm (c). The rest of M2's tuner paragraph stands:
once, in a fresh `--out` directory, with full stdout, the run directory, start and end UTC, the `-ncmoe` and cache size
it picked, and the `recommended:` line recorded. Prompts, runs per cell, the cold request, memory guard, A1 conditions
and void rules are as in M5 and M6.

**Projected fit (Mark):** 9,017 (the (a27) arm peak) + 1,856 + 392 ≈ 11,265 MiB against 11,909. This is a projection
and adds no gate. **If the tuner still runs out of memory, the run stops and is reported. There is no further
amendment.**

**Scoring under A1.** **C1 = (c) / (a24)**, holding if ≥ 1.5 with non-overlapping ranges, scored at each length as in
M8. **(c) / (b27)** is also reported: both arms are at `-ncmoe 27`, so this is the CPU-share effect, plus the cache
size difference if the tuner's Mt isn't 1,866. Our prediction 1, (c)/(a24) at 1.1-1.3x, is read against the amended
(c). C2, the cache effect alone, H0 and prediction 2 are as already scored. **Every (c) figure is labelled "amended arm
(A1, post-results)"** in the record and in any article.

The text above this section is byte-identical to the lock as committed in c22ff41b (sha256
`f047318b9eceb00315e803e94189af1b68484293ab6b187ab0ddc2c07746f6a4`, the `.sha256` file beside it).
