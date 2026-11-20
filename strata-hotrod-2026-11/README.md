# Strata HotRod vs upstream Strata, Rushuna (RTX 3060 12 GB, 32 GB) and Tamanna (RTX 3090 24 GB, 64 GB), 2026-11-20

Results record for the pre-registration `docs/candidates/strata-hotrod-2026-11.md`: lock commit `c06003fc`
(file sha256 `1ca64bda…`), amendment **A1** commit `3f9cfe68` (file sha256 `703312de…`; the text above A1 is
byte-identical to `c06003fc`). Arms: **U** upstream `v0.2.16` (`64524fb9`), **H** Strata-HotRod `main` (`251dec43`),
**B** upstream `v0.1.45` (`477ac13c`, HotRod's merge base). Model: ISTA-DASLab Qwen3.8-Flash-Next GSQ-RCO IQ3_S at
revision `ed59f920`, both shards re-hashed on each rig and matching the lock. 131072 context, setup flags identical
across arms, each config used as its setup wrote it.

**A corrected-config HotRod can get a NEW pre-registration later. No amendment to this one** (Mark, 2026-11-20).

## Results

Our cells (H5 step 2): per cell (priming, measured) × 3, value = mean of the 3 measured requests (min–max). Void rules
H6 (Rule P4 with A1's reading). Produced by `harness/summarize.py .`.

### Rushuna (RTX 3060 12 GB, i7-7700, 32 GB DDR4-2133, PCIe 3.0 x16; swap off and services stopped per A1)

| arm | length | prefill tok/s | decode tok/s | draft accept | prompt_n spread | status |
|---|---|---|---|---|---|---|
| U | 4096 | 183.5 (171.7–193.7) | 18.8 (18.6–19.0) | 0.74 | 2 | valid |
| U | 16384 | 329.7 (314.5–338.5) | 18.8 (18.1–19.1) | 0.70 | 2 | valid |
| U | 32512 | 341.0 (333.4–350.2) | 18.5 (18.2–18.7) | 0.69 | 2 | valid on re-run (first pass void: spread 4) |
| H | – | – | – | – | – | **arm ended by the memory floor (H5)**, during server load |
| B | 4096 | 192.2 (191.5–193.1) | 17.2 (16.8–17.9) | 0.67 | 2 | valid |
| B | 16384 | 221.7 (216.2–226.7) | 17.0 (16.4–17.5) | 0.63 | 3 | valid |
| B | 32512 | 251.9 (232.8–262.2) | 17.2 (16.7–17.6) | 0.65 | 2 | valid on re-run (first pass void: spread 4) |

Every Rushuna request: cache_n 0, swap-out 0 KiB, PCIe gen 3 x16 during prefill, no empty answers.

**Predictions R1, R2: unscorable** (H has no cells on Rushuna).

**U vs B (descriptive, no prediction):** U decodes faster than B at 4K, 16K and 32K (ranges don't overlap); U prefills
faster at 16K and 32K; at 4K the prefill ranges overlap (no difference shown).

`strata_bench.py` (the arm's own tool, default suite), medians (range), reported as the tool prints them, no void rule:

| arm | chat decode | 4K prompt | 16K prompt | agent decode |
|---|---|---|---|---|
| U | 17.1 (15.4–19.3) | 172.8 (151.5–192.3) | 326.4 (309.2–332.6) | 14.5 (9.0–19.5) |
| H | see below (post-trip, descriptive only) | | | |
| B | 18.2 (15.4–20.4) | 174.4 (173.3–195.4) | 218.9 (197.9–219.6) | 12.5 (7.5–14.9) |

#### H on Rushuna: ended by the memory floor

- Scored attempt (`rushuna/H/`), 04:58:45 UTC: H's server started under `sb_prestart.sh`. MemAvailable fell from 31.0
  GiB to **1,682 MiB at 04:59:21 (36 s, still loading)**; memwatch tripped at the 2 GiB floor and the arm ended (H5).
- **Post-trip, unguarded:** memwatch killed the wrapper script, not its children. H's server and `strata_bench.py`
  kept running for about 75 s with no memory guard, until they were stopped by hand (05:00:37). The tool's output from
  that window (chat decode median 28.0 (24.0–34.8), n=9; 4K prompt 647.9 (640.1–700.3), n=3; the 16K test was cut off)
  is **descriptive only**: it was measured after the arm had ended. `run_arm.sh` was fixed afterwards to stop the
  arm's server and engine, and (2026-11-20) the egress-watch loop, on a trip.
- H's learned files after the attempt are in `rushuna/H/learned/SHA256SUMS-learned.txt` (names, sizes, sha256; the
  binaries are not in the record): the downloaded predictor `predictor-5400e1ae…` is unchanged (`04367a17…`, the
  lock's hash); a second predictor `predictor-3918fb62…` (`0e96c863…`) and `ram-reserve.json`/`vram-reserve.json` were
  written.

#### H memory diagnosis (EXPLORATORY, UNSCORED, Mark 2026-11-19)

`harness/explore_rss.py` sampled every 1 s every process whose command line names the work folder (VmRSS, RssAnon,
RssFile, RssShmem, VmLck, VmPin, VmSwap), MemAvailable and card memory, and killed the engine/server/tool at 2 GiB
MemAvailable. Two runs, both with the scored arm's install:

1. **Default config** (`rushuna/H-exploratory-1-default/`): the **engine** is the only process that grows. Its
   anonymous RSS climbs about 1.1 GB/s during load, 0.4 → 25.3 GB in 30 s; the server stays at ~0.2 GB. The engine log
   names it: `FileExpertSource: RAM budget 23.19 GiB … allocating 23.19 GiB pageable resident cache complement`, plus
   KV streaming's `1.55 GiB of pinned RAM`. 23.19 GiB + 1.55 GiB ≈ the 25.3 GB plateau. The curve flattens as the copy
   completes (25,305 → 25,317 MiB over the last second): it levels off, it is not heading for OOM, but the auto budget
   leaves ~1.9 GiB available on a 32 GB machine, under the lock's 2 GiB floor. Tripped at 1,942 MiB.
2. **One variant, `--resident-budget-gib 20`** (only change; `rushuna/H-exploratory-2-budget20/config-used.json`
   diff): completed the whole `strata_bench.py` suite. Engine anon 23.3–24.0 GB, flat through 16K and agent; lowest
   MemAvailable 3.2 GiB. Medians (range): chat decode 26.0 (23.2–35.9), 4K prompt 649.6 (636.1–684.9), 16K prompt
   633.3 (630.6–635.7), agent decode 25.0 (11.9–28.5). Exploratory only; not scored, not comparable under the lock.

Likely cause: HotRod's automatic RAM budget for its resident expert tier, sized from available RAM at start with too
small a reserve for this floor. KV streaming is not it (1.55 GiB). U and B have no such tier.

### Tamanna (RTX 3090 24 GB, Ryzen 7 5700X, 64 GB DDR4-3000, PCIe 4.0 x16; inside bwrap, no network)

Run 2026-11-20 15:55–16:15 UTC, unattended (`tamanna/chain.log`). Both shards re-hashed before the arms and match the
lock (`tamanna/model-sha256.txt`); all five engine/library sha256 match Rushuna's (`tamanna/machine-state-2026-11-20.txt`).
Swap is on (8 GB file, ~58 MiB used before the arms); A1 is Rushuna-only. No memory floor tripped: lowest MemAvailable
U 5.5 GiB, H 7.8 GiB, B 10.5 GiB. Egress: every run inside `bwrap --unshare-net`; the per-pid watch logged 0
non-loopback lines.

| arm | length | prefill tok/s | decode tok/s | draft accept | prompt_n spread | status |
|---|---|---|---|---|---|---|
| U | 4096 | 2450.4 (2432.9–2462.1) | 154.3 (143.2–161.7) | 0.77 | 5, then 4 | **void twice** (prompt_n spread 5 first pass, 4 on re-run) |
| U | 16384 | 2950.8 (2930.7–2963.0) | 135.4 (133.4–138.3) | 0.66 | 2 | valid |
| U | 32512 | 3102.4 (3059.7–3134.8) | 141.0 (136.2–145.3) | 0.67 | 3 | valid |
| H | 4096 | 2385.3 (2349.6–2406.7) | 94.6 (92.7–98.2) | 0.64 | 2 | valid |
| H | 16384 | 2405.0 (2404.5–2405.6) | 92.0 (88.2–97.2) | 0.65 | 3 | valid |
| H | 32512 | 1967.8 (1965.5–1969.9) | 91.5 (88.2–95.1) | 0.65 | 2 | valid |
| B | 4096 | 2223.3 (2216.0–2236.1) | 115.8 (110.0–125.3) | 0.63 | 2 | valid |
| B | 16384 | 2668.0 (2660.9–2679.8) | 112.8 (109.4–118.1) | 0.63 | 3 | valid |
| B | 32512 | 2805.7 (2804.5–2806.8) | 119.7 (116.4–121.5) | 0.69 | 3 | valid |

Every Tamanna request: cache_n 0, swap-out 0 KiB, PCIe gen 4 x16 during prefill, no empty answers. NVMe reads during
the measured decode at most 17.9 MiB (no flag; the 64 MiB flag and 1 GiB void are far off). U's first pass had
swap-in during its requests (≤ 37 MiB per request); swap-in is recorded, not a void criterion. U's 4K value is shown
for reference only: a cell void twice is reported void and not scored.

**Predictions (H7):**
- **T1, decode, H slower than U at 4K, 16K and 32K: not scorable as a whole.** H is slower at 16K (0.68×) and 32K
  (0.65×), ranges far apart; 4K is void (U's cell), and the prediction must hold at every length it names. Recorded
  as: consistent at the two scored lengths, unscored at 4K.
- **T2, prefill, H/U between 1.00 and 1.30 with H's range above U's, at 4K and 16K: MISSED.** At 16K H is slower
  (H/U 0.82, ranges apart). 4K is void. The miss at 16K decides it.

**Same tests on `strata_bench.py`'s medians and ranges** (reported separately, no void rule):

| arm | chat decode | 4K prompt | 16K prompt | agent decode |
|---|---|---|---|---|
| U | 116.5 (94.6–139.4) | 2393.0 (2298.5–2393.5) | 3176.8 (3097.1–3182.1) | 144.6 (108.4–183.7) |
| H | 89.4 (74.7–120.3) | 2575.3 (2407.7–2633.0) | 3053.3 (2912.5–3058.0) | 92.8 (63.4–115.3) |
| B | 92.3 (83.3–108.8) | 2354.3 (2233.5–2357.0) | 2891.8 (2857.3–2905.7) | 103.4 (72.9–123.5) |

- T1 on the tool: chat decode ranges overlap: no difference shown, **missed**.
- T2 on the tool: 4K holds (H/U 1.08, H's range above U's); 16K H slower (H/U 0.96, ranges apart): **missed**.
  The tool's 4K result matches the reviewer's direction (+14% at 4K on 24 GB); its 16K and our cells do not.

**Read with care:** U's setup on the 3090 chose the DFlash2 drafter (U v0.2.16's Auto rule) and H and B use the MTP
layer, so part of U's decode lead on Tamanna is the drafter, as shipped. **H vs B** (same base engine, both MTP;
descriptive): H decodes slower than B at all three lengths (0.82×, 0.82×, 0.76×, ranges apart); H prefills faster at
4K (1.07×, ranges apart) and slower at 16K (0.90×) and 32K (0.70×). **U vs B:** U is faster on both measures at
16K and 32K (U 4K void).

## Deviations and events, in order

1. **U's first Rushuna pass ran with swap on** and was swapped out (≈4.3 GB swap-out in its first request). Kept as
   `rushuna/U-superseded-swap-on/`. **A1** (written after that one measured request, which it says) sets swap off and
   stops `mycoswarm`, `ollama` (already inactive), `fwupd`, `ModemManager` and the `apt-daily`, `apt-daily-upgrade`,
   `fwupd-refresh` timers on Rushuna for all three arms. `run_arm.sh` refuses to start on Rushuna otherwise
   (`rushuna/U-blocked-guard-0326/`: it stopped once because `ModemManager` was still active). **Restored 2026-11-20
   16:36–16:37 UTC** by Mark (sudo, Rushuna's journal): `swapon -a` (4 GiB `/swap.img` back on), and `mycoswarm`,
   `fwupd`, `ModemManager` and `fwupd-refresh.timer` started (all active after). `ollama` stays inactive, as before A1.
   `apt-daily.timer` and `apt-daily-upgrade.timer` stay off: they have been **masked since 2026-07-15 23:30 UTC**
   (the `/etc/systemd/system/*.timer -> /dev/null` links' timestamps), so they were inactive before the test and A1's
   stop did nothing to them. The pre-A1 state file (`rushuna/U-superseded-swap-on/state-U.txt`) predates the units
   block `run_arm.sh` gained with A1, so it doesn't list them; the mask dates are the evidence. The first restore
   command (16:36:11) also named the two timers, which systemd won't start while masked; a second (16:37:36),
   without them, started the rest and confirmed them active and the timers still masked.
2. **H's and B's `tools/strata_bench.py` (v0.1.45 lineage) crash when they start their own server**
   (`NameError: name 'port' is not defined`; `rushuna/H-aborted-sb-port-bug-0457/`). `harness/sb_prestart.sh` starts
   the arm's own `server.py` from its config (what U's tool does itself), waits for `/health` without "loading",
   runs the tool with the same options as U, then stops the server. Used for H and B on both rigs.
3. **Setup network passes.** H2 asks for downloads first with the network up. Pass a ran offline after the first fetch
   and could not fetch the MTP layer (U warned; H, B failed); pass b, network up, fetched it. U's
   `requirements-monitor.txt` (`textual==8.2.8`) and build tools (`cmake==4.4.3`, `ninja==1.13.2`) were pip-installed
   with the network on; freezes in `rushuna/U/install/pip-freeze-U-*.txt`. Every engine compile still ran with no
   route out, and every setup log says the engine was built, not downloaded.
4. **Void re-runs (H6):** U 32K and B 32K were void on the first pass (prompt_n spread 4, over A1's 3) and valid on
   re-run (`results-ARM-rerun32512.json`). Between B and U's re-run, `after_arm.sh` had deleted U's pack and MTP layer
   (H4); U's setup was re-run (pass a + b) and the chain checked that the engine arguments in U's rebuilt config were
   identical to the scored config before the re-run.
5. **Egress (Rushuna, network up):** whole-machine `ss` watch, excluding ssh (:22) and inbound polls to Mark's
   mycoSwarm daemon (:7890, seen during U's superseded pass before A1 stopped it). Logs: `egress-*.log` per arm.
   No non-loopback line was logged during any scored Rushuna run. H's whole-machine watch loop outlived H's trip (the
   bug fixed in 6c): from 05:28 to 07:24 UTC it logged the later setup passes' downloads (B's and U's re-setup: pip and
   Hugging Face on :443, DNS). Those lines are kept in `rushuna/H/egress-orphan-loop-after-trip-H.log`;
   `rushuna/H/egress-sb-H.log`, the window of H's own attempt (04:58:45–05:00:37), has no lines.
6. **Tamanna, before any measured run (2026-11-20 15:5x UTC):** (a) `run_arm.sh` now runs `sb_prestart.sh` inside a
   single `bwrap --unshare-net`: three separate `bwrap` calls would have put the server, the health check and the tool
   in three network namespaces. (b) `bench_hotrod.py` now also records NVMe reads from first token to the end of the
   request (`nvme_read_decode_mib`), the window H6's Tamanna rule names; the whole-request figure stays beside it.
   (c) `run_arm.sh` kills its egress-watch loop on any exit (a loop survived H's Rushuna trip). (d) For U's 4K
   re-run, `rerun_cell.sh` gained the same optional bwrap argument as `run_arm.sh`.
7. **U's drafter on Tamanna is DFlash2, on Rushuna the MTP layer**: U v0.2.16's Auto rule (`auto_drafter`,
   `drafting.choice_of`) keeps the MTP for IQ3_S on 12 GB cards and picks DFlash2 elsewhere. Both are "as shipped" (H2);
   H and B (v0.1.45 lineage) use the MTP layer on both rigs.
8. **Machine state on Rushuna was taken after its arms** (same UTC day, 15:56): `dd` of shard 1, 8 GiB direct, 2.7
   GB/s. Tamanna's before its arms: 2.4 GB/s.

## Files

- `harness/`: `run_arm.sh`, `sb_prestart.sh`, `after_arm.sh`, `rerun_cell.sh`, `bench_hotrod.py` (+
  `bench_hotrod.diff` against `../tamanna-strata-2026-10-09/bench_strata.py`), `memwatch.py` (unchanged),
  `explore_rss.py` (exploratory only), `summarize.py`, the prompt files and corpus.
- `rushuna/ARM/`: `sequence-ARM.log`, `state-ARM.txt`, `results-ARM*.json`, `out-*`, memwatch and egress logs, server
  logs, `strata-bench-ARM/` (the tool's report), `install/` (setup logs, configs, start script, `BUILD.json`,
  `hashes-ARM.txt` with commit, engine sha256 and pack/MTP hashes). Superseded, blocked, aborted and exploratory runs
  sit in their own folders, named for what they are.
- `tamanna/`: `machine-state-2026-11-20.txt`, `model-sha256.txt`, `chain.log`, one folder per arm.

Engine sha256 (Rushuna build, identical on Tamanna): U `c54f094e…`; H `2beaa875…` (+ `libstrata_kq.so` `4cfc8b7a…`);
B `deed28d0…` (+ `libstrata_kq.so` `2f607024…`).
