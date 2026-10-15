# power-01 PREREG (LOCKED 2026-10-14)

**Status: locked 2026-10-14, before any generate run.** The lock commit, this file's sha256 and the remote commit
URL are recorded in `NOTES.md`. The analysis rules below were each committed to git before the data they govern;
their commits are in `NOTES.md`'s history.

## What is measured

Board-level energy per token for TinyStories greedy generation on three boards:
- **S3-B:** ESP32-S3 with variant B libs (64 B cache lines, 80 MHz flash/PSRAM, in spec);
- **S3-D:** the same S3 with variant D libs (64 B, 120 MHz, experimental);
- **P4:** ESP32-P4 IA1 (insiderllm-p4: contraction off, dual-core attention, logits in internal RAM, int4 core).

The logger sits on the board's USB VBUS, so every figure includes the USB-UART/USB-JTAG bridge, LEDs, regulators
and, on the P4-ETH, the Ethernet PHY. **These are board-level figures. Never call them chip power.**

## Instrument

- **USB power logger** (`tools/power-logger`): an INA226 at 0x44 (R100 shunt, 25 µA current LSB, 1.25 mV VBUS LSB,
  ~826 Hz) on an RP2040. It sits high side on VBUS between Miu and the board.
  - Energy is integrated on the RP2040 and, independently, on the host. They must agree within 0.5%.
  - The sync input is GP15 (V12). The RC filter (1 kΩ series, 1 nF from V12 to V13) is **on the logger board**, so
    every board's sync wire passes through it, including the P4's GPIO6 jumper (Mark, 2026-10-14).
- **power-logger commit:** `7cabe8082802d45f7f7b289db359bf2a3b454d3b` (branch power-logger). The analysis code
  (`host/powerlog/`) last changed in `303d1b5`.
- **Logger firmware:** `PL_SRC_SHA` `5a14af1eb9d5e3f9` (as reported by the logger, uid E66038B7130A6739).
  - `.uf2` sha256: `6d7a93e71d8ec220fa2ac34a573f8935f9c0add21a5e5f24aa28eba4c6be9288`
    (`firmware/build/power_logger.ino.uf2`, built 2026-10-13 17:22).
  - The source tag is present in its payload.
- **Calibration:** `host/calibration.json`, sha256
  `b2e2f75f52c65c30e789c88ad9d5fe30edfa38a3915db3852cf3b92cafa939c0`, fitted 2026-10-13 against an Aneng SZ20.
  - **Current:** I = 1.065384 × raw + 0.062 mA, residuals ≤ 0.12% at 26–146 mA.
  - **VBUS:** V = 0.951643 × raw + 11.6 mV.
  - **Session recheck (1x100):** −0.01% calibrated on 10-14. The part is a suspected clone, so the 1x100 point is
    rechecked at the start of each session; over 0.5% means recalibrate before measuring.
- **Calibrated range:** up to 146 mA. The highest current seen is the P4 at 121 mA peak during generation.

## Builds (all with the sync pin; exact binaries)

**"S3-B", "S3-D" and "P4" in this PREREG, including P1–P5, mean these sync builds** (Mark, 2026-10-14):
S3-B = `06abb9ad…`, S3-D = `cf2ff730…`, P4 = `38299f17…`.

| Board | App sha256 | Sync pin | Non-sync build |
|---|---|---|---|
| S3-B | `06abb9ada33896db6f2f07adcbeed03ff45e50473009aab470f35f2af581f8f8` | GPIO4 | `907ef81e…` |
| S3-D | `cf2ff730cd0392b673fc2d25fa357092586f95e02df9269be24566cfafbf1a9d` | GPIO4 | `7641a0f2…` |
| P4 | `38299f178b6e3ff02806a5ba6793fcb02ef4c25ea6074a0d1cb34d25c3bf2b7a` | GPIO6 | `f6f9caf7…` (IA1) |

- **Step d** checked each sync build against its non-sync build on this bench: identical greedy output (`b2782783…`
  on all boards) and median ms/token within 1%.
  - **S3-B:** the reference is 33.40, not the 32.7 benchmark (deviation 1, chosen after seeing the result).
  - **S3-D:** 26.305 → 26.308 (+0.01%).
  - **P4:** 13.623 → 13.577 (−0.34%).
  - **D and P4 rule:** their references were fixed by a rule committed before their data.
- **With SYNC off,** the patch compiles to identical sketch-object instructions. This is checked for the P4 IA1
  (10-14) and for the first S3 version (10-12); the revised S3 patch is not rechecked.

## Generate protocol (checked against the brief)

The brief's generate run is: "a host script that drives interactive mode back to back (greedy, seed 42, fixed
prompt, fixed N tokens per generation …) for a fixed wall time of 5 minutes, counting every generated token and
logging firmware ms/token". `run.py gen` does that:

- **Workload:** prompt `433 447 259 405`, N = 200, t = 0, seed 42, eot = 0, back to back.
- **Window:** the window is ≥ 300 s. The generation running at the deadline finishes, so it adds at most one
  generation (~6.9 s S3-B, ~5.5 s S3-D, ~2.9 s P4). It runs from the first send to the last `D` line, with a logger
  run bracketing it.
- **Logged:** every generation's token count and firmware ms/token (`logs/<tag>.gens.csv`).
- **3% gate** (the brief's step 1): the median ms/token must be within 3% of the build's benchmark (B 32.7,
  D 25.8, P4 13.7), or stop.
- **Fresh reset before each generate rep** (Mark, 2026-10-14), as with idle: `--reset`. It requires a boot banner
  after the reset pulse.
- **Exploratory post-run idle:** right after each generate rep, a separate 60 s logger capture
  (`--post-idle 60`, tag `<tag>_postidle`). It is reported as exploratory and **not used for scoring**.
- **Repeats:** 3 generate reps per board, with 2 minutes' rest between runs.
- **`--meter` rep:** one rep per board runs with the cheap inline meter as a cross-check. The meter sits **upstream of
  the logger** (Miu → meter → male breakout → logger → board), so the logger never measures the meter's own draw.
  That rep's logger figures are measured exactly as in the other reps.
- **Order** (run order v2):
  1. P4 gen ×3.
  2. S3-D gen ×3.
  3. Restore S3-B+sync and confirm its hash.
  4. S3-B gen ×3.
- **Command:**
  `esp32-ai/.venv/bin/python evals/power-01/run.py gen --board s3|p4 --build B|D|P4 --rep N --app-sha <app> --reset --post-idle 60 [--meter]`.
- **Acceptance per rep:**
  - the app hash, boot seen after the reset, no FAILED status, and the 3% gate;
  - host vs fw ≤ 0.5%, 0 drops, 0 late conversions, 0 bus errors, 0 gaps;
  - all generations identical (greedy);
  - sync windows = generations (1:1 pairing, glitch rule applied).
- **Rerun rule** (Mark, 2026-10-14):
  - A rep that fails acceptance for a technical reason is rerun.
  - All attempts, passing and failing, are reported.
  - **Scoring uses the first three passing reps per board, in run order.**
  - No rep is excluded on the basis of its J/token or energy values.
  - If a board can't produce three passing reps within **6 attempts**, its predictions are scored **UNRESOLVED**.
  - A 3% gate failure still stops the session first (the brief: "if not, stop") and goes to Mark before any rerun.

## Metrics

| Metric | Definition | Role |
|---|---|---|
| **Total J/token** | logger energy over the whole generate window ÷ tokens in it (the brief's "generate energy / tokens") | **scores P1, P2, P4** |
| **Marginal J/token** | (window energy − fresh-reset idle power × window duration) ÷ tokens | **scores P3** |
| Window (gross) J/token | energy inside the sync windows ÷ tokens (the windows span forward passes, sampling and serial output) | **headline metric; scores no prediction** |
| Tokens per joule | 1 ÷ each of the above | reported |
| Idle power | mean power of the 3 fresh-reset idle reps per build (locked idle definition) | scores P5; used in marginal |

- **Idle powers used for the marginal figure** (idle ×3, 10-14, fresh reset, 300 s):
  - S3-B: **0.20408 W** (0.20401 / 0.20411 / 0.20413);
  - S3-D: **0.20707 W** (0.20671 / 0.20725 / 0.20725);
  - P4: **0.29952 W** (0.29950 / 0.29953 / 0.29953).
- **Window duration** is the logger run's duration (`duration_s`).
- **Error bars:** from the spread of the 3 reps, the reference-instrument term and, for marginal J/token, the idle
  term (construction below).
  - **Idle uncertainty for marginal J/token** (Mark, 2026-10-14): **±3.7% of that board's fresh-reset idle power**,
    the same rule for every board.
    - That is the relative spread of the S3's observed 40.9–42.4 mA on 10-14, covering post-generation idle drift.
    - It replaces the board-specific mA wording in the locked idle definition.
    - Idle subtracted ± 3.7%: S3-B 0.20408 ± 0.00755 W, S3-D 0.20707 ± 0.00766 W, P4 0.29952 ± 0.01108 W.
  - The brief: "don't claim differences smaller than" the error bar.
- **How an error bar is built** (Mark, 2026-10-14: the proposal is approved, with the calibration term replaced by the
  reference instrument's accuracy).
  - **For one build:** the interval runs from the lowest to the highest of its 3 reps.
    - Each rep is computed at both ends of the **reference-instrument term** (below).
    - For marginal J/token, each rep is also computed at both ends of the **idle term** (± 3.7% of that board's
      fresh-reset idle power).
  - **For a comparison** (P2, P3, P4, P5's difference): the interval is the worst case over the two builds'
    intervals (e.g. for P3, the lowest and highest possible P4 ÷ S3-B ratio).
  - All terms are added linearly as worst cases.
- **Reference-instrument term:** the logger's absolute accuracy is the accuracy of the DMM it was calibrated
  against: an Aneng SZ20, DC current ±(0.5% + 3 digits), DC volts ±(0.2% + 10 digits) (published spec).
  - **Evaluation:** at each board's operating point (mean current and VBUS), combined worst case into an energy
    uncertainty: ε_E = ε_I + ε_V.
  - **Voltage:** 1 mV per digit (6 V range; the points read 1.405 / 2.808 / 5.052 V), so 10 digits = 10 mV, which is
    ±0.40% at ~5.06 V.
  - **Current: 0.01 mA per digit** (Mark, 2026-10-14). All five calibration current points were read on the 250 mA
    range. 99.20 and 145.50 mA were entered without trailing zeros; the points file records this (power-logger
    `7cabe80`). So 3 digits = 0.03 mA.

    | Board | Operating point | ε_I | ε_V | **ε_E** |
    |---|---|---|---|---|
    | S3-B | generate ~81.7 mA | ±0.537% | ±0.397% | **±0.93%** |
    | S3-B | idle 40.2 mA | ±0.575% | ±0.397% | **±0.97%** |
    | S3-D | generate ~87.3 mA | ±0.534% | ±0.397% | **±0.93%** |
    | S3-D | idle 40.9 mA | ±0.573% | ±0.397% | **±0.97%** |
    | P4 | generate ~106.9 mA | ±0.528% | ±0.398% | **±0.93%** |
    | P4 | idle 59.2 mA | ±0.551% | ±0.398% | **±0.95%** |

    - Generate operating points are from the step d windows (window energy ÷ duration ÷ VBUS); idle points are from
      idle ×3.
    - **At scoring,** each board's generate operating point is re-evaluated from its own generate reps (mean current
      and VBUS) with the same formula: ε_I = 0.5% + 0.03 mA / I, ε_V = 0.2% + 10 mV / V.
    - The **generate** rows apply to total and window J/token. The **idle** rows apply to the subtracted idle power
      in marginal J/token, and to P5.
  - **Larger than the ~0.7–0.8% estimated in review:** the volts' 10-digit term alone is ~0.2% at 5 V, so the voltage
    side is ~0.40%, not 0.2%.
- **Fit residuals vs accuracy:** the calibration fit's residuals (≤ 0.12% current, ≤ 0.03% VBUS) describe the
  logger's **linearity** against the DMM, not its absolute accuracy. Absolute accuracy is limited by the DMM's own
  spec, so the DMM term above is the one used.
- **The reference-instrument term is common to all boards** (one logger, one calibration). It would largely cancel
  in ratios and differences, but **no credit is taken for that**: comparisons use the worst case over both builds'
  full intervals.

## Predictions (verbatim from the brief, 2026-10-12; not changed)

> P1: S3-B total energy is 10-25 mJ/token.
> P2: P4 total J/token is lower than S3-B's (its 2.3x speed outweighs its
>     higher board power).
> P3: P4 marginal J/token is <= 0.6x S3-B's.
> P4: S3-D total J/token is lower than S3-B's (speed rises more than power).
> P5: P4 idle power exceeds S3 idle by >= 0.2 W (Ethernet PHY plus the
>     bigger chip).

### How each is scored

**Verdict rule** (Mark, 2026-10-14): **HELD** if the whole error bar satisfies the prediction, **FAILED** if the
whole error bar violates it, **UNRESOLVED** if the error bar straddles the threshold.

| | Metric (as written) | Scored as |
|---|---|---|
| P1 | total J/token | S3-B total J/token (mean of 3 reps, with its error bar) is inside 10–25 mJ |
| P2 | total J/token | P4 total J/token < S3-B total J/token |
| P3 | marginal J/token | P4 marginal J/token ≤ 0.6 × S3-B marginal J/token |
| P4 | total J/token | S3-D total J/token < S3-B total J/token |
| P5 | idle power | P4 idle power − S3 idle power ≥ 0.2 W, scored **separately against S3-B and against S3-D (both reported)** (Mark, 2026-10-14) |

- **P5's error bar** (Mark, 2026-10-14):
  - **Each board's idle power interval:** from the lowest to the highest of its fresh-reset idle ×3 reps, each
    computed at both ends of the reference-instrument idle term (±0.97% S3-B and S3-D, ±0.95% P4).
  - **The difference interval:** the worst case over the two boards' intervals, i.e. (P4 low − S3 high) to
    (P4 high − S3 low).
  - **The ±3.7% idle term does not apply to P5.** It applies only to the subtracted idle power in marginal J/token.

- **P5: outcome effectively observed before the lock.** P4 is ~0.30 W against S3 ~0.204–0.207 W (0.29952 − 0.20408 =
  **+0.0954 W** against S3-B; 0.29952 − 0.20707 = **+0.0925 W** against S3-D). The brief's own order puts the PREREG
  after the idle runs, so this was unavoidable. P5 is kept as written, not dropped or reworded.
- **P2's parenthetical** ("its 2.3x speed outweighs its higher board power") is the stated reason, not a scored
  claim. The benchmark speed ratio is 32.7 / 13.7 = 2.39×.

### Flags: decided by Mark, 2026-10-14

1. **Sync builds:** "S3-B", "S3-D" and "P4" mean the sync builds (Builds, above).
2. **Idle uncertainty:** ±3.7% of each board's fresh-reset idle power, the same rule for all boards (Metrics).
3. **Verdict rule:** HELD / FAILED / UNRESOLVED (above).
4. **RC filter:** it is on the logger board, so every board's sync wire passes through it (Instrument).
5. **"S3 idle" in P5:** both S3-B and S3-D (decided earlier).

**Nothing is open:** the DMM current digit (0.01 mA) is confirmed and the error-bar construction is approved.

## Disclosures: what was observed before the lock

1. **Step d window (gross) J/token** (3 greedy N=200 gens with 1 s rests, inside sync windows):
   - **S3-B 14.37 mJ** (10-13);
   - **S3-D 12.19 mJ** (10-14);
   - **P4 IA1 7.83 mJ** (10-14).

   Whole-run figures from the same short runs, including the 1 s rests: 15.85 / 13.72 / 9.93 mJ. These are not the
   brief's protocol.
   - **Consequence:** a generate window is back-to-back generations, so total J/token will be close to the window
     figures. **P1, P2 and P4 are therefore largely anticipated** by these numbers.
2. **All idle powers** (above), which is what P5 is scored on. P5's outcome is effectively known.
3. **ms/token for every build** (benchmarks, step d references and step d sync runs).
4. **No marginal J/token estimate was computed from step d data, or any other data, before the lock** (confirmed
   by Mark, 2026-10-14). The inputs to compute one (step d window energies and durations, and the idle powers) were
   available.
5. **P4 current during one generation** (10-14 current check): 106.6 mA mean, 121.4 mA peak, ~0.54 W.

## Deviations from the brief (all decided before the lock)

- **Instrument:** the USB power logger replaces the inline meter as the instrument (protocol v2, 2026-10-12
  evening). Error bars come from calibration and repeat spread, not from meter resolution. The cheap meter stays as
  a cross-check: one generate run per board.
- **Builds:** sync-pin builds replace the exact existing binaries, verified at step d. See flag 1.
- **FAST_SAMPLE=1 instead of "off":** greedy (t = 0) takes the benchmark's argmax loop and never touches the fast
  sampler (Mark, 2026-10-12: "fine for greedy runs").
- **Idle:** "firmware booted, waiting at the prompt" became a fresh reset before each rep (locked idle definition).
- **Generate reps also start from a fresh reset** (Mark, 2026-10-14).
- **S3-B step d reference:** 33.40 same-bench, not the 32.7 benchmark (deviation 1). The 3% run gate still uses 32.7.
- **Post-generation idle:** dropped from the inter-generation gaps (see analysis rule 4); replaced by the
  exploratory 60 s post-run capture.
- **Room temperature isn't measured.** It is a suspected idle-drift factor.

## Analysis rules (pre-committed)

1. **Glitch rule** (Mark, 2026-10-14, after D idle rep 1). Sync windows shorter than **10 ms** are discarded as glitches.
   - They are counted and reported (`sync_glitches` in each summary and in runs.jsonl).
   - They are left out of window pairing and out of sync energy.
   - Real windows are ≥ 0.4 s at the smallest N used (Mark, 2026-10-14, after the N=20 filter check gave 0.41 s; was "≥ 0.5 s"). The 10 ms glitch threshold is unchanged.
   - Applies to all runs, including re-analysis of earlier ones.
   - Implemented in power-logger `powerlog/analysis.py` (`GLITCH_MAX_S`).
2. **Step d ms/token reference for D and P4 IA1** (Mark, 2026-10-13; NOTES "Step d ms/token reference").
   - The reference is the same-bench non-sync build through the logger: 3 greedy gens, median ms/token.
   - The sync build must be within 1% of it.
3. **J/token definition** (NOTES decision 4): energy inside the sync windows ÷ tokens.
   - A window spans the whole generation loop: forward passes, sampling and serial output.
   - This is the **window (gross)** metric above. The brief's total and marginal J/token are defined over the whole
     generate window (Metrics).
4. **Idle definition and headline metric** (Mark, 2026-10-14, locked after the idle diagnosis in NOTES):
   > "Primary idle = 300 s after a fresh S3 reset, before any G (reset before each rep). Headline metric = window J/token (gross). Any net-of-idle figure is secondary and carries the measured idle spread (40.9–42.4 mA observed 10-14) as uncertainty. Post-generation idle is reported from the inter-generation gaps of the generate runs."
   - **Superseded in part** (Mark, 2026-10-14): the last sentence ("Post-generation idle … inter-generation gaps") is
     dropped. It is replaced by the 60 s exploratory capture after each generate rep.
   - **Uncertainty restated** (Mark, 2026-10-14): the board-specific "40.9–42.4 mA" is replaced by ±3.7% of each
     board's fresh-reset idle power, the same rule for all boards (Metrics).
   - **Suspected idle-drift factor:** ambient temperature (not measured). On 10-14, fresh-boot idle was 40.86 mA
     at 11:00 and 41.53 mA at 12:00.
   - **Idle reset applies to the P4 too:** "fresh S3 reset" is applied to the P4 as a fresh P4 reset.
5. **Sync line hardware** (2026-10-14, before the D idle reruns): an RC filter, 1 kΩ in series into V12 and 1 nF from
   V12 to V13. It is **on the logger board** (Mark), so every board's sync wire passes through it, including the P4's
   GPIO6 jumper.
6. **Idle acceptance bands** (mean power over the 300 s window): S3 0.19–0.23 W (since 10-13); **P4 0.27–0.33 W**
   (Mark, 2026-10-14, ±10% around the 0.3007 W step d line check, committed before the P4 idle reps).
   - The P4's generation current (~106 mA mean, 121 mA peak) is inside the 146 mA calibrated range, so there's no
     calibration extension.
7. **Liveness** (`run.py`): a missed end-of-window ping is retried (3 tries, ~5 s apart, reopening the port). If all
   fail, the rep is FAILED (liveness unconfirmed) but its data is kept. The logger run is always finalized.

## Lock procedure

1. Mark reviews the draft (flags 1–4, the error-bar construction and the DMM digit decided 2026-10-14) and says
   "lock".
2. Fill in the power-logger commit.
3. `git mv PREREG_DRAFT.md PREREG.md`, and record its sha256 and a timestamp in `NOTES.md`.
4. Commit that lock on its own.
5. **Before the first generate run:** push the power-01 repo (at least the lock commit) to a GitHub repo under
   `msb-msb` (private is fine). Record the remote commit URL and PREREG.md's sha256 in `NOTES.md`.
