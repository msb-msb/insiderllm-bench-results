# Calibrating the power logger (run on 2026-10-13, when the hardware arrives)

**Goal:** fit current gain and offset against a DMM used as the reference ammeter,
check VBUS against the same DMM, store the coefficients in
`host/calibration.json` (the host software applies them to every run), and
report residuals per point.

**Pass criterion:** every point at 25–200 mA has a residual within **0.5% of
reading** after calibration.

**What this calibrates against:** the fit is only as good as the DMM. Write down the
DMM's model, the range used and its spec (e.g. "±(0.8% + 3 digits)"); `cal-fit
--dmm` records it. The 0.5% criterion checks the logger's linearity and its
agreement with this DMM, not absolute accuracy beyond the DMM's.

All commands run from `~/Desktop/esp32-llm/tools/power-logger/host`. Each one
discovers the logger itself; nothing touches the S3 or P4 ports. Every point is
appended to `host/calibration_points.jsonl` under a session name, today's date by
default.

## You need

- The logger, flashed with the **real** build (`firmware/build.sh`, not `--sim`),
  plugged into Miu on its own USB port. `pl.py id` shows `state=running`.
- **The USB-A male side plugged into Miu,** so VBUS (about 5 V) reaches IN+. Nothing on the
  female side to start with.
- 100 Ω 1/4 W resistors (at least 4), and clip leads or a breadboard.
- **A DMM.** Before the 200 mA point, check its mA range. Many meters have a 200 mA range that
  reads over-range at ~200 mA, and its fuse may be rated near that. If so, use the next range
  up (400 mA, or the 10 A jack) for that point, and note the change.

**The loads** go across the output: the female breakout's VBUS and GND pads. The DMM goes in
SERIES with them as the ammeter. The resistor values don't matter, because the DMM is the
reference. What matters is that the current is stable while you read.

```
  female VBUS ──── DMM (mA, in series) ──── load ──── female GND
```

## Steps

### 0. Identity and configuration

```bash
python3 pl.py id
python3 pl.py config
```

Check:

- `identity ok: mfr=0x5449 die=0x2260`;
- `addr=` in CFG2 matches the module (0x44 for ours: the INA226 address is set by the
  module's A1/A0 straps, so it is per module). `no answer on I2C at 0x..` usually means a
  different address: scan for it as in the README ("Finding the INA226's address"), set
  `PL_INA226_ADDR` in `pl_config.h`, rebuild and reflash;
- `cal=2048`, `current_lsb_nA=25000`, `period_us=1240`;
- `mode=alert` if ALERT is wired, `mode=poll` if not.

Leave it powered for 5 minutes before step 1, so the INA226 and the shunt reach their working
temperature.

### 1. Zero-current offset and noise (nothing on the output)

Remove everything from the female side: no DUT, no load, no DMM.

```bash
python3 pl.py cal-zero --secs 10
python3 pl.py noise --sweep --secs 5
```

`cal-zero` stores the mean reading at a true 0 A, which goes into the fit as a point with
y = 0. It also prints the standard deviation.

`noise --sweep` measures per-sample current noise at five conversion settings, then restores
the default (1.1 ms shunt, 140 µs bus, ×1). Paste its table into the calibration notes: it
settles the timing trade-off in `pl_config.h` with numbers. No noise figure is predicted here;
this is the first measurement of it.

### 2. VBUS against the DMM (DMM on DC volts)

Put the DMM's probes across the female side's VBUS and GND, which is the point the INA226
measures. Take two points:

```bash
python3 pl.py cal-vbus --label "open"            # no load
python3 pl.py cal-vbus --label "1x100 load"      # with one 100 ohm across the output too
```

For each: watch the live line until it settles. Press Enter at the moment you read the DMM,
then type its value in volts. A USB rail spans too little voltage to separate a voltage
offset from a gain, so the fit is gain-only through zero. Expect the logger's raw value
within about 0.1% of the DMM.

### 3. Known loads (DMM in SERIES, mA range)

Build each load, wire it through the DMM, and run `cal-point`. Then:

1. Watch the live line (1 s mean, plus the sd of the samples in it) until it stops drifting.
   Resistors warm up and change a little, which is why both readings are taken at the same
   moment.
2. Press **Enter at the moment you read the DMM**. The logger value saved is the mean of
   the samples from 0.5 s before to 0.5 s after the keypress.
3. Type the DMM reading in mA.

| Point | Load | Measured R (unpowered) | Expected | Notes |
|---|---|---|---|---|
| 1 | 2 × 100 Ω in series | 194.77 Ω | ~27 mA | 0.15 W total |
| 2 | 1 × 100 Ω | 98.60 Ω | ~54 mA | 0.29 W: over a 1/4 W rating, read promptly |
| 3 | 2 × 100 Ω in parallel | 49.68 Ω | ~107 mA | 0.29 W each: read promptly |
| 4 | 3 × 100 Ω in parallel | 33.05 Ω | ~160 mA | 0.29 W each, ~0.85 W total: **a few seconds only**. Connect, let it settle ~2 s, Enter, disconnect, then type the value |

The top step is 3 in parallel (~160 mA), not 4 (~200 mA), because the DMM's mA jack is fused
at 250 mA (2026-10-13). Expected currents are V/R at ~5.37 V (Miu's unloaded VBUS), before
the DMM's burden.

```bash
python3 pl.py cal-point --label "2x100 series"   --r-ohm 194.77
python3 pl.py cal-point --label "1x100"          --r-ohm 98.60
python3 pl.py cal-point --label "2x100 parallel" --r-ohm 49.68
python3 pl.py cal-point --label "3x100 parallel" --r-ohm 33.05
```

`--r-ohm` records the load's unpowered resistance as a cross-check only; the DMM's current
reading is the reference and the only thing the fit uses. `cal-fit` prints V/R against the
DMM and the implied series resistance V/I_dmm − R (the DMM's burden, plus resistor heating),
which should be a few ohms and similar at every point, and stores them in calibration.json
under `load_crosscheck`.

The DMM's burden voltage and the 5 V supply's droop make the real currents a little
lower than nominal. That doesn't matter: the DMM reads what flows. After each point
`cal-point` prints the uncalibrated error against the DMM. Up to about ±1% is just the
shunt's tolerance; much more than that suggests a wiring problem.

**Recommended:** repeat point 1 or 2 at the end. Same load, a new label, e.g. "1x100
repeat". The fit then also shows drift.

### 4. Fit, report, store

```bash
python3 pl.py cal-fit --dry-run                   # look first
python3 pl.py cal-fit --dmm "<model>, <range>, <spec>"
```

**What it prints:**

- current gain and offset: `I = gain * I_raw + offset`, least squares over the load points
  plus the zero point;
- for each point: the DMM value, raw, calibrated, residual in mA and in % of reading, the
  uncalibrated error, and the logger's sd;
- the VBUS gain and its residuals;
- **PASS/FAIL** against the criterion.

`cal-fit` writes `host/calibration.json` and keeps any previous one as
`calibration.json.prev`. From then on, `monitor`, `record`, plots and power-01 runs report
calibrated values. Every run's `meta.json` records which calibration it used.

**If a point fails:** first suspect that reading. It may have been taken before it settled,
or a resistor may have been hot at 200 mA. Re-take it with the same label suffixed "(retake)",
delete the bad line from `calibration_points.jsonl` (keep a note of it in the calibration
notes), and refit. If the residuals curve (the middle points one sign, the ends the other),
the response isn't linear. Stop and report rather than adding terms to the fit.

### 5. Record it

Commit `host/calibration.json` and `host/calibration_points.jsonl` on the `power-logger`
branch, along with the noise table and the DMM details. Then go on to power-01: the cheap
meter goes inline for one cross-check run per board (see `evals/power-01/NOTES.md`).

## What the numbers mean afterwards

The logger's per-run energy carries three uncertainties:

1. **The calibration residual:** ≤ 0.5% by the pass criterion; the actual figure is in
   calibration.json.
2. **The DMM's own accuracy**, which the fit inherits.
3. **A run-level statistical part,** which is negligible over 10⁵ samples.

The power-01 RESULTS should quote 1 and 2 separately.
