# Arm P bands (lock tamanna-3090-offload-powercap-2026-11.md, sha256 6329e122…2d8b, P4 PP3/PP4)

Computed from block B420a (420 W, run 2026-11-25 19:45-19:47 PST) and committed **before block B350 runs**.
B420a: no void request, every prefill gen 4 x16, no swap, NVMe 0 MiB.

B420a medians of 3:

| measure | value |
|---|---|
| decode 512 | 42.00 tok/s |
| decode 4096 | 41.38 tok/s |
| prompt 4096 | 1,503.2 tok/s |
| P0 = prefill-4096 watts | 378.2 W (25 samples per window) |
| D0 = decode-512 watts | 416.6 W |
| decode-4096 watts | 417.4 W |

Recorded before the capped blocks:
- **Decode sits on the 420 W limit:** `sw_power_cap` was active in 100% of decode samples. D0 = 416.6 W is outside
  the PP2 decode band of [230..380] W, so **PP2-decode misses**.
- P0 = 378.2 W is inside the PP2 prefill band of [330..420] W.
- `sw_power_cap` was also active in 100% of prefill samples, although the mean instant draw there is below 420.
  Prefill watts rose across the 3 reps: 362.4, 378.2, 415.4.

With D0 above every cap, all four caps take the C < D0 branch of PP4. P0 = 378.2 W is above every cap
(350 W is the highest), so every cap also takes the C < P0 branch of PP3.

| cap C | PP3 prefill-4096 ratio | prompt 4096 tok/s | PP4 decode ratio | decode 512 tok/s | decode 4096 tok/s |
|---|---|---|---|---|---|
| 350 W | [0.935..0.995] | [1,405..1,495] | [0.924..1.020] | [38.81..42.84] | [38.24..42.21] |
| 320 W | [0.885..0.966] | [1,330..1,453] | [0.900..1.020] | [37.80..42.84] | [37.24..42.21] |
| 280 W | [0.815..0.926] | [1,225..1,391] | [0.900..1.020] | [37.80..42.84] | [37.24..42.21] |
| 250 W | [0.760..0.892] | [1,143..1,341] | [0.900..1.020] | [37.80..42.84] | [37.24..42.21] |

The PP4 floor of 0.90 binds at 320, 280 and 250 W, where (C/D0)^0.33 − 0.02 falls below 0.90.

PP5 (prefill ratio below decode ratio at 250 W; decode ratio ≥ 0.97 at 280 W) and PP6 (B420b decode 512 within ±2%
of 42.00, so [41.16..42.84]) are unchanged.
