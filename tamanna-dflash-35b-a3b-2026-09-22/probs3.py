#!/usr/bin/env python3
"""DIAGNOSTIC 3: top candidates at the divergence position. Probe the n_probs response shape, then for each
prompt: single-token decode (baseline run, probs at gen index i) and the batched prefix evaluation
(prompt + baseline[:i] as prompt, probs at its first generated token). Baseline server only: the spec path
leaves result.probs unset (server-context.cpp 'TODO: set result.probs')."""
import json, os, subprocess, time, signal, ast
from urllib import request
BIN=os.path.expanduser("~/llama-v0.4.0/build/bin"); SERVER=BIN+"/llama-server"
T=os.path.expanduser("~/bench-models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf")
ARGS=["-m",T,"-ngl","99","-fa","on","-c","8192","-np","1","--host","127.0.0.1","--port","8080"]
OUT=os.path.expanduser("~/tamanna-dflash-35b-a3b-2026-09-22")
_src=open(os.path.expanduser("~/am17an_bench.py")).read()
PROMPTS={p["name"]:p["prompt"] for p in ast.literal_eval(next(n for n in ast.parse(_src).body if isinstance(n,ast.Assign) and n.targets[0].id=="PROMPTS").value)}
d2=json.load(open(OUT+"/divergence2.json")); d1=json.load(open(OUT+"/divergence.json"))
def post(path,payload):
    req=request.Request("http://127.0.0.1:8080"+path,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
    with request.urlopen(req,timeout=300) as r: return json.loads(r.read())
env=dict(os.environ); env["LD_LIBRARY_PATH"]=BIN
p=subprocess.Popen([SERVER]+ARGS,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=env)
for _ in range(400):
    try:
        with request.urlopen("http://127.0.0.1:8080/health",timeout=2) as r:
            if b"ok" in r.read(): break
    except Exception: time.sleep(0.5)
GEN={"temperature":0.0,"seed":42,"cache_prompt":False,"return_tokens":True,"n_probs":10,"post_sampling_probs":False}
probe=post("/completion",dict(GEN,prompt="Q: What is 2+2?\nA:",n_predict=2))
print("probe keys:",sorted(probe.keys()))
cp=probe.get("completion_probabilities"); print("completion_probabilities type/len:",type(cp).__name__, len(cp) if cp else cp)
if cp: print("first entry:",json.dumps(cp[0])[:600])
def extract(e):
    tp=e.get("top_probs") or e.get("top_logprobs") or []
    out=[]
    for x in tp:
        out.append({"id":x.get("id"),"tok":x.get("token"),"p":x.get("prob"),"logprob":x.get("logprob")})
    return out
res={}
for n,x in d2.items():
    i=x["i"]; base=d1["baseline"][n]["tokens"]; dfl=d1["dflash"][n]["tokens"]
    ptoks=post("/tokenize",{"content":PROMPTS[n]})["tokens"]
    r=post("/completion",dict(GEN,prompt=PROMPTS[n],n_predict=i+1))
    assert r["tokens"][:i+1]==base[:i+1]
    single=extract(r["completion_probabilities"][i])
    pre=post("/completion",dict(GEN,prompt=ptoks+base[:i],n_predict=1))
    batched=extract(pre["completion_probabilities"][0])
    def rank(l,t): return next((k for k,e in enumerate(l) if e["id"]==t),None)
    res[n]={"i":i,"base_tok":base[i],"dflash_tok":dfl[i],"single_token_top":single,"batched_prefix_top":batched,
            "single":{"base_rank":rank(single,base[i]),"dflash_rank":rank(single,dfl[i])},
            "batched":{"pick":pre["tokens"][0],"base_rank":rank(batched,base[i]),"dflash_rank":rank(batched,dfl[i])}}
    def fmt(l): return "  ".join(f"[{e['id']}{e['tok']!r} {e['p'] if e['p'] is not None else e['logprob']}]" for e in l[:3])
    print(f"\n{n} i={i} base={base[i]} dflash={dfl[i]}")
    print(f"  single-token path top3 : {fmt(single)}   ranks base={res[n]['single']['base_rank']} dflash={res[n]['single']['dflash_rank']}")
    print(f"  batched-prefix   top3 : {fmt(batched)}   ranks base={res[n]['batched']['base_rank']} dflash={res[n]['batched']['dflash_rank']}  pick={pre['tokens'][0]}")
p.send_signal(signal.SIGINT); p.wait(timeout=30)
json.dump(res,open(OUT+"/divergence3-probs.json","w"),indent=1)
