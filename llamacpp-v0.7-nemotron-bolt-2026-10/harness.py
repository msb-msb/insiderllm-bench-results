#!/usr/bin/env python3
"""llama.cpp v0.7.0 on Tamanna: build A/B, --moe-cache-mib, Nemotron 3.5 Bolt 24GB, run 2026-11-03.

Runs docs/candidates/llamacpp-v0.7-nemotron-bolt-2026-10.md as locked at 9cc92ae5 (prereg sha256 3857cbb2...).
  python3 harness.py A      # build A/B, llama-bench, both builds
  python3 harness.py B      # --moe-cache-mib, llama-server, am17an nine prompts
  python3 harness.py C      # Bolt fit (C1), allocation (C2), depth (C3), sanity (C4)
  python3 harness.py serve TAG MODEL   # Q server for run_quality.py from Miu; Ctrl-C / SIGTERM stops it
Sampler and summaries are the 10-09 ramspeed.py / 09-22 dflash_bench.py ones, with three additions the prereg asks
for: the esp32 guard (empty compute-apps list and no `pgrep -af esp32-llm` before, during at 1 s, and after every
invocation; a tainted cell is discarded and re-run), memory.total, and board-level power/clocks for every arm.
"""
import json, os, subprocess, sys, time, threading, statistics as st, glob, signal, hashlib, ast
from urllib import request

OUT = os.path.expanduser("~/llamacpp-v0.7-nemotron-bolt-2026-10")
B04 = os.path.expanduser("~/llama-v0.4.0/build/bin")
B07 = os.path.expanduser("~/llama-v0.7.0/build/bin")
QWEN = os.path.expanduser("~/bench-models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf")
QWEN_Q0 = os.path.expanduser("~/bench-models/qwen3.6-35b-a3b-Q4_K_M.gguf")
BOLT = os.path.expanduser("~/bench-models/nemotron-3.5-bolt-24gb/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB.gguf")
PORT = 8081
URL = f"http://127.0.0.1:{PORT}"
SMI = ["timestamp", "pcie.link.gen.current", "pcie.link.width.current", "temperature.gpu", "clocks.sm", "clocks.mem",
       "clocks.gr", "power.draw", "utilization.gpu", "memory.used", "memory.total", "pstate", "fan.speed",
       "clocks_event_reasons.active"]
NVME = "nvme0n1"


def log(s):
    line = time.strftime("%H:%M:%S ") + s
    print(line, flush=True)
    with open(os.path.join(OUT, "run.log"), "a") as f: f.write(line + "\n")


def nvme_read_bytes():
    for l in open("/proc/diskstats"):
        p = l.split()
        if p[2] == NVME: return int(p[5]) * 512
    return 0


def mem_available_mib():
    for l in open("/proc/meminfo"):
        if l.startswith("MemAvailable:"): return int(l.split()[1]) // 1024


def tctl_path():
    for h in glob.glob("/sys/class/hwmon/hwmon*"):
        try:
            if open(h + "/name").read().strip() == "k10temp": return h + "/temp1_input"
        except OSError: pass


TCTL = tctl_path()


def cpu_mhz_mean():
    v = []
    for p in glob.glob("/sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq"):
        try: v.append(int(open(p).read()) / 1000)
        except OSError: pass
    return round(st.mean(v)) if v else None


def guard():
    """The prereg's two checks. Returns a list of offenders (empty = clear). Our own processes never match."""
    bad = []
    apps = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader"],
                          capture_output=True, text=True).stdout.strip()
    pg = subprocess.run(["pgrep", "-af", "esp32-llm"], capture_output=True, text=True).stdout.strip()
    if pg: bad.append("esp32: " + pg.replace("\n", " | "))
    return bad, apps


def guard_before():
    bad, apps = guard()
    if apps: bad.append("compute-apps: " + apps.replace("\n", " | "))
    return bad


class Sampler:
    """nvidia-smi at 1 s to CSV; CPU Tctl, mean core MHz and the esp32 guard at 1 s in a thread.
    Compute-apps is not part of the in-run guard: our own llama process is on that list while it runs."""
    def __init__(self, path, own_pids=()):
        self.f = open(path, "w"); self.f.write(",".join(SMI) + "\n"); self.f.flush()
        self.cpu, self.mhz, self.taint, self.stop = [], [], [], False
        self.own = set(own_pids)
        self.p = subprocess.Popen(["nvidia-smi", "--query-gpu=" + ",".join(SMI), "--format=csv,noheader,nounits", "-lms", "1000"],
                                  stdout=self.f, stderr=subprocess.DEVNULL)
        self.t = threading.Thread(target=self._loop, daemon=True); self.t.start()

    def _loop(self):
        while not self.stop:
            if TCTL: self.cpu.append(int(open(TCTL).read()) / 1000)
            m = cpu_mhz_mean(); m and self.mhz.append(m)
            pg = subprocess.run(["pgrep", "-af", "esp32-llm"], capture_output=True, text=True).stdout.strip()
            if pg: self.taint.append(time.strftime("%H:%M:%S ") + pg)
            time.sleep(1)

    def close(self):
        self.stop = True; self.t.join(); self.p.send_signal(signal.SIGINT)
        try: self.p.wait(timeout=5)
        except subprocess.TimeoutExpired: self.p.kill(); self.p.wait()
        self.f.close()


def parse_tel(path):
    rows = []
    with open(path) as f:
        next(f)
        for l in f:
            p = [x.strip() for x in l.split(",")]
            if len(p) != len(SMI): continue
            try:
                rows.append({"gen": p[1], "width": p[2], "temp": float(p[3]), "sm": float(p[4]), "mem_clock": float(p[5]),
                             "gr": float(p[6]), "power": float(p[7]), "util": float(p[8]), "vram": float(p[9]),
                             "total": float(p[10]), "pstate": p[11], "fan": p[12], "reasons": p[13]})
            except ValueError: pass
    return rows


def summ_tel(rows):
    if not rows: return {}
    load = [r for r in rows if r["util"] >= 50] or [r for r in rows if r["util"] > 0] or rows
    def s(v): return {"mean": round(st.mean(v), 1), "median": st.median(v), "min": min(v), "max": max(v)}
    return {"samples": len(rows), "samples_under_load": len(load), "peak_vram_mib": max(r["vram"] for r in rows),
            "memory_total_mib": rows[0]["total"], "pcie_gen_under_load": sorted({r["gen"] for r in load}),
            "pcie_width_under_load": sorted({r["width"] for r in load}), "gpu_temp_max": max(r["temp"] for r in rows),
            "power_w": s([r["power"] for r in load]), "sm_clock_mhz": s([r["sm"] for r in load]),
            "mem_clock_mhz": s([r["mem_clock"] for r in load]), "pstates_under_load": sorted({r["pstate"] for r in load}),
            "reasons_under_load": sorted({r["reasons"] for r in load})}


def wait_clear(name):
    """Before an invocation: wait (never kill) until the guard is clear; log every wait."""
    n = 0
    while True:
        bad = guard_before()
        if not bad: return
        if n % 30 == 0: log(f"  GUARD holds {name}: {bad}")
        n += 1; time.sleep(10)


def invoke(name, fn):
    """Run fn() under the sampler and the guard. Re-run the cell if an esp32 process appeared at any point."""
    for attempt in range(1, 6):
        wait_clear(name)
        tpath = os.path.join(OUT, f"telemetry-{name}.csv")
        ma0, rd0 = mem_available_mib(), nvme_read_bytes()
        s = Sampler(tpath); time.sleep(1.2)
        t0 = time.time()
        try: res = fn()
        finally:
            el = time.time() - t0
            time.sleep(1.2); s.close()
        bad_after, _ = guard()
        taint = s.taint + bad_after
        rd = nvme_read_bytes() - rd0; ma1 = mem_available_mib()
        meta = {"name": name, "attempt": attempt, "started": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(t0)),
                "elapsed_s": round(el, 1), "nvme_read_mib": round(rd / 2**20, 1), "mem_available_mib": [ma0, ma1],
                "cpu_tctl_max": max(s.cpu) if s.cpu else None, "cpu_tctl_mean": round(st.mean(s.cpu), 1) if s.cpu else None,
                "cpu_mhz_mean": round(st.mean(s.mhz)) if s.mhz else None, "telemetry": summ_tel(parse_tel(tpath)),
                "esp32_taint": taint}
        if taint:
            log(f"  TAINTED {name} attempt {attempt}: {taint[:3]} -> discarded, re-run")
            os.rename(tpath, tpath.replace(".csv", f".tainted{attempt}.csv"))
            continue
        return res, meta
    raise SystemExit(f"{name}: tainted 5 times, stopping")


def tel_line(m):
    t = m["telemetry"]
    if not t: return ""
    return (f"vram {t['peak_vram_mib']:.0f}/{t['memory_total_mib']:.0f}  pwr {t['power_w']['mean']:.0f}W (max {t['power_w']['max']:.0f})  "
            f"sm {t['sm_clock_mhz']['median']:.0f}MHz  mem {t['mem_clock_mhz']['median']:.0f}  {t['pstates_under_load']}  "
            f"pcie {t['pcie_gen_under_load']}x{t['pcie_width_under_load']}  gpu {t['gpu_temp_max']:.0f}C  cpu {m['cpu_tctl_max']}C "
            f"{m['cpu_mhz_mean']}MHz  nvme {m['nvme_read_mib']}MiB  avail {m['mem_available_mib'][0]}->{m['mem_available_mib'][1]}  ({m['elapsed_s']:.0f}s)")


# ---------- llama-bench ----------

def bench(binary_dir, model, args, name):
    cmd = [os.path.join(binary_dir, "llama-bench"), "-m", model] + args + ["-o", "json"]
    env = dict(os.environ); env["LD_LIBRARY_PATH"] = binary_dir
    def fn(): return subprocess.run(cmd, capture_output=True, text=True, env=env)
    p, meta = invoke(name, fn)
    rec = {"cmd": cmd, "rc": p.returncode, "meta": meta, "stderr_tail": p.stderr[-6000:]}
    if p.returncode == 0:
        rec["stdout"] = json.loads(p.stdout)
        rec["rows"] = [{"kind": "pp" if r["n_prompt"] > 0 else "tg", "n_prompt": r["n_prompt"], "n_gen": r["n_gen"],
                        "depth": r.get("n_depth", 0), "avg_ts": r["avg_ts"], "stddev_ts": r["stddev_ts"],
                        "samples": r.get("samples_ts", []), "build_commit": r.get("build_commit"),
                        "type_k": r.get("type_k"), "type_v": r.get("type_v")} for r in rec["stdout"]]
    json.dump(rec, open(os.path.join(OUT, f"raw-{name}.json"), "w"), indent=1)
    if p.returncode != 0:
        log(f"  FAILED {name} rc={p.returncode}: {p.stderr[-600:]}")
        return rec
    cells = "  ".join(f"{x['kind']}{x['n_prompt'] or x['n_gen']}@d{x['depth']} {x['avg_ts']:.2f}" for x in rec["rows"])
    log(f"  {name:28s} {cells}")
    log(f"    {tel_line(meta)}")
    return rec


def arm_A():
    args = ["-ngl", "99", "-ncmoe", "0", "-fa", "1", "-p", "512", "-n", "128", "-d", "0,4096", "-r", "5", "-t", "8", "-lm", "mmap"]
    log("arm A start: llama-bench " + " ".join(args) + "  order (v04 prime, v04, v07 prime, v07) x 3")
    res = []
    for rep in (1, 2, 3):
        for b, d in (("v04", B04), ("v07", B07)):
            bench(d, QWEN, args, f"prime-A-{b}-rep{rep}")
            r = bench(d, QWEN, args, f"A-{b}-rep{rep}"); r["build"] = b; r["rep"] = rep; res.append(r)
    ref = {("tg", 0): 162.90, ("tg", 4096): 160.69, ("pp", 0): 3768.8, ("pp", 4096): 3605.0}
    summ = {}
    for b in ("v04", "v07"):
        for (k, dep) in ref:
            v = [x["avg_ts"] for r in res if r["build"] == b and r["rc"] == 0 for x in r["rows"] if x["kind"] == k and x["depth"] == dep]
            if v: summ[f"{b}|{k}|{dep}"] = {"mean": st.mean(v), "min": min(v), "max": max(v), "reps": v}
    log("arm A drift check vs 10-09 (v0.4.0 cells, >2% is reported first):")
    for (k, dep), r0 in ref.items():
        c = summ.get(f"v04|{k}|{dep}")
        if c:
            for i, v in enumerate(c["reps"], 1):
                dv = (v / r0 - 1) * 100
                log(f"  v04 rep{i} {k} d={dep}: {v:.2f} vs {r0} ({dv:+.2f}%){'  DRIFT >2%' if abs(dv) > 2 else ''}")
    for (k, dep) in ref:
        a, b = summ.get(f"v04|{k}|{dep}"), summ.get(f"v07|{k}|{dep}")
        if a and b:
            ov = not (b["min"] > a["max"] or a["min"] > b["max"])
            log(f"  {k} d={dep}: v04 {a['mean']:.2f} [{a['min']:.2f}..{a['max']:.2f}]  v07 {b['mean']:.2f} [{b['min']:.2f}..{b['max']:.2f}]  "
                f"ratio {b['mean']/a['mean']:.4f}  {'within noise' if ov else 'MOVED'}")
    json.dump({"summary": summ, "results": [{k: r[k] for k in ("build", "rep", "rc", "rows", "meta") if k in r} for r in res]},
              open(os.path.join(OUT, "A-summary.json"), "w"), indent=1)
    log("arm A done")


# ---------- llama-server ----------

def post(path, payload, timeout=1800):
    req = request.Request(URL + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())


def wait_health(proc, timeout=600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if proc.poll() is not None: return False
        try:
            with request.urlopen(URL + "/health", timeout=2) as r:
                if b"ok" in r.read(): return True
        except Exception: pass
        time.sleep(0.5)
    return False


def smi_q(q):
    return subprocess.run(["nvidia-smi", f"--query-gpu={q}", "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout.strip()


def server_session(binary_dir, args, name, body):
    """Fresh llama-server, health-wait, body(ctx) for the requests, SIGINT. Whole lifetime under the sampler."""
    cmd = [os.path.join(binary_dir, "llama-server")] + args
    env = dict(os.environ); env["LD_LIBRARY_PATH"] = binary_dir
    lpath = os.path.join(OUT, f"server-{name}.log")
    def fn():
        slog = open(lpath, "w")
        t0 = time.time()
        proc = subprocess.Popen(cmd, stdout=slog, stderr=subprocess.STDOUT, env=env)
        ok = wait_health(proc); t_load = time.time() - t0
        out = {"cmd": cmd, "load_ok": ok, "load_s": round(t_load, 1), "rc_at_load": proc.poll()}
        if ok:
            out["vram_after_load_mib"] = int(smi_q("memory.used"))
            try: out.update(body())
            except Exception as e: out["error"] = repr(e); out["rc_after_error"] = proc.poll()
        proc.send_signal(signal.SIGINT)
        try: proc.wait(timeout=60)
        except subprocess.TimeoutExpired: proc.kill(); proc.wait()
        out["rc"] = proc.returncode; slog.close()
        return out
    out, meta = invoke(name, fn)
    out["meta"] = meta
    json.dump(out, open(os.path.join(OUT, f"raw-{name}.json"), "w"), indent=1)
    return out


_src = open(os.path.expanduser("~/am17an_bench.py")).read()
PROMPTS = ast.literal_eval(next(n for n in ast.parse(_src).body if isinstance(n, ast.Assign) and n.targets[0].id == "PROMPTS").value)
GEN_B = {"n_predict": 192, "temperature": 0.0, "seed": 42, "cache_prompt": False, "stream": False}


def nine():
    rs = []
    for p in PROMPTS:
        tq = time.time(); r = post("/completion", dict(GEN_B, prompt=p["prompt"])); wall = time.time() - tq
        t = r.get("timings", {}) or {}
        rs.append({"name": p["name"], "wall_s": round(wall, 3), "prompt_n": t.get("prompt_n"), "prompt_ms": t.get("prompt_ms"),
                   "prompt_per_second": t.get("prompt_per_second"), "predicted_n": t.get("predicted_n"),
                   "predicted_ms": t.get("predicted_ms"), "predicted_per_second": t.get("predicted_per_second"),
                   "content_sha_head": hashlib.sha256(r.get("content", "").encode()).hexdigest()[:12], "stop_type": r.get("stop_type")})
    tp = sum(x["predicted_n"] or 0 for x in rs); tms = sum(x["predicted_ms"] or 0 for x in rs)
    pn = sum(x["prompt_n"] or 0 for x in rs); pms = sum(x["prompt_ms"] or 0 for x in rs)
    return {"results": rs, "aggregate": {"gen_tok_s": round(tp / (tms / 1000), 2) if tms else None, "total_predicted": tp,
            "prompt_tok_s": round(pn / (pms / 1000), 2) if pms else None, "total_prompt": pn,
            "mean_per_prompt_tok_s": round(st.mean(x["predicted_per_second"] for x in rs), 2)}}


def expert_bytes(model):
    """Sum of n_bytes over *_exps tensors (ffn_down/gate/up_exps), and over all tensors. Tamanna's system python has no
    numpy, so this was read 2026-11-03 with ~/llama-v0.7.0/gguf-py GGUFReader under ~/voice-01/envs/train/bin/python
    from the hash-verified file (ac0e2c11...) and is fixed here."""
    assert model == QWEN
    return 19568525312, 22123538944


def arm_B():
    common = ["-m", QWEN, "-ngl", "99", "-ncmoe", "20", "-fa", "on", "-c", "8192", "-np", "1", "--fit", "off", "-lm", "mmap",
              "-t", "8", "--port", str(PORT)]
    exp, tot = expert_bytes(QWEN)
    log(f"arm B start: common {' '.join(common)}")
    log(f"  expert tensor bytes (*_exps) {exp} = {exp/2**20:.0f} MiB of {tot/2**20:.0f} MiB; 10% = {exp/2**20/10:.0f} MiB")
    cfg = {"B1": (B04, common), "B2": (B07, common)}
    res, primes = [], []
    def one(c, name):
        d, a = cfg[c]
        r = server_session(d, a, name, nine)
        if not r.get("load_ok") or "error" in r:
            log(f"  FAILED {name}: load_ok={r.get('load_ok')} err={r.get('error')} rc={r.get('rc')}"); return r
        ag = r["aggregate"]
        log(f"  {name:16s} gen {ag['gen_tok_s']:7.2f}  prompt {ag['prompt_tok_s']:8.2f}  per-prompt {ag['mean_per_prompt_tok_s']:.2f}  load {r['load_s']}s")
        log(f"    {tel_line(r['meta'])}")
        return r
    for c in ("B1", "B2"): primes.append(dict(one(c, f"prime-{c}"), config=c))
    peak = primes[1]["meta"]["telemetry"]["peak_vram_mib"]; total = primes[1]["meta"]["telemetry"]["memory_total_mib"]
    free = total - peak - 1024; tenpct = exp / 2**20 / 10
    M = int(min(free, tenpct))
    arith = {"b2_prime_peak_vram_mib": peak, "memory_total_mib": total, "margin_mib": 1024, "free_mib": free,
             "expert_bytes": exp, "ten_pct_expert_mib": round(tenpct, 1), "M": M}
    log(f"  B3 size rule (from the B2 priming run's peak, before any B3 run): free = {total:.0f} - {peak:.0f} - 1024 = {free:.0f} MiB; "
        f"10% of experts = {tenpct:.0f} MiB; M = min = {M} MiB")
    json.dump(arith, open(os.path.join(OUT, "B3-size-rule.json"), "w"), indent=1)
    if free < 512:
        log("  free < 512 MiB: prereg says B1/B2/B3 at -ncmoe 24. STOPPING arm B here for a human decision.")
        return
    cfg["B3"] = (B07, common + ["--moe-cache-mib", str(M)])
    primes.append(dict(one("B3", "prime-B3"), config="B3"))
    for rep in (1, 2, 3):
        for c in ("B1", "B2", "B3"):
            r = one(c, f"{c}-rep{rep}"); r["config"] = c; r["rep"] = rep; res.append(r)
    summ = {"size_rule": arith}
    for c in ("B1", "B2", "B3"):
        rs = [r for r in res if r["config"] == c and "aggregate" in r]
        if not rs: continue
        for k in ("gen_tok_s", "prompt_tok_s"):
            v = [r["aggregate"][k] for r in rs]
            summ[f"{c}|{k}"] = {"mean": round(st.mean(v), 2), "min": min(v), "max": max(v), "reps": v}
        log(f"  {c}: gen {summ[f'{c}|gen_tok_s']['mean']:.2f} [{summ[f'{c}|gen_tok_s']['min']:.2f}..{summ[f'{c}|gen_tok_s']['max']:.2f}]  "
            f"prompt {summ[f'{c}|prompt_tok_s']['mean']:.1f} [{summ[f'{c}|prompt_tok_s']['min']:.1f}..{summ[f'{c}|prompt_tok_s']['max']:.1f}]")
    json.dump({"summary": summ, "results": res, "primes": primes}, open(os.path.join(OUT, "B-summary.json"), "w"), indent=1)
    log("arm B done")


# ---------- arm C ----------

def c_prompt_tokens():
    """Bolt tokens for the 10-09 Strata source cut, trimmed to exactly 4,096 through the server's own /tokenize."""
    text = open(os.path.join(OUT, "strata-prompt-32512.txt")).read()
    toks = post("/tokenize", {"content": text, "add_special": False})["tokens"][:4096]
    det = post("/detokenize", {"tokens": toks})["content"]
    return toks, det


def arm_C():
    base = lambda ctx, k: ["-m", BOLT, "-ngl", "99", "-fa", "on", "-c", str(ctx), "-np", "1", "-ctk", k, "-ctv", k,
                           "--fit", "off", "-lm", "mmap", "-t", "8", "--port", str(PORT)]
    log("arm C start (v0.7.0 only, text only, no mmproj, no drafter)")
    cells, loaded = {}, {}
    prompt_rec = {}
    for k in ("f16", "q8_0"):
        for ctx in (32768, 131072):
            name = f"C1C2-{k}-{ctx}"
            def body():
                toks, det = c_prompt_tokens()
                if not prompt_rec:
                    prompt_rec.update({"n_tokens": len(toks), "tokens_sha256": hashlib.sha256(json.dumps(toks).encode()).hexdigest(),
                                       "text_sha256": hashlib.sha256(det.encode()).hexdigest()})
                    open(os.path.join(OUT, "C2-prompt-4096.txt"), "w").write(det)
                    json.dump(toks, open(os.path.join(OUT, "C2-prompt-4096.tokens.json"), "w"))
                g = {"prompt": toks, "n_predict": 128, "ignore_eos": True, "temperature": 0.0, "cache_prompt": False, "stream": False}
                reqs = []
                pk, done = [], threading.Event()
                def poll():
                    while not done.is_set(): pk.append(int(smi_q("memory.used"))); time.sleep(0.2)
                th = threading.Thread(target=poll, daemon=True); th.start()
                for i in range(4):
                    r = post("/completion", g); t = r.get("timings", {})
                    if i == 0:
                        done.set(); th.join(); pk.append(int(smi_q("memory.used")))
                        peak_after_first = max(pk)
                    reqs.append({"i": i, "discard": i == 0, "prompt_n": t.get("prompt_n"), "prompt_per_second": t.get("prompt_per_second"),
                                 "predicted_n": t.get("predicted_n"), "predicted_per_second": t.get("predicted_per_second"),
                                 "content_head": r.get("content", "")[:200]})
                return {"requests": reqs, "vram_after_first_request_mib": peak_after_first}
            r = server_session(B07, base(ctx, k), name, body)
            cells[name] = r
            if not r.get("load_ok") or "error" in r:
                log(f"  {name}: LOAD/RUN FAILED load_ok={r.get('load_ok')} rc_at_load={r.get('rc_at_load')} err={r.get('error')} rc={r.get('rc')}")
                loaded[(k, ctx)] = False
                continue
            loaded[(k, ctx)] = True
            m = [x for x in r["requests"] if not x["discard"]]
            dec = st.mean(x["predicted_per_second"] for x in m); pp = st.mean(x["prompt_per_second"] for x in m)
            total = r["meta"]["telemetry"]["memory_total_mib"]
            r["headroom_after_first_mib"] = total - r["vram_after_first_request_mib"]
            r["headroom_peak_sampler_mib"] = total - r["meta"]["telemetry"]["peak_vram_mib"]
            log(f"  {name}: loaded  decode {dec:.2f} [{min(x['predicted_per_second'] for x in m):.2f}..{max(x['predicted_per_second'] for x in m):.2f}]  "
                f"pp4096 {pp:.1f}  prompt_n {[x['prompt_n'] for x in m]}  used after 1st req {r['vram_after_first_request_mib']} -> headroom "
                f"{r['headroom_after_first_mib']:.0f} MiB (sampler peak {r['meta']['telemetry']['peak_vram_mib']:.0f} -> {r['headroom_peak_sampler_mib']:.0f})")
            log(f"    {tel_line(r['meta'])}")
            json.dump(r, open(os.path.join(OUT, f"raw-{name}.json"), "w"), indent=1)
    json.dump(prompt_rec, open(os.path.join(OUT, "C2-prompt.json"), "w"), indent=1)
    log(f"  C2 prompt: {prompt_rec}")
    # C3
    c3 = {}
    for k in ("f16", "q8_0"):
        if not (loaded.get((k, 32768)) or loaded.get((k, 131072))):
            log(f"  C3 {k}: not run (no server load at either context)"); continue
        c3[f"{k}-short"] = bench(B07, BOLT, ["-ngl", "99", "-fa", "1", "-ctk", k, "-ctv", k, "-p", "4096", "-n", "128", "-d", "0,4096",
                                             "-r", "3", "-t", "8", "-lm", "mmap"], f"C3-{k}-short")
        if loaded.get((k, 131072)):
            c3[f"{k}-deep"] = bench(B07, BOLT, ["-ngl", "99", "-fa", "1", "-ctk", k, "-ctv", k, "-p", "0", "-n", "128", "-d", "102400",
                                                "-r", "1", "-t", "8", "-lm", "mmap"], f"C3-{k}-deep")
        else:
            log(f"  C3 {k} d=102400: NOT RUN (131072 cell did not load)")
    # C4
    def c4body():
        outs = []
        for p in PROMPTS[:3]:
            r = post("/completion", dict(GEN_B, prompt=p["prompt"]))
            outs.append({"name": p["name"], "content": r.get("content"), "timings": r.get("timings"), "stop_type": r.get("stop_type")})
        return {"outputs": outs}
    if loaded.get(("f16", 32768)):
        r = server_session(B07, base(32768, "f16"), "C4-sanity", c4body)
        for o in r.get("outputs", []):
            log(f"  C4 {o['name']}: {o['timings'].get('predicted_n')} tok @ {o['timings'].get('predicted_per_second'):.1f}  "
                f"head: {o['content'][:120]!r}")
    json.dump({"loaded": {f"{k}|{c}": v for (k, c), v in loaded.items()}, "prompt": prompt_rec},
              open(os.path.join(OUT, "C-summary.json"), "w"), indent=1)
    log("arm C done")


# ---------- Q server ----------

def serve(tag, model):
    """Q1/Q0 server, the prereg's command plus --host 0.0.0.0 so run_quality.py reaches it from Miu (as the 10-07 serve.sh).
    Lives until SIGTERM; the sampler and guard cover its whole life."""
    mp = {"bolt": BOLT, "q0": QWEN_Q0}[model]
    args = ["-m", mp, "-ngl", "99", "-fa", "on", "-c", "4096", "--jinja", "--fit", "off", "-lm", "mmap", "--host", "0.0.0.0", "--port", str(PORT)]
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *a: stop.set())
    def body():
        log(f"  serve {tag}: ready")
        open(os.path.join(OUT, f"serve-{tag}.ready"), "w").write("ok")
        while not stop.is_set(): time.sleep(1)
        return {}
    r = server_session(B07, args, f"Q-{tag}", body)
    log(f"  serve {tag} stopped: load_ok {r.get('load_ok')}  {tel_line(r['meta'])}")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    a = sys.argv[1]
    if a == "A": arm_A()
    elif a == "B": arm_B()
    elif a == "C": arm_C()
    elif a == "serve": serve(sys.argv[2], sys.argv[3])
