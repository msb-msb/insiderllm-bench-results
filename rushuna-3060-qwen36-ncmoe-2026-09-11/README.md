# Qwen3.6-35B-A3B UD-Q4_K_M, -ncmoe 40 and 24 on llama.cpp v0.4.0 — Rushuna RTX 3060 12 GB, 2026-09-11

Results record; facts as measured. Harness `ncmoe_sweep.py rushuna3060b` (this directory), run 12:11–12:16 PDT (log timestamps UTC). The 3060 went back into slot 01:00.0 the same day, replacing the GTX 1650 of the morning run; box rebooted 12:07 PDT. Same 32 GB DDR4-2133, same NVMe, same v0.4.0 sm_75/86 bundle, same file (sha256 `ac0e2c11…31a61`), 4 threads, mmap. The file was pre-read into page cache before the run (13 s, 22.2 GB cached) so no invocation pays the page-in.

Purpose: put the 1650 rows beside the same card family on the same build, and put v0.4.0 beside the July b10088 published rows on this card.

## Result (mmap, 4 threads)

| -ncmoe | expert layers on GPU | peak VRAM MiB | tg128 d=0 | tg128 d=4096 | server prefill (2,343 tok) | server decode |
|---:|---:|---:|---|---|---:|---:|
| 40 | 0 | 2,765 | 28.12 [28.00..28.22] | 27.99 [27.93..28.02] | 242.1 tok/s | 27.51 |
| 24 | 16 | 10,259 | 38.55 [38.10..38.86] | 38.39 [38.34..38.44] | 365.0 | 37.74 |

Zero disk reads during every decode; the cache holds the file.

## Beside the 1650 (same day, same box, same build, same file) and the July b10088 rows

| | GTX 1650 4 GB, v0.4.0 | RTX 3060 12 GB, v0.4.0 | RTX 3060 12 GB, b10088 (published, 2026-07) |
|---|---:|---:|---:|
| -ncmoe 40, tg128 d=0 | 20.22 [20.19..20.24] | 28.12 [28.00..28.22] | 28.1 |
| -ncmoe 40, tg128 d=4096 | 19.76 [19.74..19.77] | 27.99 [27.93..28.02] | not published |
| -ncmoe 40, peak VRAM | 2,701 MiB | 2,765 MiB | not recorded |
| -ncmoe 40, server prefill / decode | 65.0 / 19.7 | 242.1 / 27.5 | — |
| best fit | -ncmoe 38 (2 layers), 3,665 MiB | -ncmoe 24 (16 layers), 10,259 MiB | -ncmoe 24 |
| best fit, tg128 d=0 | 20.63 [20.62..20.65] | 38.55 [38.10..38.86] | 38.9 |
| best fit, tg128 d=4096 | 20.15 [20.12..20.17] | 38.39 [38.34..38.44] | 38.5 |
| best fit, pp512 d=0 / d=4096 | not run (-p 0) | not run (-p 0) | 413 / 394 |
| best fit, server prefill / decode | 66.0 / 20.2 | 365.0 / 37.7 | — |

**Build effect on the 3060: none.** v0.4.0 against b10088 at the same flags is +0.1 percent at -ncmoe 40 and −0.9 / −0.3 percent at -ncmoe 24, on a harness that differs only in `-p 0` and `-t 4`. Consistent with the 2026-09-07 gate.

**Card effect at full offload: −28 percent on the 1650.** With every routed expert on the host and only attention, the shared expert and the output head on the card, the 1650 decodes at 20.2 against the 3060's 28.1 on identical RAM. Decode at -ncmoe 40 is not purely host-bound: the on-card share is enough for the card to matter, and the sm_75 path on TU117 carries llama.cpp's own no-tensor-cores warning. Prefill is 3.7x apart (65 vs 242), which is the card doing the work.

**Card effect at best fit: −47 percent**, because the 3060 takes 16 layers and the 1650 takes 2. The two 1060 6 GB claims of 17 tok/s sit under both.

## Files

`run.log`, `results.json`, `raw-ncmoe{40,24}-mmap-rep{1,2,3}.json`, `server-stock-ncmoe40.log`, `server-best-ncmoe24.log`, `iostat-*.log`, `ncmoe_sweep.py`, `prompt-2k.txt`, `nohup.out`.
