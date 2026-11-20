# Strata HotRod vs upstream Strata on an RTX 3060 (32 GB) and an RTX 3090 (64 GB) (pre-registration)

**LOCKED on commit.** Written 2026-11-19 before any model download to a rig, any engine build and any measured
request. The sha256 of this file is recorded in the lock commit message and in `strata-hotrod-2026-11.md.sha256` next
to it, and the file is published byte-exact to the public mirror (`candidates/`) before the first measurement. Anything
added later is appended after section H10 as a dated amendment or deviation. Nothing above H10 changes.

Machines are named, never addressed: **Rushuna** (RTX 3060 12 GB), **Tamanna** (RTX 3090 24 GB), **Miu** (the model
store). Prior records this builds on: `rushuna-strata-coder-2026-10-05/`, `tamanna-strata-2026-10-09/` (harness,
prompts, void rules), `qwen-coder-article-2026-11.md` P4 and A1 (Rule P4, the strict prompt_n reading).

## H1. Question and claim under test

**The claim.** github.com/sangharshadhyeta/Strata-HotRod (MIT; a fork of github.com/Niko1221/Strata, MIT) says that on
one RTX 3060 12 GB with 30 GB of RAM and an NVMe SSD it runs Qwen3.8-Flash-Next as ISTA-DASLab's GSQ-RCO IQ3_S (78 GB of
files by its count; 83.6 GB as downloaded) with the experts that don't fit in RAM read from the SSD. The README gives
two speed figures for the same setup that don't agree:
- the hero text, the tile and the FAQ: **35-45 tok/s** (131K context, short answers);
- the IQ3_S badge image and the "How fast" table (24 Oct): **50-70 tok/s** (code 52-55, reasoning 66-71, story 50-53);
  the long-prompt table (20 Oct, 262K context): an 8,554-token prompt read in 16.9 s, answer at 52-54 tok/s.
Its measured machine: i5-12400F, 30 GB RAM, WD Blue SN5000 on PCIe 3.0, Rocky Linux 9.6, gcc-toolset-13, CUDA 13.3,
"Strata 0.1.45 (upstream, merged 17 Oct 2026) plus this fork's changes".

**What the fork changes** (README, "How it works"): stand-in experts (a missing expert replaced by a resident one when
router weight × logit gap ≤ budget; ranks 3-9 any stand-in, rank 2 within 1 logit, ranks 0-1 exact), a learned
look-ahead that prefetches experts 1/2/4 layers ahead (setup downloads a trained state, `predictor-qwen38-iq3s-v2`,
5.4 MB, sha256 `04367a17…01b70`, and it keeps learning), a card → RAM → SSD tiering, and setup-written engine env for
CUDA IQ3_S only (`STRATA_ROUTE_RESIDENT=1e30`, `STRATA_ROUTE_RESIDENT_RANKS=3-9`, `STRATA_ROUTE_RESIDENT_EDGE=1`,
`STRATA_SWAP2_MAX=2`, `STRATA_SWAP2_GAP=1`, `STRATA_KV_GROW_INIT=4096`). The flip re-check is off by default since 9 Nov.

**The build flag.** `setup.sh ... --build` compiles the fork's engine. Without it, setup downloads **upstream's
ready-made engine** (`PREBUILT_TAG_URL = github.com/Niko1221/Strata/releases/download/v{version}/`), which lacks the
fork's changes: an install without `--build` is upstream with HotRod's config. Setup also downloads, either way: Python
packages, the pinned llama.cpp source (`3cf03257f219afbe7334045ff7c6a06ac68c627d`, the same pin in all three trees
below), the MTP draft layer from Hugging Face, the model if not given, and for IQ3_S the predictor file above.

**The reviewer.** No Place Like Localhost ("Doubling Qwen Flash Next speed with Strata HotRod", uploaded 2026-11-19;
raw files github.com/scorbo2/ai-playground `benchmarking/`, commit `d9ee3128`) ran Strata's own `tools/strata_bench.py`
on two machines, IQ3_S, 131072 context, thinking off, temperature 0:

| machine | Strata (engine) | HotRod (engine 0.1.45, `ded1bd7c`) |
|---|---|---|
| "Saturn": RTX 4070 12 GB, i7-13700KF, **125.6 GiB RAM** | engine 0.1.62: short-chat decode 28.8, 4K prefill 130.9, 16K prefill 192.0, agent decode 35.2 | 39.2 / 688.5 / 282.5 / 36.9 |
| "Titan": RTX PRO 4000 Blackwell 24 GB, **125.1 GiB RAM** | engine 0.1.58: 103.1 / 2,148.2 / 2,755.1 / 116.6 | 86.8 / 2,442.9 / 2,915.4 / 88.9 |

Both of the reviewer's machines hold the whole model in RAM. **Neither tested the 30 GB low-RAM, SSD-streaming case the
README is about.** Rushuna (32 GB) does. And the reviewer's baselines are on a newer engine than HotRod's base, so a
fork gain and an upstream change are mixed in their comparison. Arm B separates them.

**Questions.** (1) On Rushuna, does HotRod reach the README's speed, and how does it compare with upstream at its base
release and at the current release? (2) On Tamanna, where the model fits in RAM, does HotRod help or hurt, as the
reviewer's 24 GB result suggests?

## H2. Arms (same model, same context, same setup flags)

| arm | tree | pin | engine version |
|---|---|---|---|
| **U** upstream, current release | github.com/Niko1221/Strata `v0.2.16` (released 2026-11-18) | `64524fb9fc82222ddce554c0643b64f056ec8366` | 0.1.62 (the reviewer's Saturn baseline engine) |
| **H** HotRod | github.com/sangharshadhyeta/Strata-HotRod `main` | `251dec4336218a1ef8db8f3364692817ddf30a2a` (2026-11-19). Its diff from `ded1bd7c`, the reviewer's commit, is README.md only | 0.1.45 + 471 fork commits |
| **B** upstream at HotRod's base | github.com/Niko1221/Strata `v0.1.45` (2026-10-17) | `477ac13cbe8e582c20484871ce459d20d82df09d`, the fork's merge base with upstream | 0.1.45 |

If HotRod's `main` has moved by checkout, H still uses this commit.

- **Model, all arms:** `ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF` at revision
  `ed59f92082b1e93c0e96d60a8b11aab089b52f09`, folder `IQ3_S/`:
  - shard 1: 54,817,524,224 B, sha256 `4c1eb2ceb4915e1192f4f386021897bde56a97f40a0bb78bb86465e0f7d2aca3`
  - shard 2: 28,800,138,432 B, sha256 `316b46f3a2dbd68c900f43136ab9449f9dcc3725dfd8c794847c204bc161e113` (the same
    bytes in every GSQ-RCO quant and the Coder; already in the store under `IQ3_XXS/`).
- **Setup, all arms, the same flags:** `setup.sh --model IQ3_S --gguf-dir <rig's IQ3_S dir> --context 131072
  --vision no --build --no-start --yes` plus `--no-browser` where the tree accepts it (a flag a tree rejects is dropped
  for that tree and recorded). 131072 is the README's and the reviewer's context. Each install's config is used as its
  setup writes it ("as shipped"), including H's env above and H's predictor download. Each tree's memory mode (normal /
  low-RAM resident / mmap) is whatever its setup picks on that rig; it's recorded, not forced.
- **Each arm installs from a fresh clone with an empty data folder**, apart from the MTP draft layer, which may be
  shared once fetched and hash-checked. HotRod's learned files are recorded (names, sizes, sha256) after its run.
- **B is the third arm "if cheap".** If B's build or setup fails on Rushuna, B is dropped on both rigs, recorded, and
  not debugged. U and H are required.

## H3. Builds: from source, network off for the compile

- **No prebuilt engine in any arm.** `--build` everywhere. A log line showing a ready-made engine download voids the
  install.
- **Where:** all three engines are compiled on **Rushuna** (sm_86, `~/cuda-13.0` nvcc V13.0.88, gcc 13.3.0). Tamanna
  can't compile CUDA 13 (glibc 2.43 vs CUDA 13.0's math headers, `tamanna-strata-2026-10-09/`), so, as on 10-09, Tamanna
  runs the Rushuna-built binaries. Each engine binary's sha256 is recorded on both rigs and must match.
- **Egress isolation.** Downloads (clones, pip packages, the llama.cpp archive at the pin, the MTP layer, H's predictor)
  happen first, with the network up, each hashed in the record. The compile itself (cmake configure + build) runs inside
  a network namespace with no route out (`unshare -Un` on Rushuna; verified 2026-11-19: no route, no DNS). If a build
  step tries to fetch, it fails, the failure is recorded, the fetch is done outside with its hash, and the compile is
  re-run inside.
- **Measured runs:** on Tamanna inside `bwrap --dev-bind / / --unshare-net` (loopback up, no route out; verified
  2026-11-19), with the bench client in the same namespace. Rushuna can't do that without root (no bubblewrap;
  `unshare -Un` leaves loopback down), so Rushuna's runs have the network up, with an **egress watch**: `ss -tnpH` every
  2 s for the server and engine processes, any non-loopback peer logged. An outbound connection is reported, not a void.

## H4. Storage

- **Store:** shard 1 is downloaded once into `LLM_repo/qwen3.8-flash-next-gsq-rco-gguf/IQ3_S/` on Miu, checked
  against the LFS oid above. Shard 2 is a hard link to the store's existing `IQ3_XXS/` copy. A `SHA256SUMS` goes in the
  folder. Rigs get copies, each re-hashed on arrival.
- **On each rig the model and every file setup writes (pack, low-RAM experts copy, MTP layer) sit on an NVMe drive.**
  Rushuna's 8 TB drive (HGST HUS728T8TAL, SATA, rotational) is an HDD and is **not** used for anything a measured run
  reads. Rushuna's NVMe: SSSTC CA6-8D256, PCIe 3.0 x4. Tamanna's: Micron MTFDKBA512TFH, PCIe 4.0.
- **Space:** U/H/B setups need about 84 GB of model plus, in low-RAM mode, a ~51 GB experts copy per install
  (setup.py: `need = to_fetch + MTP + arena`; IQ3_S arena 50.3 GB). Arms run one after another; an arm's own pack is
  deleted before the next arm's setup if space requires. The model files stay.
- **Tamanna:** at least 20 GB stays free throughout, and the voice-run files for 2026-11-24 (`~/voice-pipeline`,
  `~/bench-models/voice-pipeline`, `~/voice-01`) are not touched. **Nothing that exists today on either rig is deleted
  without Mark's say-so.** If a rig lacks the space, its arms wait and the record says what's needed.

## H5. Measurements

Per arm, in this order, one server resident at a time, card at 0 MiB between arms:

1. **Strata's benchmark tool:** the arm's own `tools/strata_bench.py` (U: `terminal/tools/strata_bench.py`), default
   suite, no options: one warm-up chat and a 1K prompt discarded, then short chat (3 questions × 3, 100 new tokens), 4K
   and 16K fresh prompts (3 each, 24 new tokens), the 5-turn agent session (3 sessions). This is the reviewer's method.
   Each tree runs its own copy of the tool, as the reviewer did; our cells below are the common harness. This step also
   serves as every arm's warm-up, so HotRod's live learning gets the same ~10 minutes of use in every arm.
2. **Our cells:** `bench_hotrod.py`, derived from `tamanna-strata-2026-10-09/bench_strata.py` (Strata arm only; the
   server is started from the arm's config; the diff goes in the record). Prompts: the record's existing
   `prompt-4096.txt`, `prompt-16384.txt`, `prompt-32512.txt` (exact token counts on the Flash-Next tokenizer, which IQ3_S
   shares). Each request: a fresh 8-hex nonce line first, a chat completion, streamed, thinking off, temperature 0,
   `max_tokens 256`. **Per cell: (priming request, measured request) × 3; value = mean of the 3 measured (min..max).**
   - **Prefill** = the engine's `prompt_per_second`; client TTFT recorded beside it.
   - **Decode** = the engine's `predicted_per_second`, as shipped (MTP and prompt lookup as each config sets them);
     draft acceptance recorded.
   - Recorded per request, as in the Tamanna record: prompt_n, cache_n, swap-in/out KiB, NVMe read bytes (the rig's
     model drive), PCIe gen/width during prefill, peak card MiB, server/engine RSS, plus the first 200 characters of
     each answer (a sanity check: an empty, looping or garbled answer is flagged).
3. **Machine state,** once per rig per day: free RAM, the NVMe's sequential read (`dd` of shard 1 with `iflag=direct`,
   8 GiB), the PCIe probe the engine logs at start, driver version.

**Memory guard:** `memwatch.py` from the Strata records, unchanged. A tripped floor ends the arm; it's reported.

**Arm order on each rig: U, H, B.**

## H6. Void rules (Rule P4 as in the Qwen Coder lock, with A1's reading)

A cell is void if any measured or priming request in it has:
- prompt_n spread over 3 tokens across all 6 requests (max − min ≤ 3, A1);
- cache_n above the template header (≈0);
- swap-out above 0 KiB;
- the PCIe link below gen 3 x16 (Rushuna) or gen 4 x16 (Tamanna) during any prefill;
- **on Tamanna only:** NVMe reads over 1 GiB during the measured decode (flag over 64 MiB). On Tamanna the model is
  meant to sit in RAM, so reads mean page-cache pressure. **On Rushuna, NVMe reads are not a void criterion:** streaming
  experts from the SSD is the mechanism under test. They are reported per request.

A void cell is re-run once; void twice is reported as void. `strata_bench.py` results are reported as the tool prints
them, with no void rule applied; its median and range sit beside our cells, never mixed in.

## H7. Predictions (set before any number exists)

From the reviewer's data, as Mark set them. "Faster" or "slower" means the means differ in that direction **and** the
min..max ranges don't overlap; overlapping ranges count as "no difference shown", which misses a directional prediction.

**Rushuna (RTX 3060, 32 GB):**
- **R1, decode:** H faster than U at 4K, 16K and 32K (our cells), **and** H's mean below 50 tok/s at each length, i.e.
  under the README's 50-70 band. Reported beside the README's other figure, 35-45, with no prediction attached to that.
- **R2, prefill:** H "much faster" than U = at least 2.0× U's mean at 4K and at 16K (the reviewer: 5.3× at 4K on 12 GB).

**Tamanna (RTX 3090, 64 GB):**
- **T1, decode:** H slower than U at 4K, 16K and 32K.
- **T2, prefill:** H "modestly faster" than U = H/U between 1.00 and 1.30 at 4K and at 16K, with H's range above U's
  (the reviewer: +14% at 4K, +6% at 16K on 24 GB).

Each prediction is scored per length, and holds only if it holds at every length it names. The same tests are run on
`strata_bench.py`'s short-chat decode (R1, T1) and 4K/16K prefill (R2, T2) medians and ranges, and reported separately.

**B is descriptive, with no prediction.** H vs B is the fork's own effect; U vs B is what upstream changed since the
fork. If U is slower than B on a metric, an H-over-U gain on that metric is partly an upstream regression, and the
write-up says so.

## H8. What gets written down

`docs/bench-results/strata-hotrod-2026-11/` (public via the mirror, through the leak gate): this registration's
section numbers, every install log, every config as written (`*.setup.json`), commits, engine and binary sha256s,
download hashes, the `strata_bench.py` reports and JSON, the per-request JSONL of our cells, `summarize.py` output,
egress-watch logs, the machine-state block, and every void and deviation. Machine names only.

## H9. Limits stated in advance

- **One model, two rigs, one run each.** Not a ranking of engines in general.
- **Speed only.** No quality check beyond the sanity flag. HotRod's stand-ins replace experts, so its answers are not
  the same computation as upstream's; the README's own small quality test is its claim, not ours.
- **HotRod learns from use.** It gets ~10 minutes of warm-up here. Its README says the first hour is fitting, so a
  longer-used install may be faster than what we measure. The write-up says so whatever the result.
- **Rushuna isn't the README's machine:** i7-7700 (4 cores) vs i5-12400F (6 cores), DDR4-2133, a 256 GB SSSTC NVMe vs
  a WD SN5000, 32 GB vs 30 GB, Ubuntu 24.04 vs Rocky 9.6, CUDA 13.0 vs 13.3. Close in kind, not identical.
- **Short answers.** Our decode cells cap at 256 tokens, the tool's at 100; the README's table spans 100-1,000 tokens.

## H10. Gates

1. No measured request before this file is committed, its sha256 recorded, pushed, and published to the mirror with
   the public copy's sha256 matching.
2. No run on a rig until both model shards on that rig hash to the values in H2.
3. No deletion of existing files on either rig without Mark's say-so (H4).
4. The draft article is written only after the record exists, on a local branch, previewed on the LAN, not deployed.

## A1. Amendment (2026-11-19, Mark): Rushuna runs with swap off and non-essential services stopped

**Written after one measured request existed, not before.** Arm U's first Rushuna pass (started 2026-11-20 02:00 UTC,
Rushuna's clock) showed the engine's own memory going to swap: `/swap.img` (4 GiB, on the NVMe) full, `strata-host`
holding 3.7 GiB of it, 0.4-4.3 GiB of swap-out per request. Under H6 every Rushuna cell in every arm would be void.
That was seen at U's first priming request and first measured request (4K rep 1); Mark decided this amendment then. The
pass was allowed to finish and is **discarded: it is not scored**. It stays in the record, unaltered, as
`rushuna/U-superseded-swap-on/`, and the write-up reports it as a superseded run.

Changes, Rushuna only, the same for all three arms (U re-run first, then H, then B), from before U's re-run until after
B's last request:
- **Swap off:** `swapoff -a` (Mark, by hand; no sudo in the sessions). H6's swap rule is unchanged; with no swap device,
  swap-out is 0 by construction, and `memwatch.py`'s 2 GiB MemAvailable floor remains the stop rule.
- **Non-essential services stopped:** `mycoswarm` (Mark's mycoSwarm node daemon, ~47 MB RSS, and inbound LAN traffic on
  port 7890), `fwupd`, `ModemManager`, and the `apt-daily`, `apt-daily-upgrade` and `fwupd-refresh` timers (so no package
  or firmware job starts mid-arm). `ollama` was already inactive before U's first pass; the stop command includes it so
  it stays so. Storage, thermal and SMART services (`multipathd`, `thermald`, `smartmontools`) keep running.
- The state of swap and of those units is recorded in every arm's machine-state file. After B, swap and the stopped
  units are restored (ollama to its prior state, inactive).

Nothing else changes: arms, flags, cells, void rules, predictions and order stay as locked. Tamanna is unaffected
(64 GB; the model is meant to sit in RAM there). The text above this section is byte-identical to the lock as committed
in c06003fc (sha256 `1ca64bda12295de692623a68b39294f65e371da95c5837b9ff2c7656c04f3b68`, the `.sha256` file beside it).
