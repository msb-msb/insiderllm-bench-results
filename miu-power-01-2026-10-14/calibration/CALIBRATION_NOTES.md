# Calibration notes

## 2026-10-13 (session "2026-10-13")

Logger uid E66038B7130A6739, firmware src 5a14af1eb9d5e3f9, INA226 at 0x44.
Points: `host/calibration_points.jsonl`. Fit: `host/calibration.json`.

**DMM:** Aneng SZ20. DC current ±(0.5% + 3 digits), DC volts ±(0.2% + 10 digits)
(published spec). DC mA on auto-ranging; all five current points read on the same range.

### Result

| | Fit | Residuals |
|---|---|---|
| Current | I = 1.065384 × I_raw + 0.062 mA (5 loads + zero) | ≤ 0.12% of reading, 26–146 mA: **PASS** (0.5% criterion) |
| VBUS | V = 0.951643 × V_raw + 11.6 mV (3 unloaded points) | ≤ 0.7 mV (0.03%) |

Raw errors before calibration: current −6.1% to −6.4%, VBUS +4.2% to +5.1%.
Both channels are linear after a gain + offset fit; a quadratic didn't improve
the current residuals beyond the DMM's resolution.

**Drift:** "1x100" read −6.295% raw, "1x100 repeat" (end of session) −6.266%:
0.03% across the session.

### Suspected clone INA226

The part reports a genuine identity (mfr 0x5449, die 0x2260) but:

- raw bus gain is about **+5%** (spec ±0.1%);
- raw current gain is about **−6%**; the shunt tolerance would explain ~1%;
- bus readings fall on a ~3.1 mV grid instead of the 1.25 mV LSB;
- bus noise is ~27 mV sd on both USB and AA cells, so it isn't supply ripple.

Both channels are linear after calibration, so the fit corrects them, but
a part like this may not hold its gain. **Before each measurement session,
recheck one point:** `pl.py cal-point --label "1x100 check <date>" --r-ohm 98.60`
against the DMM. If the calibrated error is over 0.5%, recalibrate.

### Deviations from CALIBRATION.md

- **VBUS points "AA cell" and "2xAA"**: the male breakout was unplugged and the
  cells were connected into the female side, giving points well below 5 V. They
  were 5 s scripted captures from the sample frames, not the cal-vbus 1 s keypress
  window. With them the voltage fit is gain + offset rather than gain-only.
- **"1x100 load" VBUS point is excluded from the fit** (`exclude_from_fit` in the
  points file). It was measured at the cable end under load, so it includes the
  female breakout + cable drop that the INA226's VBUS pin (before the shunt)
  doesn't see. It is kept as a cross-check: +12.4 mV at 48 mA, i.e. ~0.26 Ω.
- **Top current point is 3 × 100 Ω in parallel (~146 mA), not 4 (~200 mA)**:
  the DMM's mA jack is fused at 250 mA.
- The floating-input capture (male breakout unplugged, nothing on the female
  side) read median 0 counts with 60 Hz pickup up to 0.4 V; no fixed offset.

### Noise sweep (`pl.py noise --sweep --secs 5`, ~18:30, output side empty)

| shunt_ct | bus_ct | avg | rate | mean I | I sd/sample | VBUS sd |
|---|---|---|---|---|---|---|
| 1100 µs | 140 µs | ×1 | 821 Hz | −0.082 mA | 0.034 mA (1.37 LSB) | 25.8 mV (default) |
| 588 µs | 140 µs | ×1 | 1404 Hz | −0.079 mA | 0.045 mA (1.78 LSB) | 25.7 mV |
| 332 µs | 140 µs | ×1 | 2163 Hz | −0.080 mA | 0.062 mA (2.47 LSB) | 24.8 mV |
| 2116 µs | 140 µs | ×1 | 452 Hz | −0.079 mA | 0.024 mA (0.95 LSB) | 25.1 mV |
| 1100 µs | 140 µs | ×4 | 206 Hz | −0.086 mA | 0.025 mA (0.98 LSB) | 16.0 mV |

Default (1100 µs shunt, 140 µs bus, ×1) kept. The ~26 mV VBUS noise persists on
battery input too (AA cell and 2xAA points), so it's chip/input noise, not USB ripple.

## 2026-10-14 session-start recheck

Logger moved to Miu's rear USB port (by-id unchanged). 1x100 (98.60 Ω): DMM 51.03 mA, raw 47.835 mA
(−6.26%; 10-13 end of session −6.266%), calibrated 51.025 mA (**−0.01%: PASS**, limit 0.5%). No recalibration.

Two points-file entry errors fixed (Mark's instructions):
- The recheck point was first entered as "3x100 parallel", 33.05 Ω. It has been relabelled "1x100 recheck 10-14", 98.60 Ω.
- A row entered as "1x100 recheck 10-14" with DMM 21.09 µA (raw 26.42 mA) is kept but tagged `exclude_from_fit`:
  "DMM entry error at recheck 10-14, load and units mislabelled".

## 2026-10-14: DMM current resolution

All five 10-13 current points were read on the SZ20's **250 mA range, 0.01 mA steps** (Mark).
- The 2x100 parallel and 3x100 parallel points displayed 99.20 and 145.50 mA. They were entered without the
  trailing zero, so the points file looks like it has 0.1 mA steps.
- The values are unchanged. The two rows now record `dmm_display`, `dmm_range` and `dmm_resolution_A` with a note.
- power-01's PREREG takes its reference-instrument term from this: at 0.01 mA steps, ±(0.5% + 3 digits) is
  ~0.53–0.58% at 40–107 mA.
