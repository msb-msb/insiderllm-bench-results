# Lock A1: bands recomputed from the day's bandwidth (written before any measured request)

**Written 2026-11-25, after A1.4 and before the gates and the first measured request on Tamanna.**
- Lock: `docs/candidates/inkling-2-mini-3060-2026-11.md` + A1, commit `9c2a7dee`, sha256
  `312c4fdb4b4da9d5d8d401ba48250807e3f8279cabdf6352b8aea1ab7afd86c4`.
- Mirror: `d946fb3`, with the public hash checked equal.

## A1.4 bandwidth

The measurement ran at 2026-11-25 12:33 PST (20:33 UTC) on an idle card: 1 MiB used, no compute process.
`stream_read.c` (sha256 `09858c7f…`), `gcc-13 -O3 -fopenmp`, 4 threads, each run best of 8.

| | runs | median |
|---|---|---|
| **Tamanna, read, 4 threads** | 42.17, 42.45, 42.30 GB/s | **BW_Tamanna = 42.30 GB/s** |
| Tamanna, read, other thread counts (context only) | 1: 11.82; 2: 23.55; 8: 40.25 | |
| Tamanna, STREAM 5.10 triad, 4 threads (record only) | 26,691.1, 26,725.7, 26,660.0 MB/s | 26.69 GB/s |
| **Rushuna, read, 4 threads** (from its record, 2026-11-25) | | **BW_Rushuna = 26.94 GB/s** |

STREAM was built with `gcc-13 -O3 -march=native -fopenmp -DSTREAM_ARRAY_SIZE=80000000 -DNTIMES=20` and run with
`OMP_PROC_BIND=spread`; its source sha256 is `a52bae5e…`.

**Stop rule (< 38 GB/s): not triggered.** Tamanna is at DDR4-3000. The board is a B550 Phantom Gaming 4/ac on BIOS
P4.00.

**r = 42.30 / 26.94 = 1.5702.**

## Scored bands (±15%)

| # | cell | Rushuna value | × r | band |
|---|---|---|---|---|
| **A1-P1** | U-8k short decode | 10.41 | **16.35** | **[13.89 .. 18.80]** |
| A1-P2 | L-8k short decode | 9.92 | 15.58 | [13.24 .. 17.91] |
| A1-P3 | U-32k short decode | 10.37 | 16.28 | [13.84 .. 18.72] |
| A1-P3 | U-256k short decode | 10.36 | 16.27 | [13.83 .. 18.71] |

The other predictions, A1-P4 to A1-P7, are unchanged from the lock: they don't depend on bandwidth.

**The CPU confound (A1.6) applies.** A result inside a band is consistent with bandwidth, but doesn't rule out the CPU
explanation.

**T-2133 is not run today.** Go condition 6 isn't met: Mark is not available for the BIOS changes. A1-P8 and A1-P9
stay pending, as an optional arm.
