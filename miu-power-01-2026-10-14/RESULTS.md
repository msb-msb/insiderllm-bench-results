# power-01 RESULTS: board-level energy per token, ESP32-S3 (B, D) and ESP32-P4

**Scored per `PREREG.md`**, locked 2026-10-14 16:56:46 −07:00:
- sha256 `b75eb427b6a54b39c2fe750aa76b907ffdb0c00007a6ea0f2500d6f3dadc9e04`;
- lock commit `63e8801`, pushed to the private `msb-msb/power-01` before any generate run.

**Scoring code:** `score.py`, committed and pushed (`f0c888e`) before it was run. It writes `scores.json` and
`score_output.md`; the sections below "Every number" are `score_output.md` unchanged.

**What the figures cover:** they are **board-level**. The logger sits on each board's USB VBUS, so they include the
USB bridge, LEDs, regulators and, on the P4-ETH, the Ethernet PHY. They are not chip power.

**Builds** (sync-pin builds, step d verified):
- S3-B = `06abb9ad…`
- S3-D = `cf2ff730…`
- P4 = `38299f17…`

**Instrument:**
- the USB power logger (power-logger `7cabe808`, firmware `5a14af1eb9d5e3f9`);
- calibration `b2e2f75f…` against an Aneng SZ20.

## Verdicts

| | Prediction (verbatim) | Metric | Interval that decided it | Verdict |
|---|---|---|---|---|
| P1 | S3-B total energy is 10-25 mJ/token. | total J/token | S3-B 14.5619 to 15.0104 mJ, inside 10–25 at both ends | **HELD** |
| P2 | P4 total J/token is lower than S3-B's (its 2.3x speed outweighs its higher board power). | total J/token | P4 − S3-B = −7.1058 to −6.5051 mJ, < 0 at both ends | **HELD** |
| P3 | P4 marginal J/token is <= 0.6x S3-B's. | marginal J/token | P4 / S3-B = 0.4015 to 0.5447, ≤ 0.6 at both ends | **HELD** |
| P4 | S3-D total J/token is lower than S3-B's (speed rises more than power). | total J/token | S3-D − S3-B = −2.7219 to −1.9664 mJ, < 0 at both ends | **HELD** |
| P5 | P4 idle power exceeds S3 idle by >= 0.2 W (Ethernet PHY plus the bigger chip). | idle power | P4 − S3-B = 0.09055 to 0.10034 W; P4 − S3-D = 0.08740 to 0.09767 W; < 0.2 at both ends, against both | **FAILED** (outcome observed before lock) |

**What was known before the lock** (PREREG disclosures):
- **P5's outcome:** the idle runs come before the lock in the brief's own order.
- **The step d window figures:** S3-B 14.37, S3-D 12.19, P4 7.83 mJ/token. Because generate windows are back-to-back
  generations, these anticipated P1, P2 and P4.
- **No marginal figure was computed before the lock.**

## Headline: window (gross) J/token

Energy inside the sync windows ÷ tokens. A window spans prefill, decode, sampling and serial output. This is the
headline figure; it scores no prediction.

| Board | Window J/token (mean of 3) | Interval (rep spread + ±ε_E) | Tokens per joule | ms/token (median of the rep medians) |
|---|---|---|---|---|
| P4 | **7.909 mJ** | 7.8334–7.9850 mJ | 126.4 | 13.572 |
| S3-D | **12.357 mJ** | 12.2148–12.5240 mJ | 80.9 | 26.308 |
| S3-B | **14.709 mJ** | 14.4718–14.9191 mJ | 68.0 | 33.401 |

## Board-level vs marginal, in plain language

**Total (board-level) J/token** is everything the board drew from USB during the 5-minute generate window, divided
by the tokens it produced. It includes the power the board burns just by being switched on: regulators, the USB
bridge, LEDs, and the P4's Ethernet PHY.

**Marginal J/token** subtracts what the same board draws when it sits idle at its prompt after a fresh reset, so
it estimates the extra energy that generating costs.

The two answer different questions:
- **Total** is what a battery would see if the board did nothing but generate.
- **Marginal** is the cost of generation on a board that is powered anyway.

Here idle draw is a large share of generate power: fresh-reset idle is 48% of mean generate power on S3-B, 46% on
S3-D and 55% on the P4. So marginal J/token is 52% (S3-B), 54% (S3-D) and 45% (P4) of total J/token. They also carry a wider error bar, because the subtracted idle power has a ±3.7%
uncertainty for drift (from the S3's 40.9–42.4 mA spread on 10-14).

## Every number (from `score.py`)

## Idle power (fresh reset, 300 s; scores P5, subtracted in marginal J/token)

| Board | Reps | Power per rep (W) | Mean (W) | Operating point | ε_I | ε_V | ε_E (instrument, idle) | Rep ends at ±ε_E (W) | Interval (W) |
|---|---|---|---|---|---|---|---|---|---|
| S3-B | B_idle_1r, B_idle_2r, B_idle_3r | 0.20401, 0.20411, 0.20413 | 0.20408 | 40.24 mA, 5.0710 V | ±0.575% | ±0.397% | ±0.972% | 0.20203–0.20599; 0.20212–0.20609; 0.20215–0.20611 | 0.20203–0.20611 |
| S3-D | D_idle_1r, D_idle_2r, D_idle_3r | 0.20671, 0.20725, 0.20725 | 0.20707 | 40.85 mA, 5.0687 V | ±0.573% | ±0.397% | ±0.971% | 0.20470–0.20872; 0.20524–0.20926; 0.20524–0.20926 | 0.20470–0.20926 |
| P4 | P4_idle_1r, P4_idle_2r, P4_idle_3r | 0.29950, 0.29953, 0.29953 | 0.29952 | 59.24 mA, 5.0559 V | ±0.551% | ±0.398% | ±0.948% | 0.29666–0.30235; 0.29669–0.30237; 0.29669–0.30237 | 0.29666–0.30237 |

## Generate attempts (all, in run order) and scored reps

| Board | Attempt | Tag | Pass | Failed checks | Status | Meter rep |
|---|---|---|---|---|---|---|
| P4 | 1 | P4_gen_1 | yes | – | – | yes |
| P4 | 2 | P4_gen_2 | yes | – | – |  |
| P4 | 3 | P4_gen_3 | yes | – | – |  |
| S3-D | 1 | D_gen_1 | yes | – | – | yes |
| S3-D | 2 | D_gen_2 | yes | – | – |  |
| S3-D | 3 | D_gen_3 | NO | status_ok, gate_3pct, all_generations_identical, sync_windows==generations | FAILED (window aborted: SystemExit: board error: no prompt (send P first)) |  |
| S3-D | 4 | D_gen_4 | yes | – | – |  |
| S3-B | 1 | B_gen_1 | yes | – | – | yes |
| S3-B | 2 | B_gen_2 | yes | – | – |  |
| S3-B | 3 | B_gen_3 | yes | – | – |  |

- **P4 scored reps:** P4_gen_1, P4_gen_2, P4_gen_3 (first three passing, in run order).
- **S3-D scored reps:** D_gen_1, D_gen_2, D_gen_4 (first three passing, in run order).
- **S3-B scored reps:** B_gen_1, B_gen_2, B_gen_3 (first three passing, in run order).

## Reference-instrument term at the generate operating points

| Board | Mean current (scored reps) | Mean VBUS | ε_I = 0.5% + 0.03 mA / I | ε_V = 0.2% + 10 mV / V | **ε_E** |
|---|---|---|---|---|---|
| P4 | 108.74 mA | 4.9918 V | ±0.528% | ±0.400% | **±0.928%** |
| S3-D | 89.33 mA | 5.0144 V | ±0.534% | ±0.399% | **±0.933%** |
| S3-B | 84.23 mA | 5.0206 V | ±0.536% | ±0.399% | **±0.935%** |

## Per-rep figures and their ends

All J/token in mJ. Total ends: energy at ±ε_E(generate). Marginal ends: the min and max over energy at ±ε_E(generate) × subtracted idle at ±3.7% × subtracted idle at ±ε_E(idle) (8 combinations). Window ends: ±ε_E(generate).

| Board | Rep | Gens | Tokens | Energy (J) | Duration (s) | Mean W | ms/token | Total | Total ends | Marginal | Marginal ends | Window | Window ends | Post-run idle W (exploratory) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P4 | P4_gen_1 | 103 | 20600 | 164.4435 | 302.810 | 0.5431 | 13.568 | 7.9827 | 7.9086–8.0568 | 3.5799 | 3.2996–3.8571 | 7.9116 | 7.8382–7.9850 | 0.3049 |
| P4 | P4_gen_2 | 102 | 20400 | 162.8027 | 300.228 | 0.5423 | 13.578 | 7.9805 | 7.9065–8.0546 | 3.5724 | 3.2919–3.8499 | 7.9068 | 7.8334–7.9802 | 0.3038 |
| P4 | P4_gen_3 | 103 | 20600 | 164.3601 | 302.821 | 0.5428 | 13.572 | 7.9786 | 7.9046–8.0527 | 3.5757 | 3.2954–3.8528 | 7.9088 | 7.8354–7.9822 | 0.3037 |
| S3-D | D_gen_1 | 55 | 11000 | 137.2704 | 305.195 | 0.4498 | 26.308 | 12.4791 | 12.3627–12.5956 | 6.7340 | 6.3472–7.1167 | 12.4083 | 12.2925–12.5240 | 0.2233 |
| S3-D | D_gen_2 | 55 | 11000 | 136.4647 | 305.312 | 0.4470 | 26.306 | 12.4059 | 12.2901–12.5216 | 6.6585 | 6.2723–7.0407 | 12.3327 | 12.2176–12.4477 | 0.2177 |
| S3-D | D_gen_4 | 55 | 11000 | 136.4463 | 305.403 | 0.4468 | 26.308 | 12.4042 | 12.2885–12.5199 | 6.6552 | 6.2688–7.0373 | 12.3298 | 12.2148–12.4449 | 0.2188 |
| S3-B | B_gen_1 | 43 | 8600 | 126.4142 | 301.074 | 0.4199 | 33.400 | 14.6993 | 14.5619–14.8367 | 7.5546 | 7.0809–8.0233 | 14.6083 | 14.4718–14.7449 | 0.2131 |
| S3-B | B_gen_2 | 43 | 8600 | 127.5185 | 300.971 | 0.4237 | 33.401 | 14.8277 | 14.6891–14.9663 | 7.6855 | 7.2107–8.1552 | 14.7384 | 14.6007–14.8762 | 0.2167 |
| S3-B | B_gen_3 | 43 | 8600 | 127.8937 | 301.002 | 0.4249 | 33.401 | 14.8714 | 14.7323–15.0104 | 7.7284 | 7.2531–8.1985 | 14.7809 | 14.6428–14.9191 | 0.2169 |

## Board intervals (lowest to highest end over the three scored reps)

| Board | Total mean | Total interval | Marginal mean | Marginal interval | Window mean | Window interval | Idle subtracted (W) |
|---|---|---|---|---|---|---|---|
| P4 | 7.9806 | 7.9046–8.0568 | 3.5760 | 3.2919–3.8571 | 7.9091 | 7.8334–7.9850 | 0.29952 ± 3.7% ± 0.948% |
| S3-D | 12.4297 | 12.2885–12.5956 | 6.6826 | 6.2688–7.1167 | 12.3569 | 12.2148–12.5240 | 0.20707 ± 3.7% ± 0.971% |
| S3-B | 14.7995 | 14.5619–15.0104 | 7.6562 | 7.0809–8.1985 | 14.7092 | 14.4718–14.9191 | 0.20408 ± 3.7% ± 0.972% |

## Tokens per joule (means of the scored reps)

| Board | Total | Marginal | Window |
|---|---|---|---|
| P4 | 125.30 | 279.64 | 126.44 |
| S3-D | 80.45 | 149.65 | 80.93 |
| S3-B | 67.57 | 130.63 | 67.99 |

## Predictions: comparisons and verdicts

- **P1** (S3-B total J/token in 10–25 mJ): interval 14.5619 to 15.0104 mJ. Threshold: 10 ≤ x ≤ 25 mJ at both ends. → **HELD**.
- **P2** (P4 total < S3-B total): difference interval [P4 low - S3-B high, P4 high - S3-B low] = -7.1058 to -6.5051 mJ. Threshold: difference < 0. → **HELD**.
- **P4** (S3-D total < S3-B total): difference interval [S3-D low - S3-B high, S3-D high - S3-B low] = -2.7219 to -1.9664 mJ. Threshold: difference < 0. → **HELD**.
- **P3** (P4 marginal ≤ 0.6 × S3-B marginal): ratio interval [P4 low / S3-B high, P4 high / S3-B low] = 0.4015 to 0.5447. Threshold: ratio ≤ 0.6. → **HELD**.
- **P5 against S3-B** (P4 idle − S3 idle ≥ 0.2 W): difference interval [P4 low - S3-B high, P4 high - S3-B low] = 0.09055 to 0.10034 W. Threshold: ≥ 0.2 W. → **FAILED** (outcome observed before lock).
- **P5 against S3-D** (P4 idle − S3 idle ≥ 0.2 W): difference interval [P4 low - S3-D high, P4 high - S3-D low] = 0.08740 to 0.09767 W. Threshold: ≥ 0.2 W. → **FAILED** (outcome observed before lock).


## Failed and rerun attempts, and the meter

**Idle:**
- `D_idle_1` (11 zero-length sync glitches, before the RC filter and the glitch rule) is superseded.
- `D_idle_2r` (end-of-window ping missed; logger snapshot lost) was rerun. Its logs are in `logs/lost_ping/`.
- The S3-B idle ×3 of 10-13 (no fresh reset) is superseded by `B_idle_{1,2,3}r`.
- Scored idle: `{B,D,P4}_idle_{1,2,3}r`, all with a fresh reset and passing every check.

**Generate:** `D_gen_3` aborted at the start, with 0 generations. The board answered `E no prompt (send P first)`:
the prompt line was lost right after boot.
- **Classification:** a technical failure, rerun as `D_gen_4` (attempt 4 of 6).
- **My script's error:** it first mislabelled `D_gen_3` as a 3% gate failure (commit message `1672808`); NOTES
  records the correction.
- **Pre-approved fix not needed:** Mark pre-approved a ping-before-prompt fix in case this recurred. It didn't, so
  `run.py` is unchanged since the lock.

**Meter cross-check** (one `--meter` rep per board: `P4_gen_1`, `D_gen_1`, `B_gen_1`):
- **Not possible.** The meter showed 0.00 A, and its mWh and timer didn't move, on all three boards.
- **Threshold:** it registers a phone load, so its threshold is above ~110 mA. It sat upstream of the logger, so the
  logger figures don't include it.
- **Status:** those reps stand on the logger, per the PREREG.

**USB dropout:** after the meter came out of the P4 chain, the P4 had power (56.8 mA) but didn't enumerate until the
breakout was reseated. This was between reps; no data is affected.

## Deviations from the brief (all decided before the lock; detailed in PREREG.md)

- **Instrument:** the USB power logger instead of the inline meter; error bars from the DMM's spec and the rep
  spread.
- **Builds:** sync-pin builds instead of the exact earlier binaries, verified at step d.
- **FAST_SAMPLE=1:** the greedy path never uses it.
- **Fresh reset** before every idle and generate rep.
- **S3-B step d reference:** 33.40 same-bench, not the 32.7 benchmark (deviation 1).
- **Post-generation idle:** "from the inter-generation gaps" was replaced by a separate 60 s exploratory capture
  after each generate rep.
- **Room temperature:** not measured.

## Open items

- **The bench is ~2% slower than the benchmarks for S3-B and S3-D.**
  - S3-B: 33.40 against 32.7 (+2.14%). S3-D: 26.31 against 25.8 (+1.97%). P4: 13.57 against 13.7 (−0.9%).
  - The same offset shows on the non-sync builds (S3-B 33.40 in v1; S3-D 26.305), so it isn't the sync pin.
  - Unexplained.
- **Suspected clone INA226.** Raw gains are off by −6% (current) and +5% (VBUS), with a ~3.1 mV bus grid and
  ~26 mV bus noise.
  - The calibration corrects the gains, and the session rechecks held (−0.01% on 10-14).
  - Its long-term gain stability isn't established.
- **Meter below threshold:** the planned cross-check was not possible on any board.
- **Post-run idle is above fresh-reset idle.** In the 60 s exploratory capture after each rep:

  | Board | After a rep | Fresh-reset idle | Difference |
  |---|---|---|---|
  | S3-B | 0.2131–0.2169 W | 0.2041 W | +4 to +6% |
  | S3-D | 0.2177–0.2233 W | 0.2071 W | +5 to +8% |
  | P4 | 0.3037–0.3049 W | 0.2995 W | +1.4 to +1.8% |

  - This matches the 10-14 diagnosis: idle current rises after any `G` and stays up.
  - For S3-D the post-run figure exceeds the ±3.7% idle term used for the marginal error bar. Marginal J/token uses
    fresh-reset idle, per the locked definition.
- **Rep-1 offsets on S3-D and S3-B** (both rep 1s were meter reps, after the meter insertion power-cycled the board).
  - **S3-D:** `D_gen_1` is +0.6% above reps 2 and 4 (0.4498 W against 0.4470 / 0.4468 W).
  - **S3-B:** `B_gen_1` is −0.9% below reps 2 and 3, and power rose rep by rep (0.4199 → 0.4237 → 0.4249 W).
  - **Common factors:** ms/token was identical within each board, and the meter was upstream of the logger. The
    offsets go in opposite directions, so there's no consistent meter-rep effect.
  - **Status:** unexplained; included in the rep spread.
