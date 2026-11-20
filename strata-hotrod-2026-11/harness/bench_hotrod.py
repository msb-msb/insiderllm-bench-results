#!/usr/bin/env python3
"""Strata HotRod vs upstream Strata, Rushuna (RTX 3060 12 GB) and Tamanna (RTX 3090 24 GB), 2026-11.

Pre-registered in docs/candidates/strata-hotrod-2026-11.md (lock c06003fc), section H5 step 2 ("our cells"). This is
../../tamanna-strata-2026-10-09/bench_strata.py with these changes only (the diff is in bench_hotrod.diff):
  - Strata arms only; the llama.cpp, prep and stage modes are gone;
  - the server is started from the arm's own install: `strata ARM CFG ROOT`, where ROOT is the folder holding the
    arm's .venv and serve/server.py (upstream 0.2.16: <clone>/terminal), and CFG is the config its setup wrote;
  - results and logs go to the current directory (one per arm and rig), not the script's folder;
  - the NVMe device counted is the one holding the model shard (MODEL_DIR env), found from /proc/self/mountinfo;
  - each request also keeps the first 200 characters of the answer (H5's sanity check);
  - an egress watch (H3): `ss -tnpH` every 2 s for the server and engine processes, non-loopback peers logged.

  bench_hotrod.py strata ARM CFG ROOT

Every request: a fresh 8-hex nonce line first (defeats prefix caches), chat completion, streamed, thinking off,
temperature 0, max_tokens 256. Per cell: (priming request, measured request) x 3. Recorded per request: engine
timings (prompt_n, cache_n, prompt_per_second, predicted_per_second, drafts), client TTFT and total, swap-in and
swap-out KiB (/proc/vmstat), NVMe read bytes (/proc/diskstats), PCIe rx MB/s over the prefill window (nvidia-smi
dmon -s t), PCIe gen/width during prefill, peak card MiB, and the server/engine processes' VmRSS/VmLck/VmPin/VmSwap.
"""
import json, os, random, signal, subprocess, sys, threading, time, urllib.request

SCRIPT = os.path.dirname(os.path.abspath(__file__))     # prompts live beside the script
HERE = os.getcwd()                                      # results and logs: the arm's run folder
PORT = 8099
LENGTHS = [int(x) for x in os.environ.get("HOTROD_LENGTHS", "4096,16384,32512").split(",")]   # H6 re-run of a void cell: one length
REPS = 3


def model_disk():
    """The whole-disk name (e.g. nvme0n1) under the filesystem holding MODEL_DIR."""
    st = os.stat(os.path.realpath(os.environ["MODEL_DIR"]))
    major, minor = os.major(st.st_dev), os.minor(st.st_dev)
    dev = os.path.basename(os.path.realpath(f"/sys/dev/block/{major}:{minor}"))
    while True:                                         # a partition or a dm device: walk to the disk
        slaves = f"/sys/class/block/{dev}/slaves"
        if os.path.isdir(slaves) and os.listdir(slaves):
            dev = os.listdir(slaves)[0]; continue
        if os.path.exists(f"/sys/class/block/{dev}/partition"):
            dev = os.path.basename(os.path.dirname(os.path.realpath(f"/sys/class/block/{dev}"))); continue
        return dev


DISK = model_disk()


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
    t0 = time.time(); ttft = None; timings = usage = None; nchunks = 0; err = None; text = ""; d_ttft = None
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
                        d_ttft = disk_read_bytes()       # H6 (Tamanna): NVMe reads during the decode, first token -> end
                    if d.get("content") or d.get("reasoning_content"):
                        nchunks += 1
                        if len(text) < 200:
                            text += d.get("content") or d.get("reasoning_content") or ""
                timings = o.get("timings") or timings
                usage = o.get("usage") or usage
    except Exception as e:
        err = repr(e)[:300]
    return {"nonce": nonce, "t0": t0, "ttft_s": ttft, "total_s": time.time() - t0, "content_chunks": nchunks,
            "timings": timings, "usage": usage, "error": err, "answer_head": text[:200], "_d_ttft": d_ttft}


def measured_request(prompt, pids, tag):
    v0, d0, m0 = vmstat(), disk_read_bytes(), meminfo()
    with Sampler() as s:
        r = chat(prompt)
    v1, d1, m1 = vmstat(), disk_read_bytes(), meminfo()
    t_pf_end = r["t0"] + (r["ttft_s"] or r["total_s"])
    rx = [x[1] for x in s.rx if r["t0"] <= x[0] <= t_pf_end]
    links = sorted({(g, w) for t, g, w in s.links if r["t0"] <= t <= t_pf_end})
    r.update({"tag": tag, "swapin_kib": (v1["pswpin"] - v0["pswpin"]) * 4, "swapout_kib": (v1["pswpout"] - v0["pswpout"]) * 4,
              "nvme_read_mib": round((d1 - d0) / 2**20, 1), "nvme_read_decode_mib": round((d1 - r.pop("_d_ttft")) / 2**20, 1) if r.get("_d_ttft") is not None else None, "mem_before": m0, "mem_after": m1, "peak_card_mib": s.peak,
              "prefill_rx_mb_s_mean": round(sum(rx) / len(rx), 1) if rx else None, "prefill_rx_samples": len(rx),
              "prefill_pcie_links": links, "procs": {p: proc_status(p) for p in pids}})
    t = r["timings"] or {}
    log(f"  {tag}: prompt_n {t.get('prompt_n')} cache_n {t.get('cache_n')} pp {t.get('prompt_per_second')} "
        f"tg {t.get('predicted_per_second')} ttft {r['ttft_s'] and round(r['ttft_s'], 2)} rx {r['prefill_rx_mb_s_mean']} MB/s "
        f"swap in/out {r['swapin_kib']}/{r['swapout_kib']} KiB nvme {r['nvme_read_mib']} MiB (decode {r['nvme_read_decode_mib']}) card {s.peak} "
        f"avail {m1['avail_mib']} {r['error'] or ''}")
    return r


def prompts():
    return {n: open(os.path.join(SCRIPT, f"prompt-{n}.txt"), encoding="utf-8").read() for n in LENGTHS}


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


class EgressWatch:
    """H3: every 2 s, `ss -tnpH`; any TCP socket of the server/engine processes whose peer is not loopback is logged."""
    def __init__(self, root_pid, path):
        self.root = root_pid; self.path = path; self.stop = False; self.hits = 0
        self.t = threading.Thread(target=self.run, daemon=True)

    def run(self):
        with open(self.path, "a") as f:
            f.write(f"{time.strftime('%H:%M:%S')} watch start, root pid {self.root}\n")
            while not self.stop:
                pids = {self.root, *child_pids(self.root)}
                out = subprocess.run(["ss", "-tnpH"], capture_output=True, text=True).stdout
                for line in out.splitlines():
                    if not any(f"pid={p}," in line for p in pids):
                        continue
                    peer = line.split()[4] if len(line.split()) > 4 else ""
                    if peer.startswith(("127.", "[::1]", "[::ffff:127.")) or peer in ("*:*", "0.0.0.0:*"):
                        continue
                    self.hits += 1
                    f.write(f"{time.strftime('%H:%M:%S')} NON-LOOPBACK {line}\n"); f.flush()
                time.sleep(2)
            f.write(f"{time.strftime('%H:%M:%S')} watch end, {self.hits} non-loopback lines\n")

    def __enter__(self):
        self.t.start(); return self

    def __exit__(self, *a):
        self.stop = True; self.t.join()


def start(cmd, env, logname, timeout, cwd):
    lf = open(os.path.join(HERE, logname), "w")
    t0 = time.time()
    p = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT, env=env, cwd=cwd)
    ok = wait_health(p, timeout)
    log(f"start {logname}: {'ready' if ok else 'FAILED'} in {time.time() - t0:.1f}s card {gpu_q('memory.used')[0]} MiB mem {meminfo()}")
    return p, ok


def main():
    what = sys.argv[1]
    assert what == "strata", "usage: bench_hotrod.py strata ARM CFG ROOT"
    arm, cfg, root = sys.argv[2], os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4])
    log(f"arm {arm} cfg {cfg} root {root} disk {DISK}")
    cmd = [f"{root}/.venv/bin/python", f"{root}/serve/server.py", "--engine", "strata", "--config", cfg, "--port", str(PORT)]
    p, ok = start(cmd, dict(os.environ), f"server-strata-{arm}.log", 3600, root)
    assert ok, f"strata {arm} did not start"
    with EgressWatch(p.pid, os.path.join(HERE, f"egress-{arm}.log")):
        run_cells(arm, p.pid, LENGTHS, os.path.join(HERE, f"results-{arm}.json"))
    stop_server(p)


if __name__ == "__main__":
    main()
