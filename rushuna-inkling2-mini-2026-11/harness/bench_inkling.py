#!/usr/bin/env python3
"""Inkling 2 Mini on Rushuna's RTX 3060 (lock docs/candidates/inkling-2-mini-3060-2026-11.md, commit 35324447,
sha256 588819cd...54baf). Built from ../moe-cache-cpu-share-2026-11/harness/bench_moecache.py, changed to the lock's I5/I6:

  - any server command (llama-server for L/U/Q, `strata launch` for S), given after `--`;
  - cells from --cells "name:prompt_n:reps,..." with prompts from --prompts DIR (prompt-<TAG>-<n>.txt);
  - model sampling (temperature 1.0, top-p 1.0, top-k 0, min-p 0, seed 1234) unless --temp 0 (greedy cells);
    reasoning left at the template default (no chat_template_kwargs);
  - per cell: free -m and swapon before and after, pswpout per request, card peak, MemAvailable min;
  - optional --ballast MiB: start ./ballast first and keep it for the arm (I5, "fits in 4 GiB");
  - strata: --kind strata, --stop-cmd for its stop; the engine PID is found by --engine-name.

  bench_inkling.py ARM --tag inkling --cells short:512:3,deep:7372:3 [--temp 1.0] [--ballast 4096]
                   [--kind llama|strata] [--port 8081] [--stop-cmd "..."] [--engine-name NAME] -- SERVER CMD ...

Every request: fresh 8-hex nonce line first, chat completion, streamed, cache_prompt false, ignore_eos, max_tokens 256.
"""
import argparse, json, os, random, signal, subprocess, sys, threading, time, urllib.request

HERE = os.getcwd()
SCRIPT = os.path.dirname(os.path.abspath(__file__))

ap = argparse.ArgumentParser()
ap.add_argument("arm")
ap.add_argument("--tag", required=True)
ap.add_argument("--cells", required=True)
ap.add_argument("--prompts", default=os.path.join(SCRIPT, "prompts"))
ap.add_argument("--temp", type=float, default=1.0)
ap.add_argument("--ballast", type=int, default=0)
ap.add_argument("--kind", default="llama", choices=["llama", "strata"])
ap.add_argument("--port", type=int, default=8081)
ap.add_argument("--stop-cmd", default="")
ap.add_argument("--engine-name", default="llama-server")
ap.add_argument("--load-timeout", type=int, default=2400)
_argv = sys.argv[1:]
_cut = _argv.index("--") if "--" in _argv else len(_argv)   # everything after "--" is the server command
A = ap.parse_args(_argv[:_cut])
CMD = _argv[_cut + 1:]
PORT = A.port
CELLS = [(c.split(":")[0], int(c.split(":")[1]), int(c.split(":")[2])) for c in A.cells.split(",")]


def model_disk():
    st = os.stat(os.path.expanduser("~/inkling2-2026-11/model"))
    dev = os.path.basename(os.path.realpath(f"/sys/dev/block/{os.major(st.st_dev)}:{os.minor(st.st_dev)}"))
    while True:
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


def free_swap():
    f = subprocess.run(["free", "-m"], capture_output=True, text=True).stdout
    s = subprocess.run(["swapon", "--show"], capture_output=True, text=True).stdout
    return {"free_m": f, "swapon": s, "vmstat": vmstat(), "t": time.time()}


def proc_status(pid):
    out = {}
    try:
        for l in open(f"/proc/{pid}/status"):
            k = l.split(":")[0]
            if k in ("VmRSS", "RssAnon", "RssFile", "RssShmem", "VmSwap"):
                out[k] = l.split(":")[1].strip()
    except (OSError, TypeError):
        pass
    return out


def gpu_q(fields):
    r = subprocess.run(["nvidia-smi", f"--query-gpu={fields}", "--format=csv,noheader,nounits"], capture_output=True, text=True)
    return [x.strip() for x in r.stdout.strip().split(",")]


def engine_pid():
    r = subprocess.run(["pgrep", "-n", "-x", A.engine_name], capture_output=True, text=True)
    return int(r.stdout.split()[0]) if r.stdout.split() else None


class ArmSampler:
    def __init__(self):
        self.stop = False; self.phase = "load"; self.rows = []
        self.t = threading.Thread(target=self.run, daemon=True)

    def run(self):
        f = open(os.path.join(HERE, f"card-1s-{A.arm}.csv"), "a")
        while not self.stop:
            try:
                used, gen, width = gpu_q("memory.used,pcie.link.gen.current,pcie.link.width.current")
                row = (time.time(), self.phase, int(used), gen, width, meminfo()["avail_mib"])
                self.rows.append(row); f.write(",".join(map(str, row)) + "\n"); f.flush()
            except Exception:
                pass
            time.sleep(1)

    def peak(self, phase=None):
        v = [r[2] for r in self.rows if phase is None or r[1] == phase]
        return max(v) if v else None

    def min_avail(self, phase=None):
        v = [r[5] for r in self.rows if phase is None or r[1] == phase]
        return min(v) if v else None

    def __enter__(self):
        self.t.start(); return self

    def __exit__(self, *a):
        self.stop = True; self.t.join()


class ReqSampler:
    def __init__(self):
        self.stop = False; self.peak = 0; self.links = []
        self.t = threading.Thread(target=self.run, daemon=True)

    def run(self):
        while not self.stop:
            try:
                used, gen, width = gpu_q("memory.used,pcie.link.gen.current,pcie.link.width.current")
                self.peak = max(self.peak, int(used)); self.links.append((time.time(), gen, width))
            except Exception:
                pass
            time.sleep(0.5)

    def __enter__(self):
        self.t.start(); return self

    def __exit__(self, *a):
        self.stop = True; self.t.join()


def wait_ready(p, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if A.kind == "llama" and p.poll() is not None:
            return False
        for path in ("/health", "/v1/models"):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=3) as r:
                    if r.status == 200 and b"loading" not in r.read().lower():
                        return True
            except Exception:
                pass
        time.sleep(2)
    return False


def stop_server(p):
    if A.stop_cmd:
        subprocess.run(A.stop_cmd, shell=True, timeout=300)
    if p is not None and p.poll() is None:
        p.send_signal(signal.SIGTERM)
        for _ in range(30):
            if p.poll() is not None:
                break
            time.sleep(1)
        if p.poll() is None:
            p.kill(); p.wait()
    subprocess.run(["pkill", "-KILL", "-x", A.engine_name])
    for _ in range(60):
        if int(gpu_q("memory.used")[0]) <= 50 + (A.ballast_hold if hasattr(A, "ballast_hold") else 0):
            break
        time.sleep(1)


def chat(prompt, max_tokens=256):
    nonce = "%08x" % random.getrandbits(32)
    body = {"model": "bench", "stream": True, "stream_options": {"include_usage": True}, "max_tokens": max_tokens,
            "temperature": A.temp, "top_p": 1.0, "top_k": 0, "min_p": 0.0, "seed": 1234,
            "cache_prompt": False, "ignore_eos": True,
            "messages": [{"role": "user", "content": f"request {nonce}\n{prompt}\n\nSummarise what this code does."}]}
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time(); ttft = None; timings = usage = None; nchunks = 0; err = None; text = ""; d_ttft = None
    try:
        with urllib.request.urlopen(req, timeout=7200) as r:
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
                    piece = d.get("content") or d.get("reasoning_content") or ""
                    if piece:
                        if ttft is None:
                            ttft = time.time() - t0; d_ttft = disk_read_bytes()
                        nchunks += 1
                        text += piece
                timings = o.get("timings") or timings
                usage = o.get("usage") or usage
    except Exception as e:
        err = repr(e)[:300]
    return {"nonce": nonce, "t0": t0, "ttft_s": ttft, "total_s": time.time() - t0, "content_chunks": nchunks,
            "timings": timings, "usage": usage, "error": err, "answer_head": text[:200], "answer_full": text,
            "_d_ttft": d_ttft}


def request(prompt, tag):
    pid = engine_pid()
    v0, d0 = vmstat(), disk_read_bytes()
    with ReqSampler() as s:
        r = chat(prompt)
    v1, d1, m1 = vmstat(), disk_read_bytes(), meminfo()
    t_pf_end = r["t0"] + (r["ttft_s"] or r["total_s"])
    d_ttft = r.pop("_d_ttft")
    links = sorted({(g, w) for t, g, w in s.links if r["t0"] <= t <= t_pf_end})
    r.update({"tag": tag, "swapin_kib": (v1["pswpin"] - v0["pswpin"]) * 4, "swapout_kib": (v1["pswpout"] - v0["pswpout"]) * 4,
              "nvme_read_prefill_mib": round(((d_ttft if d_ttft is not None else d1) - d0) / 2**20, 1),
              "nvme_read_decode_mib": round((d1 - d_ttft) / 2**20, 1) if d_ttft is not None else None,
              "mem_after": m1, "peak_card_mib": s.peak, "prefill_pcie_links": links, "proc": proc_status(pid)})
    t = r["timings"] or {}
    u = r["usage"] or {}
    log(f"  {tag}: prompt_n {t.get('prompt_n', u.get('prompt_tokens'))} cache_n {t.get('cache_n')} pp {t.get('prompt_per_second')} "
        f"tg {t.get('predicted_per_second')} n {t.get('predicted_n', u.get('completion_tokens'))} "
        f"draft {t.get('draft_n')}/{t.get('draft_n_accepted')} ttft {r['ttft_s'] and round(r['ttft_s'], 2)} "
        f"swap {r['swapin_kib']}/{r['swapout_kib']} nvme pf/dec {r['nvme_read_prefill_mib']}/{r['nvme_read_decode_mib']} MiB "
        f"card {s.peak} links {links} avail {m1['avail_mib']} rss {r['proc'].get('RssAnon')}/{r['proc'].get('RssFile')} "
        f"{r['error'] or ''} | {r['answer_head'][:60]!r}")
    return r


def prompt(n):
    return open(os.path.join(A.prompts, f"prompt-{A.tag}-{n}.txt"), encoding="utf-8").read()


def main():
    out = os.path.join(HERE, f"results-{A.arm}.json")
    R = {"arm": A.arm, "tag": A.tag, "kind": A.kind, "cmd": CMD, "cells_spec": A.cells, "temp": A.temp,
         "ballast_mib_target": A.ballast, "disk": DISK, "cells": {}, "start_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    log(f"arm {A.arm} cells {CELLS} temp {A.temp} ballast {A.ballast} cmd: {' '.join(CMD)}")
    bal = None
    if A.ballast:
        bal = subprocess.Popen([os.path.join(SCRIPT, "ballast"), str(A.ballast)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        line = bal.stdout.readline().strip()
        R["ballast_line"] = line; log(f"ballast: {line}")
        if not line.startswith("READY"):
            R["error"] = "ballast failed"; json.dump(R, open(out, "w"), indent=1); bal.kill(); sys.exit(1)
        A.ballast_hold = int(gpu_q("memory.used")[0])
    R["state_before"] = free_swap()
    with ArmSampler() as S:
        lf = open(os.path.join(HERE, f"server-{A.arm}.log"), "w")
        t0 = time.time()
        p = subprocess.Popen(CMD, stdout=lf, stderr=subprocess.STDOUT, start_new_session=True)
        ok = wait_ready(p, A.load_timeout)
        R["load_s"] = round(time.time() - t0, 1)
        time.sleep(2); S.phase = "idle-after-load"; time.sleep(3)
        R["load_peak_mib"] = S.peak("load"); R["card_after_load_mib"] = S.peak("idle-after-load")
        R["avail_after_load_mib"] = meminfo()["avail_mib"]; R["proc_after_load"] = proc_status(engine_pid())
        log(f"start: {'ready' if ok else 'FAILED'} in {R['load_s']}s load peak {R['load_peak_mib']} MiB, idle {R['card_after_load_mib']} MiB, avail {R['avail_after_load_mib']}")
        if not ok:
            R["error"] = "server did not start"; S.phase = "stop"; stop_server(p)
            R["state_after"] = free_swap(); json.dump(R, open(out, "w"), indent=1)
            if bal: bal.kill()
            log(f"arm {A.arm}: did not start (see server-{A.arm}.log)"); sys.exit(2)
        for path in ("/props", "/v1/models"):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=10) as r:
                    R[f"info{path.replace('/', '_')}"] = json.loads(r.read())
            except Exception as e:
                R[f"info{path.replace('/', '_')}"] = repr(e)
        S.phase = "cold"
        R["cold"] = request(prompt(512), f"{A.arm}-cold")
        R["cold_peak_mib"] = S.peak("cold")
        for name, n, reps in CELLS:
            S.phase = f"cell-{name}"
            before = free_swap()
            reqs = [request(prompt(n), f"{A.arm}-{name}-{n}-rep{i}") for i in range(1, reps + 1)]
            after = free_swap()
            R["cells"][name] = {"prompt_target": n, "reqs": reqs, "free_before": before, "free_after": after,
                                "pswpout_delta": after["vmstat"]["pswpout"] - before["vmstat"]["pswpout"],
                                "peak_card_mib": S.peak(f"cell-{name}"), "min_avail_mib": S.min_avail(f"cell-{name}")}
            json.dump(R, open(out, "w"), indent=1)
        S.phase = "stop"
        stop_server(p)
        R["arm_peak_mib"] = S.peak(); R["min_avail_mib"] = S.min_avail()
    if bal:
        bal.kill(); bal.wait()
    R["state_after"] = free_swap()
    R["end_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    json.dump(R, open(out, "w"), indent=1)
    log(f"arm {A.arm} done: arm peak {R['arm_peak_mib']} MiB, min MemAvailable {R['min_avail_mib']} MiB, card now {gpu_q('memory.used')[0]} MiB")


if __name__ == "__main__":
    main()
