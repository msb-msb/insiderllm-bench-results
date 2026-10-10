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

## Amendment before setup (2026-10-05): the engine is compiled, not ready-made

**Strata ships no Linux engine.** Every release, v0.1.0 through v0.1.39, carries Windows zips only (GitHub
releases API), and `setup.py` compiles the engine on Linux. The candidate doc's "ready-made engine, no toolkit
needed" was wrong for Linux. So:

- **Toolchain:** CUDA **13.0.2** toolkit (`cuda_13.0.2_580.95.05_linux.run`, md5 `3f092554675f004250d4dfc1d6c3acc9`
  matching NVIDIA's list), installed toolkit-only, no root, into `~/cuda-13.0` (nvcc V13.0.88). Selected with
  `STRATA_NVCC=~/cuda-13.0/bin/nvcc`, which setup treats as the only toolkit it may use. CUDA 13.0 is what Strata's
  Linux docs name. Its code would accept Rushuna's 12.8 for sm_86, but that's not the documented path.
- **Host:** gcc/g++ 13.3, cmake 3.30.5 (`~/cmake/bin` on PATH for setup only).
- **Untouched:** `~/cuda-12.8`, `.bashrc`, and the llama.cpp bundles, which run on their own shipped CUDA 12 libs.
- **Recorded instead of a zip hash:** setup's build log, the engine binary's sha256, and `BUILD.json` if the build
  writes one.

Everything else in this pre-registration is unchanged.

## Setup outcome (2026-10-05, 22:39–22:51 UTC), before any measured run

- **Engine:** compiled from the v0.1.39 checkout with nvcc 13.0.88 for sm_86 (`setup.log`; `engine-BUILD.json`:
  version 0.1.39, src `d63ddbc6a262e39e`). `engine/strata` sha256
  `aeb18940ab33e81129f5f04e6efbd2720293386d490d218c2f280d75178242ea`. Setup first tried release v0.1.39's engine
  (404), then "the latest release", then compiled. No release carries a Linux engine.
- **Memory mode setup picked: resident low-RAM** (`--resident-experts`). Setup's own line: the Coder "uses ~23 GB of
  RAM <- fits in the low-RAM mode (the GPU holds ~30%, the rest in RAM)". It wrote the 23 GB `experts.bin` once.
- **Config as written** (`strata-coder-iq1_m.setup.json`): `--expert-profile data/expert-profile-coder.bin
  --expert-cache auto --prefill auto --spec 4 --spec-min-p 0.5 --mtp …/mtp/rt --max-context 34816 --kv int8
  --resident-experts`. Images off, speed projection off (not in the args), draft vocab at the default (setup suggested
  `--draft-vocab en` for 12 GB cards as a tip; not applied, the S1 arm is setup's config as written).
- **Draft layer:** fetched by setup, `Strata-data/mtp/` (`mtp-q2_0.gguf` 889 MB + runtime).
- Disk after setup: 32 GB free. RAM before the first load: MemAvailable 31,067 MiB, swap used 118 MiB.
- How much free memory Strata leaves once loaded is recorded per arm in `run.log` (MemAvailable at server ready)
  and in `memwatch-*.log`.

## Results (2026-10-05 22:52 – 2026-10-06 00:50 UTC)

Run unattended by `run_all.sh` (`sequence.log`). The memory floor never tripped: lowest MemAvailable across the
sequence was 5,605 MiB (S2-8192). The mycoSwarm daemon ran throughout. Every measured request reported prompt_n
within 33 tokens of the others at its length (4,124–4,127 / 16,414–16,416 / 32,541–32,544) and cache_n 0, so no
cell is void. PCIe link during every prefill: gen 3, x16.

**Strata's memory mode, as run:** resident low-RAM. The engine page-locks its expert complement in RAM through CUDA
(engine log: "resident 21.69 GiB, pinned 21.69 GiB; page-locked and mapped"; VmLck/VmPin read 0 because CUDA's
registration doesn't show there). Strata process RSS ~24.9 GB. **Free memory left with Strata loaded: MemAvailable
5.6–6.4 GB** (llama.cpp arms: 22–29 GB, because its mmapped weights count as reclaimable page cache).
`--prefill auto` chose **8,192-token chunks** (engine log), so S1 and S2-8192 are the same configuration; they agree
(1,094.4 vs 1,095.6 at 32K).

### S0 did not run

`--spec 0` is refused on this model file. The engine exits at start: "…/coder-iq1_m is a native (IQ) pack: it needs
--native SHARD1, --spec T (T >= 2) and --prefill CHUNK" (`engine-S0.log`). Recorded, not retried, per the S2 rule.
So **there is no drafter-off Strata number and no engine-speed decode comparison** in this record. Every decode
figure below compares Strata with MTP + prompt lookup against llama.cpp with no drafter.

### Prefill, mean of 3 measured (min..max), tok/s

| prompt | S1 Strata | L1 llama.cpp (ub 512) | L2 (ub 4096) | L3 (ub 4096 + pinned) | S1÷L1 | S1÷L2 | S1÷L3 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 4,096 | **933.4** (928.8..938.4) | 157.9 (157.6..158.0) | 398.7 (361.9..424.6) | 404.6 (377.6..419.5) | 5.9× | 2.3× | 2.3× |
| 16,384 | **1,024.6** (1,023.3..1,025.5) | 159.7 (156.2..161.5) | 470.6 (449.7..492.9) | 485.0 (478.1..489.7) | 6.4× | 2.2× | 2.1× |
| 32,512 | **1,094.4** (1,094.0..1,095.2) | 157.6 (156.4..158.3) | 416.2 (392.1..433.1) | 440.5 (406.0..467.5) | 6.9× | 2.6× | 2.5× |

**Verdict (primary): Strata is faster at every length against every llama.cpp arm.** No min..max ranges overlap.
llama.cpp ran at `-ncmoe 44` (stage: lowest that serves 32,512 tokens under L2; 42 loaded but failed to serve).
Strata's spreads are under 1%; llama.cpp's L2/L3 spreads run 2–17%. The two slowest llama.cpp 32K requests (L2 rep 3,
L3 rep 3) coincide with the largest NVMe reads in the run (660 and 523 MiB); swap-out volume doesn't track speed.
At stage, L2 at N=44 did 470 tok/s on one 32K request; the measured mean is 416.

### Decode, tok/s: MTP + prompt lookup (Strata) vs no drafter (llama.cpp)

| prompt | S1 Strata, MTP + prompt lookup | draft acceptance | L1 | L2 | L3 |
|---:|---:|---:|---:|---:|---:|
| 4,096 | 30.2 (29.8..30.7) | 70% | 9.1 | 9.1 | 9.0 |
| 16,384 | 30.9 (29.5..31.9) | 73% | 8.6 | 8.5 | 8.6 |
| 32,512 | 30.6 (29.5..31.9) | 72% | 8.0 | 7.9 | 7.9 |

S1 decode is inside the loose 25–45 expectation. This is not an engine-speed comparison (S0 couldn't run). Decode
expert-cache hit rate per Strata's log: 75–77%, with ~7.5% of routed experts read over PCIe.

### Expected range (S1), set before measuring

| prompt | expected | measured | |
|---:|---:|---:|---|
| 4,096 | 600–900 | 933.4 | **above range** (+3.7% over the top) |
| 16,384 | 750–1,150 | 1,024.6 | in range |
| 32,512 | 800–1,200 | 1,094.4 | in range |

Why 4K came in above, from the logs: the 4,127-token prompt fits in one 8,192-token chunk, so there's a single
expert pass with no chunk boundaries; the expert complement is pinned (no pageable host copies); 0 blob reads from
the file; swap-in on the three measured 4K requests was 36 KiB–2.8 MiB and NVMe reads 2–27 MiB. The prediction's
per-chunk cost was set too high for a single-chunk prompt.

### PCIe (R5): split

| arm (32,512 prompt) | chunk | prefill tok/s | time per token | prefill time | mean rx | rx ÷ 13.9 GB/s | pinned expert RAM | prompt-path VRAM slots |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S2-2048 | 2,048 | 802.0 | 1.247 ms | 40.6 s | 8.25 GB/s | 59% | 19.44 GiB | 605 (1.15 GiB) |
| S2-4096 | 4,096 | 986.9 | 1.013 ms | 33.0 s | 5.20 GB/s | 37% | 20.19 GiB | 999 (1.90 GiB) |
| S2-8192 | 8,192 | 1,095.6 | 0.913 ms | 29.7 s | 3.34 GB/s | 24% | 21.69 GiB | 1,779 (3.40 GiB) |

- Not PCIe-dominated: mean rx stays under 70% at every chunk size (S1: 41% at 4K, 31% at 16K, 27% at 32K).
- Not compute-dominated: per-token time is not flat. It falls 27% from 2,048 to 8,192.
- Going from 16 chunks to 4 saves 10.9 s, about **0.9 s per chunk removed**, under the 1.2–1.4 s per-chunk stream
  estimate.
- Caveat, from the logs: chunk size isn't the only thing that changes. A smaller chunk borrows fewer VRAM cache
  slots for the prompt path and pins less RAM, so S2 doesn't isolate PCIe streaming by itself.

### Swap and NVMe, per measured request

Every Strata measured request swapped out 0 KiB; swap-in ranged 4 KiB–5.0 MiB. llama.cpp measured requests swapped
in 0–4.2 MiB and **swapped out up to 460 MiB in one request** (L1 4K rep 2), with swap used peaking at 2.4 GB in L1,
while MemAvailable stayed above 21.9 GB. No request read more than 1 GiB from NVMe (max 660 MiB, L2 32K rep 3).
**44 of 45 measured requests had swap-in > 0 and are flagged** in the table below (the exception: L3 4K rep 1).

`memwatch.py` only recognises `llama-server`/`llama-bench` processes, so in the Strata arms it booked every sample
as "idle" phase (`memwatch-summary-S*.json`). The MemAvailable floor was checked on every sample regardless of
phase. The per-request swap figures come from `bench_coder.py`, not memwatch.

### Every measured request

| arm | prompt | rep | prompt_n | prefill tok/s | decode tok/s | drafts acc/n | TTFT s | rx MB/s | swap-in KiB | swap-out KiB | NVMe MiB | MemAvail after MiB | flag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| S1 | 4096 | 1 | 4127 | 928.8 | 30.7 | 161/221 | 4.6 | 6712 | 2,868 | 0 | 26.5 | 6,071 | swap-in |
| S1 | 4096 | 2 | 4127 | 932.9 | 30.1 | 155/225 | 4.5 | 6720 | 48 | 0 | 3.3 | 6,079 | swap-in |
| S1 | 4096 | 3 | 4126 | 938.4 | 29.8 | 155/231 | 4.5 | 3592 | 36 | 0 | 2.2 | 6,065 | swap-in |
| S1 | 16384 | 1 | 16415 | 1024.9 | 29.5 | 152/219 | 16.1 | 6010 | 256 | 0 | 11.9 | 5,924 | swap-in |
| S1 | 16384 | 2 | 16415 | 1023.3 | 31.2 | 163/224 | 16.3 | 3237 | 152 | 0 | 8.0 | 5,893 | swap-in |
| S1 | 16384 | 3 | 16414 | 1025.5 | 31.9 | 163/208 | 16.2 | 3820 | 1,012 | 0 | 3.9 | 5,903 | swap-in |
| S1 | 32512 | 1 | 32543 | 1095.2 | 30.5 | 142/196 | 29.9 | 4120 | 80 | 0 | 6.2 | 5,886 | swap-in |
| S1 | 32512 | 2 | 32543 | 1094.1 | 29.5 | 155/232 | 30.1 | 3384 | 44 | 0 | 9.9 | 5,880 | swap-in |
| S1 | 32512 | 3 | 32543 | 1094.0 | 31.9 | 160/206 | 30.1 | 3787 | 756 | 0 | 3.3 | 5,908 | swap-in |
| S2-2048 | 32512 | 1 | 32543 | 802.5 | 31.8 | 161/193 | 40.9 | 8006 | 5,120 | 0 | 18.4 | 8,118 | swap-in |
| S2-2048 | 32512 | 2 | 32543 | 800.5 | 29.1 | 161/226 | 41.0 | 8938 | 280 | 0 | 9.0 | 8,150 | swap-in |
| S2-2048 | 32512 | 3 | 32541 | 803.1 | 30.3 | 160/208 | 40.8 | 7817 | 4 | 0 | 14.0 | 8,141 | swap-in |
| S2-4096 | 32512 | 1 | 32542 | 987.8 | 29.4 | 159/213 | 33.3 | 5314 | 4 | 0 | 14.8 | 7,308 | swap-in |
| S2-4096 | 32512 | 2 | 32544 | 986.2 | 29.9 | 157/222 | 33.3 | 5533 | 60 | 0 | 6.3 | 7,308 | swap-in |
| S2-4096 | 32512 | 3 | 32544 | 986.6 | 30.9 | 163/206 | 33.3 | 4748 | 12 | 0 | 8.4 | 7,320 | swap-in |
| S2-8192 | 32512 | 1 | 32544 | 1098.8 | 32.5 | 157/205 | 29.9 | 2775 | 28 | 0 | 5.6 | 5,658 | swap-in |
| S2-8192 | 32512 | 2 | 32543 | 1093.5 | 30.2 | 155/220 | 30.0 | 3906 | 3,212 | 0 | 13.6 | 5,640 | swap-in |
| S2-8192 | 32512 | 3 | 32542 | 1094.5 | 31.1 | 155/210 | 29.9 | 3348 | 28 | 0 | 6.0 | 5,605 | swap-in |
| L1 | 4096 | 1 | 4127 | 157.6 | 9.1 | – | 26.6 | 6130 | 128 | 0 | 4.4 | 29,187 | swap-in |
| L1 | 4096 | 2 | 4124 | 158.0 | 9.2 | – | 27.1 | 6496 | 3,080 | 470,752 | 29.3 | 28,847 | swap-in |
| L1 | 4096 | 3 | 4125 | 158.0 | 9.1 | – | 26.5 | 7058 | 520 | 0 | 11.6 | 28,336 | swap-in |
| L1 | 16384 | 1 | 16415 | 156.2 | 8.6 | – | 106.6 | 6529 | 4,308 | 296 | 174.5 | 26,885 | swap-in |
| L1 | 16384 | 2 | 16416 | 161.5 | 8.6 | – | 102.3 | 7154 | 136 | 0 | 14.4 | 25,104 | swap-in |
| L1 | 16384 | 3 | 16416 | 161.3 | 8.5 | – | 103.1 | 7127 | 400 | 152,976 | 31.4 | 24,311 | swap-in |
| L1 | 32512 | 1 | 32544 | 156.4 | 7.9 | – | 209.6 | 7148 | 600 | 30,916 | 143.2 | 22,877 | swap-in |
| L1 | 32512 | 2 | 32541 | 158.3 | 8.0 | – | 206.6 | 7094 | 2,392 | 0 | 13.0 | 22,904 | swap-in |
| L1 | 32512 | 3 | 32543 | 158.0 | 8.0 | – | 206.8 | 6763 | 872 | 0 | 7.3 | 22,448 | swap-in |
| L2 | 4096 | 1 | 4124 | 361.9 | 8.9 | – | 12.1 | 652 | 20 | 568 | 95.3 | 28,752 | swap-in |
| L2 | 4096 | 2 | 4127 | 409.5 | 9.2 | – | 10.7 | 2472 | 1,036 | 89,400 | 18.2 | 28,245 | swap-in |
| L2 | 4096 | 3 | 4126 | 424.6 | 9.2 | – | 10.0 | 2010 | 92 | 0 | 21.7 | 27,307 | swap-in |
| L2 | 16384 | 1 | 16416 | 469.2 | 8.5 | – | 35.5 | 3015 | 892 | 0 | 94.2 | 25,854 | swap-in |
| L2 | 16384 | 2 | 16416 | 449.7 | 8.5 | – | 38.1 | 3778 | 224 | 171,944 | 177.3 | 24,658 | swap-in |
| L2 | 16384 | 3 | 16416 | 492.9 | 8.5 | – | 33.9 | 3413 | 56 | 0 | 18.5 | 23,224 | swap-in |
| L2 | 32512 | 1 | 32543 | 433.1 | 8.0 | – | 77.0 | 2348 | 2,208 | 268,164 | 300.7 | 22,353 | swap-in |
| L2 | 32512 | 2 | 32544 | 423.5 | 7.9 | – | 78.4 | 2280 | 1,552 | 31,184 | 420.7 | 22,176 | swap-in |
| L2 | 32512 | 3 | 32542 | 392.1 | 7.9 | – | 84.2 | 2398 | 1,476 | 424,328 | 659.5 | 22,405 | swap-in |
| L3 | 4096 | 1 | 4125 | 377.6 | 9.0 | – | 11.3 | 1907 | 0 | 416 | 64.1 | 28,793 | – |
| L3 | 4096 | 2 | 4126 | 416.7 | 9.0 | – | 11.1 | 3254 | 340 | 227,720 | 25.4 | 28,443 | swap-in |
| L3 | 4096 | 3 | 4126 | 419.5 | 9.0 | – | 10.2 | 2358 | 232 | 0 | 25.4 | 27,485 | swap-in |
| L3 | 16384 | 1 | 16416 | 489.7 | 8.6 | – | 34.0 | 3375 | 1,504 | 0 | 14.5 | 26,080 | swap-in |
| L3 | 16384 | 2 | 16414 | 478.1 | 8.7 | – | 35.0 | 2685 | 56 | 0 | 13.7 | 24,350 | swap-in |
| L3 | 16384 | 3 | 16416 | 487.2 | 8.6 | – | 34.2 | 3942 | 48 | 1,768 | 28.0 | 22,577 | swap-in |
| L3 | 32512 | 1 | 32544 | 447.9 | 8.0 | – | 73.6 | 3126 | 808 | 289,336 | 132.8 | 22,486 | swap-in |
| L3 | 32512 | 2 | 32543 | 467.5 | 8.0 | – | 70.6 | 2988 | 3,108 | 0 | 12.0 | 22,651 | swap-in |
| L3 | 32512 | 3 | 32543 | 406.0 | 7.8 | – | 81.3 | 2760 | 1,040 | 220,036 | 522.8 | 22,129 | swap-in |

## Feasibility check for the prompt-lookup-only arm (2026-10-06, after the results above, before any amendment)

Mark approved a new arm: Strata at `--spec 2` without the draft model (prompt lookup only). Before writing it into
the pre-registration I checked whether the engine can run it. It can't, as specified:

- **The server needs the draft model.** `src/program/generate.cpp` (v0.1.39), serve mode: `if (o.spec < 2 ||
  o.mtp.empty() || …)` → "strata serve: needs --spec T, --mtp DIR and --prefill CHUNK". Only the CLI (non-serve) path
  runs without `--mtp`, and there a no-lookup round verifies a placeholder draft token, so it isn't lookup-only
  either. It's also a different harness from every other arm.
- **In serve mode, prompt lookup depends on the draft model.** A lookup window is taken only when its first token
  matches the MTP's own first guess (`k > 0 && sbuf[0] == drafts[0]`).
- **`--spec 2` with `--mtp` is changed by the engine:** with prompt lookup on and no `--mtp-max-t`, it sets the
  MTP's window to 2 and the verify window to 4 (`o.mtp_max_t = o.spec; o.spec = min(o.spec + 2, 8)`). For the same
  reason S1's `--spec 4` ran with MTP windows of 4 and lookup windows of up to 6.

**Check run** (`cfg-check.json`, `server-check.log`, `engine-check.log`): S1's config with `--spec 2 --mtp-max-t 1`
(MTP may draft 0 tokens), lookup left at its default. The server started (draft layer loaded, 839 MiB of VRAM). Two
short requests of ~840 tokens, one asking the model to copy code verbatim: **draft_n 0 on both**. Prompt lookup never
fired, because there's no MTP guess for it to match. The engine log prints speeds for these two requests. They are
short prompts outside the protocol and aren't used anywhere.

## Amendment 2 (2026-10-06, Mark), written and committed before the arm runs: S3, no drafts

**New arm S3:** Strata, S1's config with `--spec 2 --mtp-max-t 1` (`cfg-S3.json`). The draft layer stays loaded
because the server won't start without it (feasibility check above). The MTP may draft 0 tokens, and prompt lookup,
left at its default, can't fire without an MTP guess to match.

- **Cells:** all three lengths (4,096 / 16,384 / 32,512), (priming, measured) × 3, same prompts, nonce, template,
  temperature 0, max_tokens 256 as every other arm.
- **Memory rule:** unchanged. Only MemAvailable < 2 GiB stops it; swap counted and published per measured request.
  mycoSwarm daemon left running.
- **Validity:** every measured request must report **draft_n = 0**. A request with draft_n > 0 voids its cell.
- **Primary figure:** decode tok/s. Prefill is recorded too, but S1 remains the prefill figure.
- **What it is, stated now:** decode with no drafted tokens verified, with the draft layer loaded (839 MiB of VRAM
  that S1 also spends). Any cost of carrying the draft layer counts against Strata. This is the **engine-speed**
  decode figure, and the comparison with llama.cpp L1–L3 (no drafter) uses it.

**How the article presents decode (decided now, whatever the numbers):** three figures side by side:
1. S1, **"as shipped"**: MTP + prompt lookup, Strata's default, what readers run;
2. S3, **"engine speed, no drafts"**: the like-for-like number against llama.cpp;
3. llama.cpp L1–L3 (no drafter), 8–9 tok/s in this record.

Neither Strata figure is shown without the other. Any Strata-vs-llama.cpp decode ratio in the article uses S3.

### S3 results (2026-10-06 01:17–01:27 UTC), per amendment 2

All 9 measured requests: **draft_n 0** (valid), cache_n 0, prompt_n 4,125–4,127 / 16,415–16,416 / 32,541–32,544.
Memory floor never tripped (lowest MemAvailable 5,586 MiB). Swap-out 0 on every measured request; swap-in 0–796 KiB
(7 of 9 flagged swap-in > 0). NVMe reads 1.2–20.7 MiB. Decode expert-cache hit rate 73.7–76.3%, ~7% of routed
experts read over PCIe, the same as S1.

**Decode, tok/s, mean of 3 (min..max):**

| prompt | S1 **as shipped** (MTP + prompt lookup) | S3 **engine speed, no drafts** | llama.cpp L1 / L2 / L3 (no drafter) | S3 ÷ best llama.cpp |
|---:|---:|---:|---:|---:|
| 4,096 | 30.2 (29.8..30.7) | **21.1** (17.2..23.4) | 9.1 / 9.1 / 9.0 | 2.3× |
| 16,384 | 30.9 (29.5..31.9) | **20.1** (18.6..22.7) | 8.6 / 8.5 / 8.6 | 2.3× |
| 32,512 | 30.6 (29.5..31.9) | **19.7** (17.3..21.0) | 8.0 / 7.9 / 7.9 | 2.5× |

**Verdict (decode, engine speed): Strata is faster at every length.** S3's lowest request (17.2) is well above
llama.cpp's highest (9.2). S3's spread is wide (up to 30% within a cell), much wider than S1's, so the ratios are
approximate. Drafting as shipped adds 43–55% over S3 (S1 ÷ S3: 1.43 / 1.54 / 1.55).

S3 prefill (909 / 1,011 / 1,086 tok/s) is within 3% of S1's at each length. S1 remains the prefill figure.


**Dated note 2026-10-10:** `GGML_CUDA_REGISTER_HOST=1` is a no-op for model weights on llama.cpp v0.4.0 (nothing calls
the registration function; `../tamanna-register-host-2026-10-10/`). So L3 here is a repeat of L2, not a pinned-memory arm; "L3 adds nothing" says nothing about pinning.
