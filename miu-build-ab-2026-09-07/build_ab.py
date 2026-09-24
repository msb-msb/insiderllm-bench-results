#!/usr/bin/env python3
"""b10088 vs v0.4.0 on the two canonical 3090 rows — gate (b) for the 2026-09-08 marker.

Harness string is byte-identical to the published rows and the 08-28 A-B-B-A:
  llama-bench -ngl 99 -fa 1 -p 512 -n 128 -d 0,4096,8192 -r 5
Two models x two builds x three reps. Builds alternate within each rep, with the
starting build flipped on rep 2, so neither build systematically follows the other:
  rep1: b10088, v040   rep2: v040, b10088   rep3: b10088, v040
No root here, so no page-cache eviction between runs (the 08-28 bracket needed it);
both builds therefore read the same warm cache, which is symmetric for a build delta.

Pre-registered: |delta| < 3% is "no change"; >= 3% either way is a stated build effect.
"""
import json, os, subprocess, sys, time, statistics as st

OUT = os.path.dirname(os.path.abspath(__file__))
BUILDS = {
    "b10088": "/home/minotaur/llama-bench-src/build/bin/llama-bench",
    "v0.4.0": "/home/minotaur/llama-v0.4.0/build/bin/llama-bench",
}
MODELS = {
    "ornith-1.5-35b-a3b": "/home/minotaur/bench-models/Ornith-1.5-35B-A3B-Q4_K_M.gguf",
    "qwen3.6-35b-a3b":    "/home/minotaur/bench-models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf",
}
ARGS = ["-ngl", "99", "-fa", "1", "-p", "512", "-n", "128", "-d", "0,4096,8192", "-r", "5"]
HARNESS = "llama-bench " + " ".join(ARGS)
ORDER = [["b10088", "v0.4.0"], ["v0.4.0", "b10088"], ["b10088", "v0.4.0"]]

def log(s):
    line = f"{time.strftime('%H:%M:%S')} {s}"
    print(line, flush=True)
    with open(os.path.join(OUT, "run.log"), "a") as f: f.write(line + "\n")

def gpu_idle_mib():
    return int(subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                              capture_output=True, text=True).stdout.strip().split("\n")[0])

def run(build, model, rep):
    cmd = [BUILDS[build], "-m", MODELS[model]] + ARGS + ["-o", "json"]
    env = dict(os.environ)
    if build == "v0.4.0":
        env["LD_LIBRARY_PATH"] = "/home/minotaur/llama-v0.4.0/build/bin"
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    el = time.time() - t0
    if p.returncode != 0:
        log(f"  FAILED {build} {model} rep{rep} rc={p.returncode}: {p.stderr[-300:]}")
        return None
    try:
        rows = json.loads(p.stdout)
    except Exception:
        log(f"  could not parse JSON for {build} {model} rep{rep}"); return None
    rec = {"build": build, "model": model, "rep": rep, "elapsed_s": round(el, 1), "rows": []}
    for r in rows:
        kind = "pp" if r["n_prompt"] > 0 else "tg"
        rec["rows"].append({"kind": kind, "depth": r.get("n_depth", 0), "avg_ts": r["avg_ts"], "stddev_ts": r["stddev_ts"],
                            "samples": r.get("samples_ts", []), "build_commit": r.get("build_commit"), "build_number": r.get("build_number")})
    with open(os.path.join(OUT, f"raw-{build}-{model}-rep{rep}.json"), "w") as f: json.dump({"cmd": cmd, "stdout": rows, "stderr_tail": p.stderr[-2000:]}, f, indent=1)
    tg = {x["depth"]: x["avg_ts"] for x in rec["rows"] if x["kind"] == "tg"}
    pp = {x["depth"]: x["avg_ts"] for x in rec["rows"] if x["kind"] == "pp"}
    log(f"  {build:7s} {model:20s} rep{rep}  tg128 d0/4k/8k {tg.get(0,0):.2f}/{tg.get(4096,0):.2f}/{tg.get(8192,0):.2f}  pp512 {pp.get(0,0):.0f}/{pp.get(4096,0):.0f}/{pp.get(8192,0):.0f}  ({el:.0f}s)")
    return rec

def main():
    idle = gpu_idle_mib()
    log(f"start  harness: {HARNESS}  card at {idle} MiB before first load")
    for b, path in BUILDS.items():
        v = subprocess.run([path, "--version"] if False else ["bash", "-c", f"LD_LIBRARY_PATH=/home/minotaur/llama-v0.4.0/build/bin {path} --help 2>&1 | head -1"], capture_output=True, text=True).stdout.strip()
        log(f"  build {b}: {path}")
    results = []
    for rep, order in enumerate(ORDER, 1):
        for build in order:
            for model in MODELS:
                r = run(build, model, rep)
                if r: results.append(r)
    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump({"harness": HARNESS, "order": ORDER, "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "results": results}, f, indent=1)
    # summary
    log("summary (mean of 3 reps of the per-run 5-repeat average; spread = min..max over reps)")
    summ = {}
    for model in MODELS:
        for kind in ("tg", "pp"):
            for depth in (0, 4096, 8192):
                vals = {}
                for b in BUILDS:
                    v = [x["avg_ts"] for r in results if r["build"] == b and r["model"] == model for x in r["rows"] if x["kind"] == kind and x["depth"] == depth]
                    vals[b] = v
                a, c = vals["b10088"], vals["v0.4.0"]
                if not a or not c: continue
                ma, mc = st.mean(a), st.mean(c)
                delta = (mc - ma) / ma * 100
                verdict = "no change" if abs(delta) < 3 else ("v0.4.0 FASTER" if delta > 0 else "v0.4.0 SLOWER")
                summ[f"{model}|{kind}|{depth}"] = {"b10088": {"mean": ma, "min": min(a), "max": max(a)}, "v0.4.0": {"mean": mc, "min": min(c), "max": max(c)}, "delta_pct": delta, "verdict": verdict}
                log(f"  {model:20s} {kind}{'128' if kind=='tg' else '512'} d={depth:<5d} b10088 {ma:8.2f} [{min(a):.2f}..{max(a):.2f}]   v0.4.0 {mc:8.2f} [{min(c):.2f}..{max(c):.2f}]   delta {delta:+.2f}%  -> {verdict}")
    with open(os.path.join(OUT, "summary.json"), "w") as f: json.dump(summ, f, indent=1)
    log(f"done  card at {gpu_idle_mib()} MiB after last run")

if __name__ == "__main__":
    main()
