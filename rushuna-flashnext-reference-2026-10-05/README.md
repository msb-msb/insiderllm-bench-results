# Qwen3.8-Flash-Next UD-IQ3_XXS on Rushuna, llama.cpp v0.4.0: reference re-run before the copy is deleted — 2026-10-05

PRE-REGISTRATION, written and committed before the first run. Step 2(a) of the Strata-on-Rushuna plan
(`docs/candidates/strata-rushuna-2026-10-05.md`). This is the last run on Rushuna's copy of the Unsloth UD-IQ3_XXS
file before that copy is deleted to make room for the Coder IQ1_M. The Miu store copy stays; its hash is checked
first.

**Model license:** Qwen3.8-Flash-Next is under the **Qwen Community License 1.0**, whatever a quant repo's tag says.

## Method: identical to `../rushuna-flashnext-ncmoe-2026-09-08/`

- Harness `ncmoe_sweep.py rushuna` copied from that record. The only change is the output directory
  (`~/flashnext-reference-2026-10-05`); `diff` shows one line.
- `prompt-2k.txt` copied unchanged.
- Order as in September:
  1. stock server `-ncmoe 48`, 3 reps, with `iostat -dxt nvme0n1 1`;
  2. `llama-bench -ngl 99 -ncmoe N -fa 1 -p 0 -n 128 -d 0,4096 -r 3 -t 4 -lm mmap` for N = 48, 44, 41, 38, three
     invocations each, stopping at the first OOM;
  3. server at the best fit, 3 reps, 2,343-token prompt, n_predict 128, temperature 0, `/proc/diskstats` at start,
     first token and end.
- Engine `~/llama-v0.4.0` (v0.4.0 `5266f24`, CUDA 12.8 bundle, sm_86).
- Model: the three shards in `~/bench-models/qwen3.8-flash-next/`, re-hashed on Rushuna before the run against
  `SHA256SUMS` (`268f81fd…`, `cfe600b2…`, `f1912ba3…`, the 09-08 article's hashes).

## Conditions that differ from September, stated before the run

| | 2026-09-08 | 2026-10-05 |
|---|---|---|
| Ollama | 0.30.0 idle in a tmux, nothing loaded | **systemd service stopped** (20:58:04 UTC, by Mark) |
| Uptime | not recorded | rebooted 05:34 UTC after the 2026-10-04 22:33 PDT mains outage; fsck replayed the ext4 journal, clean |
| Driver | 580.173.02 | 580.173.02 |
| Free disk | 85 GB | 53 GB |
| Page cache at start | not recorded | recorded (`free`, `Cached`) at start |

## What gets compared, decided now

Each figure against its September value: stock tg128 d=0 / d=4096 (8.66 / 10.92), `-ncmoe 41` tg128 d=0 / d=4096
(9.64 / 12.22), OOM point (38), server decode at the best fit (11.11–11.45), settled server prefill (69.5–70.5),
stock server prefill and decode (31.2–41.1 / 8.71–8.90).

- **Within 3%: the September figure stands**, and this record backs it on the current driver and build.
- **Outside 3%: flagged to Mark**, with the delta and these conditions. It is not auto-corrected: the published
  figures came from a different page-cache history on the same box, and this rig's stock server numbers were
  already cache-dependent in September (rep 3 prefill 41.1 against 31.2).

The d=4096 decode is the headline per the September record ("read d=4096 as the decode number on this rig").

## Result: stopped by the stop rule before the first measurement (2026-10-05 21:08 UTC)

The memory watchdog (`memwatch.py`, the stop rule: "if the box starts swapping or the OS has under 2 GB free, stop and report")
tripped **1 second into the stock server's model load**: `swap-out began: pswpout +1 pages`. That was **one 4 KiB page**,
with **MemAvailable 30,734 MiB**, MemFree 331 MiB, Cached 30,631 MiB (`memwatch.log`). The watchdog sent SIGTERM to the
harness; the orphaned `llama-server` was then stopped by PID. By the time it was stopped, swap used was 9 MiB of 4,095.
The card was back to 0 MiB.

No figure was measured. Nothing in this record replaces or backs a September number.

Reading, not a ruling: an mmap load of an 82 GB model into 31 GB of RAM with 30 GB of page cache already full makes
the kernel reclaim memory. It pushed a few idle anonymous pages to swap while the bulk of reclaim came from the page
cache. The September run's swap behaviour was not recorded, so whether this also happened then is unknown. Whether
"starts swapping" means any swap-out or sustained swap traffic is Mark's decision. The watchdog's threshold is not
changed in this record.

Side effect, fixed for the next attempt: `pkill -f ncmoe_sweep.py` also matched the SSH command line that launched the
run, so the launching session died with exit 255. The next attempt launches from a script file, not an inline command.

Precondition for step 2(b) checked the same session: the Miu store copy
(`LLM_repo/qwen3.8-flash-next-gguf/UD-IQ3_XXS/`) hashes to `268f81fd…`, `cfe600b2…`, `f1912ba3…`, matching
`SHA256SUMS`. **Rushuna's copy is not deleted.** Step 2(a) has not produced its reference row yet.

## Attempt 2: stop rule v2 (agreed with Mark 2026-10-05, before attempt 2 ran)

Attempt 1's files are in `attempt1-tripped/` (watchdog v1 as `memwatch-v1.py`). Rule v2, implemented in `memwatch.py`:

- **MemAvailable < 2 GiB at any time: stop.** MemAvailable, not MemFree, because the mmapped model fills "free"
  memory with page cache by design.
- **Swap-out outside model load totalling more than 64 MiB over the run: stop.**
- **Any swap-in outside model load: stop.**
- **Swap during model load is logged and not ruled on.** A load runs from a new `llama-server`/`llama-bench` PID
  until the card's memory.used has grown ≤64 MiB across 3 samples (6 s).
- Killing is by PID and exact process name (`pkill -x`), never `-f`. Launch goes through `run.sh`.

**Counters recorded for future comparison** (September recorded none): every 2 s in `memwatch.log` (MemAvailable,
MemFree, Cached, swap used, swap-in/out KiB, phase, card MiB), and per phase in `memwatch-summary.json` (swap-in and
swap-out totals for load / measured / idle, min MemAvailable, max swap used, min/max Cached). The start state is
in `conditions-at-start.txt`, including the cumulative `pswpin`/`pswpout`.

Note for comparability: attempt 1 left ~9 MiB in swap and the model's pages in the page cache. Attempt 2 starts from
that state, recorded in `conditions-at-start.txt`.

## Attempt 2: tripped by a watchdog bug (2026-10-05 21:24 UTC), files in `attempt2-tripped/`

14 s in, still inside the stock server's model load, a 20 KiB swap-in was ruled on as "measured". The v2 detector
ended the load when the card's memory stopped growing, but the card sat at the ~113 MiB CUDA-context plateau while
the mmap loader was still reading the file. The counters were recorded:
- during load: 23,440 KiB swapped out, 0 in;
- during the misclassified "measured" seconds: 11,012 KiB out, 20 KiB in;
- MemAvailable never below 30,631 MiB; swap used peaked at 41 MiB.

**v2.1 (the rule is unchanged, only the detector):** a load ends only once the card holds more than 1,024 MiB and has
grown ≤64 MiB across 3 samples. Attempt 3 runs with it; the cumulative swap state at its start is in
`conditions-at-start.txt`.

## Attempt 3: stopped by the stop rule, a genuine trip (2026-10-05 21:26 UTC), files in `attempt3-tripped/`

- The stock server (`-ncmoe 48`, mmap) loaded in 14.7 s: RSS 29,601 MiB, card 4,825 MiB, Cached 30,657 MiB.
- 8 s into the first measured request (the 2,343-token prefill), **8,908 KiB swapped in within one 2-second
  sample**. That trips rule v2.1. MemAvailable never fell below 30,187 MiB, so the 2 GiB floor was never close.

| phase | swapped out | swapped in |
|---|---:|---:|
| load | 22,856 KiB | 1,300 KiB |
| measured, before the trip | 15,048 KiB | 8,908 KiB |

- Swap used peaked at 77 MiB in the samples. After the trip it read about 740 MiB.
- **Whose pages:** per-process `VmSwap` just after the trip: **`llama-server` 633,088 kB**, `mycoswarm` 49,780 kB,
  `fwupd` 6,504 kB, the rest under 3.3 MB each. `vm.swappiness` is 60.
- So the stock config on this box pushes the process under test's own anonymous memory into swap while the mmap'd
  82 GB file churns through 30 GB of page cache, then faults it back during the prefill.
- September did not record swap, so whether its stock figures (prefill 31.2–41.1, decode 8.71–8.90) included
  swap-in time is **unknown**.

No figure was measured.

**Watchdog note:** the SIGTERM did not stop `llama-server`. It treated the signal as "cancel task" and kept the
model resident, and it was stopped by PID afterwards. `memwatch.py` now follows with SIGKILL after 10 s.

**Stopped here, per the rule. Step 2(b) not done** (Rushuna's copy kept). Decision needed from Mark, below in the
session report.

## Attempt 4: swap allowed, counted and published (Mark's decision, 2026-10-05, before attempt 4 ran)

**The stock config swaps on a 32 GB box.** Run as published (`-ncmoe 48`, mmap, 31 GiB RAM, 4 GiB swap,
`vm.swappiness` 60), loading and prefilling the 82 GB model pushes the llama-server process's own memory into swap
and faults it back during measurement (attempt 3). **September's run did not record swap, so its figures may include
swap time.** That holds for the stock rows (prefill 31.2–41.1, decode 8.71–8.90) and is possible for the others.

Rule for attempt 4: **only MemAvailable < 2 GiB stops the run.** Swap is not a stop condition. It is counted every
2 s (`memwatch.log`) and per phase (`memwatch-summary.json`), and the swap-in/swap-out inside each measured server
request window is reported beside its speed figures below. `memwatch.py --count-swap` (v3).

**Left running, as Mark asked: the `mycoswarm` daemon** (PID 982, polling five LAN peers' `/health` every few
seconds). It held 49,780 kB in swap after attempt 3, so some of the swap traffic counted here is its, not the
model's. Per-process `VmSwap` is sampled at the end of the run to show the split.

## Attempt 4: RUN AND COMPLETE (2026-10-05 21:30–22:00 UTC), swap counted

Never tripped. MemAvailable minimum **30,088 MiB**; swap used peaked at **870 MiB** of 4,095. Whole-run swap
(`memwatch-summary.json`):

| phase | swapped out | swapped in |
|---|---:|---:|
| load (12 loads) | 1,971 MiB | 413 MiB |
| measured | 2,030 MiB | 1,250 MiB |
| idle between loads | 0 | 352 MiB |

Per-process `VmSwap` at the end (`end-snapshot.txt`): `mycoswarm` 64,280 kB, `fwupd` 6,500 kB, the rest under
3.3 MB. The llama processes had exited, so the bulk of the swap traffic was theirs.

### llama-bench, `-lm mmap`, 4 threads, mean of 3 invocations [min..max], against 09-08

| -ncmoe | tg128 d=0 | 09-08 | delta | tg128 d=4096 | 09-08 | delta | swap out / in over the 3 invocations |
|---:|---|---:|---:|---|---:|---:|---|
| 48 (stock) | 8.68 [8.65..8.74] | 8.66 | +0.3% | 10.93 [10.89..10.98] | 10.92 | +0.1% | 839 / 438 MiB |
| 44 | 9.16 [9.12..9.19] | 9.22 | −0.7% | 11.59 [11.57..11.61] | 11.65 | −0.5% | 635 / 384 MiB |
| 41 | 9.58 [9.50..9.68] | 9.64 | −0.7% | 12.14 [12.12..12.17] | 12.22 | −0.6% | 659 / 334 MiB |
| 38 | fails to load (same llama-bench output as 09-08) | OOM | same | | | | |

**All six decode cells within 0.7%.** The September figures stand and this record backs them on driver 580.173.02,
with the swap now counted.

### Server, 2,343-token prompt, 3 reps (swap out / in in each request's window, from `memwatch.log`)

| config | rep | prefill | decode | NVMe read, prefill | swap out / in |
|---|---:|---:|---:|---:|---|
| stock `-ncmoe 48` | 1 | 29.1 | 8.60 | 70,814 MiB | 520 / 157 MiB |
| | 2 | 39.0 | 8.41 | 31,626 MiB | 144 / 137 MiB |
| | 3 | 39.3 | 8.63 | 29,541 MiB | 136 / 135 MiB |
| best `-ncmoe 41` | 1 | 41.9 | 11.18 | 35,199 MiB | 453 / 89 MiB |
| | 2 | 70.5 | 11.90 | 5,831 MiB | 28 / 47 MiB |
| | 3 | 69.4 | 11.35 | 5,879 MiB | 119 / 57 MiB |

Against 09-08:
- **Best-fit server:** settled prefill 69.4–70.5 against 69.5–70.5, so it stands. Decode mean 11.48 against
  11.27 (+1.8%), with rep 2 (11.90) above September's range.
- **Stock server decode:** mean 8.55 against 8.78, **−2.6%**, within 3%.
- **Flagged: stock server prefill, outside 3% per rep.** Rep 1 read 29.1 against September's 31.2 (−6.7%). Reps 2–3
  read 39.0/39.3 where September read 31.8 then 41.1. Both runs show the stock prefill depending on what the previous
  request left in a 30 GB cache, so the published "31–41 tok/s" range still covers this run (29.1–39.3 overlaps
  it), but the low end is 2 tok/s lower. Not auto-corrected, per the pre-registration.

**Every measured server request swapped in, 47–157 MiB each.** Stock config: 135–157 MiB per request. This is the
condition the attempt-3 note describes, now counted: on a 32 GB box the stock config swaps during measurement.
September's figures were very likely made the same way, unrecorded.
