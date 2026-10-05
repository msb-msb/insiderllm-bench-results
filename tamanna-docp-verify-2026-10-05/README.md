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
