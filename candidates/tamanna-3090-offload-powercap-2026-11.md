# Tamanna RTX 3090: expert offload and power cap (pre-registration, 2026-11-25)

Machine: **tamanna** (Ryzen 7 5700X, RTX 3090 24 GB, PCIe 4.0 x16, 64 GB DDR4-3000). Measured host read
bandwidth 42.30 GB/s (`stream_read.c`, 4 threads, median of 3, Inkling A1 record 68199f65, same day). VRAM
bandwidth is taken as the 936 GB/s spec figure. Driver 580.178.04, VBIOS 94.02.42.80.14. Card defaults read
2026-11-25 19:42 PST: power limit 420 W (default 420, min 100, max 450), persistence on.

Claims under test come from the YouTube video "Two $300 GPUs vs RTX 5090". They are community claims, not
measurements of this card.

## P0. Scope

- **Arm O (expert offload, Qwen3-30B-A3B Q4_K_M): SKIPPED.** The model is not on Tamanna. A search of `~` and
  `~/bench-models`, following symlinks, found no Qwen3-30B-A3B file. `Qwen_Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf`
  is in LLM_repo but not staged, and per Mark's instruction the arm is skipped rather than staged today. So the
  offload claims (~0.5 ms/token per layer moved; all experts in RAM keeps ~1/4 of full-GPU speed) and the tie-in to
  Rushuna's 26.22 tok/s `-cmoe` result (Qwen3.6-35B-A3B, Inkling record b6003805) are **not tested here**. If Arm O
  runs later, it comes as an appended amendment.
- **Arm P (power cap)** runs, with the dense model only. Its MoE leg ("same model fully on the GPU") needs the Arm O
  model, so it is skipped for the same reason.

## P1. Model, build, command

- Model: `~/nariq-t/model/Qwen3.8-27B-UD-Q4_K_XL.gguf`, sha256
  `bee238bbeb3dc0a34bde4d0dedbaee1f98c009e8bb4226f03070054c12fb1372`. This is the NariQ record's R-Q4 file; it is
  hashed again on Tamanna before the run.
- Build: the NariQ mainline build, `~/nariq-2026-11/mainline/build/bin/llama-server` (`b12431-a946eb541`). Its
  sha256 is recorded in the run, and `/props` must report `b12431-a946eb541`.
- Command, as in the NariQ T5 arm: `-ngl 99 -fa on -c 8192 -np 1 --fit off -lm mmap -t 4 --cache-ram 0`, with
  `LD_LIBRARY_PATH=~/nariq-t/cuda-libs`.
- Requests, as in NariQ T5 except for `max_tokens`:
  - streamed chat completion with a fresh 8-hex nonce line first;
  - thinking off, temperature 0, `cache_prompt` false, `ignore_eos`;
  - `max_tokens` 512, not 256, so each decode window is long enough for power sampling.
  - Prompts are the NariQ files: `prompt-512.txt` (510 tokens) and `prompt-4096.txt` (4,094 tokens).
- Each block, at one power limit:
  - load the model and wait for `/health`;
  - one cold 512 request, reported and excluded;
  - 3 measured requests at 512, then 3 at 4096;
  - stop the server and check the card is back at ≤ 50 MiB.

## P2. Power-limit sequence

| block | limit | what changes it |
|---|---|---|
| B420a | 420 W (default) | none (as found) |
| B350 | 350 W | Mark: `sudo nvidia-smi -pl 350` |
| B320 | 320 W | Mark: `sudo nvidia-smi -pl 320` |
| B280 | 280 W | Mark: `sudo nvidia-smi -pl 280` |
| B250 | 250 W | Mark: `sudo nvidia-smi -pl 250` |
| B420b | 420 W (restored) | Mark: `sudo nvidia-smi -pl 420` |

- Mark's step list was 350/320/280/250. This card's default is 420 W (a partner card, not the 350 W reference), so
  420 W is added as the baseline (B420a) and as the restore plus drift check (B420b).
- Each sudo line goes to Mark on its own, and the next block waits for him.
- Before each block, `nvidia-smi --query-gpu=power.limit,enforced.power.limit` must read the intended limit;
  otherwise the block does not start.
- B420b is the restore. Its logged `power.limit` and `power.default_limit` (both 420) are the "default restored"
  record.
- Card temperature must be ≤ 50 °C at each block start. The harness waits for this, up to 10 minutes, and logs it.

## P3. What is logged

- **Per request**, everything the NariQ `bench_t.py` already logs:
  - prompt and decode tok/s from server timings;
  - swap in and out, NVMe reads, MemAvailable;
  - peak card MiB;
  - PCIe link during prefill.
- **Power**, sampled by a 100 ms `nvidia-smi` loop (`--query-gpu=timestamp,power.draw.instant,power.draw,clocks.sm,clocks.mem,temperature.gpu,clocks_event_reasons.sw_power_cap,clocks_event_reasons.hw_slowdown` with `-lms 100`) and written to `power-<block>.csv`.
  - The request timings define two windows. The prefill window is [t0 + 0.2 s, t0 + TTFT]. The decode window runs
    from t0 + TTFT + 0.5 s to the end of the request.
  - Mean `power.draw.instant` in each window is that request's prefill watts and decode watts. The per-cell figure
    is the median of the 3 reps.
  - Mean SM clock and the share of samples with `sw_power_cap` active are reported the same way.
- **Joules per token:** decode J/token is decode watts ÷ decode tok/s. Prefill J/token is prefill watts ÷ prompt
  tok/s.
- **Void rule:** a request is void on any swap-out, NVMe read during decode above 64 MiB, or a PCIe link other than
  gen 4 x16 during prefill. A void rep is re-run once; if it is void again, the cell is reported as void.
- **Prefill-window floor:** with fewer than 5 power samples in a prefill window (the 512 cell's prefill is about
  0.4 s), that cell reports prefill watts as "n/a, window too short". **Prefill watts and the prefill claim are
  scored on the 4096 cell only.**

## P4. Predictions (written before any measured request)

Anchors are NariQ T5 on this card at 420 W (R-Q4, same file and build): decode 512/4096 = 42.03 / 41.40 tok/s,
prompt 512/4096 = 1,265.5 / 1,512.4 tok/s.

- **PP1 (B420a speed):**
  - decode 512 in [39.9..44.1] tok/s;
  - decode 4096 in [39.3..43.5] tok/s;
  - prompt 4096 in [1,437..1,588] tok/s.
  - All three are ±5% of the anchor.
- **PP2 (B420a watts):**
  - prefill-4096 watts (P0) in [330..420] W;
  - decode-512 watts (D0) in [230..380] W.
- **Bands for the capped blocks, computed from B420a and committed before B350 runs:** for a cap C, the
  prediction is a ratio of the capped block's speed to B420a's.
  - **PP3 prefill (compute-bound), 4096 cell:**
    - If C ≥ P0: ratio in [0.98..1.02].
    - If C < P0: ratio in [(C/P0)^0.6 − 0.02 .. (C/P0)^0.33 + 0.02].
    - The exponent range covers frequency scaling between roughly P ∝ f² and P ∝ f³ near the top of the voltage
      curve.
  - **PP4 decode (bandwidth-bound), 512 and 4096 cells:**
    - If C ≥ D0: ratio in [0.98..1.02].
    - If C < D0: ratio in [max(0.90, (C/D0)^0.33 − 0.02) .. 1.02].
    - The direction is the point: decode loses less than prefill at every cap where both are capped.
- **PP5 (shape):**
  - At 250 W, the prefill ratio is lower than the decode ratio.
  - The decode ratio at 280 W is ≥ 0.97.
- **PP6 (drift):** B420b decode 512 is within ±2% of B420a. If it is not, the capped blocks carry a drift flag.

## P5. Claim scoring ("280 W saves ~70 W for <1% speed")

The claim's baseline is taken as 350 W, the 3090 reference board power. The claim is scored on B350 vs B280, once
for prefill (4096 cell) and once for decode (512 cell):

- **Speed part holds** if speed at B280 is ≥ 0.99 × speed at B350.
- **Watts part holds** if watts at B350 minus watts at B280 is in [50..90] W.
- **The claim holds for a phase only if both parts hold.**

Also reported, not scored: the same comparison from the card's own 420 W default (B420a vs B280), and J/token at
every cap.

Prediction, before running:
- **Decode:** the speed part holds and the watts part fails. Decode draws less than 350 W, so a 280 W cap removes
  less than 50 W.
- **Prefill:** the watts part holds and the speed part fails (more than 1% lost).

## P6. Machine state and safety

- Before each block, log:
  - card MiB, which must be ≤ 50;
  - MemAvailable and swap;
  - any other GPU processes, of which there must be none;
  - CPU governor;
  - uptime.
- If the run stops partway, the last sudo line given to Mark is still `sudo nvidia-smi -pl 420`, and the record
  logs the final limit.
- `--cache-ram 0` is set on every server start.
