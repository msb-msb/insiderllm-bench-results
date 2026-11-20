# llama.cpp v1.0.0 vs 0.9 builds, Qwen3.5-27B with and without MTP, on an RTX 3090 (pre-registration)

**LOCKED on commit.** Written 2026-11-20 before any model download to a rig, any engine build and any measured
request. The sha256 of this file is in the lock commit message and in `llamacpp-v1-mtp-3090-2026-11.md.sha256` next
to it, and the file is published byte-exact to the public mirror (`candidates/`) before the first measurement.
Anything added later is appended after section M9 as a dated amendment or deviation. Nothing above M9 changes.

Machines are named, never addressed: **Tamanna** (RTX 3090 24 GB, Ryzen 7 5700X, 64 GB DDR4-3000), **Miu** (the
model store). Serves the article "Your GPU Is Mostly Waiting: The Next Step in Local AI Speed", section 2 (what
already works, measured here). Prior records this builds on: `tamanna-strata-2026-10-09/` and
`strata-hotrod-2026-11/` (void rules, bwrap runs), `qwen-coder-article-2026-11.md` P4 and A1 (Rule P4, strict
prompt_n reading).

## M1. Question and the claim under test

**The claim.** homebrewserver.club, "Llama.cpp v1.0 on an RTX 3090: up to 55% faster with speculative decoding"
(published 2026-11-14, updated 2026-11-20; scripts and raw results at github.com/homebrewserver/selfhosted,
`llama-cpp-v1/`, commit `9ea02603`). On an RTX 3090 (Ryzen 9 5900X, 62 GB, Fedora 44, driver 615.78.08, official
CUDA server Docker images), Qwen3.5-27B Q4_K_M with its MTP head, `-c 32768 -np 1`, temperature 0, thinking off:

| 27B, decode tok/s (median of 5) | build 12199 (0.9.0-dev, 8 Nov) | v1.0.0 (build 12359) |
|---|---|---|
| short prompt, no MTP | 40.6 | 40.4 |
| short prompt, MTP | 45.1 | 68.5 (+52%) |
| long prompt (~4,120 tok), no MTP | 39.8 | 40.2 |
| long prompt, MTP | 46.5 | 71.9 (+55%) |

Draft acceptance about 32-33% on both builds. The report credits llama.cpp PR #31533 ("CUDA: few-row MMQ for BS
2-24"): the gain is in verifying the drafts, not in drafting better ones.

**What the version number hides (checked 2026-11-20 against github.com/ggml-org/llama.cpp).** PR #31533 landed at
`0fb8f1577` = **b12342** (2026-11-12), inside the 0.9-dev series. The last published 0.9 build tag is **b12352**
(`5676dfbe0`, 2026-11-12 23:11). Between b12352 and v1.0.0 (b12359, `b1b770d90`) there are seven commits: CI, example
clean-up, docs and the two version bumps (`3bfde28f9` ggml, `4cda6227a` llama.cpp). None touches inference code. So
"1.0 vs 0.9" depends on which 0.9: the report's b12199 predates the kernel; the last 0.9 tag already has it.

**Questions.** (1) Does the report's MTP gain reproduce on Tamanna, v1.0.0 vs b12199? (2) Is the last 0.9 build
(b12352) the same speed as v1.0.0, with MTP on and off? (3) With MTP off, is there any version difference at all?

## M2. Arms

| arm | tree, pin | reports as |
|---|---|---|
| **O** the report's baseline | ggml-org/llama.cpp tag `b12199`, `372dc5ca157276beb6c67b2e92477e8d662e964a` | 0.9.0-dev, build 12199 |
| **Z** the last 0.9 build | tag `b12352`, `5676dfbe01e7ebe0387913680eee0ed39bf4a363` | 0.9.0-dev, build 12352 |
| **V** v1.0.0 | tag `v1.0.0` → commit `b1b770d90d94cad9e9ea5b993bdbc383a522fb28` (= `b12359`) | 1.0.0, build 12359 |

Each arm runs in two modes: **off** (no speculative decoding) and **mtp** (`--spec-type draft-mtp
--spec-draft-n-max 6`, the report's flags, the value unsloth's card suggests). Six setups in all.

- **Model, all setups:** `unsloth/Qwen3.5-27B-MTP-GGUF` at revision `88fb5663d646bc78e1140648e8d8cb7d3e849908` (also
  the repo head on 2026-11-20), file `Qwen3.5-27B-Q4_K_M.gguf`, 17,106,773,056 B, sha256
  `130865c3ef0fd037cbc517021c39eace6b714ac8dc53645bdd2fe7311320b2f7` (the LFS oid, and the hash in the report's
  `checksums.txt`). The same file serves both modes; with MTP off its MTP layer is simply unused, as in the report.
- **Server, every setup:** `llama-server -m <model> -c 32768 -np 1 --host 127.0.0.1 --port 8081`, plus the two MTP
  flags in mtp mode. Nothing else: `-ngl`, `-fa`, batch sizes and threads at each build's defaults, as in the report.
  The effective values (layers offloaded, flash attention, n_batch/n_ubatch, threads, context) are read from each
  server's start log and recorded. If two arms' defaults differ, that's recorded and reported, not forced.
- **Request, as the report's `bench.py`:** `/v1/chat/completions`, streamed, `temperature 0`, `seed 42`,
  `chat_template_kwargs: {enable_thinking: false}`, one user message.
  - **short:** a nonce line, then the report's prompt, verbatim: "Write a long, detailed essay of at least 2000 words
    about the history of the bicycle, with many sections." `max_tokens 512`.
  - **long:** a nonce line, then the report's `long-context.txt` (16,815 B, sha256
    `e004418bcd8335f8c967906af54006ebdfba7c77cbb2a24fa5f24ea0d88d6e53`), then "\n\nSummarize the text above in five
    bullet points." `max_tokens 256`.
  - **Nonce:** "Request id <8 hex>.\n", not the report's 32-hex uuid, so the prompt_n void rule (M5) can hold.

## M3. Builds and runs

- **Built from source on Tamanna, all three the same way:** nvcc 12.4.131, gcc-13, `-DGGML_CUDA=ON
  -DCMAKE_CUDA_ARCHITECTURES=86 -DGGML_NATIVE=OFF -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF` (the
  `build-llama-v0.7.0.sh` recipe). Each clone's HEAD is checked against M2 before configuring; `llama-server
  --version` and the sha256 of `llama-server` and `libggml-cuda.so` go in the record.
  - **If any of the three fails to build on CUDA 12.4,** all three are built on Rushuna instead (`~/cuda-13.0`, gcc
    13.3.0, sm_86, same flags) and run on Tamanna, as the Strata records did. All arms always share one toolchain.
- **Deviation from the report, stated in advance:** the report ran the official Docker images (CUDA toolkit not
  stated) on driver 615.78.08. We build from source with our toolchain on driver 580.178.04. Absolute speeds can
  differ; the comparison is between arms on one machine.
- **Measured runs inside `bwrap --dev-bind / / --unshare-net`** (loopback only), bench client in the same namespace,
  as in the HotRod record.

## M4. Measurement (Rule P4)

**Order.** 3 rounds. Setups in a fixed list: V-mtp, Z-mtp, O-mtp, V-off, Z-off, O-off. Round r (1..3) runs
setups[(k + 2(r−1)) mod 6] for k = 0..5, so each arm and mode moves position between rounds (the report interleaved
the same way). For each setup:

1. Start the server, wait for `/health`. Card at 0 MiB before every start.
2. Warm-up: one short request with `max_tokens 32`, discarded (the report's warm-up).
3. **short:** priming request, then measured request. **long:** priming request, then measured request.
4. Wait for the GPU at ≤ 50 °C before every measured request (the report's cool-down rule). Stop the server.

A **cell** is (arm, mode, prompt): 12 cells, each with 3 (priming, measured) pairs, one per round. **Value = mean of
the 3 measured requests (min..max).**

- **Decode** = the server's `predicted_per_second` (the report's `tg_tps`). **Prefill** = `prompt_per_second`;
  client TTFT beside it.
- **Recorded per request:** prompt_n, cache_n, predicted_n, draft acceptance (the server's `draft acceptance` log
  line, mtp mode), swap-in/out KiB, NVMe read bytes on the model's drive, PCIe gen/width sampled during prefill,
  peak card MiB, GPU temperature at start and end, the first 200 characters of the answer (sanity: empty, looping or
  garbled answers are flagged).
- **Model hash** checked on arrival on Tamanna and again after the last round. A mismatch voids the run.
- **Machine state,** once: free RAM and disk, driver version, GPU clocks and power limit as set (not changed).

## M5. Void rules (P4 with A1's reading)

A cell is void if any of its 6 requests has:
- a prompt_n spread over 3 tokens (max − min ≤ 3 across all 6, A1);
- cache_n above the chat template's header (≈0; the nonce line comes first);
- swap-out above 0 KiB;
- the PCIe link below gen 4 x16 during prefill;
- NVMe reads over 1 GiB during the measured decode (flag over 64 MiB; the model sits in VRAM).

A void cell is re-run once (all 3 pairs, same setup, appended after round 3). Void twice is reported as void.

## M6. Predictions (set before any number exists)

"Faster" means V's mean is higher **and** the min..max ranges don't overlap. "Within ±3%" means the ratio of the
means V/X is in [0.97, 1.03]. Each prediction is scored on decode, per prompt, and holds only if it holds at both
prompts (short and long).

- **P1, MTP off, the version question (Mark):** V within ±3% of O, and V within ±3% of Z.
- **P2, MTP on, the report's claim (Mark; band set here):** V faster than O, with V/O in **[1.30, 1.70]**. The report
  got 1.52 (short) and 1.55 (long) on the same card model. The band allows for a different CPU, driver and
  toolchain, and still calls anything under +30% a miss.
- **P3, MTP on, the last 0.9 build:** V within ±3% of Z. (Same inference code; this checks that.)

Descriptive, with no prediction: prefill and TTFT for every cell, draft acceptance per arm (the report found it
unchanged across builds), MTP-on vs MTP-off within each arm, and peak VRAM with and without MTP (the report: about
+1,490 MiB for the 27B).

If P1 or P3 fails, the write-up looks for a cause before drawing any version conclusion. Two candidates: the
interleave didn't cancel thermal or clock drift, or a build default differs (M2).

## M7. What gets written down

`docs/bench-results/tamanna-llamacpp-v1-mtp-2026-11/` (public via the mirror, through the leak gate): this
registration's section numbers, build logs, `--version` output and binary sha256s, each server's start log (the
effective defaults), the harness and its diff from the report's `bench.py` (`06fdc812…` at commit `9ea02603`), the
per-request JSONL, `summarize.py` output, acceptance lines, the machine-state block, every void and deviation.
Machine names only.

## M8. Limits stated in advance

- **One model, one card, one prompt pair, 3 runs per cell.** It tests one claim, not llama.cpp speed in general.
- **Single request only.** The report's 4-request (+22% for the 27B) and CPU tests are not repeated.
- **Speed only.** At temperature 0, MTP shouldn't change the output text. The sanity flag is the only check on it.
- **MTP on Qwen3.5-27B is an older model's head.** Newer models (Qwen3.8) aren't tested here.

## M9. Gates

1. No download, build or measured request before this file is committed, its sha256 recorded, pushed, and
   published to the mirror with the public copy's sha256 matching.
2. Disk on Tamanna: at least 20 GB free throughout (88 GB free before this registration; the model is 17.1 GB, the
   three builds a few GB). The model's canonical copy goes to Miu's `LLM_repo/qwen3.5-27b-mtp-gguf/` with a
   `SHA256SUMS`, and Tamanna gets a working copy. The voice-run files for 2026-11-24 (`~/voice-pipeline`,
   `~/bench-models/voice-pipeline`, `~/voice-01`) and the HotRod record's files (`~/hotrod-2026-11`, the Flash-Next
   shards under `~/bench-models/`) are not touched. Nothing that exists on Tamanna is deleted.
3. The article draft is written only after the record exists, on a local branch, previewed on the LAN, not
   deployed. It links to none of the frozen 8 (open-threads.md).
