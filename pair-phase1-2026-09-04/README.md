# NVIDIA PAIR hands-on, phases 1 to 3 — Miu + Rushuna, 2026-09-04

Results record. Facts as measured. Every number is reproducible from a file in this directory.

## Setup

| item | Miu | Rushuna |
|---|---|---|
| GPU | RTX 3090 24 GB | RTX 3060 12 GB |
| PAIR | v0.1.1 headless archive (`service-binaries-linux-x64.zip`, sha256 in `release-assets.sha256`), product 0.91.7, broker 0.40.2, TUI 0.7.2, `ollama-proxy` 0.26.2 (`nvpair-manifest.json`) | same |
| run as | `nvpair-tui` in tmux, `NVPAIR_LOG_LEVEL=debug`, no desktop, no sudo | same |
| engine PAIR adopted | system Ollama 0.30.0 on 11434 (`User=ollama`) | system Ollama 0.17.5 on 0.0.0.0:11434 |
| PAIR proxy | 11435 (takeover of 11434 blocked, warning raised) | 11435 |
| other ports | 1234, 14318–14323, mDNS 5353 | same |
| data dir | `~/.config/Nvidia Corporation/Personal AI Router/` (settings.json, node-id.json, cluster/, workloads-history.json) | same |
| logs | none on disk in TUI mode; Logs tab only. `logs/` never created | same |
| peer address PAIR chose | 192.168.x.x (WiFi) | 192.168.x.x (WiFi). Wired 192.168.50.x not selectable |
| model, steps 3–4 | `qwen3.5:9b` Q4_K_M, digest 6488c96fa5fa on both | same |
| model, step 5 | `qwen3.6:27b` Q4_K_M (Ollama library tag; 17 GB) | absent |

The `.deb` (`NVPAIR-Setup-0.1.1-amd64.deb`, sha256 in `release-assets.sha256`) needs sudo and GTK and was not installed. Qwen3.6 has no 9B on the Ollama library or in `LLM_repo`, so `qwen3.5:9b` stands in.

Pairing: invite from Miu's Nodes tab, PIN accepted on Rushuna's Cluster tab, cluster `e3c6f1f2` committed 18 s after the invite (PIN exchange itself under 0.5 s). Both Ollamas serve one request at a time (`OLLAMA_NUM_PARALLEL=1`), so "concurrent" means queued at the engine.

## Phase 1, step 4 — 20 concurrent requests, direct vs PAIR (`results-step4.jsonl`, `pairlogs/`)

| rep | direct (Miu Ollama) | PAIR | split |
|---|---:|---:|---|
| 1 | 50.32 s | 50.27 s | 10 Miu / 10 Rushuna |
| 2 | 48.88 s | 50.20 s | 10 / 10 |
| 3 | 48.18 s | 50.22 s | 10 / 10 |
| mean, SD | 49.12 s, 1.09 | 50.23 s, 0.03 | |

Ratio direct/PAIR **0.98x** against a pre-registered 1.3–1.4x. Per-request service time from the proxy's `proxy request complete` lines: Miu 2.45 s, Rushuna 5.0 s; wall = Rushuna's ten. A 13/7 split would have given 1.40x on the same numbers.

## Phase 1, step 5 — `qwen3.6:27b` on Miu only, 20 requests via PAIR (`results-step5.jsonl`)

Eligibility gate held: `candidates=1 eligible=1`, all 20 to Miu, none to Rushuna. Direct: 226.5 s, 20/20. PAIR: 10/20 succeeded, 10 failed with `502 timeout awaiting response headers` at 120.2–120.3 s. Miu GPU utilization fell to 0 within 1 s of the 502s (`gpu/miu.csv`). Issue draft: `upstream-issue-120s-header-timeout.md`.

## Phase 2, step 3 — same test, rerun (`phase2/results-step4-phase2.jsonl`, `phase2/pairlogs/`)

| rep | direct | PAIR | split | Miu svc | Rushuna svc |
|---|---:|---:|---|---:|---:|
| 1 | 57.30 s | 50.09 s | 10 / 10 | 2.53 s | 4.98 s |
| 2 | 50.32 s | 50.00 s | 10 / 10 | 2.51 s | 4.97 s |
| 3 | 50.16 s | 50.39 s | 10 / 10 | 2.50 s | 5.01 s |
| mean, SD | 52.59 s, 4.08 | 50.16 s, 0.20 | | | |

Ratio 1.05x; the direct mean is dragged by a 57.3 s first rep (page cache cold after the 16 GB pull). Reps 2–3 alone give 1.00x. Rushuna targets still `192.168.x.x:11435`.

## Phase 2, step 4 — same 20 requests through mycoSwarm (`phase2/results-myco.jsonl`)

| rep | wall | split | Rushuna svc (completion spacing) | tok/s reported |
|---|---:|---|---:|---:|
| 1 | 101.29 s | 20 Rushuna / 0 Miu | 5.07 s | 46.0 |
| 2 | 100.93 s | 20 / 0 | | 46.0 |
| 3 | 102.00 s | 20 / 0 | | 46.0 |
| mean, SD | 101.41 s, 0.55 | | | |

Ratio direct/mycoSwarm **0.52x**. mycoSwarm's inference router scores a specialist node +500 and the executive +200, subtracts in-flight load only from the local score, and so sends every request to the 3060. Before this could run, Rushuna's daemon had to be restarted: its router was holding a six-day-old identity with no models, which produced a Miu↔Rushuna routing ping-pong. Write-up: `mycoswarm-stale-identity-pingpong.md`.

## Phase 2, step 5 — `qwen3.6:27b`, 8 requests (`phase2/results-step5-n8.jsonl`)

Direct 86.48 s, 8/8. PAIR 85.55 s, 8/8, all Miu, **zero 502s**, last completion at 85.6 s. The 20-request failure is queue depth against the 120 s header timeout, not the model.

## Phase 3 — same test with Ollama 0.30.0 on both nodes (`phase3/`)

Rushuna's system Ollama 0.17.5 stopped by Mark (`sudo systemctl stop ollama`). The user-level 0.30.0 (`~/ollama-0.30`, store `~/ollama-models`, `qwen3.5:9b` digest 6488c96fa5fa, same as Miu) started on the default 127.0.0.1:11434 and was adopted by PAIR (`local backend updated ... port=11434`, listener pid = the user-level binary). Cluster `e3c6f1f2` persisted across the PAIR restart on both nodes; merged inventory carried `qwen3.5:9b` from both. Soak paused 20:30–20:38 PDT.

| rep | direct | PAIR | split | Miu svc | Rushuna svc |
|---|---:|---:|---|---:|---:|
| 1 | 48.05 s | 44.46 s | 10 / 10 | 2.36 s | 4.42 s |
| 2 | 46.66 s | 43.95 s | 10 / 10 | 2.32 s | 4.36 s |
| 3 | 46.56 s | 43.89 s | 10 / 10 | 2.31 s | 4.36 s |
| mean, SD | 47.09 s, 0.83 | 44.10 s, 0.31 | | | |

Ratio direct/PAIR **1.07x**, against 1.05x in phase 2 (1.00x on phase 2's warm reps) and 0.98x in phase 1. The engine upgrade took Rushuna's per-request time from 5.0 s to 4.4 s; the split stayed 10/10, so the wall clock is still Rushuna's ten. Rushuna targets still `192.168.x.x:11435` (WiFi). Single-request tok/s on Rushuna: 46.2 on 0.17.5, 50.1 on 0.30.0 (`phase3/rushuna-ollama-0.30.0-startup.log`).

## Phase 2, steps 1–2 — what could not be done without sudo

- **Same Ollama version on both nodes for PAIR.** Ollama 0.30.0 was installed user-level on Rushuna (`~/ollama-0.30`, model store `~/ollama-models`, port 11436) and served the model on GPU. PAIR adopts whatever is on the compatibility port 11434 and cannot be redirected: `OLLAMA_HOST` only creates a proxy alias (`prepared inherited OLLAMA_HOST loopback alias address=127.0.0.1:11436`, then `alias unavailable ... address already in use`), and the adopted backend stayed `port=11434`. PAIR exposes no engine-version field anywhere (Engines tab, `/v1/node-info`). One `sudo systemctl stop ollama` on Rushuna, then the user-level Ollama on 11434, would close this. The user-level instance was stopped again so it did not contend for the 3060.
- **Pin to the wired interface.** No flag, env var, or `settings.json` key selects an interface or advertised address (all six service binaries' `--help` checked, strings searched). A Manual-nodes entry for 192.168.x.x registered and bridged to the engine port (`manual node updated: 70506f7d (192.168.x.x:11434)`), but routing kept using the discovery record's `192.168.x.x:11435`. Entry removed.

## Environment notes

Memfault soak paused via `~/.soak-pause` 10:43–12:57 PDT and again 20:30–20:38, resumed and timer confirmed active each time. PAIR stopped on both nodes at 12:58 and again at 20:38 (all `143xx`/11435/1234 listeners gone). After phase 3 the user-level Ollama 0.30.0 is left running on Rushuna's 11434 in tmux session `ollama30`, since the system 0.17.5 service is stopped and mycoSwarm there expects an engine on that port. Rushuna's clock is UTC (+7 h to Miu's PDT) — log timestamps in `phase2/` and journal excerpts differ by that offset.

## Files

| path | content |
|---|---|
| `bench.py`, `run_step4.sh`, `run_step5.sh` | load generator and runners (phase 1 and 2) |
| `results-step4.jsonl`, `results-step5.jsonl`, `step4.log`, `step5.log` | phase 1 raw results and runner output |
| `pairlogs/*.complete` | per-request `proxy request complete` lines (node, target, duration, status), phase 1 |
| `gpu/` | 1 s nvidia-smi samples on both nodes during phase 1 |
| `miu-workloads-history.json` | PAIR's persisted workload records (`scheduledOn` per request) |
| `phase2/` | step 3 rerun, mycoSwarm reps (`bench_myco.py`), step 5 at N=8, their runner and logs |
| `phase3/` | step 3 rerun with Ollama 0.30.0 adopted on both nodes, attribution logs, Rushuna engine startup lines |
| `upstream-issue-120s-header-timeout.md` | draft issue for NVIDIA/Personal-AI-Router, not filed |
| `mycoswarm-stale-identity-pingpong.md` | mycoSwarm routing bug found on the way |
| `nvpair-manifest.json`, `latest-linux.yml`, `release-assets.sha256` | release provenance |
