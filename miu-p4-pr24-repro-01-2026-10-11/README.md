# ESP32-P4 (v3.2) reproduction of esp32-ai PR #24, 2026-10-11, CONFIRMATORY: P1 held, P2 held, P3 failed

Results record for `~/Desktop/esp32-llm/p4/evals/pr24-repro-01/PREREG.md`. This reproduces the ESP32-P4 port in esp32-ai PR #24 (Barkın Sarıkartal) on our board.

**What the PR does**
- PIE int8 matvec and an int4 head unpacked in registers.
- Quantised KV cache: int8 keys, int16 values.
- Dual-core attention and L1 preload.

**What changed for our board:** only `ChipVariant=postv3`, because our silicon is v3.2. The PR ran on v1.3 at 360 MHz.

**Status:** confirmatory, not blind. The PR's 14.6 ms/token was known.

## Pre-registration

- **PREREG.md** sha256 `01a0461ff5ae354c5c76d73b887ce6125ffa646d79a2d525ece98a6cdb388a12`.
- **Written 2026-10-11T19:56:28-07:00**, after compile-only builds and before the first flash (model, 19:56:35). The first run capture was at 20:01:29.
- Unchanged after the runs.

## Hardware

- Waveshare ESP32-P4-ETH: ESP32-P4 **silicon v3.2**, 2 cores at **400 MHz**.
- 32 MB AP Memory hex PSRAM at 200 MHz; 32 MB GD QIO flash at 80 MHz.
- CH343 UART bridge, `/dev/serial/by-id/usb-1a86_USB_Single_Serial_5C93015982-if00`.
- No display. Host: Miu.
- The S3 on the same host was not touched.

## Firmware

**Source**
- PR #24 head `2906bde9c4387381a2962a3c123e51b675bf7d46` (fork `barkinsarikartal/esp32-ai`, branch `esp32-p4`).
- **Public source, pinned:** [https://github.com/msb-msb/esp32-ai/tree/2906bde9c4387381a2962a3c123e51b675bf7d46](https://github.com/msb-msb/esp32-ai/tree/2906bde9c4387381a2962a3c123e51b675bf7d46). This is the PR #24 head (Barkın Sarıkartal), mirrored on `msb-msb/esp32-ai` as the base of branch `insiderllm-p4`. Upstream PR: https://github.com/slvDev/esp32-ai/pull/24. The bench harness used here is commit [`9914179`](https://github.com/msb-msb/esp32-ai/tree/991417919f52da873365c52fcb9439dcef1e5f49).

**Toolchain and FQBN**
- arduino-cli 1.5.1, core esp32:esp32 **3.3.10**, `esp32p4-libs` (IDF v5.5.4 `735507283d`), `-O3`.
- FQBN `esp32:esp32:esp32p4:ChipVariant=postv3,UploadSpeed=921600,USBMode=hwcdc,CDCOnBoot=default,UploadMode=default,FlashMode=qio,FlashFreq=80,FlashSize=32M,PartitionScheme=custom,PSRAM=enabled,DebugLevel=info`.
- The libs give rev 301–399, 400 MHz, **L2 256 KB / 128 B line**, PSRAM hex 200 MHz.

**Steps**
- `deploy.sh` was not run: it defaults to a macOS port glob and flashes immediately.
- Its steps were run by hand:
  - headers (tokenizers 0.23.1);
  - `staging_verify` at align 1 and 16: PASS;
  - compile;
  - esptool 5.3.0 `write-flash @flash_args`.

**Harness** `bench-harness.patch` (sha256 `e446eb734a649419f58573c51db976ccc56680412ae0aa041f8bf3b302b7bd95`), for B1–B4:
- `PR24_BENCH=1`: compiled prompt 433 447 259 405, greedy, 200 tokens, no EOT stop.
- `LOGIT_CHECKSUM=1`: our S3 hash.
- `PR24_KV_QUANT=0`: the PR's upstream fp32 KV path.
- It is inert by default: forward-pass functions are identical by address-normalised disassembly between B0 and the patched build with no defines.

**Builds and app sha256 (16)**
- B0 PR unchanged `c2a4e67579b9607a`
- B1 bench `c7ba8d9c76c43740`
- B2 bench+hash `0416229dfeba9aaa`
- B3 bench fp32-KV `0adaf69a5f1915f0`
- B4 bench fp32-KV+hash `d5ced944f9acd3be`

## Model

Release model.bin `1d8326c05c383ccfa615f5455575802817cb453dbc7ab28875d41a9dbb45477e`, flashed to 0x110000. Every boot printed `fp=a9bdd778`.

## Predictions (verbatim) and verdicts

| | prediction (verbatim) | verdict | measured |
|---|---|---|---|
| P1 | "P1: the PR's boot self-checks pass on v3.2 silicon." | **held** | 18/18 boots: `matvec max \|vector - scalar\| = 0, dot mismatches 0 -> ok`; no FATAL, panic or abort |
| P2 | "P2: ms/token (the PR's own forward-pass timing, 200 tokens, the compiled prompt) is within +/-15% of the PR's reported 14.6 ms/token." | **held** | B1: 13.6 / 13.6 / 13.6 (−6.8%) |
| P3 | "P3: if the PR has an exact mode (fp32 KV, no approximations), its logits for the first 20 tokens hash to 4400a1cbf4a5137d (our S3 gate); if it only has the quantised-KV mode, report how its 200-token greedy text differs from b9abf55b... (first divergent token, and overall)." | **failed** | Exact mode (B4) `eac9915b0114d2e7` ×3. 9/20 per-token hashes equal the S3's (tokens 0, 1, 4, 6, 13, 15–18); first difference at token 2. **Greedy text identical** to the S3: `b9abf55b…`, 763 B |

**Quantised-KV mode (the PR default), reported**
- `logit_hash_all 36562c9f40f95e98` ×3. All 20 per-token hashes differ from token 0.
- Text `7797db061c15f3fb…`, 786 B.
- First divergent token: generated step 39 by retokenization, S3 `' she'` against P4 `' her'`, after "…She wanted to touch it, but".
- 112/203 tokens in matching blocks (ratio 0.552). Coherent prose in both.

## Result (ms/token, n = 3 per build, within-build range ≤ 0.0 except B0's 129-token run)

| build | KV | ms/token | tok/s | input | attn | ffn | ple | head |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| PR #24 reported (v1.3, 360 MHz) | quant | 14.6 | 63 | — | 4.4 | — | — | 7.1 |
| B0, as intended (typed prompt, T 0.8 top-k 40, EOT stop; 200/200/129 tokens) | quant | 13.6 / 13.6 / 13.1 | 67.2–69.7 | 0.7 | 4.0 / 4.0 / 3.5 | 1.0–1.1 | 1.2 | 6.7 |
| **B1, bench** | quant | **13.6** | 68.5 | 0.7 | 4.0 | 1.0 | 1.2 | 6.7 |
| B3, bench | **fp32 (exact)** | **16.3** | 58.0 | 0.7 | 6.8 | 1.0 | 1.2 | 6.6 |

**Readings**
- 7% faster than the PR's figure, consistent with 400 against 360 MHz.
- Exact mode costs +2.7 ms, all in attention: single-core and fp32 KV.
- The exact-mode figure matches the mcu-survey-01 ESTIMATE (15.8–16.0 ms) to within 3%.
- The head runs at ~189 MB/s effective, ~80% of `p4/bw_test` read streaming (231–241 MB/s).

## What our S3 work adds (ESTIMATES, see RESULTS.md)

- **int4 core:** −1.0 to −1.5 ms.
  - Not in internal RAM as-is: 259 KB free against 287 KB needed.
- **Logits in SRAM:** −0.3 to −0.6 ms.
- **Exact-path dual-core attention:** 16.3 → ~13.5–14 ms.
- **Prefill skip:** −6.7 ms per prompt token except the last.
- Seeded and interactive protocol, flag-gated EOT.
- **Nothing to add:** the 256 KB / 128 B L2 is already set by the Arduino libs, and the top-k sampler costs only ~0.3 ms over argmax.

**Board state:** P4 left on **B0** (PR unchanged + ChipVariant=postv3), flashed 20:05:59, with the release model at 0x110000.

## Files

Paths are local on Miu, under `~/Desktop/esp32-llm/`.

- `p4/evals/pr24-repro-01/`:
  - PREREG.md, RESULTS.md (sha256 `a0e384e464713b95a178f587dcd71f310ffdeaba3826b52c74ad00b5183f650b`);
  - `FQBN.txt`, `bench-harness.patch`, `capture_prompt.py`, `text_diff.py`, `text_diff_quant.txt`;
  - `logs/`: `build_*`, `flash_*`, `run_B{0..4}_{1,2,3}.txt`, `run_B2_hash_{1,2,3}.txt`.
- Builds: `p4/builds/pr24_{B0,B0p,B1,B2,B3,B4}`.
- Clone: `p4/pr24`, with the harness applied in the working tree.
- Board bring-up and bandwidth: `p4/NOTES.md`, `p4/bw_test/`.
