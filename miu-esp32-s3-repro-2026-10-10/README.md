# ESP32-S3 N16R8, esp32-ai TinyStories release model as shipped: dry-run reproduction, 2026-10-10

**Confirmatory, not blind.** This run flashed the upstream build unmodified and read the numbers. No pre-registration
existed: the first pre-registration in this chain (`../miu-cpu-clock-01-2026-10-10/`) was written at 20:35:04, ten
minutes after this capture (20:25:05). Every later pre-registration was written with this run's 95.0 ms/token
profile already seen. Labelled UNOFFICIAL in NOTES.md at the time: not a benchmark.

## Hardware

- ESP32-S3 rev 2, 16 MB quad flash at 80 MHz, 8 MB octal PSRAM (`../miu-esp32-s3-board-check-2026-10-10/`).
- **Port:** native USB only. `/dev/ttyACM0` = Espressif native USB JTAG/serial. The CH343
  cable was unplugged.
- **Display: none attached.** The shipped sketch hard-codes `#define USE_DISPLAY 1` and drives an SH1106 OLED on
  GPIO18/46 every token. See "Conditions".
- Host: Miu.

## Firmware

- slvDev/esp32-ai @ `52ebcbbd905270592c1d415efd1128d04d0fa365`, `firmware/esp32_tinystories`, **no patches, no extra
  defines**.
- Arduino-ESP32 core **3.3.10** (IDF v5.5.4), arduino-cli 1.5.1, global `-O3` (`compiler.optimization_flags`).
- **FQBN** (from `scripts/deploy.sh`):
  `esp32:esp32:esp32s3:UploadSpeed=921600,USBMode=hwcdc,CDCOnBoot=cdc,UploadMode=default,CPUFreq=240,FlashMode=qio,FlashSize=16M,PartitionScheme=custom,PSRAM=opi,DebugLevel=info`
- **Libraries** (needed because of `USE_DISPLAY 1`): Adafruit SH110X 2.1.14, Adafruit GFX Library 1.12.6, Adafruit
  BusIO 1.17.4. These are the pins in upstream's `firmware/esp32_fly/README.md`.
- Command: `PORT=/dev/ttyACM0 scripts/deploy.sh tinystories`.
  - Golden gate: **SKIPPED, no golden**.
  - Staging gate: `PASS (0 failures)`.
  - Sketch: 682,094 B.
  - Model written at 0x110000 (`deploy_2026-10-10.txt`).

## Model

- Release `artifacts/tinystories/model.bin`, 14,912,348 B, sha256
  `1d8326c05c383ccfa615f5455575802817cb453dbc7ab28875d41a9dbb45477e`.
- The device boot fingerprint `fp=a9bdd778` (FNV-1a) matches deploy.sh's `expect  : fp=a9bdd778  bytes=14912348`.
- Tokenizer sha256 `4e28163669f2249af31a528a54fc25064dcbd0a34edbfa7bedb16d2d600ec7ae`.
- Host staging gate before flashing: `staging_verify_2026-10-10.txt`, PASS, 0 failures.

## Conditions

- One capture of 60 s after an RTS reset (`tools/capture_serial.py`), fixed compiled prompt "Once upon a time"
  (ids 433 447 259 405), 200 greedy tokens.
- **No OLED attached.** The capture holds **1,965** `i2cWrite(): i2c_master_transmit failed: [259]
  ESP_ERR_INVALID_STATE` lines, logged at `DebugLevel=info`. They inflate wall time, so **tok/s is not comparable**.
  ms/token times only `llm_forward` and is unaffected.

## Result (n = 1)

```
build: bytes=14912348 fp=a9bdd778 sram=29320B psram=4.19MB
--- 200 tokens in 36.83 s ---
throughput: 5.43 tok/s   (95.0 ms/token)
profile ms/token: input 2.2 | attn 20.5 | ffn 6.4 | ple 6.4 | head 59.4
```

| | upstream (RESULTS.md "Current runtime", firmware README "Measured") | this run (n=1) |
|---|---:|---:|
| ms/token | 94.9 | 95.0 |
| head | 59.4 | 59.4 |
| attention | 20.5 | 20.5 |
| PLE path | 6.4 | 6.4 |
| FFN | 6.5 (RESULTS.md) / 6.4 (README) | 6.4 |
| input | 2.2 | 2.2 |
| tok/s | 9.88 attached | 5.43 (I2C error spam; not comparable) |

The compute profile reproduces upstream to 0.1 ms. The generated text is coherent ("Once upon a time, there was a
little girl named Lily…") and contains a story restart; see `../tamanna-decode-01-2026-10-10/`.

## Files

Paths are local, not in this repo: `tools/` is under Miu `~/Desktop/esp32-llm/`; `artifacts/`, `firmware/` and `scripts/` are in slvDev/esp32-ai @ `52ebcbb` (Miu `~/Desktop/esp32-llm/esp32-ai/`).

- `~/Desktop/esp32-llm/logs/deploy_2026-10-10.txt`
- `~/Desktop/esp32-llm/logs/dryrun_2026-10-10.txt` (208 KB, mostly I2C errors)
- `~/Desktop/esp32-llm/logs/staging_verify_2026-10-10.txt`
