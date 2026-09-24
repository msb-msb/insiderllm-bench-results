#!/usr/bin/env python3
"""Tamanna Gen 4 baseline — the two canonical 3090 rows on the new platform, 2026-09-21.

Harness string is byte-identical to the published rows, the 08-28 A-B-B-A and the 09-07 build A/B:
  llama-bench -ngl 99 -fa 1 -p 512 -n 128 -d 0,4096,8192 -r 5
One build (llama.cpp v0.4.0, 5266f24, CUDA sm_86, GGML_NATIVE=OFF), two models, three reps.
Models alternate within each rep with the starting model flipped on rep 2, the 09-07 pattern:
  rep1: ornith, qwen   rep2: qwen, ornith   rep3: ornith, qwen
Alongside every run a 1 s nvidia-smi sampler records PCIe current generation, temperature,
SM clock, memory clock, power draw, utilisation, memory used and the active clock-event
reasons; the sampler starts before llama-bench launches and stops after it exits.
No root on Tamanna, so no page-cache eviction bracket (same as 09-07). Both models are
22 GB against 31 GB of RAM, so alternating them evicts each other's pages anyway.

Pre-registered: this is a platform change (5700X, DDR4-3200, PCIe 4.0, open frame, CUDA
12.4 toolkit), not a build change. Any delta is reported as "Tamanna vs Miu" and is not
attributed to the bus until the Gen 3 half runs.
"""
import json, os, subprocess, sys, time, statistics as st, signal

OUT = os.path.expanduser("~/tamanna-gen4-baseline-2026-09-21")
BENCH = os.path.expanduser("~/llama-v0.4.0/build/bin/llama-bench")
LIBDIR = os.path.expanduser("~/llama-v0.4.0/build/bin")
MODELS = {
    "ornith-1.5-35b-a3b": os.path.expanduser("~/bench-models/Ornith-1.5-35B-A3B-Q4_K_M.gguf"),
    "qwen3.6-35b-a3b":    os.path.expanduser("~/bench-models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf"),
}
ARGS = ["-ngl", "99", "-fa", "1", "-p", "512", "-n", "128", "-d", "0,4096,8192", "-r", "5"]
HARNESS = "llama-bench " + " ".join(ARGS)
ORDER = [["ornith-1.5-35b-a3b", "qwen3.6-35b-a3b"], ["qwen3.6-35b-a3b", "ornith-1.5-35b-a3b"], ["ornith-1.5-35b-a3b", "qwen3.6-35b-a3b"]]
SMI_FIELDS = ["timestamp", "pcie.link.gen.current", "pcie.link.gen.gpucurrent", "pcie.link.width.current",
              "temperature.gpu", "clocks.sm", "clocks.mem", "power.draw", "utilization.gpu", "memory.used",
              "clocks_event_reasons.active"]

def log(s):
    line = f"{time.strftime('%H:%M:%S')} {s}"
    print(line, flush=True)
    with open(os.path.join(OUT, "run.log"), "a") as f: f.write(line + "\n")

def smi(q):
    return subprocess.run(["nvidia-smi", f"--query-gpu={q}", "--format=csv,noheader,nounits"],
                          capture_output=True, text=True).stdout.strip().split("\n")[0]

def start_sampler(path):
    f = open(path, "w")
    f.write(",".join(SMI_FIELDS) + "\n"); f.flush()
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
                    "pcie_width_under_load": sorted(set(r["pcie_width"] for r in load)),
                    "sm_clock": s([r["sm"] for r in load]), "mem_clock": s([r["mem"] for r in load]),
                    "power": s([r["power"] for r in load]), "temp_under_load": s([r["temp"] for r in load]),
                    "clock_event_reasons_under_load": sorted(set(r["reasons"] for r in load))})
    return out

def run(model, rep):
    cmd = [BENCH, "-m", MODELS[model]] + ARGS + ["-o", "json"]
    env = dict(os.environ); env["LD_LIBRARY_PATH"] = LIBDIR
    tpath = os.path.join(OUT, f"telemetry-{model}-rep{rep}.csv")
    sp, sf = start_sampler(tpath)
    time.sleep(1.2)
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    el = time.time() - t0
    time.sleep(1.2)
    stop_sampler(sp, sf)
    if p.returncode != 0:
        log(f"  FAILED {model} rep{rep} rc={p.returncode}: {p.stderr[-300:]}")
        return None
    try:
        rows = json.loads(p.stdout)
    except Exception:
        log(f"  could not parse JSON for {model} rep{rep}"); return None
    tel = summarise_telemetry(parse_telemetry(tpath))
    rec = {"model": model, "rep": rep, "started": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(t0)), "elapsed_s": round(el, 1), "rows": [], "telemetry": tel}
    for r in rows:
        kind = "pp" if r["n_prompt"] > 0 else "tg"
        rec["rows"].append({"kind": kind, "depth": r.get("n_depth", 0), "avg_ts": r["avg_ts"], "stddev_ts": r["stddev_ts"],
                            "samples": r.get("samples_ts", []), "build_commit": r.get("build_commit"), "build_number": r.get("build_number"),
                            "n_threads": r.get("n_threads"), "gpu_info": r.get("gpu_info")})
    with open(os.path.join(OUT, f"raw-{model}-rep{rep}.json"), "w") as f:
        json.dump({"cmd": cmd, "stdout": rows, "stderr_tail": p.stderr[-2000:]}, f, indent=1)
    tg = {x["depth"]: x["avg_ts"] for x in rec["rows"] if x["kind"] == "tg"}
    pp = {x["depth"]: x["avg_ts"] for x in rec["rows"] if x["kind"] == "pp"}
    log(f"  {model:20s} rep{rep}  tg128 d0/4k/8k {tg.get(0,0):.2f}/{tg.get(4096,0):.2f}/{tg.get(8192,0):.2f}  pp512 {pp.get(0,0):.0f}/{pp.get(4096,0):.0f}/{pp.get(8192,0):.0f}  ({el:.0f}s)")
    if tel.get("sm_clock"):
        log(f"    load: pcie gen {tel['pcie_gen_under_load']} x{tel['pcie_width_under_load']}  sm {tel['sm_clock']['median']:.0f} MHz (min {tel['sm_clock']['min']})  mem {tel['mem_clock']['median']:.0f}  "
            f"power {tel['power']['mean']:.0f} W (max {tel['power']['max']:.0f})  temp {tel['temp_start']}->{tel['temp_max']} C  reasons {tel['clock_event_reasons_under_load']}  n={tel['samples_under_load']}/{tel['samples']}")
    return rec

def main():
    os.makedirs(OUT, exist_ok=True)
    log(f"start  harness: {HARNESS}")
    log(f"  bench: {BENCH}")
    log(f"  card: {smi('name,driver_version,pcie.link.gen.max,pcie.link.gen.current,memory.used,temperature.gpu,power.draw')}")
    log(f"  free -g: " + subprocess.run(["free", "-g"], capture_output=True, text=True).stdout.strip().split("\n")[1])
    results = []
    for rep, order in enumerate(ORDER, 1):
        for model in order:
            r = run(model, rep)
            if r: results.append(r)
    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump({"harness": HARNESS, "order": ORDER, "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "results": results}, f, indent=1)
    log("summary (mean of 3 reps of the per-run 5-repeat average; spread = min..max over reps)")
    summ = {}
    for model in MODELS:
        for kind in ("tg", "pp"):
            for depth in (0, 4096, 8192):
                v = [x["avg_ts"] for r in results if r["model"] == model for x in r["rows"] if x["kind"] == kind and x["depth"] == depth]
                sd = [x["stddev_ts"] for r in results if r["model"] == model for x in r["rows"] if x["kind"] == kind and x["depth"] == depth]
                if not v: continue
                summ[f"{model}|{kind}|{depth}"] = {"mean": st.mean(v), "min": min(v), "max": max(v), "reps": v, "within_run_stddev": sd}
                log(f"  {model:20s} {kind}{'128' if kind=='tg' else '512'} d={depth:<5d} {st.mean(v):8.2f} [{min(v):.2f}..{max(v):.2f}]  reps {' '.join(f'{x:.2f}' for x in v)}")
    with open(os.path.join(OUT, "summary.json"), "w") as f: json.dump(summ, f, indent=1)
    log(f"done  card at {smi('memory.used')} MiB, {smi('temperature.gpu')} C after last run")

if __name__ == "__main__":
    main()
