# Strata v0.1.39 vs llama.cpp v0.4.0 on the ISTA Coder IQ1_M — Rushuna (RTX 3060 12 GB, PCIe 3.0 x16, 32 GB DDR4-2133), 2026-10-05

PRE-REGISTRATION, written and committed before any download to Rushuna or any measured run. It implements R6 of
`docs/candidates/strata-rushuna-2026-10-05.md`, with the changes listed under "Changes from R6".

**License.** The model is Qwen3.8-Flash-Next, under the **Qwen Community License 1.0**. That holds whatever a quant
repo's tag says: ISTA-DASLab tags the GGUF repos `apache-2.0`, and a quantisation can't relicense its base model.

## Files under test

- **Model:** `ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF` at revision
  `5348543e0147355ac9cbcb031184a3546350988e`, folder `IQ1_M/`. Downloaded directly on Rushuna into
  `~/bench-models/qwen3.8-flash-next-coder/`, each shard sha256-checked against the hub's LFS oid:
  - shard 1: 29,608,446,496 B, `e11083ba855e7666b48ea3f2db6a9c3a20c18751a012cc24f948de91b7087fad`
  - shard 2: 28,800,138,432 B, `316b46f3a2dbd68c900f43136ab9449f9dcc3725dfd8c794847c204bc161e113`
- **Strata:** github.com/Niko1221/Strata at `6f32ec070f23ced9f50e704d854d775da52591ab` (v0.1.39), ready-made engine.
  Installed with:
  ```
  ./setup.sh --setup --family coder --gguf-dir <IQ1_M dir> --context 34816 --vision no
             --experimental-speed-projection off --no-browser --no-start --yes
  ```
  Setup fetches the MTP draft layer itself, on Rushuna. Recorded: the engine zip's sha256, the pip versions, the
  memory mode setup picks (normal / resident / mmap), and whether the arena pinned.
- **llama.cpp:** `~/llama-v0.4.0` (v0.4.0 `5266f24`, CUDA 12.8 bundle, sm_86), same shards.

## Prompts

`corpus.txt` is the first 600,000 characters of the llama.cpp v0.4.0 source (`git ls-files src common
ggml/src/ggml-cuda`, *.c/cpp/h/cu/cuh, sorted path order, list in `corpus-files.txt`), sha256 `09a0975d…421d475`.
`bench_coder.py prep` cuts it on the model's tokenizer (llama.cpp `/tokenize` on the Coder file) to **4,096,
16,384 and 32,512 tokens**. Each request is a single user message:

```
request <8-hex nonce>\n<prompt>\n\nSummarise what this code does.
```

The nonce is fresh per request, priming included, and breaks prefix reuse in both engines.
`chat_template_kwargs.enable_thinking=false`, temperature 0, max_tokens 256, streamed. The prompt_n each engine
reports must agree within 1% per length, or the cell is void. `cache_n` must be ≈0 (template header at most).

## Arms

| arm | engine | config |
|---|---|---|
| S1 | Strata | setup's config as written (`--prefill auto`, MTP + prompt lookup) |
| S2-2048 / S2-4096 / S2-8192 | Strata | S1 with `--prefill` set to 2048 / 4096 / 8192; **32,512-token prompt only**; any that fails to start is recorded, not retried |
| S0 | Strata | S1 with `--spec 0` (no MTP, no prompt lookup; the engine ignores `--mtp` below spec 2) |
| L1 | llama.cpp | `-ngl 99 -ncmoe N -fa on -c 34816 -np 1 --lazy-mode on -t 4`, defaults `-b 2048 -ub 512` |
| L2 | llama.cpp | L1 + `-b 4096 -ub 4096` |
| L3 | llama.cpp | L2 + `GGML_CUDA_REGISTER_HOST=1` |

**N** is found by `bench_coder.py stage` *before* any measured cell. It is the lowest `-ncmoe` (48 down in steps of
2) at which the **L2** config loads at `-c 34816` and serves a 32,512-token prompt. L2/L3 need more VRAM than L1, and
one N is used for all three arms.

Order: S1, S2-2048, S2-4096, S2-8192, S0, then L1, L2, L3. One server resident at a time, card at 0 MiB between.

**Cells:** for each length, (priming request, measured request) × 3. Value = mean of the 3 measured; spread = min..max.

## Memory rule (Mark, 2026-10-05): the same for both engines

- **Only MemAvailable < 2 GiB stops a run.**
- Swap is allowed. **Swap-in and swap-out KiB are reported per measured request beside its speed figures**, from
  `/proc/vmstat` before and after each request.
- `memwatch.py --count-swap` (copied from the reference record) samples every 2 s across each arm.
- The mycoSwarm daemon stays running and is noted.

## Recorded per request

- Engine `timings`: prompt_n, cache_n, prompt_per_second, predicted_per_second, draft_n / draft_n_accepted.
- Client TTFT and total time.
- Swap-in and swap-out KiB; NVMe read MiB.
- PCIe rx MB/s mean over the prefill window (`nvidia-smi dmon -s t`), PCIe gen/width seen during prefill.
- Peak card MiB; MemAvailable / Cached / swap used before and after.
- VmRSS / VmLck / VmPin / VmSwap of the server and engine processes.
- Strata's server log, kept per arm: logged chunk size, expert-cache slots, PCIe probe, memory mode, pinning.

## Expected Strata prefill (S1), set before measuring and not revised after

From R5/R6 of the candidate doc, unchanged:

| prompt | expected | central |
|---|---:|---:|
| 4,096 | 600–900 | ~750 |
| 16,384 | 750–1,150 | ~900 |
| 32,512 | 800–1,200 | ~950 |

S1 decode with MTP on: 25–45 tok/s, stated loosely. Codacus's ~900 tok/s on his own machine is context, not a target.

## Verdict rules

- **Primary:** Strata ÷ llama.cpp prefill per length, against L1, L2 and L3 separately. "Faster" only when the
  min..max ranges don't overlap; otherwise "within noise".
- **Decode:** S1 vs L-arms is labelled "MTP + prompt lookup vs no drafter" every time it appears. S0 vs L-arms is
  the engine-speed comparison.
- **PCIe (R5):**
  - *PCIe-dominated* if mean prefill rx > 70% of 13.9 GB/s **and** S2 per-token time falls from 2,048 to 8,192 by
    at least the estimated 1.2–1.4 s stream per chunk.
  - *Compute-dominated* if rx < 30% and S2 per-token time is flat within 10%.
  - Otherwise split, with the numbers.
- **Expected range:** each S1 length is reported in or out of range. When out, the reason comes from the logs
  (chunk size, pinning, host copies, SSD reads, swap).
- Any measured request with swap-in > 0 or NVMe reads above 1 GiB is flagged beside its number.
- Not in scope: answer quality, contexts past 32K, other variants, the speed projection (off).

## Changes from R6

- The memory rule (above) replaces "stop on swap": Mark's decision after the reference run's attempts 1–3.
- The download happens on Rushuna (Miu's WiFi was degraded), not through the Miu store.
- N is chosen on the L2 config, for the VRAM reason above.
- A fixed one-line instruction follows the prompt, so the model has a task to answer.
