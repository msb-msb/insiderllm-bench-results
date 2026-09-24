# Archive re-hash of the 2026-08-14 memory-fault files, and the bench-record audit — 2026-09-24

Follows the 09-23 finding that the store's Qwen3.8-27B copy (event #3 in `docs/memory-fault-2026-08-15.md`) was still
corrupt. This closes the other two on-platter events in that table, #1 and #2, and audits every record that could have
read either file after 2026-08-14. No article, no deploy.

## The files

Both live in the store under the 08-04 rsync tree, `LLM_repo/from-miu/Desktop/lucebox-hub/`, copied from Miu's NVMe on
2026-08-04 through the DIMM that was bisected as faulty on 08-18 and replaced on 08-24. Neither directory carries
`huggingface_hub` download metadata (they were rsynced, not downloaded there), so the reference is the NVMe original in
`~/Desktop/lucebox-hub/` on Miu, cross-checked against the hub where the hub still serves the same revision.

| file | copy | bytes | sha256 | verdict |
|---|---|---:|---|---|
| `dflash/models/unsloth/Qwen3.6-27B-UD-Q4_K_XL.gguf` | **archive, as found** | 17,612,564,704 | `0484a51fd6d96cd4c9a15db186918dce97c69b2b21870d52a39c2c16e87ac4c3` | **corrupt** (event #1) |
| same | NVMe original | 17,612,564,704 | `ff6941ded525b34eb159496762c29dd0ec6e71dc31b74d57e75d871a03eec259` | matches hub LFS oid (unsloth/Qwen3.6-27B-GGUF, same size, repo last modified 2026-04-22), the 3.8-vs-3.6 article, and 3 dataset rows |
| same | **archive, restored** | 17,612,564,704 | `ff6941de…` | verified |
| `gemma-4-test/gemma-4-26B-A4B-it-UD-Q4_K_XL.gguf` | **archive, as found** | 17,010,978,592 | `7172046111f7aa5ce7ab9a4c58919156f8d5b4b291a0b3275ff6117570845566` | **corrupt** (event #2) |
| same | NVMe original | 17,010,978,592 | `453cf049ba87a29b9ed5739087b84b7fa0265a4f2b11eefa2c77683dec6a8020` | **not hub-verifiable**: unsloth/gemma-4-26B-A4B-it-GGUF now serves a different revision (17,010,980,576 bytes, `ef728c8e…`, modified 2026-07-17), and no digest of the May-8 download was recorded anywhere in the repo |
| same | **archive, restored** | 17,010,978,592 | `453cf049…` | matches the NVMe original |

The two archive hashes the brief asked for: **`0484a51f…` (Qwen3.6-27B) and `71720461…` (gemma-4-26B-A4B)**, both wrong.

**Byte-level confirmation** (`cmp -l`, corrupt archive against NVMe original): exactly one differing byte in each file, and
in both the archive byte is the original with bit 6 cleared — the fault's signature, four for four now.

| file | differing bytes | offset (0-based) | offset mod 4096 | archive → original | xor |
|---|---:|---:|---:|---|---|
| Qwen3.6-27B | 1 | 9,294,969,093 | **2309** | 0x22 → 0x62 | 0x40 (bit 6, 1→0) |
| gemma-4-26B-A4B | 1 | 15,713,532,165 | **2309** | 0x9C → 0xDC | 0x40 (bit 6, 1→0) |

The fault record's table gives offset mod 4096 = 2309 for both; the offsets measured here are the byte positions of the
same single-bit errors as read today. What was done: each corrupt file renamed in place to `…gguf.CORRUPT-event{1,2}-2026-08-14-bit6`
(kept as evidence, 17.6 + 17.0 GB), the NVMe original copied over, and the copy re-hashed on the HDD. With the 09-23
repair of event #3, all three on-platter copies in the fault table are now restored and verified against their references.

## Bench-record audit: everything that could have read either file after 2026-08-14

Method: every `docs/bench-results/` directory dated 08-14 or later and every `benchmarks.json` row for Qwen3.6-27B or
Gemma 4 26B-A4B, checked for which file path it read and whether a hash was recorded at run time. Also the window
between the 08-04 rsync and 08-14, since a corrupt archive copy was equally corrupt then.

| record | date | file read | path | hash at run time | verdict |
|---|---|---|---|---|---|
| `benchmarks.json` rows `miu-qwen36-27b-udq4kxl-abba-d0/-d4096/-d8192` (the 3.8-vs-3.6 A-B-B-A) | 2026-08-14 | Qwen3.6-27B UD-Q4_K_XL | NVMe (`~/Desktop/lucebox-hub/…`) | `sha256_verified_against: upstream-lfs-oid`, `sha256_verified_at: 2026-08-14`, `ff6941de…` | **unaffected** |
| `miu-humaneval-chat-path-2026-08-17` | 2026-08-17 | Qwen3.6-27B UD-Q4_K_XL (and 3.8) | NVMe, per `scripts/chat_orch.py` | full bracket, "All eight hashes matched" | **unaffected** |
| `miu-memory-retest-humaneval-2026-08-16` | 2026-08-16 | Qwen3.8-27B only | NVMe | bracketed | out of scope (not either file) |
| `rushuna-moe-routing-trace-2026-08-24` | 2026-08-24 | neither — the fault table appears verbatim inside `prompts/longctx.txt` as prompt text | — | — | not a use of the file |
| `rushuna-gemma-repro-2026-08-02` | 2026-08-02 | gemma-4-26B-A4B-it **UD-Q4_K_M** (a different file) | Rushuna `~/bench-models/` | — | not either file |
| `benchmarks.json` Gemma 4 26B-A4B rows (11, `rushuna-…-udq4km-…`) | 2026-07-22 | UD-Q4_K_M | Rushuna | none recorded | not either file, and before the rsync |
| `benchmarks.json` Qwen3.6-27B shootout rows (`miu-shootout-mainline-20260522` etc.) | 2026-05-22/25 | UD-Q4_K_XL and others | NVMe at the time | none recorded | before the rsync — the copy did not yet exist |
| `~/Desktop/lucebox-hub/backend-shootout.sh` | repointed to the **archive** paths 2026-08-04 (`docs/model-storage-convention.md`) | Qwen3.6-27B UD-Q4_K_XL mainline arm | archive | — | **not run since**: no result newer than the 05-25 article `lastmod`, no bench-results directory references `from-miu`. Had it been run between 08-04 and today it would have read the corrupt copy. It now reads the restored file |
| `gemma-4-26B-A4B-it-UD-Q4_K_XL` — any record after 08-14 | — | — | — | — | **none exist**; the only record ever is the 05-08 `gemma-4-test` comparison, run on the NVMe original before the rsync |

**Affected list: empty.** No record after 2026-08-14 (or after the 08-04 rsync) read either archive copy. Every result on
either file was taken from the NVMe originals, and the two that fall after 08-14 were hash-bracketed at run time.
**Suspect list: empty** for these two files on this window. The 05-22 shootout and 07-22 Gemma rows carry no hash but
predate the corrupt copies' existence.

## What stays open

- The gemma NVMe original `453cf049…` is the reference only because the archive was copied from it and the fault record
  says the archive was "written wrong"; it was downloaded 2026-05-08, inside the period the DIMM was in the box, and there
  is no upstream digest to test it against because Unsloth has since replaced the file. It is as verified as it can be.
- Two archive files were repaired without a hub check being possible. Anything that would publish a number on the gemma
  UD-Q4_K_XL file should re-pull the current hub revision (`ef728c8e…`) rather than use the May-8 file.
- The store now holds three `*.CORRUPT-event*` files as evidence (52 GB). Delete them when the fault record is closed for good.

## Reproduction

Hashes: `sha256sum` on Miu, 2026-09-24 10:05–10:35 PDT. Byte diff: `cmp -l <archive> <nvme> | head`. Restore: `cp` from
`~/Desktop/lucebox-hub/` to the archive path, then `sha256sum` on the HDD copy.
