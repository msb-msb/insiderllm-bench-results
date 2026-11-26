# Tamanna (RTX 3090 24 GB): power cap sweep on a dense 27B, Arm P, 2026-11-25

## Pre-registration and scope

- **Lock:** `docs/candidates/tamanna-3090-offload-powercap-2026-11.md`, LOCKED 2026-11-25 in `3ad713de`.
  - sha256 `6329e12202fe9037928303d5cbf651e7d25f158ce826c207693bdd2b08f42d8b`.
  - Mirror `455b72a`; the public raw copy hashed equal before the first block.
- **Bands for the capped blocks:** computed from B420a and committed in `83f2b560` before B350 ran (`bands-P.md`).
- **Claims under test:** from the YouTube video "Two $300 GPUs vs RTX 5090". They are community claims.
- **Arm O (expert offload) was not run:** Qwen3-30B-A3B Q4_K_M is not on Tamanna (lock P0). The MoE leg of Arm P
  was skipped for the same reason. This record is Arm P on the dense model only.

## Clock

- `sequence.log` and the `state-*.txt` headers are UTC: 2026-11-26 03:45 to 06:49.
- `run.log` and the `power-*.csv` timestamps are Unix time or Tamanna's local time (PST): 2026-11-25 19:45 to 22:49.
- The gaps between blocks are Mark's sudo steps.

## Setup

- **Rig:** Tamanna.
  - RTX 3090 24 GB on PCIe 4.0 x16; every prefill read gen 4 x16.
  - Ryzen 7 5700X; 64 GB DDR4-3000.
  - Driver 580.178.04; VBIOS 94.02.42.80.14; persistence on.
- **Card limits as found:** 420 W limit and 420 W default (min 100, max 450). This is a partner card, not the
  350 W reference board.
- **Model:** `Qwen3.8-27B-UD-Q4_K_XL.gguf`, sha256 `bee238bb…1372`. This is the NariQ record's R-Q4 file, hashed at
  the start and end of the run (`rec/sums-at-start.txt`, `rec/sums-at-end.txt`).
- **Build:** the NariQ mainline `llama-server` (sha256 `7b55b988…89d7`). `/props` reported `b12431-a946eb541` in
  every block.
- **Command (lock P1):** `-ngl 99 -fa on -c 8192 -np 1 --fit off -lm mmap -t 4 --cache-ram 0`. `--cache-ram 0` was
  set on every server start.
- **Requests:**
  - streamed chat with a fresh nonce line first;
  - thinking off, temperature 0, `cache_prompt` false, `ignore_eos`, `max_tokens` 512;
  - per block: 1 cold request (excluded), then 3 at 512 prompt tokens, then 3 at 4,096.
  - The prompts are the NariQ files, `fe9c7420…` and `7ad80637…`.
- **Power:** `nvidia-smi -lms 100` all through each block. Watts are the mean `power.draw.instant` inside each
  request's prefill window [t0 + 0.2 s, t0 + TTFT] and decode window [t0 + TTFT + 0.5 s, end]. Each cell is the
  median of 3.
  - Prefill watts are scored on the 4096 cell only, where each window has 25 samples. The 512 cell's prefill window
    has 2.
- **Harness:** `harness/`.
  - `bench_p.py` is NariQ's `bench_t.py` plus the power sampler, the windows, the void re-run and the limit check.
  - `run_block.sh` handles the precheck, the ≤ 50 °C start-temperature wait and memwatch v3.
  - `summarize_p.py` was written during the run; it only reads the results.
- **State:** CPU governor `powersave` (amd-pstate) in every block. MemAvailable never fell below 61.6 GiB.

## Results

Every block passed its checks:
- the limit was checked before the block started;
- **no void request in any block**;
- no swap-out (`pswpout` unchanged at 4603 across all blocks), 0 MiB NVMe read and gen 4 x16 throughout;
- no `hw_slowdown`;
- `sw_power_cap` was active in 100% of decode samples in every block, 420 W included.

Full table: `rec/summary.txt`.

| limit | decode 512 | decode 4096 | prompt 4096 | W decode | W prefill 4096 | J/token decode | SM MHz decode | ratio vs 420 W (decode / prompt) |
|---|---|---|---|---|---|---|---|---|
| **420 W (default)** | **42.00** | 41.38 | 1,503.2 | 416.6 | 378.2 | 9.92 | 1,795 | 1.000 / 1.000 |
| 350 W | 41.28 | 40.71 | 1,438.7 | 349.9 | 343.5 | 8.48 | 1,616 | 0.983 / 0.957 |
| 320 W | 40.69 | 40.17 | 1,394.7 | 319.1 | 318.8 | 7.84 | 1,508 | 0.969 / 0.928 |
| 280 W | 36.17 | 36.08 | 1,318.6 | 274.7 | 273.2 | **7.59** | 1,053 | **0.861** / 0.877 |
| 250 W | 29.38 | 29.46 | 1,226.6 | 251.1 | 249.0 | 8.55 | 808 | **0.700** / 0.816 |
| 420 W (restored) | 41.95 | 41.37 | 1,506.3 | 418.2 | 361.1 | 9.97 | 1,803 | 0.999 / 1.002 |

Speeds are tok/s, medians of 3. The memory clock read 9,501 MHz in every block. The highest card temperature was
72 °C (B420b).

**Restore:** `power.limit` 420 W, `enforced.power.limit` 420 W and `power.default_limit` 420 W, logged 2026-11-25
22:49:06 PST in `rec/final-limit.txt`. The card was at 1 MiB.

## Predictions (lock P4), scored

| # | prediction | band | measured | verdict |
|---|---|---|---|---|
| PP1 | B420a decode 512 / decode 4096 / prompt 4096 | [39.9..44.1] / [39.3..43.5] / [1,437..1,588] | 42.00 / 41.38 / 1,503.2 | **inside** |
| PP2 | B420a prefill watts / decode watts | [330..420] / [230..380] W | 378.2 / **416.6** | prefill inside, **decode outside** |
| PP3 | prompt 4096 ratio at 350 / 320 / 280 / 250 W | bands-P.md | 0.957 / 0.928 / 0.877 / 0.816 | **inside, all four** |
| PP4 | decode ratio (512 and 4096) at 350 / 320 W | [0.924..1.020] / [0.900..1.020] | 0.983, 0.984 / 0.969, 0.971 | **inside** |
| PP4 | decode ratio at 280 / 250 W | [0.900..1.020] | 0.861, 0.872 / 0.700, 0.712 | **outside** |
| PP5 | at 250 W, prefill ratio below decode ratio; decode ratio ≥ 0.97 at 280 W | – | 0.816 vs 0.700; 0.861 | **outside, both parts** |
| PP6 | B420b decode 512 within ±2% of B420a | [41.16..42.84] | 41.95 (0.999) | **inside**; no drift flag |

**The decode prediction was wrong in direction.** The lock expected bandwidth-bound decode to lose less than
prefill at every cap. That held at 350 and 320 W. **From 280 W down, decode lost more than prefill.** The memory clock
never moved (9,501 MHz). What fell was the SM clock: from 1,508 MHz at 320 W to 1,053 at 280 and 808 at 250.

**Reading (hypothesis, not tested here).** GDDR6X at full clock takes a large, fixed share of board power. Decode
also keeps the card on its limit even at 420 W. Under a cap, the memory's share stays, so the GPU core gets what is
left. Below about 300 W the core clock falls far enough that the dequantize-and-matmul work, not memory bandwidth,
sets decode speed. Memory power was not measured separately.

## Claim scoring (lock P5): "280 W saves ~70 W for <1% speed"

Compared at 350 W (the 3090 reference board power) and 280 W:

| phase | speed at 280 W vs 350 W | watts saved, 350 → 280 W | speed part (≥ 0.99) | watts part ([50..90] W) | claim |
|---|---|---|---|---|---|
| decode (512) | 36.17 / 41.28 = **0.876 (−12.4%)** | 349.9 − 274.7 = **75.2 W** | fails | holds | **does not hold** |
| prefill (4096) | 1,318.6 / 1,438.7 = **0.917 (−8.3%)** | 343.5 − 273.2 = **70.3 W** | fails | holds | **does not hold** |

- **The watts half is right:** about 70 W saved.
- **The speed half is not.** On this card and model, 280 W costs 8% of prefill speed and 12% of decode speed.
- **My lock prediction was half right:** prefill came out as predicted (watts hold, speed fails). Decode did not: I
  predicted the speed would hold and the watts would fail, and it was the reverse.

**Reported, not scored:**
- **From the card's own 420 W default:** 280 W saves 141.9 W in decode for −13.9% speed.
- **Energy per decoded token:** lowest at 280 W, 7.59 J, which is −23% vs 420 W. **320 W** gives 7.84 J (−21%) for
  only −3.1% decode and −7.2% prefill. 250 W is worse than 280 W on both speed and energy (8.55 J).

## Limits

- One card (a 420 W partner board), one dense model, one build, one day.
- The claim's video used different GPUs, so this measures the claim on a 3090, not its source.
- The power readings are the driver's `power.draw.instant`. No wall meter was used.
- The 512-token prefill window is too short for power, so prefill watts come from the 4096 cell only.
- 3 requests per cell. Temperature never reached a throttle, and `hw_slowdown` stayed at 0.
- Arm O and the MoE leg were not run (no model on Tamanna).

## Deviations from the lock

1. **The first B420a launch failed with rc 127.** The script path was relative and wrong. Nothing ran: no
   `sequence.log` was written and no server started. It was relaunched with the absolute path at 19:45 PST.
2. **`summarize_p.py` was added during the run, after B350.** It reads the results only. Its hash is in
   `rec/sums-at-end.txt`.

## Files

- `bands-P.md`: the bands, committed before B350.
- `rec/`, per block:
  - `results-*.json`: every request, its timings, power windows, swap, NVMe and PCIe;
  - `power-*.csv`: 100 ms samples;
  - `server-*.log`, `state-*.txt`, `out-*.txt`, `memwatch-*`.
- `rec/run.log`, `rec/sequence.log`, `rec/card-1s.csv`.
- `rec/summary.txt`, `rec/final-limit.txt`.
- `rec/sums-at-start.txt`, `rec/sums-at-end.txt`.
- `harness/`.
