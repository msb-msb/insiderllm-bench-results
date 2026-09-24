#!/usr/bin/env python3
"""z-lab Qwen3.6-35B-A3B-DFlash drafter vs the published negative spec-decode result, 2026-09-22.

PRE-REGISTERED before the first measured run (smoke test excepted; see README).

Published negative (benchmarks.json rushuna-qwen36-35b-a3b-udq4km-specdec-qwen35-08b): Qwen 3.5 0.8B as
a conventional drafter took the 35B-A3B from 38.9 to 11 tok/s on the 3060 at -ncmoe 24, a 3.5x regression
at 65% acceptance. The marker's own success condition: either a purpose-built drafter OVERTURNS the negative
(drafter faster than no drafter on the same box, same file, same prompts) or it REPRODUCES it (drafter slower).

Box: Tamanna (RTX 3090, Ryzen 7 5700X, 31 GiB DDR4, PCIe slot at whatever gen the BIOS is set to; the 1 s
nvidia-smi sampler records the gen actually negotiated under load and the README reports it as found).
Build: llama.cpp v0.4.0 (5266f24), CUDA 12.4, gcc-13, sm_86, GGML_NATIVE=OFF — the build of the 09-21 rows.
Target: ~/bench-models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf, sha256 ac0e2c11...31a61, the same file as every
published 35B-A3B row (Miu 08-28, Rushuna, Tamanna 09-21). Fully resident: -ngl 99, no -ncmoe.
Drafter: z-lab/Qwen3.6-35B-A3B-DFlash at HF revision f181eece (weights from the 2026-06-19 Modal retrain;
model.safetensors sha256 1fb90ef5...72b7 verified against the LFS record), converted with v0.4.0's own
convert_hf_to_gguf.py (--target-model-dir = the Qwen/Qwen3.6-35B-A3B HF tree for the tokenizer) to F16 and
quantized to Q8_0 with v0.4.0's llama-quantize on Tamanna. The starskyzheng GGUF was NOT used: it predates
the June retrain.

Prompt set: am17an's nine-prompt gist exactly as published in docs/bench-results/mtp-2026-05-06 and the
DFlash-vs-MTP article — /completion, n_predict 192, temperature 0, seed 42, cache_prompt false. The
published 3060 negative never had its harness published, so this is the site's published spec-decode
prompt set, not that run's.

Design: two configs, A = baseline (no drafter) and B = drafter (-md, --spec-type draft-dflash,
--spec-draft-n-max 15 = trained block size 16 minus the anchor; llama.cpp clamps anything higher). Each run
is a fresh llama-server (-ngl 99 -fa on -c 8192 -np 1), health-wait, the nine prompts in order, shutdown.
One discarded PRIMING run of each config first (takes the cold NVMe load; kept as raw-prime-*), then three
measured reps ALTERNATING A, B, A, B, A, B on a warm page cache (22 GB target + 0.4 GB draft fit in 31 GiB;
nothing else touches the disk between runs). 1 s nvidia-smi telemetry from before launch to after exit on
every run, the 09-21 sampler.

Primary metric: aggregate generation tok/s over the nine prompts = sum(predicted_n) / sum(predicted_ms)
from the server's own timings, mean of 3 reps, spread = min..max over reps. Secondary: per-prompt
predicted_per_second, acceptance = draft_n_accepted / draft_n (aggregate and per prompt), wall time, VRAM
peak. Resolvability by the 08-28 rule: a gap counts only if it exceeds the larger of the two same-config
rep spreads. OVERTURNED if B > A and resolvable; REPRODUCED if B < A and resolvable; otherwise a null.
Nothing else is read into the run. Any config not written here (F16 draft, -ncmoe, other block sizes) is
a follow-up, not part of this result.
"""
import json, os, subprocess, sys, time, statistics as st, signal
from urllib import request, error

OUT     = os.path.expanduser("~/tamanna-dflash-35b-a3b-2026-09-22")
BIN     = os.path.expanduser("~/llama-v0.4.0/build/bin")
SERVER  = os.path.join(BIN, "llama-server")
TARGET  = os.path.expanduser("~/bench-models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf")
DRAFT   = os.path.expanduser("~/bench-models/Qwen3.6-35B-A3B-DFlash-Q8_0.gguf")
PORT    = 8080
URL     = f"http://127.0.0.1:{PORT}"
COMMON  = ["-m", TARGET, "-ngl", "99", "-fa", "on", "-c", "8192", "-np", "1", "--host", "127.0.0.1", "--port", str(PORT)]
CONFIGS = {
    "baseline": COMMON,
    "dflash":   COMMON + ["-md", DRAFT, "-ngld", "99", "--spec-type", "draft-dflash", "--spec-draft-n-max", "15"],
}
ORDER   = ["baseline", "dflash"]
REPS    = 3
GEN     = {"n_predict": 192, "temperature": 0.0, "seed": 42, "cache_prompt": False, "stream": False}
SMI_FIELDS = ["timestamp", "pcie.link.gen.current", "pcie.link.gen.gpucurrent", "pcie.link.width.current",
              "temperature.gpu", "clocks.sm", "clocks.mem", "power.draw", "utilization.gpu", "memory.used",
              "clocks_event_reasons.active"]

# the published nine, unmodified: lifted from the gist harness by AST so its argparse tail does not run on import
import ast
_src = open(os.path.expanduser("~/am17an_bench.py")).read()
_node = next(n for n in ast.parse(_src).body if isinstance(n, ast.Assign) and n.targets[0].id == "PROMPTS")
PROMPTS = ast.literal_eval(_node.value)

def log(s):
    line = f"{time.strftime('%H:%M:%S')} {s}"
    print(line, flush=True)
    with open(os.path.join(OUT, "run.log"), "a") as f: f.write(line + "\n")

def smi(q):
    return subprocess.run(["nvidia-smi", f"--query-gpu={q}", "--format=csv,noheader,nounits"],
                          capture_output=True, text=True).stdout.strip().split("\n")[0]

def start_sampler(path):
    f = open(path, "w"); f.write(",".join(SMI_FIELDS) + "\n"); f.flush()
    p = subprocess.Popen(["nvidia-smi", "--query-gpu=" + ",".join(SMI_FIELDS), "--format=csv,noheader,nounits", "-lms", "1000"],
                         stdout=f, stderr=subprocess.DEVNULL)
    return p, f

def stop_sampler(p, f):
    p.send_signal(signal.SIGINT)
    try: p.wait(timeout=5)
    except subprocess.TimeoutExpired: p.kill(); p.wait()
    f.close()

def parse_telemetry(path):
    rows = []
    with open(path) as f:
        next(f)
        for line in f:
            parts = [x.strip() for x in line.strip().split(",")]
            if len(parts) < len(SMI_FIELDS): continue
            try:
                rows.append({"ts": parts[0], "pcie_gen": int(parts[1]), "pcie_gen_gpu": int(parts[2]), "pcie_width": int(parts[3]),
                             "temp": int(parts[4]), "sm": int(parts[5]), "mem": int(parts[6]), "power": float(parts[7]),
                             "util": int(parts[8]), "vram": int(parts[9]), "reasons": parts[10]})
            except ValueError:
                continue
    return rows

def summarise_telemetry(rows):
    load = [r for r in rows if r["util"] >= 50]
    if not rows: return {}
    def s(vals): return {"mean": round(st.mean(vals), 1), "median": st.median(vals), "min": min(vals), "max": max(vals)}
    out = {"samples": len(rows), "samples_under_load": len(load), "temp_start": rows[0]["temp"], "temp_end": rows[-1]["temp"],
           "temp_max": max(r["temp"] for r in rows), "vram_peak_mib": max(r["vram"] for r in rows)}
    if load:
        gens = sorted(set(r["pcie_gen"] for r in load))
        out.update({"pcie_gen_under_load": gens, "pcie_gen_under_load_share": {str(g): round(sum(1 for r in load if r["pcie_gen"] == g) / len(load), 3) for g in gens},
                    "pcie_gen_gpu_under_load": sorted(set(r["pcie_gen_gpu"] for r in load)),
                    "pcie_width_under_load": sorted(set(r["pcie_width"] for r in load)),
                    "sm_clock": s([r["sm"] for r in load]), "mem_clock": s([r["mem"] for r in load]),
                    "power": s([r["power"] for r in load]), "temp_under_load": s([r["temp"] for r in load]),
                    "clock_event_reasons_under_load": sorted(set(r["reasons"] for r in load))})
    return out

def post(path, payload, timeout=300):
    req = request.Request(URL + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())

def wait_health(proc, timeout=180):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if proc.poll() is not None: return False
        try:
            with request.urlopen(URL + "/health", timeout=2) as r:
                if b"ok" in r.read(): return True
        except Exception: pass
        time.sleep(0.5)
    return False

def run(config, rep, tag=""):
    args = CONFIGS[config]
    env = dict(os.environ); env["LD_LIBRARY_PATH"] = BIN
    name = f"{tag}{config}-rep{rep}"
    tpath = os.path.join(OUT, f"telemetry-{name}.csv")
    slog  = open(os.path.join(OUT, f"server-{name}.log"), "w")
    sp, sf = start_sampler(tpath)
    time.sleep(1.2)
    t0 = time.time()
    proc = subprocess.Popen([SERVER] + args, stdout=slog, stderr=subprocess.STDOUT, env=env)
    ok = wait_health(proc)
    t_load = time.time() - t0
    results = []
    if ok:
        vram_loaded = smi("memory.used")
        for p in PROMPTS:
            tq = time.time()
            r = post("/completion", dict(GEN, prompt=p["prompt"]))
            wall = time.time() - tq
            t = r.get("timings", {}) or {}
            rec = {"name": p["name"], "wall_s": round(wall, 3), "prompt_n": t.get("prompt_n"), "prompt_ms": t.get("prompt_ms"),
                   "predicted_n": t.get("predicted_n"), "predicted_ms": t.get("predicted_ms"), "predicted_per_second": t.get("predicted_per_second"),
                   "draft_n": t.get("draft_n", 0) or 0, "draft_n_accepted": t.get("draft_n_accepted", 0) or 0,
                   "content_sha_head": __import__("hashlib").sha256(r.get("content", "").encode()).hexdigest()[:12],
                   "stop_type": r.get("stop_type"), "truncated": r.get("truncated")}
            rec["accept_rate"] = round(rec["draft_n_accepted"] / rec["draft_n"], 4) if rec["draft_n"] else None
            results.append(rec)
    else:
        log(f"  FAILED to start {name}")
        vram_loaded = None
    proc.send_signal(signal.SIGINT)
    try: proc.wait(timeout=30)
    except subprocess.TimeoutExpired: proc.kill(); proc.wait()
    slog.close()
    el = time.time() - t0
    time.sleep(1.2)
    stop_sampler(sp, sf)
    if not ok: return None
    tel = summarise_telemetry(parse_telemetry(tpath))
    tp = sum(x["predicted_n"] or 0 for x in results); tms = sum(x["predicted_ms"] or 0 for x in results)
    td = sum(x["draft_n"] for x in results); ta = sum(x["draft_n_accepted"] for x in results)
    agg = {"total_predicted": tp, "total_predicted_ms": round(tms, 1), "gen_tok_s": round(tp / (tms / 1000), 2) if tms else None,
           "mean_per_prompt_tok_s": round(st.mean([x["predicted_per_second"] for x in results]), 2),
           "total_draft": td, "total_draft_accepted": ta, "accept_rate": round(ta / td, 4) if td else None,
           "wall_s_prompts": round(sum(x["wall_s"] for x in results), 2), "load_s": round(t_load, 1), "vram_after_load_mib": vram_loaded}
    rec = {"config": config, "rep": rep, "tag": tag.strip("-") or "measured", "started": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(t0)),
           "elapsed_s": round(el, 1), "server_args": args, "gen": GEN, "aggregate": agg, "results": results, "telemetry": tel}
    with open(os.path.join(OUT, f"raw-{name}.json"), "w") as f: json.dump(rec, f, indent=1)
    ar = f"{agg['accept_rate']:.3f}" if agg["accept_rate"] is not None else "  n/a"
    log(f"  {tag or '':6s}{config:9s} rep{rep}  gen {agg['gen_tok_s']:7.2f} tok/s  per-prompt mean {agg['mean_per_prompt_tok_s']:7.2f}  accept {ar}  "
        f"pred {tp}  draft {td}/{ta}  wall {agg['wall_s_prompts']:.1f}s  load {t_load:.1f}s  vram {vram_loaded} MiB  ({el:.0f}s)")
    if tel.get("sm_clock"):
        log(f"    load: pcie gen {tel['pcie_gen_under_load']} (gpu view {tel['pcie_gen_gpu_under_load']}) x{tel['pcie_width_under_load']}  sm {tel['sm_clock']['median']:.0f} MHz (min {tel['sm_clock']['min']})  "
            f"mem {tel['mem_clock']['median']:.0f}  power {tel['power']['mean']:.0f} W (max {tel['power']['max']:.0f})  temp {tel['temp_start']}->{tel['temp_max']} C  "
            f"vram peak {tel['vram_peak_mib']}  reasons {tel['clock_event_reasons_under_load']}  n={tel['samples_under_load']}/{tel['samples']}")
    return rec

def main():
    os.makedirs(OUT, exist_ok=True)
    log("start  pre-registered: baseline vs z-lab DFlash drafter, 9 prompts, prime both then A,B x3 alternating")
    log(f"  server: {SERVER}")
    log(f"  card: {smi('name,driver_version,pcie.link.gen.max,pcie.link.gen.gpumax,pcie.link.gen.current,memory.used,temperature.gpu,power.draw')}")
    log(f"  free -g: " + subprocess.run(["free", "-g"], capture_output=True, text=True).stdout.strip().split("\n")[1])
    primes, results = [], []
    for config in ORDER:
        r = run(config, 0, tag="prime-")
        if r: primes.append(r)
    for rep in range(1, REPS + 1):
        for config in ORDER:
            r = run(config, rep)
            if r: results.append(r)
    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump({"order": ORDER, "reps": REPS, "configs": CONFIGS, "gen": GEN, "prompts": [p["name"] for p in PROMPTS],
                   "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "results": results, "primes": primes}, f, indent=1)
    log("summary (mean of 3 measured reps; spread = min..max over reps)")
    summ = {}
    for config in ORDER:
        rs = [r for r in results if r["config"] == config]
        if not rs: continue
        g = [r["aggregate"]["gen_tok_s"] for r in rs]; m = [r["aggregate"]["mean_per_prompt_tok_s"] for r in rs]
        a = [r["aggregate"]["accept_rate"] for r in rs if r["aggregate"]["accept_rate"] is not None]
        summ[config] = {"gen_tok_s": {"mean": round(st.mean(g), 2), "min": min(g), "max": max(g), "reps": g},
                        "mean_per_prompt_tok_s": {"mean": round(st.mean(m), 2), "min": min(m), "max": max(m), "reps": m},
                        "accept_rate": {"mean": round(st.mean(a), 4), "min": min(a), "max": max(a), "reps": a} if a else None,
                        "per_prompt": {p["name"]: {"tok_s_mean": round(st.mean([x["predicted_per_second"] for r in rs for x in r["results"] if x["name"] == p["name"]]), 2),
                                                   "accept_mean": (lambda v: round(st.mean(v), 4) if v else None)([x["accept_rate"] for r in rs for x in r["results"] if x["name"] == p["name"] and x["accept_rate"] is not None])}
                                       for p in PROMPTS}}
        log(f"  {config:9s} gen {st.mean(g):7.2f} [{min(g):.2f}..{max(g):.2f}]  per-prompt mean {st.mean(m):7.2f} [{min(m):.2f}..{max(m):.2f}]  accept {summ[config]['accept_rate']['mean'] if a else 'n/a'}")
    if "baseline" in summ and "dflash" in summ:
        A, B = summ["baseline"]["gen_tok_s"], summ["dflash"]["gen_tok_s"]
        gap = B["mean"] - A["mean"]; spread = max(A["max"] - A["min"], B["max"] - B["min"])
        verdict = ("OVERTURNED" if gap > 0 else "REPRODUCED") if abs(gap) > spread else "NULL (inside spread)"
        summ["verdict"] = {"gap_tok_s": round(gap, 2), "speedup": round(B["mean"] / A["mean"], 3), "larger_spread": round(spread, 2), "verdict": verdict}
        log(f"  verdict: {verdict}  speedup {B['mean']/A['mean']:.3f}x  gap {gap:+.2f} tok/s vs larger spread {spread:.2f}")
    with open(os.path.join(OUT, "summary.json"), "w") as f: json.dump(summ, f, indent=1)
    log(f"done  card at {smi('memory.used')} MiB, {smi('temperature.gpu')} C after last run")

if __name__ == "__main__":
    main()
