#!/usr/bin/env python3
"""llama.cpp MoE cache CPU share (PR #30966), Qwen3.6-35B-A3B on Rushuna's RTX 3060, 2026-11.

Pre-registered in docs/candidates/moe-cache-cpu-share-2026-11.md (lock c22ff41b, sha256 f047318b...). This is
../strata-hotrod-2026-11's bench_hotrod.py cut down to the lock's M5:
  - llama-server only, started from the M2 base command with the arm's -ncmoe and cache flags;
  - per arm: /health, one cold 512-token request (reported, excluded), then 3 measured at 512, then 3 at 4,096,
    on the same resident server (no priming requests between measured ones, unlike HotRod);
  - card memory.used sampled at 1 s for the whole arm, peaks reported for the load, the cold request and each cell;
  - MemAvailable minimum over the arm; server VmRSS split into RssAnon / RssFile after every request;
  - requests carry ignore_eos (M5); the egress watch is gone (not in this lock).

  bench_moecache.py ARM N [cache flags ...]       (env MOE_LENGTHS=512 or 4096 for an M6 re-run of one cell)

Every request: a fresh 8-hex nonce line first, chat completion, streamed, thinking off, temperature 0,
cache_prompt false, ignore_eos, max_tokens 256.
"""
import json, os, random, signal, subprocess, sys, threading, time, urllib.request

SCRIPT = os.path.dirname(os.path.abspath(__file__))
HERE = os.getcwd()
W = os.path.expanduser("~/moecache-2026-11")
BIN = f"{W}/llama.cpp/build/bin/llama-server"
MODEL = f"{W}/model/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf"
PORT = 8081
LENGTHS = [int(x) for x in os.environ.get("MOE_LENGTHS", "512,4096").split(",")]
REPS = 3


def base_cmd(n):  # lock M2, verbatim, N from the arm table
    return [BIN, "-m", MODEL, "-ngl", "99", "-ncmoe", str(n), "-fa", "on", "-c", "16384", "-np", "1", "--fit", "off",
            "-lm", "mmap", "-t", "4", "--port", str(PORT)]


def model_disk():
    st = os.stat(os.path.realpath(MODEL))
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


def proc_status(pid):
    out = {}
    try:
        for l in open(f"/proc/{pid}/status"):
            k = l.split(":")[0]
            if k in ("VmRSS", "RssAnon", "RssFile", "RssShmem", "VmSwap"):
                out[k] = l.split(":")[1].strip()
    except OSError:
        pass
    return out


def gpu_q(fields):
    r = subprocess.run(["nvidia-smi", f"--query-gpu={fields}", "--format=csv,noheader,nounits"], capture_output=True, text=True)
    return [x.strip() for x in r.stdout.strip().split(",")]


class ArmSampler:
    """Whole arm, 1 s: card memory.used, PCIe gen/width, MemAvailable. Phase label set by the caller."""
    def __init__(self):
        self.stop = False; self.phase = "load"; self.rows = []
        self.t = threading.Thread(target=self.run, daemon=True)

    def run(self):
        f = open(os.path.join(HERE, "card-1s.csv"), "a")
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

    def min_avail(self):
        return min(r[5] for r in self.rows) if self.rows else None

    def __enter__(self):
        self.t.start(); return self

    def __exit__(self, *a):
        self.stop = True; self.t.join()


class ReqSampler:
    """Per request, 0.5 s: PCIe gen/width (for the prefill window) and peak card MiB."""
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


def http(path, timeout=30):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=timeout) as r:
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
        for _ in range(30):
            if p.poll() is not None:
                break
            time.sleep(1)
    if p.poll() is None:
        p.kill(); p.wait()
    subprocess.run(["pkill", "-KILL", "-x", "llama-server"])
    for _ in range(30):   # lock M2: card at 0 MiB between arms
        if int(gpu_q("memory.used")[0]) <= 50:
            break
        time.sleep(1)


def chat(prompt, max_tokens=256):
    nonce = "%08x" % random.getrandbits(32)
    body = {"model": "bench", "stream": True, "stream_options": {"include_usage": True}, "max_tokens": max_tokens,
            "temperature": 0, "cache_prompt": False, "ignore_eos": True, "chat_template_kwargs": {"enable_thinking": False},
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


def request(prompt, pid, tag):
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
    log(f"  {tag}: prompt_n {t.get('prompt_n')} cache_n {t.get('cache_n')} pp {t.get('prompt_per_second')} "
        f"tg {t.get('predicted_per_second')} n {t.get('predicted_n')} ttft {r['ttft_s'] and round(r['ttft_s'], 2)} "
        f"swap {r['swapin_kib']}/{r['swapout_kib']} nvme pf/dec {r['nvme_read_prefill_mib']}/{r['nvme_read_decode_mib']} MiB "
        f"card {s.peak} links {links} avail {m1['avail_mib']} rss {r['proc'].get('RssAnon')}/{r['proc'].get('RssFile')} "
        f"{r['error'] or ''} | {r['answer_head'][:60]!r}")
    return r


def main():
    arm, n, extra = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
    cmd = base_cmd(n) + extra
    P = {k: open(os.path.join(SCRIPT, f"prompt-{k}.txt"), encoding="utf-8").read() for k in (512, 4096)}
    log(f"arm {arm} lengths {LENGTHS} disk {DISK} cmd: {' '.join(cmd)}")
    R = {"arm": arm, "ncmoe": n, "cmd": cmd, "lengths": LENGTHS, "cells": {}}
    out = os.path.join(HERE, f"results-{arm}.json")
    with ArmSampler() as S:
        lf = open(os.path.join(HERE, f"server-{arm}.log"), "w")
        t0 = time.time()
        p = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT)
        ok = wait_health(p, 1800)
        R["load_s"] = round(time.time() - t0, 1)
        time.sleep(2)   # one more card sample after /health
        S.phase = "idle-after-load"; time.sleep(2)
        R["load_peak_mib"] = S.peak("load"); R["card_after_load_mib"] = S.peak("idle-after-load")
        log(f"start: {'ready' if ok else 'FAILED'} in {R['load_s']}s load peak {R['load_peak_mib']} MiB, idle {R['card_after_load_mib']} MiB")
        if not ok:
            R["error"] = "server did not start"; json.dump(R, open(out, "w"), indent=1); stop_server(p); sys.exit(1)
        try:
            props = http("/props"); R["props_build"] = {k: props.get(k) for k in ("build_info", "build_commit", "model_path")}
            R["props_n_ctx"] = props.get("default_generation_settings", {}).get("n_ctx")
        except Exception as e:
            R["props_build"] = repr(e)
        log(f"props {R['props_build']} n_ctx {R.get('props_n_ctx')}")
        S.phase = "cold"
        R["cold"] = request(P[512], p.pid, f"{arm}-512-cold")
        R["cold_peak_mib"] = S.peak("cold")
        for k in LENGTHS:
            S.phase = f"cell-{k}"
            R["cells"][k] = [request(P[k], p.pid, f"{arm}-{k}-rep{i}") for i in range(1, REPS + 1)]
            R[f"cell_{k}_peak_mib"] = S.peak(f"cell-{k}")
            json.dump(R, open(out, "w"), indent=1)
        S.phase = "stop"
        stop_server(p)
        R["arm_peak_mib"] = S.peak(); R["min_avail_mib"] = S.min_avail()
    json.dump(R, open(out, "w"), indent=1)
    log(f"arm {arm} done: arm peak {R['arm_peak_mib']} MiB, min MemAvailable {R['min_avail_mib']} MiB, card now {gpu_q('memory.used')[0]} MiB")


if __name__ == "__main__":
    main()
