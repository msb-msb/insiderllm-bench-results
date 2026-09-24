#!/usr/bin/env python3
"""DIAGNOSTIC, outside the pre-registration: where do baseline and drafter outputs diverge at temperature 0?
One server per config, the nine prompts, content captured with per-token pieces (n_probs 0, return tokens)."""
import json, os, subprocess, time, signal, ast
from urllib import request
BIN=os.path.expanduser("~/llama-v0.4.0/build/bin"); SERVER=BIN+"/llama-server"
T=os.path.expanduser("~/bench-models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf"); D=os.path.expanduser("~/bench-models/Qwen3.6-35B-A3B-DFlash-Q8_0.gguf")
COMMON=["-m",T,"-ngl","99","-fa","on","-c","8192","-np","1","--host","127.0.0.1","--port","8080"]
CFG={"baseline":COMMON,"dflash":COMMON+["-md",D,"-ngld","99","--spec-type","draft-dflash","--spec-draft-n-max","15"]}
_src=open(os.path.expanduser("~/am17an_bench.py")).read()
PROMPTS=ast.literal_eval(next(n for n in ast.parse(_src).body if isinstance(n,ast.Assign) and n.targets[0].id=="PROMPTS").value)
def post(path,payload):
    req=request.Request("http://127.0.0.1:8080"+path,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
    with request.urlopen(req,timeout=300) as r: return json.loads(r.read())
out={}
for cfg,args in CFG.items():
    env=dict(os.environ); env["LD_LIBRARY_PATH"]=BIN
    p=subprocess.Popen([SERVER]+args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=env)
    for _ in range(300):
        try:
            with request.urlopen("http://127.0.0.1:8080/health",timeout=2) as r:
                if b"ok" in r.read(): break
        except Exception: time.sleep(0.5)
    out[cfg]={}
    for pr in PROMPTS:
        r=post("/completion",{"prompt":pr["prompt"],"n_predict":192,"temperature":0.0,"seed":42,"cache_prompt":False,"return_tokens":True})
        out[cfg][pr["name"]]={"content":r["content"],"tokens":r.get("tokens"),"timings":{k:r["timings"].get(k) for k in ("predicted_n","predicted_per_second","draft_n","draft_n_accepted")}}
    p.send_signal(signal.SIGINT); p.wait(timeout=30)
json.dump(out,open(os.path.expanduser("~/tamanna-dflash-35b-a3b-2026-09-22/divergence.json"),"w"),indent=1)
for n in out["baseline"]:
    a=out["baseline"][n]["tokens"] or []; b=out["dflash"][n]["tokens"] or []
    i=next((k for k in range(min(len(a),len(b))) if a[k]!=b[k]), None)
    same=out["baseline"][n]["content"]==out["dflash"][n]["content"]
    print(f"{n:18s} identical={same!s:5s} len {len(a)}/{len(b)} first_diverge_tok={i}")
