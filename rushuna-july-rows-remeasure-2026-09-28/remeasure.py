#!/usr/bin/env python3
"""Re-measure the ten July 2026 rushuna rows that have no docs/bench-results record, 2026-09-28.

PRE-REGISTERED in README.md before the first measured run. Rule: new value within 3% of the published value
-> keep the row, point it at this record; outside 3% -> replace the value and add a dated correction wherever
the old figure is published.

Build: ~/llama-v0.4.0 on rushuna (v0.4.0 5266f24, sm_86, the pin). Block-3 design (09-21 convention): every
measured llama-bench invocation is immediately preceded by a discarded priming invocation of the identical
command; n=3 measured invocations per config, each -r 3. Value = mean of the three invocation means; spread =
max - min of those means. Peak VRAM from nvidia-smi at 0.5 s during each invocation.

Configs (flags the July rows state or imply; everything else at llama-bench v0.4.0 defaults):
  35B  -ngl 99 -ncmoe 32 -fa 1 -p 512 -n 128 -d 0             -r 3
  35B  -ngl 99 -ncmoe 20 -fa 1 -p 512 -n 128 -d 0             -r 3
  35B  -ngl 99 -ncmoe 24 -fa 1 -p 512 -n 128 -d 0,4096,8192   -r 3
  14B  -ngl 41 / 20 / 0        -p 512 -n 128 -d 0             -r 3
Server test (the "-ncmoe 20 OOMs under real context" claim): llama-server -ngl 99 -ncmoe N -fa on -c C -np 1,
C in {8192, 16384}, N = 20 (the claim) and 24 (control). Loads? Then one request whose prompt fills C - 256
tokens, n_predict 128, temperature 0. Serves = request returns predicted_n > 0 without the server dying.
"""
import json, os, subprocess, sys, threading, time, urllib.request, statistics as st

BIN = os.path.expanduser("~/llama-v0.4.0")
OUT = os.path.expanduser("~/rushuna-july-rows-remeasure-2026-09-28")
M35 = os.path.expanduser("~/bench-models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf")
M14 = os.path.expanduser("~/bench-models/Qwen_Qwen3-14B-Q4_K_M.gguf")
ENV = dict(os.environ, LD_LIBRARY_PATH=BIN)
PORT = 8099
CONFIGS = [
    ("35b-ncmoe32", M35, ["-ngl", "99", "-ncmoe", "32", "-fa", "1", "-p", "512", "-n", "128", "-d", "0"]),
    ("35b-ncmoe20", M35, ["-ngl", "99", "-ncmoe", "20", "-fa", "1", "-p", "512", "-n", "128", "-d", "0"]),
    ("35b-ncmoe24", M35, ["-ngl", "99", "-ncmoe", "24", "-fa", "1", "-p", "512", "-n", "128", "-d", "0,4096,8192"]),
    ("14b-ngl41",   M14, ["-ngl", "41", "-p", "512", "-n", "128", "-d", "0"]),
    ("14b-ngl20",   M14, ["-ngl", "20", "-p", "512", "-n", "128", "-d", "0"]),
    ("14b-ngl0",    M14, ["-ngl", "0",  "-p", "512", "-n", "128", "-d", "0"]),
]
REPS = 3
os.makedirs(OUT, exist_ok=True)

def log(s):
    line = f"{time.strftime('%H:%M:%S')} {s}"; print(line, flush=True)
    open(os.path.join(OUT, "run.log"), "a").write(line + "\n")

def gpu_mib():
    return int(subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout.split()[0])

class PeakVram:
    def __init__(self): self.peak = 0; self.stop = False; self.t = threading.Thread(target=self.run, daemon=True)
    def run(self):
        while not self.stop:
            try: self.peak = max(self.peak, gpu_mib())
            except Exception: pass
            time.sleep(0.5)
    def __enter__(self): self.t.start(); return self
    def __exit__(self, *a): self.stop = True; self.t.join()

def bench(name, model, flags, tag):
    cmd = [f"{BIN}/llama-bench", "-m", model] + flags + ["-r", "3", "-o", "json"]
    t0 = time.time()
    with PeakVram() as pv:
        q = subprocess.run(cmd, capture_output=True, text=True, env=ENV)
    el = time.time() - t0
    json.dump({"cmd": cmd, "rc": q.returncode, "stdout": q.stdout, "stderr_tail": q.stderr[-4000:], "peak_vram_mib": pv.peak, "elapsed_s": round(el, 1)},
              open(os.path.join(OUT, f"raw-{tag}.json"), "w"), indent=1)
    if q.returncode != 0:
        log(f"  {tag} FAILED rc={q.returncode} ({el:.0f}s): {q.stderr[-300:].strip()}"); return None
    rows = [{"test": "pp" if r["n_prompt"] else "tg", "n": r["n_prompt"] or r["n_gen"], "depth": r.get("n_depth", 0),
             "avg_ts": r["avg_ts"], "stddev_ts": r["stddev_ts"], "flash_attn": r.get("flash_attn"), "n_threads": r.get("n_threads"),
             "n_gpu_layers": r.get("n_gpu_layers"), "build_commit": r.get("build_commit")} for r in json.loads(q.stdout)]
    log(f"  {tag} ({el:.0f}s) peak {pv.peak} MiB: " + "  ".join(f"{o['test']}{o['n']}@d{o['depth']} {o['avg_ts']:.2f}±{o['stddev_ts']:.2f}" for o in rows))
    return {"tag": tag, "rows": rows, "peak_vram_mib": pv.peak, "elapsed_s": round(el, 1)}

def post(path, payload, timeout=1800):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())

def server_test(ncmoe, ctx):
    tag = f"server-ncmoe{ncmoe}-c{ctx}"
    logf = open(os.path.join(OUT, f"{tag}.log"), "w")
    cmd = [f"{BIN}/llama-server", "-m", M35, "-ngl", "99", "-ncmoe", str(ncmoe), "-fa", "on", "-c", str(ctx), "-np", "1",
           "--host", "127.0.0.1", "--port", str(PORT)]
    rec = {"ncmoe": ncmoe, "ctx": ctx, "cmd": cmd}
    with PeakVram() as pv:
        p = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT, env=ENV)
        t0 = time.time(); loaded = False
        while time.time() - t0 < 240:
            if p.poll() is not None: break
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2) as r:
                    if b"ok" in r.read(): loaded = True; break
            except Exception: pass
            time.sleep(0.5)
        rec["loaded"] = loaded; rec["vram_after_load_mib"] = gpu_mib() if loaded else None
        if loaded:
            base = open(os.path.join(OUT, "prompt-2k.txt")).read()
            toks = post("/tokenize", {"content": base})["tokens"]
            want = ctx - 256
            ids = (toks * (want // len(toks) + 1))[:want]
            try:
                r = post("/completion", {"prompt": ids, "n_predict": 128, "temperature": 0, "cache_prompt": False})
                t = r.get("timings", {})
                rec.update({"served": (t.get("predicted_n") or 0) > 0, "prompt_n": t.get("prompt_n"), "predicted_n": t.get("predicted_n"),
                            "prompt_tps": t.get("prompt_per_second"), "decode_tps": t.get("predicted_per_second")})
            except Exception as e:
                rec.update({"served": False, "error": repr(e)[:300]})
            rec["server_alive_after"] = p.poll() is None
        else:
            rec["served"] = False; rec["exit_code"] = p.poll()
        p.send_signal(2)
        try: p.wait(timeout=30)
        except subprocess.TimeoutExpired: p.kill(); p.wait()
    logf.close()
    txt = open(os.path.join(OUT, f"{tag}.log")).read()
    rec["oom_in_log"] = any(k in txt for k in ("out of memory", "cudaMalloc failed", "failed to allocate"))
    rec["peak_vram_mib"] = pv.peak
    log(f"  {tag}: loaded={rec['loaded']} served={rec['served']} prompt_n={rec.get('prompt_n')} decode={rec.get('decode_tps')} "
        f"peak {pv.peak} MiB oom_in_log={rec['oom_in_log']} {rec.get('error','')}")
    time.sleep(3)
    return rec

def main():
    only = sys.argv[1:]  # optional subset of config names or "server"
    log(f"start  card {gpu_mib()} MiB  ollama={subprocess.run(['systemctl','is-active','ollama'],capture_output=True,text=True).stdout.strip()}")
    R = {"configs": {}, "server": []}
    if os.path.exists(os.path.join(OUT, "results.json")): R = json.load(open(os.path.join(OUT, "results.json")))
    for name, model, flags in CONFIGS:
        if only and name not in only: continue
        meas = []
        for rep in range(1, REPS + 1):
            bench(name, model, flags, f"prime-{name}-rep{rep}")
            m = bench(name, model, flags, f"{name}-rep{rep}")
            if m: meas.append(m)
        summ = {}
        for key in sorted({(o["test"], o["depth"]) for m in meas for o in m["rows"]}):
            v = [o["avg_ts"] for m in meas for o in m["rows"] if (o["test"], o["depth"]) == key]
            summ[f"{key[0]}@d{key[1]}"] = {"mean": round(st.mean(v), 2), "min": round(min(v), 2), "max": round(max(v), 2), "reps": [round(x, 2) for x in v]}
        R["configs"][name] = {"flags": flags, "summary": summ, "peak_vram_mib": max([m["peak_vram_mib"] for m in meas] or [0]),
                              "resolved": meas[0]["rows"][0] if meas else None}
        log(f"  SUMMARY {name}: " + "  ".join(f"{k} {v['mean']} [{v['min']}..{v['max']}]" for k, v in summ.items()) + f"  peak {R['configs'][name]['peak_vram_mib']} MiB")
        json.dump(R, open(os.path.join(OUT, "results.json"), "w"), indent=1)
    if not only or "server" in only:
        R["server"] = [server_test(n, c) for n in (20, 24) for c in (8192, 16384)]
        json.dump(R, open(os.path.join(OUT, "results.json"), "w"), indent=1)
    log("done")

if __name__ == "__main__":
    main()
