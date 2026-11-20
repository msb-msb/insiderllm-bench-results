# llama.cpp v1.0.0 vs 0.9 builds, Qwen3.5-27B MTP on/off, Tamanna RTX 3090 (2026-11-20)

Record for the pre-registration `docs/candidates/llamacpp-v1-mtp-3090-2026-11.md`: lock commit **a39c4818** (sha256
`ad62a049…2fd3`, published byte-exact to the mirror's `candidates/` before any download, build or measurement), plus
**A1** (Mark, PCIe check reading) and **D1** (build deviations), appended in d988e081 during round 1 before any cell
was summarized. Section numbers below are the lock's.

## Result

Decode tok/s, mean of 3 measured requests (min..max). Rule P4 per M5 with A1; no cell void after the one re-run.

| arm (build) | short, MTP off | long, MTP off | short, MTP on | long, MTP on |
|---|---|---|---|---|
| **O** b12199 (0.9.0-dev, the report's baseline) | 43.93 (43.92..43.94) | 43.26 (43.24..43.28) | 52.63 (51.88..53.88) | 58.49 (54.85..61.02) |
| **Z** b12352 (0.9.0-dev, last 0.9 tag) | 44.02 (44.00..44.04) | 43.36 (43.35..43.38) | 71.85 (71.18..73.15) | 78.34 (72.86..82.00) |
| **V** v1.0.0 (b12359) | 44.02 (44.01..44.03) | 43.35 (43.34..43.36) | 74.49 (73.22..75.54) ¹ | 75.02 (71.13..81.85) |

¹ Re-run cell (M5): the interleaved cell was void on prompt_n (47..51, one measured request at 47). The re-run ran
11:28-11:31, after the main run (09:45-10:08), so it is not interleaved with the other arms.

**Predictions (M6):**
- **P1, MTP off: V within ±3% of O, and of Z. HOLDS.** V/O 1.002 at both prompts; V/Z 1.000 at both.
- **P2, MTP on: V faster than O, V/O in [1.30, 1.70]. MISSES.** Short 1.415, ranges apart: holds. Long 1.283, ranges
  apart: below the band's floor. V is faster than O at both prompts with no range overlap, but less faster than the
  band at the long prompt.
- **P3, MTP on: V within ±3% of Z. MISSES.** Short 1.037 (ranges apart; V's cell is the non-interleaved re-run), long
  0.958 (ranges overlap).

**What explains P3, and why it's not a version effect.** Z and V have the same inference code (lock M1: seven
commits apart, CI/examples/docs/version only). With MTP off they agree to 0.01 tok/s. With MTP on, a request's
decode speed follows its draft acceptance, and acceptance changes with the request's text (the nonce line differs
every time). Long-prompt measured requests:
- V: acceptance 0.308 / 0.380 / 0.314 → 71.1 / 81.8 / 72.1 tok/s;
- Z: acceptance 0.320 / 0.381 / 0.370 → 72.9 / 82.0 / 80.2 tok/s.

Z's mean is higher because two of its three draws had high acceptance. Three requests per cell gives MTP cells a
spread of about ±7% (V long: 71.1..81.8). The ±3% band in P3 was set without allowing for that. The miss is
reported as a miss; it doesn't show a speed difference between the two builds. V's re-run long requests (recorded,
not used, since that cell wasn't void) averaged 75.61 (72.86..76.99).

**Descriptive (no predictions):**
- **MTP on vs off, same build:** O 1.198× (short) / 1.352× (long); Z 1.632× / 1.807×; V 1.692× / 1.730×.
- **Draft acceptance is the same across builds:** cell means 0.303-0.319 (short) and 0.334-0.363 (long). The newer
  builds don't guess better; they check the guesses faster (PR #31533, "CUDA: few-row MMQ for BS 2-24", merged
  2026-11-12 as `0fb8f1577` = b12342, between O and Z).
- **Prefill, long prompt (≈4,100 tokens):** MTP off: O 1,543.6, Z 1,552.9, V 1,540.5 tok/s. MTP on: O 1,457.3, Z
  1,503.9, V 1,500.2. TTFT 2.83-3.01 s.
- **Peak card memory:** 18,086-18,088 MiB with MTP off; 19,584-19,586 with MTP on (V, Z), 19,544-19,546 (O). MTP
  costs about 1.5 GB.

**Against the report** (homebrewserver.club, RTX 3090 / Ryzen 9 5900X, Docker images, driver 615.78.08): their no-MTP
27B was 40.6 / 39.8 tok/s (ours 43.9-44.0 / 43.3-43.4); their v1.0 MTP 68.5 / 71.9 (ours 74.5 / 75.0); their
b12199 MTP 45.1 / 46.5 (ours 52.6 / 58.5). Our b12199 already gets more from MTP than theirs did, which is why V/O
here (1.42 / 1.28) is below their 1.52 / 1.55. Different CPU, driver, build toolchain (from source, CUDA 12.4 vs
their images) and our 3-request cells; the cause of the gap isn't isolated.

## Void checks (M5, A1)

- prompt_n spread: every cell ≤ 3 except V-mtp-short (4), re-run once, clean (49..50).
- cache_n: 0 on all 84 requests (72 main + 12 re-run).
- swap-out: 0 KiB everywhere (swap-in at most 28 KiB on one request).
- PCIe (A1): every request reached gen 4 x16 during prefill; minimum width x16 everywhere. Measured requests' first
  sample reads gen 1 (link wake after the 50 °C cool-down), as A1 describes; the sets are in `results.jsonl`
  (`pcie_prefill`).
- NVMe reads during measured decode: at most 0.16 MiB (flag at 64 MiB, void at 1 GiB).
- GPU temperature at the start of measured requests: 49-50 °C.
- Answers: all read as normal essays and summaries (first 200 characters in `results.jsonl`, `text200`). No sanity
  flags.

## Setup as run

- **Machine:** Tamanna, RTX 3090 24 GB (driver 580.178.04, 420 W limit as set, PCIe gen 4 x16), Ryzen 7 5700X, 62 GiB
  visible RAM, ASRock B550 Phantom Gaming 4/ac BIOS P4.00, kernel 7.0.0-38. `machine-state.txt`.
- **Model:** `unsloth/Qwen3.5-27B-MTP-GGUF` @ `88fb5663`, `Qwen3.5-27B-Q4_K_M.gguf`, 17,106,773,056 B, sha256
  `130865c3…b2f7` on arrival, before the run and after it (`model-hash-pre.txt`, `model-hash-post.txt`). Canonical
  copy: Miu `LLM_repo/qwen3.5-27b-mtp-gguf/` (same hash, `SHA256SUMS`).
- **Server (M2):** `llama-server -m <model> -c 32768 -np 1 --host 127.0.0.1 --port 8081`, plus `--spec-type draft-mtp
  --spec-draft-n-max 6` with MTP on. Defaults otherwise. These builds don't log the offload or flash-attention choice
  at default verbosity, so the effective `-ngl`/`-fa` aren't in the logs. The whole model is on the card in every arm
  (peak 18.1 GB with MTP off for a 17.1 GB file, no NVMe reads during decode), all three log `n_threads = 8`, and
  each arm's start log matches the others on the parameters it does print.
- **Builds (M3, D1):** from source on Tamanna, nvcc 12.4.131, gcc 13.4.0, sm_86, the lock's flags plus
  `-DLLAMA_USE_PREBUILT_UI=OFF` (D1). `build.sh`, `build.log`, `builds/`:

  | arm | `llama-server --version` | llama-server sha256 | libggml-cuda sha256 |
  |---|---|---|---|
  | O | 0.9.0-dev (build 12199, commit 372dc5ca1) | `54eeef8d…7e88662` | `7454c3fd…5701e` (.so.0.29.0) |
  | Z | 0.9.0-dev (build 12352, commit 5676dfbe0) | `af46250d…723fd` | `c016b2b4…0bfff` (.so.0.29.0) |
  | V | 1.0.0-dev (build 12359, commit b1b770d90) | `84ba0dd9…043df0bc` | `daceb78a…f2043` (.so.1.0.0) |

- **Harness:** `bench_v1mtp.py` (sha256 `04306f34…4764e`), from the report's `bench.py` (kept here as
  `hbsc_bench_9ea02603.py`, sha256 `06fdc812…8f01`, selfhosted@9ea02603). Same request body, prompts
  (`long-context.txt`, sha256 `e004418b…6e53`) and token caps (512 short, 256 long). Changes: 8-hex nonce, (priming,
  measured) pairs, 3 rotated rounds over the 6 setups, per-request void metrics. Runs inside `bwrap --dev-bind / /
  --unshare-net` (loopback only).
- **Order:** round r runs setups[(k + 2(r−1)) mod 6] from V-mtp, Z-mtp, O-mtp, V-off, Z-off, O-off; each setup = warm-up
  (32 tokens, discarded), short prime + measured, long prime + measured, cool-down to ≤ 50 °C before each measured
  request. `run.log`, `rerun.log`, `logs/` (one server log per setup).
- **Summary:** `summarize.py results.jsonl` → `summary.txt`.

## Limits (M8, plus what came up)

- One model, one card, one prompt pair, 3 measured requests per cell. MTP cells vary about ±7% with acceptance, so a
  3-request mean resolves differences of roughly 10% and up, not 3%.
- Single request only (no 4-request test, no CPU test).
- The V-mtp-short value comes from a re-run 80 minutes after the main run, not interleaved.
- The effective offload/flash-attention defaults are inferred, not logged (above).
