# Lock A1, optional arm T-2133: bands recomputed from the measured bandwidth (written before any measured 2133 request)

**Written 2026-11-27, after BW(2133) and before the first T-2133 request.** Lock: `docs/candidates/inkling-2-mini-3060-2026-11.md`
+ A1, sha256 `312c4fdb4b4da9d5d8d401ba48250807e3f8279cabdf6352b8aea1ab7afd86c4`. Go condition 6 met: Mark did the BIOS change.

## State

- Idle before reboot (2026-11-27 21:54 UTC): card 7 MiB, no compute process, no transfers, load 0.00.
- Mark set DDR4-2133 in the BIOS. Board B550 Phantom Gaming 4/ac, BIOS P4.00 (`/sys/class/dmi/id`).
- `dmidecode -t memory` (run by Mark, `t2133/dmidecode-2133.txt`): 4 × 16 GB F4-3200C16-16GVK, Speed and Configured
  Memory Speed **2133 MT/s**, configured voltage 1.2 V. Timings and gear mode were not readable from Linux (A1.9).

## Bandwidth (`stream_read.c` sha256 `09858c7f…`, binary `0ff077fb…`, 4 threads, each run best of 8)

| | when (UTC) | runs | median |
|---|---|---|---|
| **BW(3000), scored: A1.4** | 2026-11-25 20:33 | 42.17, 42.45, 42.30 | **42.30 GB/s** |
| BW(3000), pre-reboot today (context only) | 2026-11-27 21:54 | 42.05, 42.21, 42.26 | 42.21 GB/s |
| **BW(2133)** | 2026-11-27 22:09 | 31.40, 31.54, 31.61 | **31.54 GB/s** |

**Bandwidth ratio = 31.54 / 42.30 = 0.7456.**

## Scored bands (±10% of the bandwidth ratio, A1.6)

| # | cell | decode(3000), main arm 2026-11-25 | band on decode(2133)/decode(3000) | implied decode(2133) |
|---|---|---|---|---|
| **A1-P8** | U-8k short | 16.40 | **[0.6711 .. 0.8202]** | 12.23 [11.01 .. 13.45] |
| **A1-P9** | U-32k short | 16.39 | **[0.6711 .. 0.8202]** | 12.22 [11.00 .. 13.44] |

Sensitivity (not scored): with today's pre-reboot 42.21 the ratio is 0.7472 and the band is [0.6725 .. 0.8219].

## Deviation, recorded now

A1 says BW(3000) and the 3000 cells come "from the same day". The main arms ran on 2026-11-25. T-2133 was deferred
(addendum 2026-11-26), so it runs two days later. The scored inputs stay the ones the lock names (A1.4's median
and the main arm's U-8k/U-32k short). Bandwidth at 3000 read 42.30, 42.21 and 42.21 GB/s on 11-25, 11-26 and 11-27.

## Unscored analysis, fixed now so it is not fitted after the fact

Fixed per-token overhead check, prompted by the Flash-Next observation (record README, 2026-11-27): fit
t = a + k / BW to the two U-8k short points (t = 1/decode). Report a, the overhead not explained by bandwidth, as a
share of t at 3000. Pure bandwidth-bound means a ≈ 0 and ratio ≈ 0.7456. A large a means a ratio above that.
