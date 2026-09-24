#!/usr/bin/env python3
"""Qwen3.8-Flash-Next UD-IQ3_XXS, stock llama.cpp v0.4.0: -ncmoe sweep.

Pre-registered 2026-09-08: decode scales roughly with the fraction of routed-expert
layers resident in VRAM. Stock (-ncmoe 48, every routed expert on host) is the
baseline; each step moves more expert layers onto the card until the first OOM.

Per host (argv[1] = miu | rushuna):
  sweep  : for each -ncmoe N in order, llama-bench -ngl 99 -ncmoe N -fa 1 -p 0 -n 128
           -d 0,4096 -r 3 -t T -lm <load mode>, 3 invocations. Peak VRAM sampled from
           nvidia-smi at 0.5 s during each invocation. First OOM stops the sweep.
  control: miu only, one invocation at stock (-ncmoe 48) with -lm mmap, to state the
           mmap-vs-none difference.
  server : llama-server at the best fitting setting, 2,343-token prompt, n_predict 128,
           temperature 0, streamed so the prefill/decode boundary is timestamped.
           Reads /proc/diskstats at request start, first token, and end, so decode
           disk traffic is isolated. rushuna runs this at stock FIRST (3 reps, with
           iostat -dx 1 in the background) because the page-cache question is the
           point of that rig; then again at the best setting if it differs.
Everything is logged to run.log and results.json in the output directory.
"""
import json, os, subprocess, sys, threading, time, glob, urllib.request

HOST = sys.argv[1]
CFG = {
    "miu": dict(
        bin="/home/minotaur/llama-v0.4.0/build/bin",
        model_dir="/home/minotaur/bench-models/qwen3.8-flash-next",
        out="/home/minotaur/Desktop/InsiderLLM/docs/bench-results/miu-flashnext-ncmoe-2026-09-08",
        ncmoe=[48, 40, 34, 29, 26], threads=6, load_mode="mmap", control_mmap=False,
        server_stock_first=False, disk="nvme0n1",
    ),
    "rushuna": dict(
        bin="/home/minotaur/llama-v0.4.0",
        model_dir="/home/minotaur/bench-models/qwen3.8-flash-next",
        out="/home/minotaur/flashnext-ncmoe-2026-09-08",
        ncmoe=[48, 44, 41, 38], threads=4, load_mode="mmap", control_mmap=False,
        server_stock_first=True, disk="nvme0n1", n_layers=48, none_pass=False,
    ),
    "rushuna1650": dict(
        bin="/home/minotaur/llama-v0.4.0-sm75",
        model="/home/minotaur/bench-models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf",
        out="/home/minotaur/gtx1650-qwen36-ncmoe-2026-09-11",
        ncmoe=list(range(40, 0, -1)), threads=4, load_mode="mmap", control_mmap=False,
        server_stock_first=True, disk="nvme0n1", n_layers=40, none_pass=True,
    ),
    "rushuna3060b": dict(
        bin="/home/minotaur/llama-v0.4.0-sm75",
        model="/home/minotaur/bench-models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf",
        out="/home/minotaur/rtx3060-qwen36-ncmoe-2026-09-11",
        ncmoe=[40, 24], threads=4, load_mode="mmap", control_mmap=False,
        server_stock_first=True, disk="nvme0n1", n_layers=40, none_pass=False, server_reps=1,
    ),
}[HOST]
CFG.setdefault("n_layers", 48); CFG.setdefault("none_pass", False); CFG.setdefault("server_reps", 3)
BIN, OUT = CFG["bin"], CFG["out"]
os.makedirs(OUT, exist_ok=True)
ENV = dict(os.environ, LD_LIBRARY_PATH=BIN)
SHARDS = [CFG["model"]] if CFG.get("model") else sorted(glob.glob(CFG["model_dir"] + "/*.gguf"))
MODEL = SHARDS[0]
N_LAYERS = CFG["n_layers"]
PORT = 8099
PROMPT = os.path.join(OUT, "prompt-2k.txt")
R = {"host": HOST, "cfg": CFG, "model": MODEL, "build": "v0.4.0 5266f24", "sweep": [], "control": None, "server": {}}


def log(s):
    line = f"{time.strftime('%H:%M:%S')} {s}"
    print(line, flush=True)
    with open(os.path.join(OUT, "run.log"), "a") as f:
        f.write(line + "\n")


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, env=ENV, **kw)


def gpu_mib():
    return int(sh(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"]).stdout.split()[0])


def meminfo():
    m = {}
    for l in open("/proc/meminfo"):
        k, v = l.split(":")
        m[k] = int(v.split()[0]) // 1024
    return {"cached_mib": m["Cached"], "avail_mib": m["MemAvailable"], "free_mib": m["MemFree"]}


def disk_read_mib():
    for l in open("/proc/diskstats"):
        f = l.split()
        if f[2] == CFG["disk"]:
            return int(f[5]) * 512 / 1048576.0
    return None


class PeakVram:
    def __init__(self):
        self.peak = 0; self.stop = False
        self.t = threading.Thread(target=self.run, daemon=True)

    def run(self):
        while not self.stop:
            try: self.peak = max(self.peak, gpu_mib())
            except Exception: pass
            time.sleep(0.5)

    def __enter__(self): self.t.start(); return self
    def __exit__(self, *a): self.stop = True; self.t.join()


def bench(ncmoe, load_mode, tag):
    cmd = [f"{BIN}/llama-bench", "-m", MODEL, "-ngl", "99", "-ncmoe", str(ncmoe), "-fa", "1",
           "-p", "0", "-n", "128", "-d", "0,4096", "-r", "3", "-t", str(CFG["threads"]),
           "-lm", load_mode, "-o", "json"]
    t0 = time.time()
    with PeakVram() as pv:
        q = sh(cmd)
    el = time.time() - t0
    rec = {"tag": tag, "ncmoe": ncmoe, "load_mode": load_mode, "cmd": cmd, "elapsed_s": round(el, 1),
           "peak_vram_mib": pv.peak, "rc": q.returncode}
    with open(os.path.join(OUT, f"raw-{tag}.json"), "w") as f:
        json.dump({"cmd": cmd, "rc": q.returncode, "stdout": q.stdout, "stderr_tail": q.stderr[-4000:]}, f, indent=1)
    if q.returncode != 0:
        err = q.stderr
        oom = any(k in err for k in ("out of memory", "cudaMalloc", "failed to allocate", "CUDA_ERROR_OUT_OF_MEMORY", "ggml_backend_cuda_buffer_type_alloc_buffer"))
        rec["oom"] = oom; rec["stderr_tail"] = err[-600:]
        log(f"  {tag} FAILED rc={q.returncode} oom={oom} peak {pv.peak} MiB ({el:.0f}s): {err[-200:].strip()}")
        return rec
    try:
        rows = json.loads(q.stdout)
    except Exception as e:
        rec["oom"] = False; rec["parse_error"] = str(e); log(f"  {tag} parse error: {e}"); return rec
    rec["rows"] = [{"depth": r.get("n_depth", 0), "threads": r.get("n_threads"), "avg_ts": r["avg_ts"], "stddev_ts": r["stddev_ts"]} for r in rows]
    rec["oom"] = False
    log(f"  {tag} ({el:.0f}s) peak {pv.peak} MiB: " + "  ".join(f"tg128@d{o['depth']} {o['avg_ts']:.2f}±{o['stddev_ts']:.2f}" for o in rec["rows"]))
    return rec


def start_server(ncmoe, load_mode, tag):
    logf = open(os.path.join(OUT, f"server-{tag}.log"), "w")
    cmd = [f"{BIN}/llama-server", "-m", MODEL, "-ngl", "99", "-ncmoe", str(ncmoe), "-fa", "on", "-c", "4096",
           "-t", str(CFG["threads"]), "--load-mode", load_mode, "--port", str(PORT), "--host", "127.0.0.1", "-np", "1", "--no-warmup"]
    t0 = time.time()
    p = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT, env=ENV)
    while True:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2) as r:
                if json.loads(r.read()).get("status") == "ok": break
        except Exception: pass
        if p.poll() is not None:
            log(f"  server {tag} exited rc={p.returncode} during load"); return None, {"rc": p.returncode, "cmd": cmd}
        time.sleep(0.5)
    load_s = time.time() - t0
    info = {"load_s": round(load_s, 1), "rss_mib": rss_of(p.pid), "vram_mib": gpu_mib(), "cmd": cmd, "mem": meminfo()}
    log(f"  server {tag} load {load_s:.1f}s RSS {info['rss_mib']} MiB card {info['vram_mib']} MiB cached {info['mem']['cached_mib']} MiB")
    return p, info


def rss_of(pid):
    return int(open(f"/proc/{pid}/status").read().split("VmRSS:")[1].split()[0]) // 1024


def stream_completion(prompt, n_predict=128):
    body = json.dumps({"prompt": prompt, "n_predict": n_predict, "temperature": 0, "cache_prompt": False, "stream": True}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/completion", data=body, headers={"Content-Type": "application/json"})
    t_start = time.time(); d_start = disk_read_mib(); t_first = None; d_first = None; final = None; n = 0
    with urllib.request.urlopen(req, timeout=7200) as r:
        for raw in r:
            line = raw.decode(errors="replace").strip()
            if not line.startswith("data: "): continue
            j = json.loads(line[6:])
            if t_first is None:
                t_first = time.time(); d_first = disk_read_mib()
            n += 1
            if j.get("stop"): final = j
    t_end = time.time(); d_end = disk_read_mib()
    t = final["timings"]
    dec_s = t_end - t_first
    return {"prompt_n": t["prompt_n"], "prompt_ms": t["prompt_ms"], "prefill_tps": t["prompt_per_second"],
            "predicted_n": t["predicted_n"], "predicted_ms": t["predicted_ms"], "decode_tps": t["predicted_per_second"],
            "wall_prefill_s": round(t_first - t_start, 2), "wall_decode_s": round(dec_s, 2),
            "disk_read_prefill_mib": round(d_first - d_start, 1), "disk_read_decode_mib": round(d_end - d_first, 1),
            "disk_read_decode_mib_per_s": round((d_end - d_first) / dec_s, 1) if dec_s > 0 else None,
            "disk_read_decode_mib_per_token": round((d_end - d_first) / max(t["predicted_n"], 1), 2)}


def server_block(ncmoe, load_mode, tag, reps, iostat=False):
    p, info = start_server(ncmoe, load_mode, tag)
    if p is None: return {"load": info, "reps": []}
    io = None
    if iostat:
        io = subprocess.Popen(["iostat", "-dxt", CFG["disk"], "1"], stdout=open(os.path.join(OUT, f"iostat-{tag}.log"), "w"), stderr=subprocess.STDOUT)
    prompt = open(PROMPT).read()
    stream_completion("hi", 1)
    out = []
    for i in range(1, reps + 1):
        m0 = meminfo()
        rec = stream_completion(prompt, 128); rec["rep"] = i; rec["rss_after_mib"] = rss_of(p.pid); rec["vram_after_mib"] = gpu_mib(); rec["mem_before"] = m0; rec["mem_after"] = meminfo()
        out.append(rec)
        log(f"  server {tag} rep{i}: prefill {rec['prompt_n']} tok {rec['prefill_tps']:.1f} tok/s; decode {rec['decode_tps']:.2f} tok/s; "
            f"disk read prefill {rec['disk_read_prefill_mib']:.0f} MiB, decode {rec['disk_read_decode_mib']:.0f} MiB = {rec['disk_read_decode_mib_per_s']} MiB/s, {rec['disk_read_decode_mib_per_token']} MiB/token; RSS {rec['rss_after_mib']} MiB cached {rec['mem_after']['cached_mib']} MiB")
    if io: io.terminate()
    p.terminate(); p.wait(); time.sleep(3)
    log(f"  server {tag} stopped, card {gpu_mib()} MiB")
    return {"load": info, "reps": out}


def save():
    with open(os.path.join(OUT, "results.json"), "w") as f: json.dump(R, f, indent=1)


def main():
    log(f"start {HOST}  card idle {gpu_mib()} MiB  mem {meminfo()}  shards {len(SHARDS)}  threads {CFG['threads']}  load-mode {CFG['load_mode']}")
    if CFG["server_stock_first"]:
        R["server"]["stock"] = server_block(N_LAYERS, CFG["load_mode"], f"stock-ncmoe{N_LAYERS}", reps=CFG["server_reps"], iostat=True); save()
    last_fit = None
    for n in CFG["ncmoe"]:
        recs = []
        for rep in range(1, 4):
            rec = bench(n, CFG["load_mode"], f"ncmoe{n}-{CFG['load_mode']}-rep{rep}")
            recs.append(rec); R["sweep"].append(rec); save()
            if rec.get("oom") or rec["rc"] != 0: break
        if any(r.get("oom") or r["rc"] != 0 for r in recs):
            log(f"  stop: -ncmoe {n} failed; last fitting value {last_fit}")
            R["first_fail"] = n; break
        last_fit = n
    R["last_fit"] = last_fit; save()
    if CFG["control_mmap"] and last_fit is not None:
        R["control"] = bench(48, "mmap", "ncmoe48-mmap-control"); save()
    if last_fit is not None and (not CFG["server_stock_first"] or last_fit != N_LAYERS):
        R["server"]["best"] = server_block(last_fit, CFG["load_mode"], f"best-ncmoe{last_fit}", reps=1 if HOST == "miu" else CFG["server_reps"], iostat=(HOST != "miu")); save()
    if CFG["none_pass"] and last_fit is not None:
        # --load-mode none at the best fit: three llama-bench invocations, then the server with iostat
        R["none"] = {"bench": [bench(last_fit, "none", f"ncmoe{last_fit}-none-rep{rep}") for rep in range(1, 4)]}; save()
        R["none"]["server"] = server_block(last_fit, "none", f"best-ncmoe{last_fit}-none", reps=3, iostat=True); save()
    log(f"done  card {gpu_mib()} MiB  mem {meminfo()}")


if __name__ == "__main__":
    main()
