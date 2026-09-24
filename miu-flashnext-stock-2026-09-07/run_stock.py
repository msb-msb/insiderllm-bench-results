#!/usr/bin/env python3
"""Qwen3.8-Flash-Next UD-IQ3_XXS, stock llama.cpp v0.4.0 on Miu (RTX 3090 24 GB, 62 GB RAM).

Steps (this file logs every number it reports to run.log and results.json):
  load   : llama-server, -ngl 99 --cpu-moe (all routed experts in RAM, dense + shared expert on GPU),
           cold (file pages evicted with posix_fadvise DONTNEED, no root needed) then warm.
           Records load time, resident VRAM, server RSS.
  server : 2k-token prompt, n_predict 128, 3 reps; prefill and decode tok/s from the server's timings.
  bench  : llama-bench -ngl 99 -ncmoe 48 -fa 1 -p 512 -n 128 -d 0,4096 -r 3, default threads (6), 3 reps.
  threads: llama-bench decode only, -p 0 -n 128, -t 3,6,12, -r 3, 3 reps.
"""
import json, os, subprocess, sys, time, glob, urllib.request

OUT = os.path.dirname(os.path.abspath(__file__))
BIN = "/home/minotaur/llama-v0.4.0/build/bin"
ENV = dict(os.environ, LD_LIBRARY_PATH=BIN)
MODEL = "/home/minotaur/bench-models/qwen3.8-flash-next/Qwen3.8-Flash-Next-UD-IQ3_XXS-00001-of-00003.gguf"
SHARDS = sorted(glob.glob("/home/minotaur/bench-models/qwen3.8-flash-next/*.gguf"))
PORT = 8099
N_LAYERS = 48
R = {"model": MODEL, "shards": SHARDS, "build": "v0.4.0 5266f24", "steps": {}}

def log(s):
    line = f"{time.strftime('%H:%M:%S')} {s}"; print(line, flush=True)
    with open(os.path.join(OUT, "run.log"), "a") as f: f.write(line + "\n")

def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, env=ENV, **kw)

def gpu_mib():
    return int(sh(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"]).stdout.split()[0])

def evict():
    for p in SHARDS:
        fd = os.open(p, os.O_RDONLY)
        try: os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
        finally: os.close(fd)
    # residency check via mincore-equivalent: vmtouch not installed; report page cache size instead
    m = {l.split(':')[0]: int(l.split()[1]) for l in open('/proc/meminfo') if l.startswith(('Cached', 'MemAvailable'))}
    log(f"  evicted model pages (fadvise DONTNEED); Cached={m['Cached']//1024} MiB MemAvailable={m['MemAvailable']//1024} MiB")

def start_server(tag):
    logf = open(os.path.join(OUT, f"server-{tag}.log"), "w")
    cmd = [f"{BIN}/llama-server", "-m", MODEL, "-ngl", "99", "--cpu-moe", "-fa", "on", "-c", "4096",
           "--port", str(PORT), "--host", "127.0.0.1", "-np", "1", "--no-warmup"]
    t0 = time.time()
    p = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT, env=ENV)
    while True:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2) as r:
                if json.loads(r.read()).get("status") == "ok": break
        except Exception: pass
        if p.poll() is not None: log(f"  server exited rc={p.returncode} during load"); sys.exit(1)
        time.sleep(0.5)
    load_s = time.time() - t0
    rss = int(open(f"/proc/{p.pid}/status").read().split("VmRSS:")[1].split()[0]) // 1024
    vram = gpu_mib()
    log(f"  {tag} load {load_s:.1f}s  server RSS {rss} MiB  card {vram} MiB")
    return p, {"load_s": round(load_s, 1), "rss_mib": rss, "vram_mib": vram, "cmd": cmd}

def completion(prompt, n_predict=128):
    body = json.dumps({"prompt": prompt, "n_predict": n_predict, "temperature": 0, "cache_prompt": False}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/completion", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r: return json.loads(r.read())

def main():
    log(f"start  card idle {gpu_mib()} MiB  shards {len(SHARDS)}")
    prompt = open(os.path.join(OUT, "prompt-2k.txt")).read()
    # ---- load cold, then warm
    evict()
    p, cold = start_server("cold")
    # tensor placement from the server log
    p.terminate(); p.wait()
    p, warm = start_server("warm")
    R["steps"]["load"] = {"cold": cold, "warm": warm}
    # ---- server 2k prompt x3
    tok = completion("hi", 1)  # tokenizer warm
    reps = []
    for i in range(1, 4):
        d = completion(prompt, 128); t = d["timings"]
        rec = {"rep": i, "prompt_n": t["prompt_n"], "prompt_ms": t["prompt_ms"], "prefill_tps": t["prompt_per_second"],
               "predicted_n": t["predicted_n"], "predicted_ms": t["predicted_ms"], "decode_tps": t["predicted_per_second"]}
        reps.append(rec); log(f"  server rep{i}: prompt {rec['prompt_n']} tok in {rec['prompt_ms']/1000:.1f}s = {rec['prefill_tps']:.1f} tok/s; decode {rec['predicted_n']} tok = {rec['decode_tps']:.2f} tok/s")
    R["steps"]["server_2k"] = reps
    rss = int(open(f"/proc/{p.pid}/status").read().split("VmRSS:")[1].split()[0]) // 1024
    log(f"  after 3 reps: server RSS {rss} MiB card {gpu_mib()} MiB")
    p.terminate(); p.wait(); time.sleep(3)
    log(f"  server stopped, card {gpu_mib()} MiB")
    # ---- llama-bench, default threads, 3 reps
    def bench(args, tag):
        cmd = [f"{BIN}/llama-bench", "-m", MODEL, "-ngl", "99", "-ncmoe", str(N_LAYERS), "-fa", "1"] + args + ["-o", "json"]
        t0 = time.time(); q = sh(cmd); el = time.time() - t0
        if q.returncode != 0: log(f"  bench {tag} FAILED rc={q.returncode}: {q.stderr[-300:]}"); return None
        rows = json.loads(q.stdout)
        with open(os.path.join(OUT, f"bench-{tag}.json"), "w") as f: json.dump({"cmd": cmd, "rows": rows, "stderr_tail": q.stderr[-1500:]}, f, indent=1)
        out = [{"kind": "pp" if r["n_prompt"] > 0 else "tg", "depth": r.get("n_depth", 0), "threads": r.get("n_threads"), "avg_ts": r["avg_ts"], "stddev_ts": r["stddev_ts"]} for r in rows]
        log(f"  bench {tag} ({el:.0f}s): " + "  ".join(f"{o['kind']}{'' if o['depth']==0 else '@'+str(o['depth'])} t{o['threads']} {o['avg_ts']:.2f}±{o['stddev_ts']:.2f}" for o in out))
        return out
    R["steps"]["bench_default"] = [bench(["-p", "512", "-n", "128", "-d", "0,4096", "-r", "3"], f"default-rep{i}") for i in range(1, 4)]
    # ---- thread sweep, decode only
    R["steps"]["threads"] = [bench(["-p", "0", "-n", "128", "-t", "3,6,12", "-r", "3"], f"threads-rep{i}") for i in range(1, 4)]
    with open(os.path.join(OUT, "results.json"), "w") as f: json.dump(R, f, indent=1)
    log(f"done  card {gpu_mib()} MiB")

if __name__ == "__main__":
    main()
