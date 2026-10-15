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

