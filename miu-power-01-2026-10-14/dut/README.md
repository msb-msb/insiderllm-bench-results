# DUT side: a sync GPIO for the bench firmware

**What it does:** with `-DSYNC_GPIO=<pin>`, the interactive firmware drives that pin **high
for each `G` command**. It rises just before the prompt's prefill and falls just after the last
token, before the `D` line. The pin is low the rest of the time.

**Always driven (revised 2026-10-13):** `SYNC_INIT()`, the first statement in `setup()`, makes the pin a
push-pull output and drives it low, so it is driven low from boot and never left floating.
- **The first version** configured the pin only on the first `G`. Until then, S3 GPIO4 was an input
  that fought the logger's pull-down and held the line at 0.945 V (DMM). That is in the RP2040's undefined zone,
  and GP15 chattered at ~35k edges/s.
- **The P4 patches match (regenerated 2026-10-14).** `ia_s3_port.h` carries the same block, and the P4 sketch's own
  `setup()` calls `SYNC_INIT()` first (`p4-sketch-sync-init.patch`). `setup()` isn't part of the extracted code.

**What it doesn't change:**

- Both edges are outside the timed `llm_forward` calls, so `decode_ms_per_tok` is not
  affected. (`ttft_us` gains a `digitalWrite`, about a microsecond.)
- Without `SYNC_GPIO` (default -1), the patch compiles to **identical object code**. Checked by comparing the
  sketch object's disassembly:
  - **First version:** checked 2026-10-12.
  - **P4, revised patches:** rechecked 2026-10-14 against IA1's own build object. The instructions are identical,
    and both are 538,758 B.
  - **S3, revised patch:** not yet rechecked (B build, unpatched vs patched).

**Flashed and verified at power-01 step d:** S3 B+sync `06abb9ad…` (2026-10-13) and S3 D+sync `cf2ff730…`
(2026-10-14). **Built, not flashed:** P4 IA1+sync `38299f17…` (2026-10-14).

## Pins

| Board | Pin | Why this one |
|---|---|---|
| ESP32-S3 N16R8 (DevKitC-style) | **GPIO4** | Plain GPIO on the left header next to RST. It avoids the strapping pins (0, 3, 45, 46), USB (19, 20), UART0 (43, 44), the octal flash/PSRAM pins (26–37), the RGB LED (48 or 38, depending on the board) and the OLED pins the display build uses (18, 46; the display is off in all our builds). |
| Waveshare ESP32-P4-ETH | **GPIO6** (header P1 pin 10; GND on P1 pin 8 or 13) | From Waveshare's schematic (`ESP32-P4-ETH-datasheet.pdf`, "Interface" block, header P1 "PICO-2*20 IO"), the GPIO6 net goes only from the chip's pin 6 to P1 pin 10: nothing else on the board uses it. It isn't a strapping pin (P4: 34–38), it isn't on the flash/PSRAM bus (dedicated FLASH_* pads, in-package PSRAM), and it's clear of the Ethernet PHY, SD card (39–44), I2C (7, 8), I2S (9–13, 53) and USB (24–27). Its reset state is no pull, input only (ESP32-P4 datasheet v0.7, Table 2-1), so the logger's pull-down holds the line low until the firmware drives it. |

**Why not GPIO2 on the P4** (the first choice, from Waveshare's GPIO example): it is broken out (P1 pin 15) and
unused on the board, but it's the pad-JTAG MTCK pin. With `EFUSE_DIS_PAD_JTAG` = 0 (the default), it comes out of
reset with its **45 kΩ pull-up enabled** (datasheet Table 2-1, note 5). The patch configures the pin only on the first
`G` command. Until then, that pull-up fights the logger's ~50–80 kΩ pull-down and holds the line at about 1.5–2 V,
an undefined level for the RP2040, which could log phantom sync edges while the board boots. GPIO6 has no
default pull. (Checked 2026-10-12 against Waveshare's schematic and Espressif's datasheet, both fetched.)

**Check before wiring:** find P1 pin 10 (GPIO6) on the P4 header silkscreen, and S3 GPIO4 on its header.

**Wiring:** DUT pin → logger GP15, DUT GND → logger GND (a wire right next to the sync
wire). Both sides are 3.3 V logic.

## Patches

| File | Applies to | How |
|---|---|---|
| `s3-sync-gpio.patch` | the S3 sketch after the power-01 stack (`…+prefill-skip+sample-profile+fast-sample`, .ino sha256 `ba7d7536…`) | `patch -p1` inside the sketch dir; same format as `esp32-llm/patches/*.patch` |
| `p4-extract-sync-gpio.patch` | `esp32-llm/p4/tools/extract_s3_interactive.sh` | `patch -p1` in `esp32-llm/` |
| `p4-ia_s3_port-sync-gpio.patch` | `p4/pr24` (insiderllm-p4 @ a96ab81) | `git apply` in `p4/pr24` |
| `p4-sketch-sync-init.patch` | `p4/pr24` (insiderllm-p4 @ a96ab81) | `git apply` in `p4/pr24` |

**The S3 patch** adds the `SYNC_GPIO` block after the FAST_SAMPLE checks, `SYNC_INIT()` at the top of
`setup()`, and `SYNC_SET(1)` / `SYNC_SET(0)` around the generation in `ia_cmd_generate`.

**The P4** gets the identical code in the usual way: `ia_s3_port.h` is extracted
verbatim from the S3 sketch, so it changes only through that extraction.

- **The extract-script patch:** it adds a second set of line ranges (`106-174, 819-836, 852-1350`), selected with
  `SYNC_GPIO_SKETCH=<patched S3 sketch>`. The revised S3 patch adds 19 lines inside the first range, 2 inside the
  last, and 1 in `setup()` outside the ranges. It also lets `OUT` be overridden.
- **Unchanged default:** without `SYNC_GPIO_SKETCH`, the script regenerates today's
  `ia_s3_port.h` byte for byte (checked).
- **`p4-ia_s3_port-sync-gpio.patch`:** it is exactly what the patched script writes from the
  patched S3 sketch (.ino `ea055c35…`; header sha256 `c2b76ca0…`). Nothing in it was edited by hand.
- **`p4-sketch-sync-init.patch`:** one line, `SYNC_INIT();` at the top of the P4 sketch's `setup()`.
- **Regenerated 2026-10-14** for the revised S3 patch. The 10-12 versions configured the pin on the first `G`;
  see git history.
- **Where they're committed:** both are on `p4/pr24` branch `power-01-sync-gpio` (`203acd5`, from a96ab81, not
  pushed). `insiderllm-p4` is left as IA1 was built.

## Building (compile-checked 2026-10-12; flash only when the power-01 protocol says so)

**S3, build B + sync.** Copy the patch into the patch directory, then build a new variant.
`build_variant.sh` writes `builds/<stack>+sync-gpio/`, so the B build directory isn't touched.

```bash
cd ~/Desktop/esp32-llm
cp tools/power-logger/dut/s3-sync-gpio.patch patches/sync-gpio.patch
NO_UPLOAD=1 VOCAB_REGEN=1 LIBS=B_64B_80M \
  DEFINES="-DHEAD_SC16=0 -DLOGITS_SRAM=1 -DCORE_INT4=1 -DINTERACTIVE=1 -DPREFILL_SKIP=1 -DFAST_SAMPLE=1 -DSYNC_GPIO=4" \
  tools/build_variant.sh "no-display+logit-checksum+simd-head+int4-head+simd-core+eot-flag+head-traffic+int4-core+interactive+prefill-skip+sample-profile+fast-sample+sync-gpio" CPUFreq=240
```

**S3, build D + sync:** the same, with `LIBS=D_64B_120M` and the overrides `CPUFreq=240,FlashMode=qio120`.

**P4, IA1 + sync:** use branch `power-01-sync-gpio`, which has both P4 patches applied. Then build as IA1 was
built, plus the define:

```bash
cd ~/Desktop/esp32-llm/p4/pr24 && git switch power-01-sync-gpio
NO_FLASH=1 ~/Desktop/esp32-llm/p4/tools/p4_step.sh IA1s \
  "-DP4_ATTN2=1 -DP4_LOGITS_SRAM=1 -DP4_CORE_INT4=1 -DINTERACTIVE=1 -DFAST_SAMPLE=1 -DPREFILL_SKIP=1 -DSYNC_GPIO=6" 0 /tmp/ia1s
```

**Compile results today (scratch copies, same FQBNs, flags and libs):**

| Build | Result |
|---|---|
| S3 B, unpatched | 372,526 B |
| S3 B, patched, SYNC off | 372,526 B; sketch object disassembly identical |
| S3 B, patched, `SYNC_GPIO=4` | 372,622 B; `pinMode` / `digitalWrite` referenced in the sketch object (first version) |
| S3 B, revised patch, `SYNC_GPIO=4` (2026-10-13) | 372,538 B; app sha256 `06abb9ad…` |
| P4 IA1, patched, SYNC off | 538,758 B; instructions identical to `p4/builds/IA1`'s sketch object (one debug-string label in an objdump comment differs) |
| P4 IA1, patched, `SYNC_GPIO=2` | 543,432 B, 0 warnings (the pin is now 6: rebuild at step d; the value of the define doesn't change the code path) |
| P4 IA1, revised patches, SYNC off (2026-10-14) | 538,758 B; sketch object instructions identical to `p4/builds/IA1` |
| P4 IA1, revised patches, `SYNC_GPIO=6` (2026-10-14) | 543,336 B, 0 warnings; app sha256 `38299f17…`; `setup()` sets GPIO6 to an output and writes it low (`li a0,6`) |

Each sync build is a **new binary** with its own app hash. That makes it a protocol decision
for power-01 (see `evals/power-01/NOTES.md`); the 3% ms/token gate still guards against any
performance change.
