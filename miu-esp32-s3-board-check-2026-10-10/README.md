# ESP32-S3 N16R8 on Miu, board check: genuine 16 MB flash + 8 MB octal PSRAM, 2026-10-10

Hardware gate before any esp32-ai work: is the board the N16R8 the upstream firmware assumes (16 MB flash, 8 MB
PSRAM in octal/OPI mode)? No pre-registration: a pass/fail identity check, not a measurement.

## Hardware

- **Chip:** ESP32-S3, rev 2 (log: `rev=2`). esptool also reported QFN56, rev v0.2, 40 MHz crystal,
  embedded PSRAM 8 MB (AP_3v3), and flash manufacturer 0x68 / device 0x4018, 16 MB, quad, 3.3 V.
  ⚠ Those esptool details are recorded only in `~/Desktop/esp32-llm/NOTES.md`; no esptool log was kept.
- **Board:** ESP32-S3 dev board with a CH343 USB-UART (1a86:55d3) and the S3's native USB. ⚠ The board's make and
  model are not recorded.
- **Display:** none attached.
- **Host:** Miu, over the CH343 port (`/dev/ttyACM0` at the time).

## Firmware

- `~/Desktop/esp32-llm/board_check/board_check.ino`, sha256 `e3e490fe1097de5b4f8aa25ecc78fbbd7974d703ecbb4f0e14ef7dc9b84b7199`.
- Arduino-ESP32 core 3.3.10 (arduino-cli 1.5.1). FQBN options `PSRAM=opi,FlashSize=16M` per NOTES.md.
  ⚠ The full FQBN of this build is not recorded.
- Not esp32-ai code; upstream commit not involved.

## Result: PASS (log 18:54 PDT)

`board_check_2026-10-10.txt`. The first line is boot-ROM output at the wrong baud (garbled). It is followed by 5
identical lines:

```
chip=ESP32-S3 rev=2 cpu=240MHz | flash=16777216 B @ 80000000 Hz | psram=8388608 B free=8384788 B found=1
```

| check | expected | measured (n=5 lines, identical) |
|---|---|---|
| flash size | 16 MB | 16,777,216 B |
| flash clock | 80 MHz | 80,000,000 Hz |
| PSRAM | 8 MB, found in OPI mode | 8,388,608 B, `found=1`, free 8,384,788 B |
| CPU | 240 MHz | 240 MHz |

Genuine N16R8; OPI PSRAM works with the core's `PSRAM=opi` libraries.

## Files

`~/Desktop/esp32-llm/logs/board_check_2026-10-10.txt`, `~/Desktop/esp32-llm/board_check/board_check.ino`.
