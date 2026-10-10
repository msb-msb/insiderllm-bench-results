# Tamanna after DOCP (DDR4-2133 → 3200): the standard gen 4 verify bench, 2026-10-05

PRE-REGISTRATION, written and committed before the run.

**What changed.** Tamanna's RAM is 2 × 16 GB G.Skill F4-3200C16-16GVK, dual rank. It ran at **DDR4-2133 from the
rig's first day (2026-09-21) until 2026-10-05**, because DOCP was never enabled. Mark enabled DOCP on 2026-10-05.
The box has been up since 13:55:43 PDT, its power-on after the 10-04 outage, so DOCP was set on that boot.
**Configured speed:** to be read by `sudo dmidecode -t memory` (Mark runs it) and pasted below before the result is
published.

**No-root bandwidth check, same session** (`stream_read.c`, written today, 320 MB array, best of 8, gcc-13 -O3
-fopenmp; `stream-read-tamanna.txt`): peak sustained read **32.36 GB/s** at 4 threads (1: 11.76, 2: 23.33, 8: 31.01,
16: 28.16). That is 95% of dual-channel DDR4-2133's 34.1 GB/s theoretical, against 80% measured on Rushuna's
DDR4-2133. It is 63% of DDR4-3200's 51.2. So it is consistent with 3200 and hard to square with 2133, but it isn't
proof. There is no pre-DOCP figure from this kernel (the 07-30 STREAM source was not kept), so it is a single point.

## Method: byte-identical to `../tamanna-gen4-verify-2026-09-23/`

- `docp_verify.py` is that record's `gen4_verify.py` with only the output directory changed (`diff`: one line).
- `llama-bench -ngl 99 -fa 1 -p 512 -n 128 -d 0,4096,8192 -r 5` on Ornith-1.5-35B-A3B Q4_K_M and Qwen3.6-35B-A3B
  UD-Q4_K_M, both re-hashed today and matching their records.
- llama.cpp v0.4.0 `5266f24`, the same build; Block 3 priming; 3 reps, models alternating.
- Both models are **fully resident** on the 3090 (`-ngl 99`, no `-ncmoe`). That is the class of result the dated
  correction line covers.

## Comparison, decided now

Each of the 12 cells against **09-23** (and against the 09-21 block 3 reference, for continuity).

- **Expected: every cell within 1%.** A resident model's decode and pp512 run from VRAM, and RAM speed should
  only touch host-side work.
- If every cell is within 1%: the correction line "resident-model results unaffected" is backed by this record.
- If any cell moves more than 1%: it is reported, and the correction line is **not** applied as worded until Mark
  decides.

## Result: aborted. dmidecode shows DOCP is not active (2026-10-05, ~14:52 PDT)

`sudo dmidecode -t memory`, run by Mark during the run:

```
Size: No Module Installed            (slot 1)
Size: 16 GB   Speed: 2133 MT/s   Part Number: F4-3200C16-16GVK   Rank: 2   Configured Memory Speed: 2133 MT/s
Size: No Module Installed            (slot 3)
Size: 16 GB   Speed: 2133 MT/s   Part Number: F4-3200C16-16GVK   Rank: 2   Configured Memory Speed: 2133 MT/s
```

**The box is still at DDR4-2133.** The DOCP change didn't take on the boot that's running (up since 13:55:43). The
verify bench was stopped after its first priming run, so no measured figure exists. The partial files are kept as
`aborted-*`. The board has **4 slots, 2 populated**.

**Retraction:** the bandwidth paragraph above read 32.36 GB/s as "consistent with 3200 and hard to square with
2133". That was wrong. **32.36 GB/s is what this kernel reads on this box at DDR4-2133**: 95% of theoretical on a
Zen 3 part. I extrapolated that efficiency from an Intel box (Rushuna, 80%), and that was not valid. The figure
stands as the **pre-DOCP baseline** for this kernel, which is now useful: the same binary re-run after DOCP gives
the before/after.

The verify bench reruns, unchanged, once dmidecode reads 3200.

## Outcome (2026-10-05, from Mark)

The DOCP attempt **failed memory training**; the board fell back to DDR4-2133. PCIe gen 4 x16 confirmed. So there is no post-DOCP state to verify and this record ends here. Tamanna runs at DDR4-2133 (memory profile not active; a 2026-10-05 attempt to enable it failed training). Resident-model results are unaffected. Board: ASRock B550 Phantom Gaming 4/ac, BIOS P3.90 (2025-09-30), from `/sys/class/dmi/id` (world-readable; no sudo needed). The 32.36 GB/s read above is the box's figure at DDR4-2133.

## Second DOCP attempt, 2026-10-09 (4 × 16 GB, BIOS P4.00): also fell back to 2133

Mark fitted two more F4-3200C16-16GVK (now 4 × 16 GB, two dual-rank sticks per channel), flashed the BIOS from P3.90
to P4.00 and set DOCP. Boot at 12:10:18 PDT. `sudo dmidecode -t memory` (Mark ran it): **Configured Memory Speed
2133 MT/s on all four slots, Configured Voltage 1.2 V** (JEDEC; the kit's 3200 profile is 1.35 V). The BIOS offers
DRAM voltage on Auto only. Read bandwidth with the same `stream_read.c` and build
(`stream-read-tamanna-2026-10-09-4x16.txt`): peak **31.68 GB/s** at 4 threads, against 32.36 at 2133 on 10-05,
so the same speed. No MCE or hardware-error lines in this boot's kernel log; the RAM is not ECC, so EDAC counts
nothing. So DOCP did not take, again, and there is still no post-DOCP state for this verify bench to measure.
Restore on AC power loss: **On** (Mark, after the flash).

## DDR4-3000 trains, 2026-10-09: the attempt ladder

All on 4 × 16 GB F4-3200C16-16GVK (two dual-rank sticks per channel), BIOS P4.00, Mark at the BIOS:

| Attempt | DRAM voltage | Result |
|---|---|---|
| DOCP 3200 | Auto (dmidecode then read 1.2 V) | failed training, fell back to 2133 (section above) |
| 3200 | 1.35 V manual | failed training, fell back to 2133 |
| 3200 | 1.38 V manual | failed training, fell back to 2133 |
| **3000** | **1.35 V manual** | **trained**: dmidecode reads 3000 MT/s on all four slots |

Gear Down Mode: Mark could not find the setting in BIOS P4.00, so it is left at whatever the board does on its own (not readable from Linux).

Read bandwidth at 3000 (`stream-read-tamanna-2026-10-09-ddr4-3000.txt`, same `stream_read.c`, rebuilt the same way):
peak **41.95 GB/s** at 4 threads (two repeats 41.74 and 42.00), against 32.36 at 2133: **+30%**, 87% of
dual-channel DDR4-3000's 48.0 GB/s theoretical. Single- and two-thread reads did not move (11.77 / 23.40), so those
are limited by the core, not the RAM. No MCE, hardware-error or memory-error lines in the kernel log for this boot
(12:38:37); the RAM is not ECC, so EDAC counts nothing.

**Not yet usable for benchmarks.** memtest86+ runs overnight at 3000 / 1.35 V; nothing is measured on Tamanna until
it passes. If it does, the Gen 4 verify bench pre-registered at the top of this record runs at 3000 (marker
2026-10-10), against 09-23, with the same "every cell within 1%" expectation for resident models.
