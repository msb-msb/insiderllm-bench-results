#!/usr/bin/env python3
"""Strata v0.1.39 vs llama.cpp v0.4.0, Tamanna (RTX 3090 24 GB, PCIe 4.0 x16, 64 GB DDR4-3000), 2026-10-09.

Pre-registered in docs/candidates/strata-2026-10-05.md section B6. This is Rushuna's bench_coder.py
(../rushuna-strata-coder-2026-10-05/) with four changes: llama.cpp is the ~/llama-v0.4.0/build/bin build; -t 8;
the model is picked by the directory the script runs from (coder/ or iq3xxs/); `prep` does not re-cut the prompts,
it tokenizes Rushuna's exact prompt files on this file and records the counts.

  bench_coder.py prep                  # cut the corpus into 4,096 / 16,384 / 32,512-token prompts (llama.cpp tokenizer)
  bench_coder.py stage                 # lowest -ncmoe N that loads at -c 34816 with -b/-ub 4096 and serves a 32,512 prompt
  bench_coder.py strata ARM [CFG]      # S1 stock, S2-2048 / S2-4096 / S2-8192 (32K only), S0 (--spec 0)
  bench_coder.py llama ARM N           # L1 defaults, L2 -b 4096 -ub 4096, L3 = L2 + GGML_CUDA_REGISTER_HOST=1

Every request: a fresh 8-hex nonce line first (defeats prefix caches), chat completion, streamed, thinking off,
temperature 0, max_tokens 256. Per cell: (priming request, measured request) x 3. Recorded per request: engine
timings (prompt_n, cache_n, prompt_per_second, predicted_per_second, drafts), client TTFT and total, swap-in and
swap-out KiB (/proc/vmstat), NVMe read bytes (/proc/diskstats), PCIe rx MB/s over the prefill window (nvidia-smi
dmon -s t), PCIe gen/width during prefill, peak card MiB, and the server/engine processes' VmRSS/VmLck/VmPin/VmSwap.
"""
import json, os, random, signal, subprocess, sys, threading, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")
LLAMA = f"{HOME}/llama-v0.4.0/build/bin"
MODEL = os.path.basename(HERE)
assert MODEL in ("coder", "iq3xxs"), MODEL
SHARD1 = {"coder": f"{HOME}/bench-models/qwen3.8-flash-next-coder/IQ1_M/Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-00001-of-00002.gguf",
          "iq3xxs": f"{HOME}/bench-models/qwen3.8-flash-next-ista-iq3xxs/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf"}[MODEL]
STRATA = f"{HOME}/strata"
PORT = 8099
CTX = 34816
LENGTHS = [4096, 16384, 32512]
REPS = 3
DISK = "nvme0n1"
LENV = dict(os.environ, LD_LIBRARY_PATH=LLAMA)


def log(s):
    line = f"{time.strftime('%H:%M:%S')} {s}"
    print(line, flush=True)
    open(os.path.join(HERE, "run.log"), "a").write(line + "\n")


def vmstat():
    d = {}
    for l in open("/proc/vmstat"):
        k, v = l.split()
        if k in ("pswpin", "pswpout"):
            d[k] = int(v)
    return d


def disk_read_bytes():
    for l in open("/proc/diskstats"):
        f = l.split()
        if f[2] == DISK:
            return int(f[5]) * 512
    return -1


def meminfo():
    d = {}
    for l in open("/proc/meminfo"):
        k, v = l.split(":")
        d[k] = int(v.split()[0])
    return {"avail_mib": d["MemAvailable"] // 1024, "free_mib": d["MemFree"] // 1024, "cached_mib": d["Cached"] // 1024,
            "swapused_mib": (d["SwapTotal"] - d["SwapFree"]) // 1024}


def proc_status(pid):
    out = {}
    try:
        for l in open(f"/proc/{pid}/status"):
            k = l.split(":")[0]
            if k in ("Name", "VmRSS", "VmLck", "VmPin", "VmSwap"):
                out[k] = l.split(":")[1].strip()
    except OSError:
        pass
    return out


def gpu_q(fields):
    r = subprocess.run(["nvidia-smi", f"--query-gpu={fields}", "--format=csv,noheader,nounits"], capture_output=True, text=True)
    return [x.strip() for x in r.stdout.strip().split(",")]


class Sampler:
    """Peak card MiB and PCIe gen/width at 0.5 s; dmon rx/tx MB/s at 1 s with wall timestamps."""
    def __init__(self):
        self.stop = False; self.peak = 0; self.links = []; self.rx = []
        self.t = threading.Thread(target=self.run, daemon=True)
        self.dmon = subprocess.Popen(["nvidia-smi", "dmon", "-s", "t", "-d", "1"], stdout=subprocess.PIPE, text=True)
        self.td = threading.Thread(target=self.read_dmon, daemon=True)

    def read_dmon(self):
        for line in self.dmon.stdout:
            f = line.split()
            if f and f[0].isdigit() and len(f) >= 3:
                self.rx.append((time.time(), float(f[1]), float(f[2])))   # gpu rxpci txpci (MB/s)

    def run(self):
        while not self.stop:
            try:
                used, gen, width = gpu_q("memory.used,pcie.link.gen.current,pcie.link.width.current")
                self.peak = max(self.peak, int(used)); self.links.append((time.time(), gen, width))
            except Exception:
                pass
            time.sleep(0.5)

    def __enter__(self):
        self.t.start(); self.td.start(); return self

    def __exit__(self, *a):
        self.stop = True; self.t.join(); self.dmon.terminate()


def http(path, payload=None, timeout=3600):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", data=json.dumps(payload).encode() if payload is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def wait_health(p, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if p.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=3) as r:
                if r.status == 200 and b"loading" not in r.read().lower():
                    return True
        except Exception:
            pass
        time.sleep(1)
    return False


def stop_server(p):
    if p.poll() is None:
        p.send_signal(signal.SIGTERM)
        for _ in range(15):
            if p.poll() is not None:
                break
            time.sleep(1)
    if p.poll() is None:
        p.kill(); p.wait()
    for n in ("llama-server", "strata"):
        subprocess.run(["pkill", "-KILL", "-x", n])
    time.sleep(3)


def child_pids(pid):
    r = subprocess.run(["pgrep", "-P", str(pid)], capture_output=True, text=True)
    kids = [int(x) for x in r.stdout.split()]
    return kids + [g for k in kids for g in child_pids(k)]


def chat(prompt, max_tokens=256):
    """One streamed request. Returns client timings and the engine's `timings`/`usage` from the stream."""
    nonce = "%08x" % random.getrandbits(32)
    body = {"model": "bench", "stream": True, "stream_options": {"include_usage": True}, "max_tokens": max_tokens,
            "temperature": 0, "cache_prompt": False, "chat_template_kwargs": {"enable_thinking": False},
            "messages": [{"role": "user", "content": f"request {nonce}\n{prompt}\n\nSummarise what this code does."}]}
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time(); ttft = None; timings = usage = None; nchunks = 0; err = None
    try:
        with urllib.request.urlopen(req, timeout=3600) as r:
            for raw in r:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:") or line == "data: [DONE]":
                    continue
                try:
                    o = json.loads(line[5:])
                except ValueError:
                    continue
                for c in o.get("choices") or []:
                    d = c.get("delta") or {}
                    if ttft is None and (d.get("content") or d.get("reasoning_content")):
                        ttft = time.time() - t0
                    if d.get("content") or d.get("reasoning_content"):
                        nchunks += 1
                timings = o.get("timings") or timings
                usage = o.get("usage") or usage
    except Exception as e:
        err = repr(e)[:300]
    return {"nonce": nonce, "t0": t0, "ttft_s": ttft, "total_s": time.time() - t0, "content_chunks": nchunks,
            "timings": timings, "usage": usage, "error": err}


def measured_request(prompt, pids, tag):
    v0, d0, m0 = vmstat(), disk_read_bytes(), meminfo()
    with Sampler() as s:
        r = chat(prompt)
    v1, d1, m1 = vmstat(), disk_read_bytes(), meminfo()
    t_pf_end = r["t0"] + (r["ttft_s"] or r["total_s"])
    rx = [x[1] for x in s.rx if r["t0"] <= x[0] <= t_pf_end]
    links = sorted({(g, w) for t, g, w in s.links if r["t0"] <= t <= t_pf_end})
    r.update({"tag": tag, "swapin_kib": (v1["pswpin"] - v0["pswpin"]) * 4, "swapout_kib": (v1["pswpout"] - v0["pswpout"]) * 4,
              "nvme_read_mib": round((d1 - d0) / 2**20, 1), "mem_before": m0, "mem_after": m1, "peak_card_mib": s.peak,
              "prefill_rx_mb_s_mean": round(sum(rx) / len(rx), 1) if rx else None, "prefill_rx_samples": len(rx),
              "prefill_pcie_links": links, "procs": {p: proc_status(p) for p in pids}})
    t = r["timings"] or {}
    log(f"  {tag}: prompt_n {t.get('prompt_n')} cache_n {t.get('cache_n')} pp {t.get('prompt_per_second')} "
        f"tg {t.get('predicted_per_second')} ttft {r['ttft_s'] and round(r['ttft_s'], 2)} rx {r['prefill_rx_mb_s_mean']} MB/s "
        f"swap in/out {r['swapin_kib']}/{r['swapout_kib']} KiB nvme {r['nvme_read_mib']} MiB card {s.peak} "
        f"avail {m1['avail_mib']} {r['error'] or ''}")
    return r


def prompts():
    return {n: open(os.path.join(HERE, f"prompt-{n}.txt"), encoding="utf-8").read() for n in LENGTHS}


def run_cells(arm, server_pid, lengths, out):
    P = prompts(); pids = [server_pid] + child_pids(server_pid)
    R = {"arm": arm, "pids": pids, "cells": {}}
    for n in lengths:
        cell = []
        for rep in range(1, REPS + 1):
            prime = measured_request(P[n], pids, f"{arm}-{n}-prime{rep}")
            meas = measured_request(P[n], pids, f"{arm}-{n}-rep{rep}")
            cell.append({"prime": prime, "measured": meas})
        R["cells"][n] = cell
        json.dump(R, open(out, "w"), indent=1)
    return R


def llama_cmd(ncmoe, arm, ctx=CTX):
    cmd = [f"{LLAMA}/llama-server", "-m", SHARD1, "-ngl", "99", "-ncmoe", str(ncmoe), "-fa", "on", "-c", str(ctx), "-np", "1",
           "--lazy-mode", "on", "-t", "8", "--host", "127.0.0.1", "--port", str(PORT)]
    if arm in ("L2", "L3"):
        cmd += ["-b", "4096", "-ub", "4096"]
    env = dict(LENV, **({"GGML_CUDA_REGISTER_HOST": "1"} if arm == "L3" else {}))
    return cmd, env


def start(cmd, env, logname, timeout):
    lf = open(os.path.join(HERE, logname), "w")
    t0 = time.time()
    p = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT, env=env, cwd=HERE if "llama" in cmd[0] else STRATA)
    ok = wait_health(p, timeout)
    log(f"start {logname}: {'ready' if ok else 'FAILED'} in {time.time() - t0:.1f}s card {gpu_q('memory.used')[0]} MiB mem {meminfo()}")
    return p, ok


def main():
    what = sys.argv[1]
    if what == "prep":
        cmd, env = llama_cmd(48, "L1", ctx=4096)
        p, ok = start(cmd, env, "server-prep.log", 900)
        assert ok, "prep server did not start"
        meta = {}
        for n in LENGTHS:
            text = open(os.path.join(HERE, f"prompt-{n}.txt"), encoding="utf-8").read()
            back = len(http("/tokenize", {"content": text})["tokens"])
            meta[n] = {"target": n, "tokens_on_this_file": back, "chars": len(text)}
            log(f"prompt-{n}: {len(text)} chars, tokenizes to {back} on {os.path.basename(SHARD1)}")
        json.dump(meta, open(os.path.join(HERE, "prompts-tokens.json"), "w"), indent=1)
        stop_server(p)
    elif what == "stage":
        P = prompts(); found = None; trail = []
        for n in range(48, -1, -2):  # Rushuna stopped at 30 (12 GB never got near it); 24 GB needs the full range
            cmd, env = llama_cmd(n, "L2")
            p, ok = start(cmd, env, f"server-stage-ncmoe{n}.log", 900)
            served = None
            if ok:
                r = chat(P[32512], max_tokens=16)
                served = r["error"] is None and bool(r["timings"])
                log(f"stage -ncmoe {n}: served={served} pp {(r['timings'] or {}).get('prompt_per_second')} card {gpu_q('memory.used')[0]} {r['error'] or ''}")
            trail.append({"ncmoe": n, "loaded": ok, "served": served})
            stop_server(p)
            if not (ok and served):
                break
            found = n
        json.dump({"lowest_ncmoe_that_serves_32512_with_ub4096": found, "trail": trail},
                  open(os.path.join(HERE, "stage.json"), "w"), indent=1)
        log(f"stage result: N = {found}")
    elif what == "strata":
        arm = sys.argv[2]; cfg = sys.argv[3]
        cmd = [f"{STRATA}/.venv/bin/python", f"{STRATA}/serve/server.py", "--engine", "strata", "--config", cfg, "--port", str(PORT)]
        p, ok = start(cmd, dict(os.environ), f"server-strata-{arm}.log", 1800)
        assert ok, f"strata {arm} did not start"
        lengths = [32512] if arm.startswith("S2-") else LENGTHS
        run_cells(arm, p.pid, lengths, os.path.join(HERE, f"results-{arm}.json"))
        stop_server(p)
    elif what == "llama":
        arm, n = sys.argv[2], int(sys.argv[3])
        cmd, env = llama_cmd(n, arm)
        p, ok = start(cmd, env, f"server-llama-{arm}.log", 900)
        assert ok, f"llama {arm} did not start"
        run_cells(arm, p.pid, LENGTHS, os.path.join(HERE, f"results-{arm}.json"))
        stop_server(p)


if __name__ == "__main__":
    main()
