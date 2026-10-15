# power-01: board-level energy per token, S3 and P4 (USB power logger; inline meter as a cross-check)

## Checklist for 2026-10-13 (Mark's order, decided 2026-10-12 evening)

- [x] **a. Sim check:** `firmware/build.sh --sim`, flash it to the RP2040, then `host/pl.py id`, and
      `host/pl.py record --tag simcheck --secs 25`. That checks USB, framing and analysis end to end.
- [x] **b. Mark builds the perfboard,** including the INA226 ALERT → GP6 wire.
- [x] **c. Real logger firmware** (`firmware/build.sh`):
  - identity check (`pl.py id`: mfr 0x5449, die 0x2260; `pl.py config`: cal 2048, `mode=alert`);
  - zero offset, then calibration per `tools/power-logger/CALIBRATION.md`. **Pass: residual ≤ 0.5% of reading at
    25–200 mA.** Commit `calibration.json` on `power-logger`.
  Done 2026-10-13: PASS, residuals ≤ 0.12% (power-logger `53f5326`; `tools/power-logger/CALIBRATION_NOTES.md`).
- [ ] **d. Sync-build verification** (decision 1 below). Build B+sync, D+sync and P4 IA1+sync. On each board, with
      the sync pin active (wired to the logger):
  - the greedy output (prompt 433 447 259 405, N = 200, t = 0, seed 42) hashes **identical** to the non-sync build's;
  - median ms/token is **within 1%** of the recorded figure for that build (B 32.7, D 25.8, P4 13.7);
  - the logger sees exactly one sync window per generation;
  - record the new app hashes in the table below.
  **If any check fails: stop and tell Mark.**
  **S3 B+sync: done 2026-10-13** (Mark: "step d is done"), with the ms/token reference deviation below.
  **S3 D+sync: done 2026-10-14**, all checks pass against the pre-committed reference (session 2026-10-14 below).
  **P4 IA1+sync: done 2026-10-14**, all checks pass against the pre-committed reference (P4 phase below).
- [ ] **e. power-01 runs in the agreed order** (below). Write and lock the PREREG after all idle runs, before any
      generate run.
  - **SUPERSEDED (Mark, 2026-10-14): they don't meet the locked idle definition.** They ran ~9 min after step d's
    generations, with no reset. The data stays in runs.jsonl and `logs/B_idle_{1,2,3}.*`. B is rerun as
    `B_idle_{1,2,3}r` (reflash B+sync, `--reset`).
    Original record: **S3 B+sync idle ×3: done 2026-10-13 21:13–21:33,** all reps pass acceptance (`runs.jsonl`). Mean
    0.20486 / 0.20478 / 0.20448 W, 300.05 s windows, host vs fw 0.0000%, 0 drops, 0 late conversions, 0 sync
    windows. Each plot ends in one short spike to ~0.22 W, which is the end-of-run `?` ping.

## Session 2026-10-14

- **Logger moved** to Miu's rear USB port (Mark). Its by-id is unchanged
  (`usb-Raspberry_Pi_PowerLogger_E66038B7130A6739-if00`).
- **Session-start 1x100 recheck: PASS.** −6.26% raw (10-13: −6.266%), −0.01% calibrated (DMM 51.03 mA, logger
  51.025 mA calibrated; limit 0.5%). No recalibration.
  - **Two entry errors fixed in `calibration_points.jsonl`** (power-logger; Mark's instructions).
    - The 51.03 mA point was entered as "3x100 parallel", 33.05 Ω. It is the recheck on 1x100, 98.60 Ω, and has
      been relabelled.
    - A first row labelled "1x100 recheck 10-14" read DMM 21.09 µA against 26.42 mA raw. It is kept, but tagged
      `exclude_from_fit`: "DMM entry error at recheck 10-14, load and units mislabelled".
- **Non-sync D flashed** 11:00, app `7641a0f2…5677`. All 4 images were written and hash-verified.
  - esptool's RTS hard reset after the write raised `OSError: [Errno 71] Protocol error`, and so did one
    `chat.Board(reset=True)`. The port drops as the chip resets. The board then answered
    `R ready … prefill_skip=1 fast_sample=1` (`logs/flash_D.txt`, `logs/D_boot.serial.log`).
  - The GPIO4 → V12 jumper was off; GND → V13 stayed on.
- **Step d reference for D (rule above): 26.305 ms/token.**
  - **Run:** non-sync D, 3 greedy gens through the logger (`logs/stepd_D_ref_nosync3.*`, not in runs.jsonl).
  - **Per gen:** 26.308 / 26.301 / 26.305 ms/token; ttft 36.57–36.60 ms.
  - **Output hash:** `b2782783…` on all 3, the same as B.
  - **Logger:** 20.7 s, 8.157 J, host vs fw 0.0000%, 0 drops, 0 late conversions, 0 edges.
  - **Benchmark comparison (reported, not the step d reference):** 26.305 is +2.0% against the 25.8 benchmark,
    within the 3% run gate.
- **D+sync built** 11:01, flashed 11:02.
  - **Build:** `-DSYNC_GPIO=4`, .ino `ea055c35…` (as B+sync), patch `ea5922bc…`, 375,125 B (`logs/build_Dsync.txt`).
  - **App:** `cf2ff730cd0392b673fc2d25fa357092586f95e02df9269be24566cfafbf1a9d`.
  - **Flash:** write verified, clean reset, board answers its ready line (`logs/flash_Dsync.txt`).
- **GPIO4 → V12 jumper reconnected** (Mark). 5 s idle capture: 0 edges, 0 sync windows, 0.2071 W, host vs fw
  0.0000%, 0 drops (`logs/stepd_Dsync_idle5.power`; no PNG, the plot step got a relative path).
- **Step d check, S3 D+sync: PASS** (`logs/stepd_Dsync_sync3.*`, not in runs.jsonl). The same workload as B's check.
  - **ms/token:** 26.316 / 26.307 / 26.308, median 26.308. That is **+0.01% against the 26.305 reference** (limit 1%).
  - **Output hash:** `b2782783…` on all 3, identical to non-sync D.
  - **Sync windows:** 3 windows for 3 generations, exactly 6 edges (1,0,1,0,1,0), no bounce.
  - **Window length:** 5.506–5.510 s, against the S3's own ~5.298 s (ttft + ms/token × n). The ~0.21 s difference
    (~1.05 ms/token) matches B's (J/token definition above).
  - **Energy:** 2.4375–2.4400 J per window, mean 0.443 W. J/token 12.19 mJ (sync windows), 13.72 mJ (whole run).
  - **Logger:** host vs fw 0.0000%, 0 drops, 0 late conversions, 0 bus errors, 0 gaps.
- **S3 D+sync idle rep 1: FAILED acceptance** (11:39–11:44; `logs/D_idle_1.*`, in runs.jsonl). The script
  stopped there, and reps 2–3 were not run.
  - **11 sync windows in an idle run** (acceptance: 0). Each is a rise and fall with the same timestamp, so the
    duration and energy are 0. They are irregular: 12, 121, 124.3, 124.6, 197, 197.0, 219, 241, 274, 296 and 300 s
    into the window. No `G` was sent, and the firmware only drives GPIO4 high on `G`.
    - **They don't line up with any load change:** current stays at 42.4 mA within ±50 ms of each edge.
    - **So this looks like sub-µs glitches picked up on the V12 line,** not the DUT driving it. The step d check
      (20.7 s) and the 5 s idle capture before it had none.
  - **Idle current is up 1.5 mA.**
    - **Logger checks otherwise pass:** host vs fw 0.0000%, 0 drops, 0 late conversions, 0 gaps.
    - **D_idle_1:** 0.2147 W, 42.38 mA at 5.066 V, flat for the whole 300 s (each 30 s bin 42.37–42.40 mA).
    - **Earlier today:** 40.86–40.87 mA at 11:00–11:07 (non-sync D, the idle before its gens; D+sync 5 s idle).
    - **B+sync idle, 10-13:** 40.37–40.43 mA.
    - It is within the 0.19–0.23 W acceptance band but unexplained.
- **Glitch rule (Mark, 2026-10-14, pre-committed before any rerun or generate run; also in `PREREG_DRAFT.md`).**
  > "sync windows shorter than 10 ms are discarded as glitches (counted and reported, excluded from window
  > pairing). Real windows are ≥ 0.5 s. Apply to all runs, including re-analysis of D_idle_1 (report what it
  > gives, but rerun the rep anyway)."
  - **Code:** power-logger `powerlog/analysis.py` `summarize()` puts windows < 10 ms (`GLITCH_MAX_S`) into
    `sync_glitches` instead of `sync_windows`, so `joules_per_token` never sees them.
    - The bounce test was updated: a zero-length window is now a glitch. 37/37 tests pass.
    - `run.py` records `sync_glitches` in runs.jsonl.
  - **Not covered:** a glitch *during* a real window would show up as a fall + rise. It would split that window
    into two windows ≥ 10 ms. The 1:1 pairing check would then refuse (a count mismatch), so it fails loudly, not
    silently.
  - **D_idle_1 re-analysed** (`logs/D_idle_1.reanalysis_glitch_rule.json`; the original summary.json is kept):
    0 sync windows, 11 glitches (all 0 s). Every other figure is unchanged, so under the rule it would pass on
    sync. **It is rerun anyway** (Mark).
- **Idle definition: pending diagnosis** (Mark's default: "idle = fresh reset, before any G").
- **Idle diagnosis** (Mark, 2026-10-14, ~12:00–12:05; `logs/idlediag.*`, `logs/idlediag_A_reset.power`,
  `logs/idlediag_B_afterG.power`; not in runs.jsonl). D+sync, jumper on.
  - **Reset:** an RTS pulse. The port drops during it (`Errno 71`). The boot log proves the reset (fp=a9bdd778,
    `R ready` 2.9 s after the pulse).

  | Capture | Mean current | Per 10 s | Power | Glitches |
  |---|---|---|---|---|
  | 60 s after a fresh reset, before any G | **41.53 mA** | 41.51–41.55 | 0.2104 W | 6 |
  | the same, aborted first attempt ~1.5 min earlier (`logs/idlediag_try1/`; the script crashed after this capture, before any G) | 41.56 mA | 41.54–41.57 | | 6 |
  | 60 s, starting 10 s after one `G n=20` (t=0, seed 42) | **42.11 mA** | 42.10–42.12 | 0.2133 W | 9 |
  | for comparison: D_idle_1, after step d's 3 × 200-token gens | 42.38 mA | 42.37–42.40 | 0.2147 W | 11 in 300 s |
  | for comparison: fresh flash, before any G (11:00–11:07) | 40.86–40.87 mA | | 0.207 W | 0 in 5 s |

  - **After a reset, before any G:** 41.5 mA. **Not back to ~40.9** (+0.67 mA against the 11:00–11:07 readings).
  - **After one G:** it rises by 0.58 mA to 42.11 and stays flat for 60 s; it does not decay like heat would.
    After 3 × 200-token gens it was 42.38 (D_idle_1), also flat over 300 s.
  - **Glitch rate is up:** 6, 6 and 9 per 60 s now, against 11 in 300 s in D_idle_1. There were 0 in the 5 s idle and
    in the 20.7 s step d check.
  - The `G n=20` gave 17.6 ms/token (short context; not comparable to the 200-token figure).
- **Idle definition locked** (Mark, 2026-10-14; also `PREREG_DRAFT.md` item 4):
  > "Primary idle = 300 s after a fresh S3 reset, before any G (reset before each rep). Headline metric = window J/token (gross). Any net-of-idle figure is secondary and carries the measured idle spread (40.9–42.4 mA observed 10-14) as uncertainty. Post-generation idle is reported from the inter-generation gaps of the generate runs."
  - **Suspected idle-drift factor: ambient temperature** (not measured). Fresh-boot idle went from 40.86 mA
    (11:00) to 41.53 mA (12:00) with nothing else changed that we know of.
- **RC filter on the sync line** (Mark): 1 kΩ in series from S3 GPIO4 to V12, 1 nF from V12 to V13. The time
  constant is 1 µs. The board was re-powered.
- **RC filter check: PASS** (`logs/rcverify.*`, not in runs.jsonl).
  - **Fresh reset:** the boot banner was seen and `R ready` came 2.9 s after the pulse.
  - **60 s idle:** 0 edges, 0 glitches, 0 windows. **40.57 mA**, 0.2056 W: the first reading after the re-power, the
    lowest fresh-boot idle today. Host vs fw 0.0000%, 0 drops.
  - **One `G n=20`:** exactly 2 edges (1,0), 1 window, 0 glitches.
    - **Window length:** 0.4099 s, against the board's own 0.3885 s (ttft 36.62 ms + 17.596 ms/token × 20). That is
      +1.07 ms/token, against +1.04–1.05 at step d (N=200, before the filter). Unchanged, as expected from the
      ~1 µs time constant.
    - **Energy:** 0.1845 J, 0.450 W.
    - **Wording fixed (Mark, 2026-10-14):** the PREREG now reads "real windows ≥ 0.4 s at the smallest N used".
    - **This window is 0.41 s,** under the "≥ 0.5 s" in the glitch rule's wording. "Real windows are ≥ 0.5 s" holds
      for N=200 generations, not for this check. The 10 ms threshold still separates the two cleanly.
- **`run.py --reset`** (needed for the idle definition) does a fresh reset before the window:
  - an RTS pulse, tolerating the port drop;
  - it then requires a boot banner (fp=) logged after the pulse, or the run exits;
  - it records `reset.boot_seen` in runs.jsonl.

  `--suffix` gives a rerun its own tag (the reruns are `D_idle_{1,2,3}r`, so the failed `D_idle_1` keeps its logs).
- **S3 D+sync idle ×3 rerun (fresh reset before each rep): STOPPED at rep 2r.**
  - **Rep 1r: PASS** (12:12–12:17; runs.jsonl).
    - **Power:** 0.20671 W, 40.79 mA at 5.067 V, 300.0 s.
    - **Checks:** 0 sync windows, 0 glitches; host vs fw 0.0000%; 0 drops, 0 late conversions, 0 bus errors,
      0 gaps; boot seen after the reset.
  - **Rep 2r: FAILED.** The board didn't answer the end-of-window `?`.
    - **What ran normally:** the reset and boot (banner and `R ready` logged) and the 300 s window.
    - **The failure:** at 12:24:25 the end-of-window `?` got no `R` line within 10 s. `run.py` exited
      ("board did not answer with an R line"), so nothing went into runs.jsonl and the logger run has no final
      snapshot (`logs/lost_ping/D_idle_2r.power/raw.bin` only).
    - **The board was fine:**
      - From raw.bin, the window drew 40.83 mA flat (each 20 s bin 40.80–40.85), 0.2069 W, 0 edges. Nothing in it
        looks like a crash or reboot.
      - It answered a ping right after (`logs/lost_ping/D_idle_2r_postcheck.serial.log`).
    - **Cause unknown.** The fault is on the host↔S3 USB-serial side; the kernel log can't be read without root.
    - **Run 1r looked the same:** its end ping got its answer, logged 0.2 ms after the ping.
  - Rep 3r and B idle ×3 were not run.
  - **D_idle_2r was lost to a missed ping** (Mark, 2026-10-14). The board was alive afterwards and the current was
    flat at 40.80–40.85 mA. The logger snapshot can't be recovered, so the rep is rerun. The lost attempt's logs
    were moved to `logs/lost_ping/` so the rerun can use the `D_idle_2r` tag.
  - **If missed pings recur,** log the time since port open, to see whether it's an idle-USB issue. `run.py`
    now records it on every ping attempt (`port_open_s`).
- **`run.py` end-of-window handling** (Mark's option b, 2026-10-14):
  1. A missed end-of-window ping reopens the port and retries: up to 3 tries in all, ~5 s apart. Each attempt is
     recorded in `ping_attempts` (time, port_open_s, reopened, ok/error), with `ping_ok`.
  2. The logger run is always finalized (final snapshot, host-vs-firmware check, summary) and the runs.jsonl record
     is always written, in a `finally` block, whether or not the window or the ping succeeded.
  3. If the ping still fails, the rep is recorded with `status: "FAILED (liveness unconfirmed)"`. Its data is kept
     and `run.py` exits non-zero. An aborted window is recorded the same way, as `FAILED (window aborted: …)`.

  The retry logic was checked with a mock board: it succeeds first time, succeeds on the 3rd try after 2 port
  reopens, and fails after 3 tries.
- **S3 D+sync idle 2r, 3r: PASS** (12:35–12:48). Both end pings answered on the 1st try, after the port had been
  open 300.1 s. **D+sync idle ×3 per the locked definition is complete: 1r, 2r, 3r.**
- **B+sync reflashed** 12:48, app `06abb9ad…5f8`; the on-disk hash was checked before the flash.
  - **Flash:** bootloader, boot_app0 and app (372,688 B) were written and hash-verified. The partition table was
    unchanged, so esptool skipped the write and verified it in place. My script expected 4 "Hash of data
    verified" lines, saw 3 and stopped. That was a false stop: all 4 regions were verified.
  - The board answered `R ready` (`logs/Bsync_1014_boot.serial.log`; `logs/flash_Bsync_1014.txt`).
- **S3 B+sync idle 1r–3r: PASS** (12:48–13:08). All end pings answered on the 1st try.
- **Idle ×3 per the locked definition** (fresh reset before each rep, 300.0 s windows; runs.jsonl). The calibrated
  current is the mean of the samples:

  | Rep | D+sync (`cf2ff730…`) | B+sync (`06abb9ad…`) |
  |---|---|---|
  | 1r | 0.20671 W, 40.79 mA, 5.067 V, 62.02 J (12:12) | 0.20401 W, 40.23 mA, 5.071 V, 61.21 J (12:48) |
  | 2r | 0.20725 W, 40.89 mA, 5.069 V, 62.19 J (12:35) | 0.20411 W, 40.25 mA, 5.071 V, 61.24 J (12:55) |
  | 3r | 0.20725 W, 40.88 mA, 5.070 V, 62.19 J (12:42) | 0.20413 W, 40.25 mA, 5.071 V, 61.24 J (13:03) |
  | mean | **0.20707 W** (spread 0.26%) | **0.20408 W** (spread 0.06%) |

  - **Checks on all 6 reps:** boot seen after the reset; host vs fw 0.0000%; 0 drops, 0 late conversions, 0 bus
    errors, 0 gaps; 0 sync windows, 0 glitches; the app hash matches.
  - **D − B = +2.99 mW (+1.5%), about +0.6 mA.** D's libs run flash and PSRAM at 120 MHz, against B's 80 MHz.
  - **B 10-13 (superseded: no reset, ~9 min after gens) averaged 0.20471 W.** The rerun is −0.3%, about 0.15 mA
    lower.
  - **D_idle_1r has no `ping_attempts`.** It ran before the retry change; its end ping answered on the old code
    (serial log).

### App hashes

| Build | Non-sync app sha256 (v1) | Sync app sha256 | Output hash: non-sync = sync? | ms/token (sync) vs recorded |
|---|---|---|---|---|
| S3 B | `907ef81e…` | `06abb9ad…` (see below) | `b2782783…` on all 3 sync generations; the same greedy hash as earlier evals (`interactive-01/p2.csv`, `sample-accuracy-01/profile_b.csv`); no non-sync B run with full ids on record | 33.40 / 32.7 (+2.1%); **vs same-bench non-sync B 33.40: 0.0%** (deviation 1) |
| S3 D | `7641a0f2…` | `cf2ff730…` | **yes:** `b2782783…` on 3 non-sync and 3 sync gens (10-14) | 26.308 / 25.8 (+2.0%); **vs same-bench non-sync D 26.305: +0.01%** (pre-committed rule) |
| P4 IA1 | `f6f9caf7…` | `38299f17…` | **yes:** `b2782783…` on 3 non-sync and 3 sync gens (10-14; same as the S3) | 13.577 / 13.7 (−0.9%); **vs same-bench non-sync IA1 13.623: −0.34%** (pre-committed rule) |

**S3 B+sync** `06abb9ada33896db6f2f07adcbeed03ff45e50473009aab470f35f2af581f8f8`: built 2026-10-13, .ino
`ea055c35…`, patch `ea5922bc…` (power-logger `dut/s3-sync-gpio.patch`); flashed 20:53, write verified, boots
fp=a9bdd778. It replaces `5f68c8a3…` (flashed 20:39, never used for a run). That build left GPIO4 an undriven input
until the first `G`. With the jumper on, the pin sat at 0.945 V against the logger's pull-down (Mark's DMM), so GP15
chattered (~35k edges/s, frames dropped). The new patch drives GPIO4 low from the start of `setup()`.

**Step d check, S3 B+sync** (2026-10-13; `logs/stepd_Bsync_sync3.*`, not in runs.jsonl):
- **Idle, 5 s:** 0 edges, sync 0, 0 drops.
- **Workload:** 3 greedy generations (prompt 433 447 259 405, N=200, t=0, seed 42).
- **Sync windows:** 3 windows for 3 generations, exactly 6 edges, no bounce.
- **Window length:** 6.942–6.948 s, against the S3's own 6.726–6.728 s (ttft + ms/token × n).
- **Energy:** 2.874–2.876 J per window. J/token 14.37 mJ (sync windows) and 15.85 mJ (whole run).
- **Logger checks:** host vs firmware 0.0000%, 0 drops, 0 late conversions.
- **Wiring:** S3 GPIO4 → V12 (GP15), plus S3 GND → V13. The first attempt had the jumper on the wrong S3 pin.

**Deviations from the plan**
1. **Step d's ms/token reference for S3 B is 33.40, not 32.7.**
   - **Figures:** the benchmark is 32.7; the non-sync B on this bench (through the meter, 13 generations, v1
     notes below) gave 33.40. B+sync gave 33.40, which is +2.1% against the benchmark and 0.0% against the
     same-bench figure.
   - **Chosen after seeing the result** (Mark, 2026-10-13).
   - **Why:** the check measures the sync pin's cost. The like-for-like comparison is the non-sync build on the
     same bench, and on that comparison the sync pin costs 0.0%.
   - **Unchanged:** the 3% run gate still uses 32.7 (33.40 is within it).

**Open items**
- The 32.7 benchmark vs 33.40 same-bench difference (+2.1%, non-sync B) is unexplained.
- **P4 sync patches are out of step** with the revised S3 patch:
  - `p4-extract-sync-gpio.patch`'s line ranges are now off: −2 lines, and the new `setup()` line shifts them too.
  - Regenerate them before building P4 IA1+sync, and drive GPIO6 low from boot, as on the S3.
- **"Identical object code with SYNC off"** has not been rechecked for the revised S3 patch.

**DUT sync pins:** S3 **GPIO4**, P4 **GPIO6** (header P1 pin 10).
- **Why not GPIO2 on the P4:** Waveshare's schematic shows it broken out (P1 pin 15) and otherwise unused, but it
  comes out of reset with a 45 kΩ pull-up (the pad-JTAG MTCK default). That fights the logger's pull-down until the
  first `G`.
- **GPIO6:** chip pin to header only, no strap or flash function, no default pull.
- Details: `tools/power-logger/dut/README.md`.


## Protocol v2 (2026-10-12 evening): the USB power logger replaces the meter as the instrument

The cheap meter doesn't accumulate below a current threshold somewhere between 0.03 and 0.07 A (so S3 idle was unmeasurable), its W reading disagreed
with V × A, and it is read by eye. power-01 now measures with **tools/power-logger**: an INA226 (R100 shunt)
high side on VBUS between USB-A breakouts, on an RP2040 streaming every sample to Miu.

- **Logger facts:**
  - 806 samples/s, 25 µA and 1.25 mV per count;
  - energy integrated on the RP2040 and independently on the host (they must agree within 0.5%);
  - a sync input timestamps each generation.
- **Documentation:** `tools/power-logger/README.md`. The logger is on Miu's other USB port; branch `power-logger`.
- **Hardware arrives 2026-10-13.** Before any power-01 run:
  1. Flash the logger, then `pl.py id` / `config` (the identity check: mfr 0x5449, die 0x2260).
  2. Calibrate per `tools/power-logger/CALIBRATION.md` (DMM in series; pass = residual ≤ 0.5% of reading at
     25–200 mA). `host/calibration.json` then exists and every run records it.
- **The cheap meter stays inline for one cross-check run per board,** as Miu → meter → logger → DUT, marked
  `--meter`. Mark reads mWh and t with fresh start and end readings, as in the v1 protocol below. RESULTS
  compares the meter's Δenergy with the logger's energy over the same window, plus the hand-off gaps at the
  logger's idle power. It is a sanity check, not the measurement.
- **Board-level:** the logger measures everything on the USB cable. Never call results chip power (unchanged).

### What a run is now

- **Command:** `esp32-ai/.venv/bin/python evals/power-01/run.py gen|idle --board s3|p4 --build B|D|P4 --rep N
  --app-sha <flashed app sha256> [--meter]`.
- **Sequence:** it opens the logger (discovery never opens a bench board's port), then the DUT. It starts a
  logger run (firmware accumulator reset) and runs the 5-minute window exactly as v1 did (same workload,
  gens.csv, 3% gate), then stops the logger.
- **runs.jsonl** gets a `logger` block: firmware and host energy, their agreement, mean power, duration,
  samples, rate, dropped frames, late conversions, gaps and sync windows. In gen mode it also gets
  `j_per_token`:
  - `J_per_token_sync`: energy inside the sync-high windows over tokens, i.e. the generation itself. A sync window
    spans the whole generation loop: the forward passes, sampling and serial output, from just before the
    prefill to just after the last token. That's about 1.1 ms/token (~216 ms per 200 tokens on S3 B) beyond the
    S3's own forward-pass timing (`decode_ms_per_tok`), and J/token is computed over that whole window;
  - `J_per_token_whole_run`: the whole window over tokens, including host turnaround;
  - the per-generation min and max.
  Windows are paired 1:1 with gens.csv rows, and a count mismatch refuses to pair.
- **Raw frames, meta and power.png** go to `logs/<tag>.power/`.
- **Idle** is now measured like any other window: mean power from the logger. The sub-threshold problem is
  gone, and so are the minute-by-minute W/V/A readings.
- **Per-run acceptance:**
  - host vs firmware ≤ 0.5%;
  - dropped frames 0, or a few, each listed in gaps;
  - late conversions 0;
  - sync windows = generations;
  - the plot shows the workload.
  Anything else: stop and report.

### Decisions (Mark, 2026-10-12 evening)

1. **Sync builds: yes.** Flash **B+sync, D+sync and P4 IA1+sync**, each verified first (checklist step d): output
   hash identical to the non-sync build, ms/token within 1%. New app hashes go in the table above, next to the
   old ones. Any failure: stop and tell Mark.
   - With SYNC_GPIO unset, the patch compiles to identical object code. With it set, it adds two
     `digitalWrite`s outside the timed region. The 3% run gate still applies to every run.
2. **P4 sync pin:** checked against Waveshare's schematic. GPIO2 was replaced by **GPIO6** (see the checklist).
3. **Cross-check:** one **generate** run per board with the cheap meter inline (`--meter`).
4. **PREREG:**
   - **Instrument:** the logger (power-logger commit hash), its firmware build (`PL_SRC_SHA` and the flashed
     .uf2's sha256), and `host/calibration.json` (sha256), plus the acceptance checks above.
   - **J/token definition:** energy inside the sync windows ÷ tokens. A window spans the whole generation loop
     (forward passes, sampling and serial output; ~1.1 ms/token beyond the board's own forward timing), not
     just the timed forward passes.
   - **P1–P5:** verbatim.
   - **When:** written and locked (sha256 and timestamp) after all idle runs and before any generate run.

### Step d ms/token reference for D and P4 (Mark, 2026-10-13, pre-committed before any D or P4 data)

> "D's same-bench ms/token reference = non-sync D measured through the logger in this setup: flash non-sync D,
> 3 greedy gens (same prompt/N/seed as B's check), median ms/token. Then flash D+sync and run step d against that
> number, 1% limit. If a same-bench non-sync D figure already exists in NOTES v1, report it alongside but the
> direct measurement is the reference."

- **The same rule applies to P4 IA1:** first non-sync IA1 (`f6f9caf7…`) through the logger, 3 greedy gens, median
  ms/token; then IA1+sync against that, 1% limit.
- **No v1 same-bench figure exists for either.** D was compiled but never flashed in v1, and v1 never got to the P4.
  The benchmark figures (D 25.8, P4 13.7) still apply to the 3% run gate.
- **The B reference** was chosen after its result was seen (deviation 1 above). These were fixed before any D or P4
  measurement.

### Run order (v2, agreed)

0. Checklist a–d above (logger sim check, perfboard, real firmware and calibration, sync-build verification).
1. S3: flash B+sync (verified hash), idle ×3. Then flash D+sync, idle ×3.
2. P4: flash IA1+sync (verified hash), idle ×3.
3. **Write and lock the PREREG.**
4. P4 gen ×3, one of them `--meter`.
5. S3 D+sync gen ×3. Then restore B+sync and confirm its hash. Then B+sync gen ×3, one of them `--meter`.

---

## (v1, superseded) Status: PAUSED 2026-10-12 ~11:30, resume 2026-10-13

- **Why paused:** the meter is plugged straight into a USB-A port on Miu, upside down with the screen facing away,
  and is too hard to read. Mark is getting a USB-A extension cable.
- **Completed runs: none.**
  - S3-B idle run 1 was started at 11:19:46. It was stopped at about 11:21, because the meter's `t` was not
    counting.
  - That attempt is logged only as aborted (`readings.jsonl`), and nothing went into `runs.jsonl`.
- **PREREG: not yet written.** Per the brief, it is written after step 0 and the IDLE runs, before any GENERATE
  run, and locked with a sha256 and a timestamp. P1–P5 go in verbatim (see the brief); predictions may be added but
  not changed.
- **Boards:**
  - **S3:** still on build B. **Nothing was flashed to the S3 in this session.**
    - Its app is byte-identical to the B binary: the fma-01 backup at 0x10000 equals the build `.bin`.
    - It answered `R ready vocab=25353 seq_len=256 checksum=0 prefill_skip=1 sample_profile=0 fast_sample=1` through
      the meter.
  - **P4:** untouched, still on IA1.

## (v1) Meter facts learned in step 0

- **What it is:** a cheap 4.5–36 V USB/Type-C tester with two buttons, K1 ("key") and K2 ("mode"). It shows V, A,
  W, mWh (5 digits) and t.
- **Implied resolution:**
  - 0.01 V, 0.01 A and 0.01 W;
  - **1 mWh** steps;
  - 1 s for t, displayed as m:ss.
  - Confirm the mWh step from the first real readings, and include it in every error bar.
- **Wiring:** current only registers in the order **Miu USB-A → meter (its USB-A plug) → USB-C data cable → S3
  native USB port.**
  - Feeding the meter through its USB-C socket read 0.00 A while the board was running.
  - The S3's port enumerates normally through the meter: `usb-Espressif_USB_JTAG_serial_debug_unit_10:51:DB:xx:xx:xx`.
- **It cannot be zeroed,** or Mark couldn't find how. mWh and t keep accumulating, and probably reset when the meter
  loses power, e.g. when it's moved between boards.
- **It only accumulates above a current threshold, somewhere between 0.03 and 0.07 A.**
  - **S3 idle:** 0.03 A, and `t` and mWh stay frozen.
  - **S3 generating:** 0.07 A, and both count.
  - **Unresolved:** during that burst W read 0.15, but 0.07 A × 5.05 V ≈ 0.35 W. Recheck whether W lags, or was
    misread, before relying on W for idle.

## (v1) Protocol as agreed (Mark, 2026-10-12)

- **Every run (idle or generate) is 5 minutes, ×3 repeats per build, with a 2-minute rest between runs.**
- **Readings, start and end, no zeroing:**
  1. I prompt **READ START VALUES**; Mark replies with mWh and t; then I start the window.
  2. At the end I prompt **READ END VALUES**; Mark replies with mWh and t, plus the V and A he saw mid-run, and the
     room temperature if available. Photos are fine.
  3. Energy = end − start; time = end − start, on the **meter's own t**.
- **Always take a fresh start reading. Never difference across a meter move.**
- **Generate runs** use mWh and t as above.
  - The sub-threshold hand-off gaps at each end aren't counted by the meter, so the meter's Δt should match the
    script window (`window_s` in `runs.jsonl`). Check it every run; a shortfall means the board dipped below the
    threshold mid-run.
  - On a board that idles *above* the threshold (the P4, probably), the gaps are counted: charge them at that
    board's measured idle power.
- **S3 idle (proposed, needs Mark's OK):** the accumulator can't run at 0.03 A, so use the brief's fallback.
  - Read **W, V and A once a minute** (six readings, 0:00 to 5:00), prompted by me.
  - Idle power = their mean, with the error from the 0.01 W step and the spread.
  - Switch to every 15 s if the readings wander.
  - The P4's idle method depends on whether it is above the threshold (check in its step 0).
- **Workload (generate):** `run.py gen`.
  - Back-to-back greedy generations: prompt 433 447 259 405, N = 200, t = 0, seed 42, eot = 0, for 5 minutes.
  - Every token is counted, and every generation's firmware ms/token is logged.
  - **Gate:** the median ms/token must be within 3% of the build's benchmark (B 32.7, D 25.8, P4 13.7), or stop.
  - For reference, S3-B through the meter gave 33.40 ms/token on 13 consecutive 200-token generations (+2.1%).

## (v1) Run order (approved)

1. S3-B idle ×3.
2. Flash D; S3-D idle ×3.
3. Move the meter to the P4: step 0 (port + firmware + whether idle is above the threshold), then P4 idle ×3.
4. **Write and lock the PREREG.**
5. P4 generate ×3.
6. Move the meter back to the S3 (fresh start readings): D generate ×3.
7. Restore B, confirm the flashed app's hash equals `907ef81e…`, then B generate ×3.

## Builds (exact binaries; FAST_SAMPLE=1 recorded)

- **FAST_SAMPLE is irrelevant here:** all three use FAST_SAMPLE=1, but `t=0` takes the benchmark's argmax loop
  unchanged (`ia_s3_port.h:506`), so no greedy run touches it (Mark, 2026-10-12: "fine for greedy runs").
- **S3-B:** the existing b-libs-interactive-01 final build, already on the board.
  - `.ino` `ba7d7536…`, libs `B_64B_80M`, defines
    `-DHEAD_SC16=0 -DLOGITS_SRAM=1 -DCORE_INT4=1 -DINTERACTIVE=1 -DPREFILL_SKIP=1 -DFAST_SAMPLE=1`.
  - App sha256 `907ef81ef8e8a89cfc93b32b33e49d4b364f148829f7682d493d92c131627ba4`, recorded before any flash in
    `logs/B_bin_before.sha256`.
- **S3-D:** **new**, compiled 2026-10-12 11:10 with Mark's approval. Not flashed yet.
  - The same `.ino` and defines, `LIBS=D_64B_120M`, `FlashMode=qio120`, CPUFreq=240, `VOCAB_REGEN=1`.
  - App sha256 `7641a0f265b06f18a3467a5106d91329e13875ff76a385bd3ab9e015018d5677`. Build log `logs/build_D.txt`.
  - Experimental: flash and PSRAM at 120 MHz, flash above its rating (see cache-psram-2x2-01).
- **P4:** IA1 from p4-interactive-01, already on the board.
  - `insiderllm-p4` with contraction off, `P4_ATTN2`, `P4_LOGITS_SRAM`, `P4_CORE_INT4`, `INTERACTIVE`,
    `PREFILL_SKIP`, `FAST_SAMPLE`.
  - App sha256 `f6f9caf7f98c74c3f04e8f65ab3af46ddac9179b856fee425cc0b85cccbdc754`.

## Files

- `run.py`: the run driver (`gen` / `idle`). It writes `runs.jsonl` and `logs/<tag>.{serial.log,gens.csv}`.
  Since v2 it also writes `logs/<tag>.power/` (logger raw.bin, meta, summary, power.png), with `--no-logger` for
  the old meter-only behaviour. It was edited 2026-10-12 evening without any hardware to test it; the logger side
  is tested in tools/power-logger/host/tests (run API over a pseudo-terminal).
- `readings.jsonl`: Mark's meter readings as given.
- `logs/`: `B_bin_before.sha256`, `build_D.txt`, and the aborted `B_idle_1.*`.

## P4 phase (2026-10-14 afternoon)

**Wiring:** the S3 is unplugged. The P4 runs through the logger (Miu ← male breakout; P4 cable → female breakout).
GND → V13 is connected; the sync jumper is OFF.

1. **The P4 enumerates through the pass-through:** `usb-1a86_USB_Single_Serial_5C93015982-if00` (CH343, ttyACM0),
   the port `run.py` already expects. The logger is ttyACM1.
2. **Current check** (`logs/p4curr.*`, not in runs.jsonl). The current P4 firmware is not re-read; its R line and
   13.6 ms/token fit IA1. One logger run: 30 s idle, one greedy generation (433 447 259 405, n=200, t=0, seed 42),
   2 s more. Calibrated per-sample current (~1.2 ms conversions):
   - **Idle:** mean **59.34 mA** (58.87–59.88), VBUS 5.051 V.
   - **Generation:** mean **106.6 mA**, p99 120.9, **peak 121.4 mA**. 13.625 ms/token, ttft 21.6 ms.
   - **Range:** the peak is under the 146 mA top calibration point and Mark's 150 mA limit, and ~15% of the
     INA226's ~0.82 A full scale (R100). **OK: no higher calibration point needed.**
   - **Logger:** host vs fw 0.0000%, 0 drops, 0 late conversions, 0 edges.
   - **Stray byte on the first ping.** The first attempt (`logs/p4curr_try1/`) got `E unknown command` for the first
     `?`, and `chat.Board` gave up after its 10 s wait. A raw test then got `R ready` for each of 3 `?`s, with no
     reboot. Most likely a stray byte from the replug sat in the P4's line buffer.
     **Consequence for `run.py` on the P4:** the start ping can fail the same way. One `?` after opening the port
     clears it.
3. **P4 sync patches regenerated** to match the revised S3 patch (power-logger `0989b12`, `dut/README.md`).
   - **Pin behaviour:** GPIO6 (P1 pin 10) is a push-pull output, driven low from the start of `setup()`.
   - **`ia_s3_port.h`:** regenerated by the extract script (new ranges `106-174, 819-836, 852-1350`) from the
     patched S3 sketch `ea055c35…`. Not edited by hand. Without `SYNC_GPIO_SKETCH`, the script still regenerates
     today's header byte for byte.
   - **New P4 sketch patch:** `p4-sketch-sync-init.patch`, which adds `SYNC_INIT();` at the top of the P4 sketch's
     own `setup()`. `setup()` isn't part of the code extracted from the S3.
   - **Branch:** `p4/pr24` `power-01-sync-gpio` @ `203acd5` (from a96ab81; not pushed). `insiderllm-p4` is unchanged.
   - **IA1+sync built, not flashed:** `-DSYNC_GPIO=6`, 543,336 B, 0 warnings, app sha256
     `38299f178b6e3ff02806a5ba6793fcb02ef4c25ea6074a0d1cb34d25c3bf2b7a` (`p4/builds/IA1s`, `logs/p4build/`).
     `setup()` sets GPIO6 to an output and writes it low (`li a0,6`).
   - **Identical object code with SYNC off: checked for the P4.** The same tree without the define (`IA1s0`) is
     538,758 B, and its sketch object instructions are identical to `p4/builds/IA1`'s. The S3 recheck is still open.
4. **Non-sync IA1 flashed** 15:29, app `f6f9caf7…c754` (`p4/builds/IA1`, the stored build): bootloader, partition
   table, boot_app0 and app (539,280 B) were written and hash-verified (`logs/flash_P4_IA1.txt`). It was reset into
   the app with `chat.Board(reset=True)` (RTS pulse; the boot R line was received).
   - **Step d reference for P4 IA1 (pre-committed rule): 13.623 ms/token.**
     - **Run:** 3 greedy gens through the logger (433 447 259 405, N=200, t=0, seed 42; `logs/stepd_P4_ref_nosync3.*`,
       not in runs.jsonl).
     - **Per gen:** 13.623 / 13.616 / 13.633 ms/token; ttft 21.55–21.59 ms.
     - **Output hash:** `b2782783…` on all 3, the same greedy output as S3 B and D.
     - **Logger:** 12.87 s, 5.945 J, 0.462 W mean; host vs fw 0.0000%, 0 drops, 0 late conversions, 0 bus errors,
       0 gaps, 0 edges.
     - **Benchmark comparison (reported, not the step d reference):** −0.56% against the 13.7 benchmark, within the
       3% gate.
5. **Stopped here** (Mark's plan). Mark connects the sync jumper (P4 GPIO6, P1 pin 10 → V12) before IA1+sync is
   flashed.
6. **GPIO6 → V12 connected** (Mark).
   - **IA1+sync flashed** 15:34, app `38299f17…2b7a`: all 4 images hash-verified (`logs/flash_P4_IA1s.txt`). Reset
     into the app (boot fp=a9bdd778, R line).
   - **10 s idle after the reset:** 0 edges, 0 glitches, the sync level low on every sample, 59.49 mA, 0.3007 W;
     host vs fw 0.0000%, 0 drops (`logs/stepd_P4s_idle10.*`).
7. **Step d check, P4 IA1+sync: PASS** (`logs/stepd_P4sync_sync3.*`, not in runs.jsonl). The same workload as the S3
   checks, after a reset.
   - **ms/token:** 13.577 / 13.586 / 13.574, median 13.577. That is **−0.34% against the 13.623 reference** (limit 1%).
     The sync build is marginally *faster*.
   - **Output hash:** `b2782783…` on all 3, identical to non-sync IA1.
   - **Sync windows:** 3 windows for 3 generations, exactly 6 edges (1,0,1,0,1,0), 0 glitches.
   - **Window length:** 2.901–2.904 s, against the P4's own 2.736–2.739 s. That is +0.82 ms/token beyond the
     forward timing; the S3's is ~1.05.
   - **Energy:** 1.565–1.567 J per window, 0.540 W. J/token 7.83 mJ (sync windows), 9.93 mJ (whole run, with 1 s
     gaps).
   - **Logger:** host vs fw 0.0000%, 0 drops, 0 late conversions, 0 bus errors, 0 gaps.
8. **P4 idle acceptance band: 0.27–0.33 W** (Mark, 2026-10-14, committed before the P4 idle reps). That is ±10% around
   the ~0.30 W of the step d line check (0.3007 W). The other acceptance checks are the S3's: app hash, boot seen
   after a fresh reset, ping_ok, no FAILED status, host vs fw ≤ 0.5%, 0 drops, 0 late conversions, 0 bus errors,
   0 gaps, 0 sync windows, a ~300 s window.
   - **No calibration extension for the P4** (Mark): generation current is ~106 mA mean (121 mA peak), inside the
     146 mA calibrated range.
9. **P4 IA1+sync idle ×3 per the locked definition: PASS** (15:38–15:58; runs.jsonl). Fresh reset before each rep,
   300.0 s windows.

   | Rep | Power | Current | VBUS | Energy |
   |---|---|---|---|---|
   | 1r | 0.29950 W | 59.24 mA | 5.056 V | 89.88 J |
   | 2r | 0.29953 W | 59.24 mA | 5.056 V | 89.89 J |
   | 3r | 0.29953 W | 59.24 mA | 5.056 V | 89.88 J |
   | mean | **0.29952 W** (spread 0.01%) | | | |

   - **Checks on all 3 reps:** app hash, boot seen after the reset, ping_ok on the 1st try (port open ~300 s), host
     vs fw 0.0000%, 0 drops, 0 late conversions, 0 bus errors, 0 gaps, 0 sync windows, 0 glitches, inside the
     0.27–0.33 W band.
   - **All idle runs are now done:** S3 B+sync 0.20408 W, S3 D+sync 0.20707 W, P4 IA1+sync 0.29952 W.
10. **Generate-run decisions for the PREREG** (Mark, 2026-10-14, before the lock):
    - **Fresh reset before each generate rep,** as with idle. `run.py --reset` already applies in both modes.
    - **"Post-generation idle from the inter-generation gaps" is dropped.** It is replaced by a 60 s idle capture right
      after each generate rep, reported as exploratory and not used for scoring. `run.py gen --post-idle 60` takes it
      as a separate logger run (`<tag>_postidle`) and records it under `post_idle` (`exploratory: true`). A failure
      there doesn't fail the rep.
    - **Tested** with a fake board and logger in a scratch directory (no board, no generate run): the window run stops,
      then the post-idle capture runs, then the logger closes and the record is written.
11. **PREREG flag decisions** (Mark, 2026-10-14; applied in `PREREG_DRAFT.md`, still unlocked):
    1. S3-B / S3-D / P4 mean the sync builds `06abb9ad…` / `cf2ff730…` / `38299f17…`.
    2. The idle uncertainty for marginal J/token is ±3.7% of each board's fresh-reset idle power (from the S3's
       40.9–42.4 mA on 10-14), the same for all boards.
    3. Verdict rule: HELD / FAILED / UNRESOLVED by whether the whole error bar is on one side of the threshold.
    4. **The RC filter is on the logger board at V12/V13.** Every board's sync wire passes through it, including the
       P4's GPIO6 jumper. This corrects "1 kΩ in series from S3 GPIO4" in the 10-14 entry above.

    Still open before the lock: how an error bar is built (proposed in the draft).

## PREREG LOCKED (2026-10-14)

- **File:** `PREREG.md` (renamed from `PREREG_DRAFT.md` in the lock commit).
- **sha256:** `b75eb427b6a54b39c2fe750aa76b907ffdb0c00007a6ea0f2500d6f3dadc9e04`
- **Locked at:** 2026-10-14T16:56:46-07:00. This is before any generate run: runs.jsonl has idle runs only.
- **Instrument at the lock:** power-logger `7cabe8082802d45f7f7b289db359bf2a3b454d3b`.
- **Lock edits** (Mark): the title and status header became "LOCKED 2026-10-14", and "Mark estimated" became
  "estimated in review". There were no other changes from the reviewed draft (`f1cccb6`) apart from filling in
  the power-logger commit.
- **Lock commit and remote URL:** recorded in the next commit (a commit can't contain its own hash).
- **Lock commit:** `63e88013f12ea4c868bf4c64421e86ed6b3ade0e`.
- **Remote** (private, created 2026-10-14):
  https://github.com/msb-msb/power-01/commit/63e88013f12ea4c868bf4c64421e86ed6b3ade0e
  - It was pushed before any generate run; the remote `main` was at the lock commit.
  - PREREG.md fetched from the remote at that commit hashes to the same sha256,
    `b75eb427b6a54b39c2fe750aa76b907ffdb0c00007a6ea0f2500d6f3dadc9e04`.

## Generate runs (after the PREREG lock, 2026-10-14)

- **P4_gen_1 (the `--meter` rep): PASS** (17:02:08–17:07:11; runs.jsonl, `logs/P4_gen_1.*`).
  - **Workload:** 103 generations, 20,600 tokens, window 302.8 s.
  - **Speed:** median 13.568 ms/token, −0.96% against 13.7 (3% gate PASS). All generations identical.
  - **Energy:** 164.44 J at 0.5431 W mean. **Total J/token 7.983 mJ**; window (gross) J/token 7.912 mJ.
  - **Checks:** 103 sync windows for 103 generations, 0 glitches. Host vs fw 0.0000%, 0 drops, 0 late conversions,
    0 bus errors, 0 gaps. App hash correct; boot seen after the reset.
  - **Post-run idle (exploratory):** 0.3049 W over 60 s.
  - **Meter readings** (readings.jsonl):
    - **Start:** 5 mWh, timer "0.01" (received 17:02:05).
    - **End:** 5 mWh, timer "0.01", 0.00 A, 4.98 V (read right after the window ended at 17:07:11).
    - **Meter cross-check not possible: below meter threshold at ~60–107 mA** (Mark's instruction). The mWh, the
      timer and A didn't move over the ~5 min window. The rep stands on the logger measurement, per the PREREG.
- **Meter removed** (Mark, 17:09–17:11). After the male breakout went back into Miu, the logger read 56.8 mA at
  5.055 V (0.287 W), but the P4's CH343 didn't enumerate: `lsusb` showed the logger only. Mark reseated the
  breakout and the P4 came back (17:11:40). It had power but no data in between. Rep 2 starts from a fresh reset,
  so this has no effect on it.
- **P4_gen_2: PASS** (17:11:49). 102 generations, 20,400 tokens, 300.2 s, median 13.578 ms/token (−0.89%),
  162.80 J at 0.5423 W. **Total 7.981 mJ/token**, window 7.907 mJ/token. 102 windows, 0 glitches, all checks pass.
  Post-run idle 0.3038 W.
- **P4_gen_3: PASS** (17:20:06). 103 generations, 20,600 tokens, 302.8 s, median 13.572 ms/token (−0.93%),
  164.36 J at 0.5428 W. **Total 7.979 mJ/token**, window 7.909 mJ/token. 103 windows, 0 glitches, all checks pass.
  Post-run idle 0.3037 W.
- **P4 generate ×3 complete:** 3 passing reps in 3 attempts (P4_gen_1–3), the first three passing in run order.
  - **Total J/token:** 7.9827 / 7.9805 / 7.9786 mJ, mean 7.981 mJ, rep spread 0.05%.
  - **Window J/token:** 7.912 / 7.907 / 7.909 mJ, mean 7.909 mJ.
  - Not scored yet: scoring needs S3-D and S3-B.
- **S3 back on the bench** (Mark, ~17:30): cable into the female breakout, S3 GPIO4 → V12, GND → V13. The 1x100
  recheck was skipped (same session, logger untouched).
  - **D+sync flashed** 17:34, app `cf2ff730…` (the on-disk hash was checked first). Bootloader, boot_app0 and app
    (375,280 B) were written and hash-verified; the partition table was verified in place
    (`logs/flash_Dsync_gen.txt`).
  - **Fresh reset:** boot seen (fp=a9bdd778).
  - **10 s idle line check:** 0 edges, sync low on every sample, 0 glitches, host vs fw 0.0000%, 0 drops
    (`logs/Dsync_gen_linecheck.*`).
  - **Idle in that check: 42.19 mA, 0.2140 W.** That is +3.4% over D's idle ×3 (0.20707 W), inside the ±3.7% idle
    term. Not an acceptance item; noted for the drift record.
- **D_gen_1 (the S3-D `--meter` rep): PASS** (17:44:01–17:49:06; runs.jsonl, `logs/D_gen_1.*`).
  - **Workload:** 55 generations, 11,000 tokens, window 305.1 s.
  - **Speed:** median 26.308 ms/token, +1.97% against 25.8 (3% gate PASS). All generations identical.
  - **Energy:** 137.27 J at 0.4498 W mean. **Total J/token 12.479 mJ**; window (gross) J/token 12.408 mJ.
  - **Checks:** 55 sync windows for 55 generations, 0 glitches. Host vs fw 0.0000%, 0 drops, 0 late conversions,
    0 bus errors, 0 gaps. App hash correct; boot seen after the reset.
  - **Post-run idle (exploratory):** 0.2233 W over 60 s, against 0.2071 W fresh-reset idle. The post-generation
    rise seen on 10-14.
  - **Meter readings** (readings.jsonl):
    - **Start:** 0 mWh, timer 0.00, 0.00 A, 5.08 V.
    - **During generation:** 0.00 A, with the mWh and timer not counting.
    - **End:** 0 mWh, timer 0.00, 0.00 A, 4.98 V.
    - **Below meter threshold (verified with a phone load: works at high current)** (Mark). The threshold is above
      ~110 mA. The rep stands on the logger measurement, per the PREREG.
- **D_gen_2: PASS** (17:52:17). 55 generations, 11,000 tokens, 305.3 s, median 26.306 ms/token (+1.96%),
  136.46 J at 0.4470 W. **Total 12.406 mJ/token**, window 12.333 mJ/token. 55 windows, 0 glitches, all checks
  pass. Post-run idle 0.2177 W.
- **D_gen_3: FAILED, technical (window aborted)** (18:00:38). The fresh reset and boot were fine (`R ready` at
  .658). `run.py` sent `P 433 447 259 405` 50 ms later and `G` right after it. The board answered
  `E no prompt (send P first)`: the P line was lost in the moments after boot. 0 generations; the record has
  `status: FAILED (window aborted …)`, and the logger run was finalized (0.05 s).
  - **Misclassified, then corrected:** my acceptance script labelled it a 3% gate failure and stopped, because no
    gate had been evaluated. Commit `1672808` says "FAIL rc=3". The gate was never reached, so per the locked rerun
    rule this is a **technical failure and is rerun** (attempt 4 of 6; passes so far: D_gen_1, D_gen_2). The script
    now reserves the stop for an explicit `gate_3pct: FAIL`.
- **D_gen_4: PASS** (18:02:50; the rerun of D_gen_3). 55 generations, 11,000 tokens, 305.4 s, median 26.308
  ms/token (+1.97%), 136.45 J at 0.4468 W. **Total 12.404 mJ/token**, window 12.330 mJ/token. 55 windows,
  0 glitches, all checks pass. Post-run idle 0.2188 W.
- **S3-D generate ×3 complete:** 4 attempts. **Scored reps: D_gen_1, D_gen_2, D_gen_4**, the first three passing
  in run order. D_gen_3 is reported as a technical failure and not scored.
  - **Total J/token:** 12.479 / 12.406 / 12.404 mJ, mean 12.430 mJ, rep spread 0.60%.
  - **Window J/token:** 12.408 / 12.333 / 12.330 mJ, mean 12.357 mJ.
  - **D_gen_1 (the meter rep) is ~0.6% higher than reps 2 and 4** (0.4498 W against 0.4470 / 0.4468 W at the same
    ms/token). It is kept: the rerun rule excludes nothing on its values. The meter sat upstream of the logger, so
    it isn't in the logger's figure. Rep 1 was the first run after the board was power-cycled by the meter insertion
    (power was 0.214 W in the line check before it).
- **S3-B: B+sync restored** 18:16, app `06abb9ad…` (the on-disk hash was checked first). Bootloader, boot_app0 and
  app (372,688 B) were written and hash-verified; the partition table was verified in place
  (`logs/flash_Bsync_gen.txt`).
  - **Fresh reset:** boot seen (fp=a9bdd778).
  - **10 s line check:** 0 edges, sync low, 0 glitches, host vs fw 0.0000%, 0 drops. 40.84 mA, 0.2073 W
    (`logs/Bsync_gen_linecheck.*`).
  - **Meter rep for S3-B** (Mark): kept as rep 1 for symmetry with S3-D, including the meter-insertion power cycle
    before it.
  - **Pre-approved** (Mark): if a prompt line is lost after boot again, `run.py` gets a ping-and-wait-for-reply
    before P (no change to window timing, workload or measurement). It is committed, disclosed here as a post-lock
    robustness fix, and the rep is rerun.
- **B_gen_1 (the S3-B `--meter` rep): PASS** (18:25:51–18:30:52; runs.jsonl, `logs/B_gen_1.*`).
  - **Workload:** 43 generations, 8,600 tokens, window 301.0 s.
  - **Speed:** median 33.400 ms/token, +2.14% against 32.7 (3% gate PASS). All generations identical.
  - **Energy:** 126.41 J at 0.4199 W mean. **Total J/token 14.699 mJ**; window (gross) J/token 14.608 mJ.
  - **Checks:** 43 sync windows for 43 generations, 0 glitches. Host vs fw 0.0000%, 0 drops, 0 late conversions,
    0 bus errors, 0 gaps. App hash correct; boot seen after the reset.
  - **Post-run idle (exploratory):** 0.2131 W, against 0.2041 W fresh-reset idle.
  - **Meter** (readings.jsonl): start 5.05 V, 0.00 W, 0.00 A, timer 0:00, 0 mWh. During generation and at the end,
    "same". **Below meter threshold** (verified with a phone load, as with S3-D). The rep stands on the logger
    measurement, per the PREREG.
  - It got the same handling as D_gen_1, including the meter-insertion power cycle before rep 1.
- **B_gen_2: PASS** (18:34:06). 43 generations, 8,600 tokens, 301.0 s, median 33.401 ms/token (+2.14%),
  127.52 J at 0.4237 W. **Total 14.828 mJ/token**, window 14.738 mJ/token. 43 windows, 0 glitches, all checks
  pass. Post-run idle 0.2167 W.
- **B_gen_3: PASS** (18:42:21). 43 generations, 8,600 tokens, 301.0 s, median 33.401 ms/token (+2.14%),
  127.89 J at 0.4249 W. **Total 14.871 mJ/token**, window 14.781 mJ/token. 43 windows, 0 glitches, all checks
  pass. Post-run idle 0.2169 W.
- **S3-B generate ×3 complete:** 3 passing reps in 3 attempts (B_gen_1–3). The lost-prompt error did not recur, so
  the pre-approved ping fix was **not** applied; `run.py` is unchanged since the lock.
  - **Total J/token:** 14.699 / 14.828 / 14.871 mJ, mean 14.800 mJ, rep spread 1.16%.
  - **Window J/token:** 14.608 / 14.738 / 14.781 mJ, mean 14.709 mJ.
  - **Mean power rose rep by rep** (0.4199 → 0.4237 → 0.4249 W) at an identical ms/token. On S3-D the meter rep
    (rep 1) was the *highest*; on S3-B it is the *lowest*. So the meter-insertion power cycle doesn't explain a
    consistent offset. Kept as is: no rep is excluded on its values.
- **All generate runs are done** (P4 ×3, S3-D ×3 of 4 attempts, S3-B ×3), in the locked order. Next: scoring and
  RESULTS.md per the PREREG.

## Scoring (2026-10-14 evening)

- **`score.py`** was committed and pushed (`f0c888e`) before it was run. Its output is `score_output.md` and
  `scores.json`; `RESULTS.md` is in `eac1bd8`.
- **Verdicts:** P1 HELD, P2 HELD, P3 HELD, P4 HELD. P5 FAILED against both S3-B and S3-D (outcome observed before the
  lock).
- **Checked by hand:** P4_gen_1 total and marginal match `score.py`.
- **Correction while writing RESULTS:** my first draft of the plain-language paragraph had the idle-share percentages
  wrong. They were fixed before the commit.
