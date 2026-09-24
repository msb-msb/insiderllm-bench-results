#!/usr/bin/env python3
"""SMOKE TEST, not a result: Bonsai 2 27B PQ2_0 under the PrismML fork on Tamanna. One llama-bench invocation,
tg128 at d=0 only (-p 0 -n 128 -r 3), -ngl 99 -fa 1, with 1 s telemetry for peak VRAM. Confirms the file loads
and generates on sm_86 under the fork; the tok/s is one number from one run and is labelled as such."""
import json, os, subprocess, time, statistics as st, signal
OUT = os.path.expanduser("~/tamanna-bonsai-2-staging-2026-09-23/smoke")
BIN = os.path.expanduser("~/llama-prismml/build/bin")
MODEL = os.path.expanduser("~/bench-models/Ternary-Bonsai-2-27B-PQ2_0.gguf")
ARGS = ["-ngl", "99", "-fa", "1", "-p", "0", "-n", "128", "-d", "0", "-r", "3"]
SMI = ["timestamp","pcie.link.gen.current","temperature.gpu","clocks.sm","clocks.mem","power.draw","utilization.gpu","memory.used"]
os.makedirs(OUT, exist_ok=True)
idle = subprocess.run(["nvidia-smi","--query-gpu=memory.used,temperature.gpu","--format=csv,noheader,nounits"],capture_output=True,text=True).stdout.strip()
tp = os.path.join(OUT, "telemetry.csv"); f = open(tp,"w"); f.write(",".join(SMI)+"\n"); f.flush()
sp = subprocess.Popen(["nvidia-smi","--query-gpu="+",".join(SMI),"--format=csv,noheader,nounits","-lms","1000"], stdout=f, stderr=subprocess.DEVNULL); time.sleep(1.2)
cmd = [os.path.join(BIN,"llama-bench"), "-m", MODEL] + ARGS + ["-o","json"]; env = dict(os.environ); env["LD_LIBRARY_PATH"] = BIN
t0 = time.time(); p = subprocess.run(cmd, capture_output=True, text=True, env=env); el = time.time()-t0; time.sleep(1.2)
sp.send_signal(signal.SIGINT); sp.wait(timeout=5); f.close()
rows=[]
for line in open(tp).read().splitlines()[1:]:
    x=[c.strip() for c in line.split(",")]
    try: rows.append({"gen":int(x[1]),"temp":int(x[2]),"sm":int(x[3]),"mem":int(x[4]),"power":float(x[5]),"util":int(x[6]),"vram":int(x[7])})
    except (ValueError,IndexError): pass
load=[r for r in rows if r["util"]>=50]
rec={"label":"SMOKE TEST, not a result","cmd":cmd,"rc":p.returncode,"elapsed_s":round(el,1),"card_idle_before":idle,"stderr_tail":p.stderr[-3000:],
     "vram_peak_mib":max((r["vram"] for r in rows),default=None),"pcie_gen_under_load":sorted(set(r["gen"] for r in load)),
     "sm_median":st.median([r["sm"] for r in load]) if load else None,"power_mean":round(st.mean([r["power"] for r in load]),1) if load else None,"temp_max":max((r["temp"] for r in rows),default=None)}
try:
    out=json.loads(p.stdout); rec["stdout"]=out
    for r in out: rec["tg128_d0"]={"avg_ts":r["avg_ts"],"stddev_ts":r["stddev_ts"],"samples":r.get("samples_ts"),"build_commit":r.get("build_commit"),"build_number":r.get("build_number"),"model_type":r.get("model_type"),"model_size":r.get("model_size"),"model_n_params":r.get("model_n_params")}
except Exception: rec["stdout_raw"]=p.stdout[-2000:]
json.dump(rec, open(os.path.join(OUT,"smoke.json"),"w"), indent=1)
print(f"rc={p.returncode} elapsed {el:.0f}s  tg128 d=0: {rec.get('tg128_d0',{}).get('avg_ts')} tok/s (sd {rec.get('tg128_d0',{}).get('stddev_ts')})  VRAM peak {rec['vram_peak_mib']} MiB  gen {rec['pcie_gen_under_load']}  sm {rec['sm_median']}  {rec['power_mean']} W  model_type {rec.get('tg128_d0',{}).get('model_type')} size {rec.get('tg128_d0',{}).get('model_size')}")
if p.returncode: print("STDERR:", p.stderr[-1500:])
