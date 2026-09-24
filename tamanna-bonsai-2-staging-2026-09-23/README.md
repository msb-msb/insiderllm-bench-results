# Bonsai 2 27B staging on Tamanna — PrismML fork built, model staged, fork sanity vs pin, 2026-09-23

Per `docs/candidates/bonsai-2-27b-2026-09-23.md`. Staging only: no 47-item run, no article, no deploy. The v0.4.0
pin at `~/llama-v0.4.0` is untouched.

## 1. Build record — PrismML llama.cpp fork

| | |
|---|---|
| Source | `git clone --depth 1 --branch prism-b10709-9a9394a https://github.com/PrismML-Eng/llama.cpp ~/llama-prismml` |
| Tag / commit | `prism-b10709-9a9394a` = `9a9394a895b96003ca842a6041cb28ac49a108f7` "build: fix Ubuntu ARM64 and Windows Vulkan release jobs (#198)", the fork's latest release (2026-09-18) |
| Upstream base | **b10709** (from the tag name), 100 builds before our pin v0.4.0 = b10809 `5266f24` |
| Configure | identical to the v0.4.0 record: `cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=86 -DGGML_NATIVE=OFF -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF -DCMAKE_C_COMPILER=gcc-13 -DCMAKE_CXX_COMPILER=g++-13 -DCMAKE_CUDA_HOST_COMPILER=g++-13` |
| Build | `cmake --build build --config Release -j 16`, 16:04:09 → 16:09:20 PDT, no errors; `build.log` and `build-flags.txt` here |
| Toolchain | nvcc 12.4.131, gcc-13, sm_86; `llama-bench` reports `build_commit 9a9394a`, `build_number 1` (shallow clone) |

## 2. Files staged and verified

| file | where | bytes | sha256 | against |
|---|---|---:|---|---|
| `Ternary-Bonsai-2-27B-PQ2_0.gguf` | `LLM_repo/bonsai-2-27b-gguf/` (pulled from the hub, 5.6–7.3 MB/s) and Tamanna `~/bench-models/` | 7,206,168,928 | `3907dc1658db1f78a9826bf8d5bcb8dc65db0d466388937af57f2294fae62ec1` | HF LFS oid — **match**, on both copies |
| `Qwen3.8-27B-UD-Q4_K_XL.gguf` | Tamanna `~/bench-models/` | 17,923,394,624 | `bee238bbeb3dc0a34bde4d0dedbaee1f98c009e8bb4226f03070054c12fb1372` | the 08-14 record (`benchmarks.json`, the 3.8-vs-3.6 article) — **match** |

### The archive copy of Qwen3.8-27B was corrupt, and is now repaired

The brief said to copy the Qwen3.8-27B file from the store. That copy, `LLM_repo/qwen3.8-27b-gguf/Qwen3.8-27B-UD-Q4_K_XL.gguf`,
hashed `eef23698b37b48eba852dc2f85950a1dbbf5b8515e2045762ed35c90ec8eca56` on the HDD and again after a faithful
copy to Tamanna — not the `bee238bb…` its own `.cache/huggingface` download metadata records and the article verified.
This is **event #3 in `docs/memory-fault-2026-08-15.md`**: "Qwen3.8-27B UD-Q4_K_XL (Aug 14 download), Storage_Disk_1,
on platter, offset mod 4096 = 684, bit 6, 1→0" — one byte written wrong through the faulty DIMM, on the platter, and the
archive copy was never repaired when the DIMM was replaced on 08-24. The verified copy lived at
`~/Desktop/qwen3.8-27b-gguf/` on Miu (the file the fault record itself hashes) and hashes `bee238bb…` today.

Done today: the corrupt archive file was renamed `Qwen3.8-27B-UD-Q4_K_XL.gguf.CORRUPT-event3-2026-08-14-bit6` (kept as
evidence, 17.9 GB) and the verified Desktop copy was copied into the store and re-hashed there: `bee238bb…`. The hub
today serves a **different** file for the same name (Unsloth re-uploaded 2026-08-20: 17,559,178,144 bytes,
`3f227079…`), so the 08-14 file can only be verified against its own record, which it now is. Events #1 and #2 in the
same table (the Qwen3.6-27B and gemma-4-26B UD-Q4_K_XL archive copies) were not checked today and should be.

## 3. Fork sanity: Qwen3.8-27B UD-Q4_K_XL, fork vs pin, same box, same file

Harness `llama-bench -ngl 99 -fa 1 -p 512 -n 128 -d 0,4096,8192 -r 5`; block 3 priming design, three reps, builds
alternating, a discarded priming run before every measured run; 1 s telemetry. **Pre-registered: any decode cell outside
3% is the finding and staging stops.** Run 2 (the record) is on the verified file; run 1 was made on the corrupt
archive copy before the digest mismatch was understood and is kept in `fork-sanity-run1-archive-copy/` — its deltas are
in the last column, and they agree with run 2, as they should: a one-byte weight difference does not move throughput.

| metric | v0.4.0 `5266f24` (n=3) | fork `9a9394a` (n=3) | delta (run 2) | verdict | run 1 delta (corrupt file) |
|---|---:|---:|---:|---|---:|
| tg128 d=0 | 41.76 [41.76..41.77] | 42.11 [42.11..42.12] | **+0.84%** | no change | +0.83% |
| tg128 d=4096 | 41.25 [41.25..41.25] | 41.60 [41.60..41.61] | **+0.86%** | no change | +0.81% |
| tg128 d=8192 | 40.77 [40.76..40.77] | 41.11 [41.11..41.11] | **+0.85%** | no change | +0.84% |
| pp512 d=0 | 1,445.0 [1,444.7..1,445.3] | 1,413.9 [1,413.5..1,414.0] | **-2.16%** | no change | -2.27% |
| pp512 d=4096 | 1,388.3 [1,387.9..1,388.8] | 1,356.7 [1,356.1..1,357.3] | **-2.28%** | no change | -2.42% |
| pp512 d=8192 | 1,331.5 [1,331.1..1,331.7] | 1,300.1 [1,299.6..1,300.9] | **-2.36%** | no change | -2.29% |

Peak VRAM, measured runs: v0.4.0 17,668 MiB, fork 17,666 MiB (the 08-14 figure on Miu was 17,942 MiB at
llama-bench's default context; this is the `-d 0,4096,8192` sweep on Tamanna). Telemetry: v0.4.0 sm 1770–1770 MHz median, 401–402 W, PCIe gen [4], temp max 73 °C; fork sm 1762–1770 MHz median, 402–406 W, PCIe gen [4], temp max 73 °C.

**Verdict: the fork reproduces the pin on decode to within 1% on every depth**, so results from it are comparable to the
v0.4.0 rows; prefill is ~2.3% slower on the fork at every depth, inside the gate but consistent, and worth stating beside
any prefill figure taken on the fork.

## 4. Bonsai 2 27B — SMOKE TEST, not a result

One `llama-bench` invocation under the fork, `-ngl 99 -fa 1 -p 0 -n 128 -d 0 -r 3` — tg128 at d=0 only, three
llama-bench repeats inside one run, no prefill row, nothing alternated, nothing primed. It answers "does the PQ2_0 file
load and generate on sm_86 under this fork" and gives one number that is **not** a benchmark figure.

| | |
|---|---|
| rc | 0 |
| tg128 d=0 | **78.204755 tok/s** (llama-bench sd 0.108779) — smoke test |
| VRAM peak | **7,162 MiB** (card idle before: 7, 52) |
| model as loaded | type `qwen35 27B PQ2_0 - 2.13 bpw (group 128)`, 6.70 GiB, 26.90 B params |
| telemetry | PCIe gen [4], sm 1845.0 MHz median, 361.1 W, temp max 66 °C |
| build | `9a9394a` / 1 |

The pre-registered comparison (Bonsai 2 PQ2_0 vs Qwen3.8-27B UD-Q4_K_XL, both under the fork, plus the 47-item split) is
in the candidate doc and has not been run.

## Files

| path | content |
|---|---|
| `build.log`, `build-flags.txt`, `build-llama-prismml.sh` | the fork build |
| `fork_sanity.py`, `fork-sanity/` | the runner and run 2 (record): `run.log`, `results.json`, `summary.json`, raw JSON and telemetry per run |
| `fork-sanity-run1-archive-copy/` | run 1, same design, on the corrupt archive copy — kept, not the record |
| `bonsai_smoke.py`, `smoke/` | the smoke test: `smoke.json`, `telemetry.csv` |
