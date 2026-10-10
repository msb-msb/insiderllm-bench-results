# Strata v0.1.39 vs llama.cpp v0.4.0 on Tamanna (RTX 3090 24 GB, PCIe 4.0 x16, 64 GB DDR4-3000), 2026-10-09

Results record for the pre-registration in `docs/candidates/strata-2026-10-05.md` section **B6** (approved by Mark
2026-10-09; Codacus reference corrected the same day). Files: Coder IQ1_M first (the bridge to Rushuna's
`../rushuna-strata-coder-2026-10-05/`), then ISTA IQ3_XXS (the claim test). Arms S1, S2-2048/4096/8192, S0, S3,
L1, L2, L3, as Rushuna, with `-t 8`.

**Gate passed:** memtest86+ one full pass at DDR4-3000, 0 errors (Mark, 13:40); gen 4 verify bench PASS
(`../tamanna-ddr4-3000-verify-2026-10-09/`); RAM-speed bench done (`../tamanna-ram-speed-offload-2026-10-09/`);
Tamanna back at 3000 / 1.350 V (dmidecode 3000 MT/s × 4, 42.30 GB/s, voltage confirmed in the BIOS by Mark).

## Staging (not results)

- **Disk:** 308 GB free at 13:47. Tamanna's copy of the Flash-Next UD-IQ3_XXS (82 GB, used by the RAM-speed bench)
  was deleted after that bench, as B6 allowed; the Miu store keeps the original. 265 GB free at 15:49.
- **ISTA IQ3_XXS shard 1:** downloaded on Tamanna over its WiFi, 8 ranged curl segments (`dl.sh`), 13:47–15:48
  with pauses: SIGSTOP by PID through every measured run of the verify and RAM-speed benches, and two BIOS reboots
  (restarted each time; segments resume). Some segments hit "connection reset" and resumed. **47,039,860,096 B,
  sha256 `219ea929900dfa9ef091f3aa473fdba6874b65fcb36526d7d851ac9e95856d15`: MATCH** with the LFS oid at revision
  `ed59f92082b1e93c0e96d60a8b11aab089b52f09` (15:50).
- **Shard 2 (n-gram table) and the Coder IQ1_M:** the Coder was never in the Miu store (Rushuna downloaded it
  directly on 10-05). Copied Rushuna → Miu store (`LLM_repo/qwen3.8-flash-next-gsq-rco-coder-gguf/IQ1_M/`, both shards
  + `SHA256SUMS.hub`), then store → Tamanna. Shard 2 is the same bytes for every variant; the IQ3_XXS directory gets
  a hard link to it under its own file name, so it costs no disk.
- **CUDA 13.0.2 toolkit:** Rushuna's installer (`cuda_13.0.2_580.95.05_linux.run`, md5
  `3f092554675f004250d4dfc1d6c3acc9`) copied over, to be installed toolkit-only into `~/cuda-13.0`, no root.
- **Harness:** `bench_strata.py`, Rushuna's `bench_coder.py` with four changes (`diff` in the file's docstring):
  llama.cpp path (`~/llama-v0.4.0/build/bin`), `-t 8`, the model picked by the run directory (`coder/` or
  `iq3xxs/`), and `prep` tokenizes Rushuna's exact prompt files instead of re-cutting them. Prompt files copied from
  Rushuna: `prompt-4096.txt` `f8f3f4b9…`, `prompt-16384.txt` `4857453e…`, `prompt-32512.txt` `24bb18f5…`;
  `corpus.txt` sha256 `09a0975d…` (same as Rushuna's). `memwatch.py` unchanged.
- **CUDA 13.0.2 on Ubuntu 26.04: the runfile installer can't run** (`./cuda-installer: error while loading shared
  libraries: libxml2.so.2`; 26.04 doesn't ship it, and installing it needs root). Instead the runfile was extracted
  (`--noexec --target`) and the toolkit components (nvcc, crt, cudart, cccl, cublas, nvrtc, nvvm and the other
  libraries; not the driver, docs, gdb or Nsight) were copied into `~/cuda-13.0`, with the `include` and `lib64` links
  the installer makes. `nvcc --version`: **V13.0.88**, the same as Rushuna's. 4.6 GB.
- **Strata checkout:** `6f32ec070f23ced9f50e704d854d775da52591ab`, the pin and Rushuna's commit. **The `v0.1.39` tag on
  GitHub has moved since 10-05:** it now points to `a1641e9f77aacad4d201b53c8a7ae8fa21059ebb`. The run uses the pinned
  commit, not the tag. (The newest `main` commit's message: "Stage buffers: pinning is opt-in (STRATA_STAGE_PIN=1); on
  by default it corrupted IQ3_S decode after a long prompt in the release gate." Not in our pin; noted only.)
- **Python:** 3.14.4 has `venv` but no `ensurepip` (Ubuntu's `python3-venv` package), and setup's fix is `sudo apt`.
  Instead `.venv` was made with `python3 -m venv --without-pip` and pip bootstrapped from PyPA's `get-pip.py` (sha256
  `fb24e693…f508ddf6`), pip 26.2.1. Rushuna ran Python 3.12; the engine is C++, Python only runs the server.
- **Engine build: FAILED** (`setup-attempt1.log`). With `STRATA_NVCC=~/cuda-13.0/bin/nvcc` and gcc-13 as host
  compiler, cmake's CUDA compiler check fails: glibc 2.43's `bits/mathcalls.h` declares `rsqrt` and `rsqrtf`
  `noexcept(true)`, CUDA 13.0.2's `crt/math_functions.h` declares them without it, and nvcc rejects the mismatch.
  This is the staging risk B6 named. Stopped for Mark's decision; nothing measured.
- **Mark's decision (2026-10-09): use Rushuna's engine binary.** `~/strata/engine/` (the `strata` binary + `BUILD.json`)
  copied from Rushuna: compiled there on 10-05 from the same commit `6f32ec07` with nvcc 13.0.88 for sm_86, **sha256
  `aeb18940ab33e81129f5f04e6efbd2720293386d490d218c2f280d75178242ea`, byte-identical to the engine of the Rushuna run**.
  Its runpath is `~/cuda-13.0/targets/x86_64-linux/lib`, which Tamanna has at the same version; `ldd` resolves
  everything. Setup accepted it (source fingerprint `d63ddbc6a262e39e` matches the checkout) and did not compile.
- **Setup (Coder, 16:2x–16:33, `setup-coder.log`):** same flags as Rushuna. Packed the model, fetched the MTP draft
  layer (`mtp-q2_0.gguf` + runtime) over Tamanna's WiFi, wrote `strata-coder-iq1_m.json` (`strata-coder-iq1_m.setup.json`
  here). **Memory mode: normal** (all routed experts pinned in RAM): the args are Rushuna's minus `--resident-experts`,
  which Rushuna's 32 GB needed and 64 GB doesn't. `ulimit -l` is 8,192 KiB; Strata pins through CUDA host registration,
  which isn't bound by it (Rushuna, 3.9 GiB limit, pinned 21.69 GiB).
- **Prompts on this file:** 4,096 / 16,384 / 32,512 tokens exactly, the same counts as Rushuna.
- **Harness fix before any measured cell (16:44):** Rushuna's stage loop searched `-ncmoe` 48 down to 30 only
  (`range(48, 29, -2)`). On 12 GB it never got near 30; on 24 GB the lowest fitting N is likely below it, which would
  have stopped the search early, against B6's "48 down in steps of 2". Changed to 48 → 0. The first launch was stopped
  by PID during stage (it had reached -ncmoe 48 only); its files are kept on Tamanna under `coder/aborted-stage-range30/`.

## Results: Coder IQ1_M (2026-10-09 16:44–17:34 PDT)

Run unattended by `run_all.sh` (`coder/sequence.log`). Memory floor never tripped. Every measured request: prompt_n
within 3 tokens of the others at its length (4,123–4,127 / 16,412–16,416 / 32,541–32,544, the same counts as Rushuna),
cache_n 0, swap-out 0, PCIe gen 4 x16 during every prefill. No cell is void.

- **llama.cpp N = 20** (stage: L2 at `-c 34816` serves 32,512 tokens at 48 down to 20; 18 loads but fails to serve).
  Rushuna's was 44 on 12 GB.
- **Strata, as run:** normal mode; the expert arena pinned with `cudaHostRegister` (engine log; 11,992 × 2 MiB, no huge
  pages). Engine RSS ~27 GB; MemAvailable with Strata loaded ~36 GB (llama.cpp arms ~53 GB). Startup PCIe probe
  **26.7 GB/s** host → device. `--prefill auto` chose **8,192-token chunks**, so S1 and S2-8192 are the same config
  and agree (2,906.7 vs 2,909.0 at 32K). Peak card 23,832 MiB.
- **S0 did not run:** refused at start, the same message as Rushuna ("…is a native (IQ) pack: it needs --native
  SHARD1, --spec T (T >= 2) and --prefill CHUNK"). S3 is the engine-speed decode figure; all 9 S3 requests had
  draft_n = 0 (valid).
- One L3 request (16K rep 2) read 285.6 MiB from the NVMe; its speed sits inside the cell's tight range, so it is
  noted, not flagged.

`python3 summarize.py coder` (`coder/summary.md`), mean of 3 measured (min..max):

### Prefill, tok/s

| prompt | S1 Strata | L1 (ub 512) | L2 (ub 4096) | L3 (ub 4096 + pinned) | S1÷L1 | S1÷L2 | S1÷L3 | S1 vs best llama.cpp ranges |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 4,096 | **2,417.7 (2,411.5..2,427.3)** | 495.3 (494.5..495.8) | 1,294.1 (1,291.7..1,298.0) | 1,292.6 (1,278.1..1,301.7) | 4.9× | 1.9× | 1.9× | no overlap |
| 16,384 | **2,750.9 (2,748.7..2,753.9)** | 495.7 (495.6..495.8) | 1,377.6 (1,377.4..1,377.7) | 1,371.4 (1,366.4..1,374.9) | 5.5× | 2.0× | 2.0× | no overlap |
| 32,512 | **2,906.7 (2,906.1..2,907.6)** | 475.1 (474.9..475.2) | 1,308.7 (1,308.2..1,309.1) | 1,308.9 (1,308.2..1,309.7) | 6.1× | 2.2× | 2.2× | no overlap |

### Decode, tok/s

| prompt | S1 as shipped (MTP + prompt lookup) | draft acceptance | S3 engine speed, no drafts | S3 draft_n | L1 | L2 | L3 | S3 ÷ best llama.cpp |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4,096 | 109.2 (107.3..110.9) | 68% | **73.4 (73.2..73.8)** | [0, 0, 0] | 32.8 (32.7..32.9) | 32.9 (32.8..33.1) | 32.8 (32.3..33.1) | 2.2× |
| 16,384 | 111.3 (108.7..113.7) | 75% | **73.1 (73.0..73.2)** | [0, 0, 0] | 30.2 (30.1..30.3) | 30.3 (30.3..30.4) | 30.1 (29.1..30.8) | 2.4× |
| 32,512 | 109.2 (100.4..114.7) | 77% | **72.6 (71.9..73.0)** | [0, 0, 0] | 28.2 (28.1..28.3) | 28.6 (28.5..28.7) | 28.5 (28.4..28.5) | 2.5× |

### S2 chunk sweep, 32,512 prompt

| arm | prefill tok/s | prefill rx GB/s mean |
|---|---:|---:|
| S2-2048 | 2,213.9 (2,212.5..2,216.4) | 10.64 |
| S2-4096 | 2,622.8 (2,620.7..2,626.3) | 6.51 |
| S2-8192 | 2,909.0 (2,905.5..2,913.7) | 4.80 |
| S1 | 2,906.7 (2,906.1..2,907.6) | 3.92 |

### Every measured request: checks

| arm | prompt | prompt_n | cache_n | swap-in / out KiB | NVMe MiB | peak card MiB | PCIe |
|---|---:|---|---|---|---|---|---|
| S1 | 4,096 | [4125, 4127, 4127] | [0, 0, 0] | [24, 0, 0] / [0, 0, 0] | [9.1, 3.0, 3.8] | 23832 | [('4', '16')] |
| S1 | 16,384 | [16414, 16415, 16414] | [0, 0, 0] | [8, 4, 4] / [0, 0, 0] | [1.1, 3.6, 9.8] | 23832 | [('4', '16')] |
| S1 | 32,512 | [32543, 32544, 32542] | [0, 0, 0] | [0, 4, 12] / [0, 0, 0] | [2.9, 8.8, 1.4] | 23832 | [('4', '16')] |
| S2-2048 | 32,512 | [32543, 32543, 32542] | [0, 0, 0] | [0, 0, 40] / [0, 0, 0] | [12.5, 3.2, 4.1] | 23822 | [('4', '16')] |
| S2-4096 | 32,512 | [32543, 32543, 32542] | [0, 0, 0] | [0, 0, 0] / [0, 0, 0] | [14.5, 7.4, 3.5] | 23832 | [('4', '16')] |
| S2-8192 | 32,512 | [32542, 32542, 32542] | [0, 0, 0] | [0, 0, 0] / [0, 0, 0] | [12.9, 6.3, 2.7] | 23828 | [('4', '16')] |
| S3 | 4,096 | [4126, 4125, 4125] | [0, 0, 0] | [0, 0, 0] / [0, 0, 0] | [3.4, 5.6, 0.7] | 23734 | [('4', '16')] |
| S3 | 16,384 | [16414, 16415, 16414] | [0, 0, 0] | [0, 0, 0] / [0, 0, 0] | [0.9, 5.1, 5.6] | 23734 | [('4', '16')] |
| S3 | 32,512 | [32544, 32544, 32542] | [0, 0, 0] | [0, 0, 0] / [0, 0, 0] | [2.4, 2.3, 4.7] | 23734 | [('4', '16')] |
| L1 | 4,096 | [4126, 4125, 4123] | [0, 0, 0] | [0, 0, 0] / [0, 0, 0] | [2.0, 1.2, 2.0] | 20704 | [('4', '16')] |
| L1 | 16,384 | [16412, 16414, 16415] | [0, 0, 0] | [0, 0, 0] / [0, 0, 0] | [7.7, 5.8, 6.5] | 20824 | [('4', '16')] |
| L1 | 32,512 | [32544, 32544, 32543] | [0, 0, 0] | [0, 0, 0] / [0, 0, 0] | [7.4, 5.6, 3.6] | 20982 | [('4', '16')] |
| L2 | 4,096 | [4123, 4127, 4125] | [0, 0, 0] | [0, 0, 0] / [0, 0, 0] | [2.3, 0.4, 0.7] | 23312 | [('4', '16')] |
| L2 | 16,384 | [16416, 16416, 16416] | [0, 0, 0] | [0, 0, 0] / [0, 0, 0] | [1.1, 2.2, 3.3] | 23312 | [('4', '16')] |
| L2 | 32,512 | [32543, 32541, 32542] | [0, 0, 0] | [0, 0, 0] / [0, 0, 0] | [1.1, 2.0, 0.5] | 23312 | [('4', '16')] |
| L3 | 4,096 | [4127, 4126, 4125] | [0, 0, 0] | [0, 0, 0] / [0, 0, 0] | [0.7, 7.1, 0.3] | 23312 | [('4', '16')] |
| L3 | 16,384 | [16415, 16414, 16414] | [0, 0, 0] | [0, 0, 0] / [0, 0, 0] | [0.3, 285.6, 0.9] | 23312 | [('4', '16')] |
| L3 | 32,512 | [32543, 32542, 32544] | [0, 0, 0] | [0, 0, 0] / [0, 0, 0] | [1.1, 1.9, 0.4] | 23312 | [('4', '16')] |

**Verdict (prefill): Strata is faster at every length against every llama.cpp arm**, no ranges overlap: 4.9–6.1×
against defaults, 1.9–2.2× against `-ub 4096`. `GGML_CUDA_REGISTER_HOST=1` (L3) adds nothing here, where it gave +28%
pp512 on Rushuna in August.

**Verdict (decode, engine speed): Strata is faster at every length**, S3 2.2–2.5× the best llama.cpp arm. As shipped
(MTP + prompt lookup, S1) it is 109–111 tok/s, 1.5× its own S3. Per amendment 2's rule, both Strata figures appear
together, and any Strata-vs-llama.cpp decode ratio uses S3.

**PCIe (R5) on gen 4: split, as on gen 3.** Mean rx during the 32K prefill falls from 10.64 GB/s at 2,048-token chunks
to 4.80 at 8,192: 40% to 18% of the 26.7 GB/s probe, under the 70% "PCIe-dominated" line. Per-token prefill time
falls 24% from 2,048 to 8,192 (0.452 → 0.344 ms), so it's not compute-dominated either (Rushuna: 27%).

### Against the expectations set in B6 (not revised)

| expectation | set | measured | |
|---|---|---|---|
| Coder S1 prefill vs Rushuna (933 / 1,025 / 1,094) | 1.5–2.5× | **2.59× / 2.68× / 2.66×** | **above range** |
| Coder S3 decode vs Rushuna (21.1 / 20.1 / 19.7) | 2–3× | **3.5× / 3.6× / 3.7×** | **above range** |
| Coder S1 vs the contributor's 3090, 32K: prefill 2,502 | ±15% | 2,906.7, **+16.2%** | just outside, above |
| Coder S1 vs the contributor's 3090, 32K: decode median 66.8 (MTP on) | ±15% | mean 109.2, median 112.6 (100.4..114.7), **+63% / +69%** | outside, far above |

Reasons from the logs and records, not tested further:
- **Above the Rushuna range:** the main one is in the engine log. **Decode expert-cache hit rate 99.7%** here (8,843
  experts resident on the card; under 0.1% of routed experts read over PCIe), against **75–77%** on Rushuna's 12 GB
  (~7.5% read over PCIe). Decode almost never leaves the card. Also: normal mode (all experts pinned) against
  Rushuna's resident low-RAM mode; PCIe gen 4 probed at 26.7 GB/s against 13.9; 8 cores on DDR4-3000 against 4 on
  DDR4-2133. B6 called the range "stated loosely"; it did not foresee a near-complete cache on 24 GB.
- **Above the contributor:** their run was engine 0.1.26, labelled preliminary, on a 280 W power cap, in a KVM guest;
  ours is 0.1.39 (13 releases later; the repo's own notes credit later releases with prefill gains). Decode with
  MTP also depends on draft acceptance (ours 68–77%, theirs about 74% on IQ3_XXS). Not the same engine, so this is a
  miss against a community number, not a disagreement with it.

## Results: ISTA IQ3_XXS, the full Qwen3.8-Flash-Next (2026-10-09 17:37–18:47 PDT)

Run unattended by `run_all.sh` (`iq3xxs/sequence.log`). Memory floor never tripped. Every measured request: prompt_n
4,123–4,127 / 16,414–16,416 / 32,540–32,544, cache_n 0, swap-out 0, PCIe gen 4 x16. The prompts tokenize to
exactly 4,096 / 16,384 / 32,512 on this file too. No cell is void.

- **llama.cpp N = 34** (stage: L2 serves 32,512 at 48 down to 34; 32 loads but fails to serve).
- **Strata, as run:** normal mode, expert arena pinned with `cudaHostRegister` (20,464 × 2 MiB); engine RSS ~43.8 GB,
  **MemAvailable with Strata loaded ~19 GB** of 62 GiB. 10,553 experts resident on the card. Probe 26.7 GB/s.
  `--prefill auto` chose 8,192-token chunks (S1 = S2-8192: 2,737.9 vs 2,739.4 at 32K).
- **S0 refused** with the same "native (IQ) pack" message. All 9 S3 requests draft_n = 0 (valid).
- **Decode expert-cache hit rate 98.7%** (0.6% of routed experts read over PCIe), against 99.7% on the Coder.
- One L1 request (4K rep 2) saw 1,296 KiB swap-in and 73.8 MiB NVMe reads; inside its cell's range, noted.

`python3 summarize.py iq3xxs` (`iq3xxs/summary.md`), mean of 3 measured (min..max):

### Prefill, tok/s

| prompt | S1 Strata | L1 (ub 512) | L2 (ub 4096) | L3 (ub 4096 + pinned) | S1÷L1 | S1÷L2 | S1÷L3 | S1 vs best llama.cpp ranges |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 4,096 | **2,186.7 (2,178.9..2,192.5)** | 254.9 (254.1..255.6) | 753.0 (747.8..757.6) | 754.5 (753.1..756.8) | 8.6× | 2.9× | 2.9× | no overlap |
| 16,384 | **2,578.9 (2,575.2..2,584.5)** | 253.6 (253.5..253.8) | 877.7 (869.4..893.4) | 877.3 (869.9..891.8) | 10.2× | 2.9× | 2.9× | no overlap |
| 32,512 | **2,737.9 (2,736.2..2,740.3)** | 242.3 (242.2..242.4) | 870.9 (870.5..871.2) | 870.8 (870.5..871.1) | 11.3× | 3.1× | 3.1× | no overlap |

### Decode, tok/s

| prompt | S1 as shipped (MTP + prompt lookup) | draft acceptance | S3 engine speed, no drafts | S3 draft_n | L1 | L2 | L3 | S3 ÷ best llama.cpp |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4,096 | 118.9 (117.6..120.1) | 67% | **77.6 (76.0..78.6)** | [0, 0, 0] | 19.0 (18.8..19.2) | 19.1 (19.0..19.2) | 19.1 (19.0..19.1) | 4.1× |
| 16,384 | 119.0 (118.5..119.6) | 67% | **78.0 (77.8..78.4)** | [0, 0, 0] | 18.3 (18.3..18.4) | 18.3 (17.9..18.5) | 18.4 (18.4..18.4) | 4.2× |
| 32,512 | 119.5 (114.2..126.4) | 70% | **78.0 (77.6..78.2)** | [0, 0, 0] | 17.6 (17.4..17.6) | 17.5 (17.4..17.6) | 17.6 (17.4..17.6) | 4.4× |

### S2 chunk sweep, 32,512 prompt

| arm | prefill tok/s | prefill rx GB/s mean |
|---|---:|---:|
| S2-2048 | 1,795.7 (1,794.7..1,796.9) | 24.66 |
| S2-4096 | 2,349.1 (2,345.3..2,355.6) | 16.10 |
| S2-8192 | 2,739.4 (2,730.2..2,748.8) | 10.02 |
| S1 | 2,737.9 (2,736.2..2,740.3) | 10.52 |

### Every measured request: checks

| arm | prompt | prompt_n | cache_n | swap-in / out KiB | NVMe MiB | peak card MiB | PCIe |
|---|---:|---|---|---|---|---|---|
| S1 | 4,096 | [4123, 4126, 4126] | [0, 0, 0] | [704, 124, 108] / [0, 0, 0] | [16.1, 5.0, 42.1] | 23824 | [('4', '16')] |
| S1 | 16,384 | [16416, 16415, 16415] | [0, 0, 0] | [136, 64, 52] / [0, 0, 0] | [8.5, 6.9, 5.1] | 23824 | [('4', '16')] |
| S1 | 32,512 | [32544, 32543, 32543] | [0, 0, 0] | [36, 136, 8] / [0, 0, 0] | [7.4, 5.9, 1.2] | 23824 | [('4', '16')] |
| S2-2048 | 32,512 | [32544, 32543, 32542] | [0, 0, 0] | [416, 28, 44] / [0, 0, 0] | [11.8, 3.9, 7.0] | 23814 | [('4', '16')] |
| S2-4096 | 32,512 | [32543, 32544, 32544] | [0, 0, 0] | [136, 0, 0] / [0, 0, 0] | [14.4, 6.7, 4.0] | 23824 | [('4', '16')] |
| S2-8192 | 32,512 | [32544, 32541, 32542] | [0, 0, 0] | [0, 52, 0] / [0, 0, 0] | [18.9, 7.5, 7.7] | 23820 | [('4', '16')] |
| S3 | 4,096 | [4127, 4126, 4127] | [0, 0, 0] | [0, 0, 0] / [0, 0, 0] | [11.6, 1.3, 8.2] | 23734 | [('4', '16')] |
| S3 | 16,384 | [16414, 16415, 16415] | [0, 0, 0] | [0, 0, 0] / [0, 0, 0] | [4.9, 4.5, 1.6] | 23734 | [('4', '16')] |
| S3 | 32,512 | [32544, 32540, 32544] | [0, 0, 0] | [0, 0, 0] / [0, 0, 0] | [5.0, 1.7, 1.2] | 23734 | [('4', '16')] |
| L1 | 4,096 | [4125, 4126, 4125] | [0, 0, 0] | [0, 1296, 4] / [0, 0, 0] | [7.4, 73.8, 8.2] | 20016 | [('4', '16')] |
| L1 | 16,384 | [16416, 16414, 16416] | [0, 0, 0] | [8, 4, 0] / [0, 0, 0] | [4.6, 5.0, 3.3] | 20136 | [('4', '16')] |
| L1 | 32,512 | [32543, 32543, 32543] | [0, 0, 0] | [0, 40, 4] / [0, 0, 0] | [2.1, 8.1, 1.0] | 20296 | [('4', '16')] |
| L2 | 4,096 | [4127, 4126, 4125] | [0, 0, 0] | [0, 0, 0] / [0, 0, 0] | [2.5, 1.7, 0.6] | 22184 | [('4', '16')] |
| L2 | 16,384 | [16414, 16415, 16416] | [0, 0, 0] | [0, 0, 0] / [0, 0, 0] | [3.2, 1.5, 0.6] | 22184 | [('4', '16')] |
| L2 | 32,512 | [32542, 32540, 32544] | [0, 0, 0] | [0, 0, 4] / [0, 0, 0] | [7.6, 1.6, 1.2] | 22184 | [('4', '16')] |
| L3 | 4,096 | [4126, 4125, 4126] | [0, 0, 0] | [0, 4, 0] / [0, 0, 0] | [5.2, 5.6, 4.3] | 22184 | [('4', '16')] |
| L3 | 16,384 | [16416, 16414, 16415] | [0, 0, 0] | [4, 0, 0] / [0, 0, 0] | [1.6, 0.4, 1.0] | 22184 | [('4', '16')] |
| L3 | 32,512 | [32544, 32543, 32544] | [0, 0, 0] | [0, 0, 0] / [0, 0, 0] | [0.5, 0.4, 0.7] | 22184 | [('4', '16')] |

**Verdict (prefill): Strata is faster at every length against every llama.cpp arm**, no ranges overlap: 8.6–11.3×
against defaults, 2.9–3.1× against `-ub 4096`. L3 (pinned host memory) again adds nothing over L2.

**Verdict (decode, engine speed): Strata is faster at every length**, S3 77.6–78.0 tok/s against llama.cpp's 17.5–19.1,
**4.1–4.4×**. As shipped (S1, MTP + prompt lookup): 118.9–119.5 tok/s, 1.5× its own S3. Both shown together; the
Strata-vs-llama.cpp ratio uses S3.

**PCIe (R5): PCIe-bound at small chunks, not at the stock size.** At 2,048-token chunks mean rx during the 32K prefill
is **24.66 GB/s, 92% of the 26.7 GB/s probe**, over the 70% line; at 8,192 (the stock pick) it is 10.02 GB/s, 38%.
Per-token prefill time falls 34% from 2,048 to 8,192 (0.557 → 0.365 ms). So on IQ3_XXS small chunks saturate gen 4,
and the stock 8K chunks get off the bus. (The Coder, with smaller experts, stayed under 40% at every chunk size.)

### Against the expectations set in B6 (not revised), and the reference figures

| reference | whose | their figure | ours (S1 unless stated) | |
|---|---|---|---|---|
| prefill 4K / 32K | contributor, 1 × 3090, engine 0.1.26, preliminary | 1,772 / 2,160 | 2,186.7 / 2,737.9: **+23.4% / +26.8%** | **outside ±15%, above** |
| decode median 4K / 32K (MTP on) | same | 89.2 / 90.6 | median 118.9 / 118.0: **+33% / +30%** | **outside ±15%, above** |
| prefill / decode as shipped | **Codacus's readings** (RTX 3060 12 GB, PCIe 4.0 x8 13.4 GB/s, Ryzen 9 7900X, 64 GB DDR5-5600, v0.1.36), same IQ3_XXS file | 926–964 / 40–43 | 2,187–2,738 / 118.9–119.5 | community reference, no range set: a 12 GB card against our 24 GB |
| prefill / decode 4K, 32K | Strata author, RTX 5070 12 GB, DDR5-5200 | 1,007 / 1,745; 61.6 / 58.5 | 2,186.7 / 2,737.9; 118.9 / 119.5 | repo's own measurement, different card |
| llama.cpp decode, Flash-Next UD-IQ3_XXS `-ncmoe 29` | **ours**, Miu 3090, DDR4-2667, 09-08 | 22.6 | L2 here: 19.1 / 17.5 at 4K / 32K on the ISTA file at N = 34 | different file and N; context only |

Reasons for the contributor miss, as for the Coder: engine 0.1.26 vs 0.1.39, a 280 W cap, a KVM guest, and a
preliminary label on their side. Against Codacus's box, the visible difference is the card: his 12 GB holds far
fewer experts than our 24 GB (we resident 10,553; decode hit rate 98.7%), which outweighs his DDR5-5600 serving the
misses faster than our DDR4-3000. Each of these is his reading and the repo's, not ours, and is labelled so.

## Coder against Rushuna, the bridge (same file, same prompts, same arms, same engine binary)

| | Rushuna (3060 12 GB, gen 3, 32 GB DDR4-2133, i7-7700) | Tamanna (3090 24 GB, gen 4, 64 GB DDR4-3000, 5700X) | Tamanna ÷ Rushuna |
|---|---|---|---|
| S1 prefill 4K / 16K / 32K | 933.4 / 1,024.6 / 1,094.4 | 2,417.7 / 2,750.9 / 2,906.7 | 2.59× / 2.68× / 2.66× |
| S3 decode 4K / 16K / 32K | 21.1 / 20.1 / 19.7 | 73.4 / 73.1 / 72.6 | 3.5× / 3.6× / 3.7× |
| S1 decode as shipped | 30.2 / 30.9 / 30.6 | 109.2 / 111.3 / 109.2 | 3.6× |
| llama.cpp N | 44 | 20 | |
| best llama.cpp decode | 9.1 / 8.6 / 8.0 | 32.9 / 30.3 / 28.6 | 3.6× |
| decode expert-cache hit rate | 75–77% | 99.7% | |
| Strata memory mode | resident low-RAM | normal | |

Everything differs between the two boxes at once (card, bus, CPU, RAM size and speed, memory mode), so the ratio is
what the bigger box buys, not what any one part does. The engine binary is the same file on both (sha256 `aeb18940…`).


**Dated note 2026-10-10:** `GGML_CUDA_REGISTER_HOST=1` is a no-op for model weights on llama.cpp v0.4.0 (nothing calls
the registration function; `../tamanna-register-host-2026-10-10/`). So L3 here is a repeat of L2, not a pinned-memory arm; "L3 adds nothing" says nothing about pinning.
