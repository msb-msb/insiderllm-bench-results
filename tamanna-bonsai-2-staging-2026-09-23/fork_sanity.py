#!/usr/bin/env python3
"""Fork sanity: Qwen3.8-27B UD-Q4_K_XL under the PrismML fork vs under the v0.4.0 pin, on Tamanna, 2026-09-23.
Harness byte-identical to the canonical rows: llama-bench -ngl 99 -fa 1 -p 512 -n 128 -d 0,4096,8192 -r 5
Block 3 priming design: three reps, builds alternating within a rep, starting build flipped on rep 2, and a
discarded priming run of the identical command before every measured run. 1 s nvidia-smi telemetry per run.
Pre-registered: any decode (tg128) cell with |delta| >= 3% is the finding and the staging stops there."""
import json, os, subprocess, time, statistics as st, signal
OUT = os.path.expanduser("~/tamanna-bonsai-2-staging-2026-09-23/fork-sanity")
BUILDS = {"v0.4.0": os.path.expanduser("~/llama-v0.4.0/build/bin"), "prism-b10709": os.path.expanduser("~/llama-prismml/build/bin")}
MODEL = os.path.expanduser("~/bench-models/Qwen3.8-27B-UD-Q4_K_XL.gguf")
ARGS = ["-ngl", "99", "-fa", "1", "-p", "512", "-n", "128", "-d", "0,4096,8192", "-r", "5"]
HARNESS = "llama-bench " + " ".join(ARGS)
ORDER = [["v0.4.0", "prism-b10709"], ["prism-b10709", "v0.4.0"], ["v0.4.0", "prism-b10709"]]
SMI = ["timestamp","pcie.link.gen.current","pcie.link.gen.gpucurrent","pcie.link.width.current","temperature.gpu","clocks.sm","clocks.mem","power.draw","utilization.gpu","memory.used","clocks_event_reasons.active"]
def log(s):
    line = f"{time.strftime('%H:%M:%S')} {s}"; print(line, flush=True)
    with open(os.path.join(OUT, "run.log"), "a") as f: f.write(line + "\n")
def sampler(path):
    f = open(path, "w"); f.write(",".join(SMI)+"\n"); f.flush()
    return subprocess.Popen(["nvidia-smi","--query-gpu="+",".join(SMI),"--format=csv,noheader,nounits","-lms","1000"], stdout=f, stderr=subprocess.DEVNULL), f
def stop(p, f):
    p.send_signal(signal.SIGINT)
    try: p.wait(timeout=5)
    except subprocess.TimeoutExpired: p.kill(); p.wait()
    f.close()
def telemetry(path):
    rows=[]
    for line in open(path).read().splitlines()[1:]:
        x=[c.strip() for c in line.split(",")]
        try: rows.append({"gen":int(x[1]),"temp":int(x[4]),"sm":int(x[5]),"mem":int(x[6]),"power":float(x[7]),"util":int(x[8]),"vram":int(x[9])})
        except (ValueError,IndexError): pass
    load=[r for r in rows if r["util"]>=50]
    if not rows: return {}
    t={"samples":len(rows),"under_load":len(load),"temp_start":rows[0]["temp"],"temp_max":max(r["temp"] for r in rows),"vram_peak_mib":max(r["vram"] for r in rows)}
    if load: t.update({"pcie_gen":sorted(set(r["gen"] for r in load)),"sm_median":st.median([r["sm"] for r in load]),"sm_min":min(r["sm"] for r in load),"mem_clock":st.median([r["mem"] for r in load]),"power_mean":round(st.mean([r["power"] for r in load]),1),"power_max":max(r["power"] for r in load)})
    return t
def run(build, rep, tag=""):
    bindir = BUILDS[build]; cmd = [os.path.join(bindir,"llama-bench"), "-m", MODEL] + ARGS + ["-o","json"]
    env = dict(os.environ); env["LD_LIBRARY_PATH"] = bindir
    tp = os.path.join(OUT, f"telemetry-{tag}{build}-rep{rep}.csv"); sp, sf = sampler(tp); time.sleep(1.2)
    t0 = time.time(); p = subprocess.run(cmd, capture_output=True, text=True, env=env); el = time.time()-t0
    time.sleep(1.2); stop(sp, sf)
    if p.returncode != 0: log(f"  FAILED {tag}{build} rep{rep} rc={p.returncode}: {p.stderr[-400:]}"); return None
    try: rows = json.loads(p.stdout)
    except Exception: log(f"  no JSON {tag}{build} rep{rep}: {p.stdout[-200:]} {p.stderr[-200:]}"); return None
    tel = telemetry(tp)
    rec = {"build": build, "rep": rep, "tag": tag.strip("-") or "measured", "elapsed_s": round(el,1), "telemetry": tel, "rows": []}
    for r in rows:
        rec["rows"].append({"kind": "pp" if r["n_prompt"]>0 else "tg", "depth": r.get("n_depth",0), "avg_ts": r["avg_ts"], "stddev_ts": r["stddev_ts"], "samples": r.get("samples_ts",[]), "build_commit": r.get("build_commit"), "build_number": r.get("build_number")})
    with open(os.path.join(OUT, f"raw-{tag}{build}-rep{rep}.json"), "w") as f: json.dump({"cmd": cmd, "stdout": rows, "stderr_tail": p.stderr[-2000:]}, f, indent=1)
    tg = {x["depth"]: x["avg_ts"] for x in rec["rows"] if x["kind"]=="tg"}; pp = {x["depth"]: x["avg_ts"] for x in rec["rows"] if x["kind"]=="pp"}
    log(f"  {tag or '':6s}{build:13s} rep{rep}  tg128 d0/4k/8k {tg.get(0,0):.2f}/{tg.get(4096,0):.2f}/{tg.get(8192,0):.2f}  pp512 {pp.get(0,0):.0f}/{pp.get(4096,0):.0f}/{pp.get(8192,0):.0f}  vram {tel.get('vram_peak_mib')} MiB  gen {tel.get('pcie_gen')}  sm {tel.get('sm_median')}  {tel.get('power_mean')} W  ({el:.0f}s) build {rows[0].get('build_commit')}/{rows[0].get('build_number')}")
    return rec
def main():
    os.makedirs(OUT, exist_ok=True); log(f"start  harness: {HARNESS}  model: {MODEL}")
    for b, d in BUILDS.items(): log(f"  build {b}: {d}")
    results, primes = [], []
    for rep, order in enumerate(ORDER, 1):
        for build in order:
            pr = run(build, rep, "prime-"); 
            if pr: primes.append(pr)
            r = run(build, rep)
            if r: results.append(r)
    json.dump({"harness": HARNESS, "order": ORDER, "results": results, "primes": primes}, open(os.path.join(OUT,"results.json"),"w"), indent=1)
    log("summary (mean of 3 measured reps of the per-run 5-repeat average; spread = min..max; delta = fork vs pin)")
    summ = {}
    for kind in ("tg","pp"):
        for depth in (0,4096,8192):
            v = {b: [x["avg_ts"] for r in results if r["build"]==b for x in r["rows"] if x["kind"]==kind and x["depth"]==depth] for b in BUILDS}
            a, c = v["v0.4.0"], v["prism-b10709"]
            if not a or not c: continue
            delta = (st.mean(c)-st.mean(a))/st.mean(a)*100
            verdict = "no change" if abs(delta) < 3 else ("fork FASTER" if delta > 0 else "fork SLOWER")
            summ[f"{kind}|{depth}"] = {"v0.4.0": {"mean": st.mean(a), "min": min(a), "max": max(a)}, "prism-b10709": {"mean": st.mean(c), "min": min(c), "max": max(c)}, "delta_pct": delta, "verdict": verdict}
            log(f"  {kind}{'128' if kind=='tg' else '512'} d={depth:<5d} v0.4.0 {st.mean(a):8.2f} [{min(a):.2f}..{max(a):.2f}]   fork {st.mean(c):8.2f} [{min(c):.2f}..{max(c):.2f}]   delta {delta:+.2f}%  -> {verdict}")
    json.dump(summ, open(os.path.join(OUT,"summary.json"),"w"), indent=1)
    vr = {b: max(r["telemetry"].get("vram_peak_mib",0) for r in results if r["build"]==b) for b in BUILDS}; log(f"peak VRAM measured runs: {vr}")
    log("done")
if __name__ == "__main__": main()
