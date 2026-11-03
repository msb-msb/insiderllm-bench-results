# llama.cpp v0.7.0 on Tamanna: build A/B, `--moe-cache-mib`, Nemotron 3.5 Bolt 24GB fit, Bolt quality. Results, 2026-11-03

Results record for `docs/candidates/llamacpp-v0.7-nemotron-bolt-2026-10.md`, run exactly as locked at commit
`9cc92ae5` (prereg sha256 `3857cbb2ddfe9c31b1e7e71b82143956992e2e2471d081daa391ba2677a9bbee`; the file is unchanged since
the lock, `git diff 9cc92ae5` empty, and its sha256 matches the one in the lock commit message). Predictions are Mark's
from 2026-10-16 and are scored below without revision. Every forced or interpretive deviation is under **Deviations**.

**Five of the thirteen prediction lines are OUTSIDE:** A-pp (both depths), B-cache, B-pp, C-load128 and C-depth.
The other eight are inside. Q is inside, but the Q0 control moved off 23; that is reported first under Q.

## Tamanna was free (checked 12:39–12:45 PST, before anything ran)

- `nvidia-smi`: no compute processes, 7 MiB used of 24,576, P8, 35 W, 42 °C.
- No esp32 or voice processes: the only python processes were `networkd-dispatcher` and `unattended-upgrade-shutdown`.
  The esp32-llm tree's last write on Tamanna was 2026-10-29 22:24 (`chat-gen-v1c/…`, its `server.pid` 453440 not
  running); voice-01's was 2026-10-29 21:56 (`runs/lock_polish/G_275000.pth`). No tmux/screen sessions, no logins.
- No user crontab; user timers are launchpadlib cache-clean and snap firmware-notifier; system timers are the stock
  Ubuntu set (sysstat, fwupd, anacron, apt, man-db, logrotate…). None uses the GPU.
- The harness's own guard (empty compute-apps list and no `pgrep -af esp32-llm`, before every invocation and at 1 s
  during it) never held and never tainted a cell: `grep -c TAINTED run.log` = 0, and every raw file has
  `esp32_taint: []`.

## Pre-run checks

- **Builds.** `~/llama-v0.7.0` HEAD `620d2225cc436ab0b001e3200e590e3b286ef9ab` (tag v0.7.0); `~/llama-v0.4.0` HEAD
  `5266f24da75dc449bd56cbed7addb9c8e4a6a73e`. All seven v0.7.0 binary sha256s match the prereg's Prep table. llama-bench
  JSON and `/props` report `build_commit` 620d222 / 5266f24.
- **Later upstream, not used.** b11881 (the `no_alloc` memory-caches change) lands after our v0.7.0 build, and v0.8.0 has
  been released since. Neither changes the locked plan: every v0.7.0 figure here is `620d2225c` only.
- **Models**, hashed on Tamanna on the day (`sha256sum`, 12:40–12:44), all equal to the prereg and to LLM_repo's
  `SHA256SUMS` on Miu:
  - `Qwen3.6-35B-A3B-UD-Q4_K_M.gguf` `ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61`
    (repo: `from-miu/bench-models/`)
  - `NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB.gguf` `91d63363e782c8a3d5f4be42816eba8e0d42dd2530bd07a7d0d2dc440599af75`
    (repo: `nemotron-3.5-bolt-74b-a9b-24gb-gguf/`)
  - `qwen3.6-35b-a3b-Q4_K_M.gguf` (Q0) `203c3a7c3becd6ebd7ba1af7d82e5363b1a5d6f84e608d3214c3fb1269230511`
    (repo: `qwen3.6-35b-a3b-gguf/`)
- **Port.** `--port 8081` on every server, as the prereg says (v0.7.0's default is 9931).
- **RAM.** `stream_read` at 4 threads: 42.03 / 42.00 / 42.08 GB/s (expected ~42.3; 10-09 at 3000 was 42.44). See
  Deviations for `dmidecode`.
- **Card state: stock, no gpu-unlock** (`card-state.txt`, `gemm-check.*`):
  - `lsmod`: only `nvidia`, `nvidia_uvm`, `nvidia_drm`, `nvidia_modeset` (+ `drm_ttm_helper`, `video`). `modinfo
    gpu_unlock`: not found. No `*unlock*` file under `/lib/modules/7.0.0-38-generic`, none in initramfs-tools hooks or
    scripts, none in `/etc/modprobe.d`; kernel cmdline has no `gpu_unlock.targets=`.
  - Driver 580.178.04, VBIOS 94.02.42.80.14, power limit 420 W (= default), PCIe gen 4 x16 max.
  - cuBLAS GEMM 8192³ via torch (voice-01 env), 20 timed after 5 warm-ups: **FP16-in/FP32-acc 75.33 TFLOPS**,
    BF16/FP32-acc 76.58, TF32 40.44; SM 1,845–1,950 MHz, mean 351 W under load. The GA102 white paper's 71 TFLOPS
    (FP16/FP32-acc) is at the 1,695 MHz boost clock, which scales to ~82 at 1,950 MHz; 75 is the stock half rate.
    An unlocked card would read near the FP16-acc rate (142 at boost; #196 measured +63%).

## Board-level power and clocks

Logged at 1 s for every invocation, primes included (`telemetry-*.csv`; summarised in each `raw-*.json` under
`meta.telemetry`), with CPU Tctl and mean core MHz from sysfs. Under load, per arm:

| arm | GPU power mean (max), W | SM clock median [min..max], MHz | mem clock | GPU max °C | PCIe | CPU Tctl max |
|---|---|---|---|---|---|---|
| A (both builds) | 342–348 (392–398) | 1,920 [1,830..1,950] | 9,501 | 65–67 | gen 4 x16 | 47–55 °C |
| B1 / B2 | 182–211 (206–211) | 1,920–1,950 | 9,501 | 58–64 | gen 4 x16 | 56–60 °C |
| B3 | 237–243 (264–272) | 1,920–1,935 | 9,501 | 59–64 | gen 4 x16 | 52–54 °C |
| C1/C2 | 380–391 (417–419) | 1,830–1,868 [1,800..1,935] | 9,501 | 70–73 | gen 4 x16 | 54–56 °C |
| C3 | 393–407 (419–420) | 1,830–1,845 [1,800..1,935] | 9,501 | 72–74 | gen 4 x16 | 56–58 °C |
| Q (both models) | 301–313 (330–339) | 1,920–1,935 | 9,501 | 62–66 | gen 4 x16 | 46–50 °C |

Clock-event reasons under load were only `0x0` and `0x4` (SW power cap) on every run: no thermal or HW slowdown.
The C cells sat at the 420 W limit and lost ~100 MHz to it; this is the card's stock behaviour on a dense 2-bit
model and is the same for every C cell.

## Deviations (recorded as they arose, before the next step)

The locked prereg has no general deviations section, and this commit is limited to the results folder, so they are
recorded here; the candidates doc was not edited.

1. **Results folder name.** The prereg names none; this folder uses the prereg's file stem.
2. **A display is attached.** The prereg's C1 says "No display is attached; the record states it." On the day,
   `/sys/class/drm/card1-HDMI-A-1/status` = connected and `display_active` = Enabled. There is no X/Wayland/GNOME
   session (no display manager active) and the card used 7 MiB at idle, which is inside every `memory.used` figure
   below, including C1 headroom.
3. **`dmidecode` not run.** It needs sudo and is Mark's step in the prereg's fixed conditions. `stream_read`
   (42.0 GB/s) is the evidence for DDR4-3000 here. Nothing else needed sudo.
4. **Guard self-match, record only.** In `card-state.txt` the pre-run `pgrep -af esp32-llm` line lists two PIDs: they
   are that record command's own `bash -c`, whose text contained the search string. Re-checked with a non-matching
   pattern: empty. The harness's guard runs `pgrep` directly and doesn't match itself; no harness check fired.
5. **Expert bytes for B3's rule** were read with `gguf-py` under the voice-01 env (Tamanna's system python has no
   numpy) and fixed in `harness.py`: `*_exps` tensors 19,568,525,312 B (18,662 MiB) of 22,123,538,944 B.
6. **B priming.** "Order: (B1, B2, B3) × 3, each with one discarded priming run" was read as one discarded priming run
   per configuration before the measured sequence (the 09-22 harness it names does that), not one before every
   measured run. B3's size M was set from the B2 priming run's peak, before any B3 run (`B3-size-rule.json`).
7. **C2 prompt.** The 10-09 Strata llama.cpp source cut (`prompt-32512.txt`, sha256 `24bb18f5…`, starts at
   `// ===== common/arg.cpp =====`) was tokenized by the Bolt server's own `/tokenize` (`add_special` false), cut to
   the first 4,096 tokens, and sent to `/completion` as that token array, so `prompt_n` is exactly 4,096 on every
   request. Tokens sha256 `75cc6b84…464f`, detokenized text sha256 `eb6da1fd…e731` (`C2-prompt*`).
8. **C1 headroom measurement.** "Peak `memory.used` after the first C2 request" is the max of `nvidia-smi` polled at
   0.2 s from server ready through the end of the first (priming) request, plus one reading after it. The 1 s session
   sampler's peak over the whole server life is recorded beside it and was identical in all four cells.
9. **C1 buffer sizes needed extra loads.** v0.7.0's server prints no KV / RS / compute buffer lines at default
   verbosity, so the measured C1 logs don't have them. After every measured arm, each C1 command was loaded once more
   with `-lv 4` added, health-checked and stopped (`c1_buffers.sh`, `buffers-C1-*.log`, `c1-buffers.txt`). No
   requests, no figures scored from these loads.
10. **C4 prompts and settings.** The first three of the am17an nine (`code_python`, `code_cpp`, `explain_concept`) at
    the am17an settings (n_predict 192, temperature 0, seed 42), on the C 32K/f16 server command.
11. **Q server `--host 0.0.0.0`.** The prereg's Q command has no host; `run_quality.py` runs from Miu, so the server was
    bound to the LAN as the 10-07 `serve.sh` was. No other flag added. `-np` left at its default as locked (the log
    shows 4 slots × 4,096, `kv_unified` true).
12. **Q first launch idled, unmeasured.** My `quality/run_q.sh` first launched the Bolt server with a `cd && … &` chain,
    which kept the ssh attached, so no request was sent. The server sat ready and idle 13:02:55–14:53:49, then stopped
    cleanly; its files are kept as `idle-launch1-*` and `quality/run_q.launch1.out`. The launch line was fixed and Q ran
    from the start at 14:54:01. No Q figure comes from the first launch.
13. **LAN address in two raw files.** `run_quality.py` (copied unchanged, sha256 `4b19bcff…276b` = the 10-07 copy) writes
    its `--base` URL into `quality/raw-*.json`, as the 10-07 raw files do. The public mirror's redaction covers it.

## Results against each prediction

Mean of the measured invocations; spreads are min..max; "moved" only where ranges don't overlap (verdict rules).

### A. Build A/B, `llama-bench … -ncmoe 0 -fa 1 -p 512 -n 128 -d 0,4096 -r 5 -t 8 -lm mmap`, 3 measured per build

**Drift check first:** every v0.4.0 cell is within 2% of 10-09 (largest gap −0.18%, pp512 d=4096 rep 2: 3,591.5 vs
3,605.0). No drift flag.

| cell | v0.4.0 `5266f24` | v0.7.0 `620d222` | v0.7.0 / v0.4.0 | noise call | prediction | result |
|---|---|---|---:|---|---|---|
| tg128 d=0 | 162.94 [162.81..163.03] | 162.24 [162.07..162.36] | 0.9957 | moved | ±5% | **inside** |
| tg128 d=4096 | 160.85 [160.83..160.88] | 160.13 [160.12..160.15] | 0.9955 | moved | ±5% | **inside** |
| pp512 d=0 | 3,768.2 [3,762.1..3,775.1] | 4,362.3 [4,355.2..4,366.6] | 1.1577 | moved | ±10% | **OUTSIDE** |
| pp512 d=4096 | 3,601.2 [3,591.5..3,611.6] | 4,110.1 [4,107.7..4,111.3] | 1.1413 | moved | ±10% | **OUTSIDE** |

- **A-decode: inside** at both depths. The −0.4% is outside the noise, so by the verdict rule it "moved", but it is
  well inside the band.
- **A-pp: OUTSIDE** at both depths. v0.7.0 processes prompts 14–16% faster on this resident row.
- **Verdict rule A:** v0.7.0 moved both metrics, so every v0.4.0 row keeps its build label, and no v0.7.0 figure goes
  next to one without the label. The bench pin doesn't move on this result alone.

### B. `--moe-cache-mib`, `llama-server … -ncmoe 20 -fa on -c 8192 -np 1 --fit off -lm mmap -t 8 --port 8081`

Size rule (from prime-B2, before any B3 run): free = 24,576 − 12,254 − 1,024 = 11,298 MiB; 10% of expert bytes =
1,866 MiB; **M = 1,866**. Free ≥ 512, so −ncmoe 20 stands. Peak VRAM: B1 12,130, B2 12,254, B3 14,134 MiB.

Aggregate over the am17an nine (sum predicted_n / sum predicted_ms; prompt = sum prompt_n / sum prompt_ms):

| config | decode tok/s | prompt tok/s |
|---|---|---|
| B1 v0.4.0 | 70.22 [70.18..70.28] | 317.0 [316.5..317.5] |
| B2 v0.7.0 | 70.07 [70.05..70.08] | 318.9 [318.5..319.4] |
| B3 v0.7.0 + `--moe-cache-mib 1866` | 73.59 [73.54..73.62] | 301.1 [300.9..301.6] |

- **B-build, B2/B1 decode = 0.998: inside** (±5%). The ranges don't overlap, so it moved, by −0.2%.
- **B-cache, B3/B2 decode = 1.050: OUTSIDE** (predicted 1.10–1.40). The cache moved decode +5.0%, a resolved gain,
  but under half the low end of the band. Far below the PR's 1.62× (4090) and 2.20× (5090).
- **B-pp, B3/B2 prompt = 0.944: OUTSIDE** (±5%). With the cache, prompt speed fell 5.6%, a resolved loss.
  The nine prompts are short, so this prompt figure is short-prompt throughput, not a long-prefill number.
- For context only (different harness): 10-09's llama-bench `-ncmoe 20` at 3000 was tg128 73.43.

### C. Nemotron 3.5 Bolt 24GB, v0.7.0, text only

C1/C2 (`llama-server … -ngl 99 -fa on -c CTX -np 1 -ctk K -ctv K --fit off -lm mmap -t 8 --port 8081`; 4,096-token
prompt, n_predict 128, ignore_eos, temperature 0, cache_prompt false; 1 discarded + 3 measured):

| K | CTX | load | peak used, MiB | headroom (24,576 − peak) | KV / RS / compute (CUDA0), MiB | decode tok/s | pp4096 tok/s |
|---|---:|---|---:|---:|---|---|---:|
| f16 | 32,768 | OK | 21,402 | 3,174 | 256.0 / 164.7 / 148.4 | 89.80 [89.76..89.87] | 1,603.3 |
| f16 | 131,072 | OK | 22,266 | **2,310** | 1,024.0 / 164.7 / 244.4 | 89.80 [89.75..89.86] | 1,605.2 |
| q8_0 | 32,768 | OK | 21,284 | 3,292 | 136.0 / 164.7 / 148.5 | 88.12 [88.09..88.14] | 1,604.4 |
| q8_0 | 131,072 | OK | 21,848 | 2,728 | 544.0 / 164.7 / 304.1 | 88.20 [88.13..88.34] | 1,605.4 |

Model buffer: CUDA0 20,446.8 MiB, CPU_Mapped 544.0 MiB in every cell. llama.cpp's own breakdown sees 24,122 MiB of
device memory, not 24,576. Against that total the 128K f16 headroom is 1,856 MiB, so C-load128's call doesn't change.

C3 (`llama-bench … -ngl 99 -fa 1 -ctk K -ctv K -p 4096 -n 128 -d 0,4096 -r 3` and `-p 0 -n 128 -d 102400 -r 1`):

| K | pp4096 d=0 | pp4096 d=4096 | tg128 d=0 | tg128 d=4096 | tg128 d=102400 |
|---|---:|---:|---:|---:|---:|
| f16 | 1,708.97 | 1,688.51 | 90.90 | 91.07 | 82.42 |
| q8_0 | 1,701.64 | 1,684.59 | 90.54 | 89.42 | 60.61 |

| prediction | cell | value | band | result |
|---|---|---|---|---|
| C-load32 | C1 32,768/f16 loads | loaded | loads | **inside** |
| C-decode | C3 f16 tg128 d=4096 | 91.07 | 70–120 | **inside** |
| C-load128 | C1 131,072/f16 loads and headroom < 1,024 MiB | loaded, headroom 2,310 MiB | < 1,024 | **OUTSIDE**: it fits with more room than predicted |
| C-alloc | C2 f16 decode, 131,072 vs 32,768 | 89.80 vs 89.80, Δ 0.0% | < 5% | **inside** |
| C-depth | C3 f16 tg128 d=102400 / d=4096 | 82.42 / 91.07 = 0.905 | 0.60–0.85 | **OUTSIDE**: decode falls less than predicted |
| C-kv | C3 tg128 d=4096, q8_0 vs f16 | 89.42 / 91.07 = 0.982 (−1.8%) | ±5% | **inside** |
| C-pp | C3 f16 pp4096 d=0 | 1,708.97 | 1,500–3,000 | **inside** |

- **Verdict rule C: fits at 128K.** The 131,072 cells loaded and completed C2 and C3 (including the 102,400-depth cell)
  with no OOM, at both K types.
- Not predicted, stated as found: at 102,400 depth, q8_0 KV decodes at 60.61 against f16's 82.42 (0.735). At short
  depth the two are within 2%.
- **C4 sanity** (`raw-C4-sanity.json`, full outputs): coherent, not looping. `code_cpp` (41 tokens, EOS) and
  `explain_concept` (147, EOS) start with a literal `</think>`, because `/completion` sends raw text with no chat
  template. `code_python` ran to the 192 limit continuing the prompt as a spec list ("The function should…"), which is
  raw-completion behaviour, not breakage.

### Q. 47-item split, v0.7.0 `llama-server … -ngl 99 -fa on -c 4096 --jinja --fit off -lm mmap --port 8081`

**Reported first, per the verdict rule: Q0 scored 22/47, not 23.** Same file (`203c3a7c…`), same harness, same
prompts; the only change is the build (v0.4.0 → v0.7.0). Five items changed prediction (idx 2, 37, 60, 61, 62): two
right → wrong (37, 61), one wrong → right (62), two wrong → differently wrong. 28 of 47 raw outputs are byte-identical
across the builds. The build moved the base model's score by −1, so Bolt is read against both numbers.

| model | pass 1 exact | pass 2 exact | effective | tool / mode / scope | valid | unparseable | thinking leaks | identical p1/p2 |
|---|---:|---:|---:|---|---:|---:|---:|---|
| Q1 Bolt 24GB | **22/47** | 22/47 | 29 | 30 / 31 / 27 | 47 | 0 | 0 | 47 preds, 47 raw |
| Q0 Qwen3.6-35B-A3B Q4_K_M, v0.7.0 | 22/47 | 22/47 | 29 | 30 / 30 / 27 | 47 | 0 | 0 | 47 preds, 47 raw |
| recorded, Q0 file on v0.4.0 (10-07) | 23/47 | 23/47 | | | | | | |

- **Q: inside.** Bolt pass 1 = 22, inside 19–27 (23 ± 4).
- Against both numbers: one below the recorded 23, and equal to the same-build control. Item by item, 21 are right
  for both, 1 only for Bolt, 1 only for Q0.
- Mean wall per item: Bolt 0.488 s, Q0 0.258 s.

## Summary

| prediction | result |
|---|---|
| A-decode (d=0, d=4096) | inside, inside |
| A-pp (d=0, d=4096) | **OUTSIDE, OUTSIDE** (+15.8%, +14.1%) |
| B-build | inside |
| B-cache | **OUTSIDE** (1.050×) |
| B-pp | **OUTSIDE** (−5.6%) |
| C-load32 | inside |
| C-decode | inside |
| C-load128 | **OUTSIDE** (headroom 2,310 MiB) |
| C-alloc | inside |
| C-depth | **OUTSIDE** (0.905) |
| C-kv | inside |
| C-pp | inside |
| Q | inside (22/47); Q0 control moved to 22 |

## Timing

- Free-check and pre-run checks: 12:39:55–12:46.
- Measured arms A, B, C: 12:47:16–13:02:38 (15 min 22 s, one unattended `harness.py` chain, exit 0).
- Q: 14:54:01–14:55:44 (both models, two passes each). The 13:02–14:53 gap is deviation 12 (idle server).
- C1 buffer loads: ~14:56–14:58.
- End to end 12:39:55 to ~14:58, about 2 h 18 min, of which about 19 min was GPU work.

## Files

- `harness.py` (arms A, B, C, and the Q server), `quality/run_q.sh` (Q driver from Miu), `quality/run_quality.py`
  (10-07 copy, unchanged), `gemm_check.py` + `gemm_run.sh`, `c1_buffers.sh`.
- `run.log` / `harness.out`: the unattended log. `card-state.txt`, `gemm-check.*`, `telemetry-gemm.csv`.
- Per invocation: `raw-*.json` (command, output, meta with telemetry, NVMe reads, MemAvailable, CPU, guard),
  `telemetry-*.csv` (1 s nvidia-smi), `server-*.log`. Primes are `*-prime-*`.
- `A-summary.json`, `B-summary.json`, `B3-size-rule.json`, `C-summary.json`, `C2-prompt*`, `quality/raw-*.json`,
  `quality/run_q.log`.
