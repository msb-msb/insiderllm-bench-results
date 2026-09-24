#!/usr/bin/env python3
"""DIAGNOSTIC 2, outside the pre-registration. For each of the six greedy-divergent prompts:
  (1) baseline server, n_probs=10: the target's top candidates at the first divergent position i under
      single-token decode;
  (2) baseline server, PREFIX TEST: prompt tokens + baseline's first i tokens as the prompt, n_predict 1,
      n_probs 10 -> the target's greedy pick at position i when that position is evaluated inside a
      multi-token batch (prefill path), with no drafter anywhere. If this equals the drafter's token, the
      divergence is the target's own batched-vs-single-token numerics;
  (3) drafter server with debug logging, n_probs=10: the verify-batch candidates at i, plus the per-step
      accept log so token i can be labelled accepted-draft or sampled-correction."""
import json, os, subprocess, time, signal, ast, re
from urllib import request
BIN=os.path.expanduser("~/llama-v0.4.0/build/bin"); SERVER=BIN+"/llama-server"
T=os.path.expanduser("~/bench-models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf"); D=os.path.expanduser("~/bench-models/Qwen3.6-35B-A3B-DFlash-Q8_0.gguf")
COMMON=["-m",T,"-ngl","99","-fa","on","-c","8192","-np","1","--host","127.0.0.1","--port","8080"]
CFG={"baseline":COMMON,"dflash":COMMON+["-md",D,"-ngld","99","--spec-type","draft-dflash","--spec-draft-n-max","15","--verbose"]}
OUT=os.path.expanduser("~/tamanna-dflash-35b-a3b-2026-09-22")
_src=open(os.path.expanduser("~/am17an_bench.py")).read()
PROMPTS={p["name"]:p["prompt"] for p in ast.literal_eval(next(n for n in ast.parse(_src).body if isinstance(n,ast.Assign) and n.targets[0].id=="PROMPTS").value)}
prev=json.load(open(OUT+"/divergence.json"))
DIV={}
for n in prev["baseline"]:
    a=prev["baseline"][n]["tokens"]; b=prev["dflash"][n]["tokens"]
    i=next((k for k in range(min(len(a),len(b))) if a[k]!=b[k]), None)
    if i is not None: DIV[n]={"i":i,"base_tokens":a,"dflash_tokens":b}
GEN={"n_predict":192,"temperature":0.0,"seed":42,"cache_prompt":False,"return_tokens":True,"n_probs":10}
def post(path,payload):
    req=request.Request("http://127.0.0.1:8080"+path,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
    with request.urlopen(req,timeout=300) as r: return json.loads(r.read())
def start(cfg,logpath):
    env=dict(os.environ); env["LD_LIBRARY_PATH"]=BIN
    lf=open(logpath,"w")
    p=subprocess.Popen([SERVER]+CFG[cfg],stdout=lf,stderr=subprocess.STDOUT,env=env)
    for _ in range(400):
        try:
            with request.urlopen("http://127.0.0.1:8080/health",timeout=2) as r:
                if b"ok" in r.read(): return p,lf
        except Exception: time.sleep(0.5)
    raise SystemExit("server did not start")
def stop(p,lf): p.send_signal(signal.SIGINT); p.wait(timeout=30); lf.close()
def probs_at(r,i):
    cp=r.get("completion_probabilities") or []
    if i>=len(cp): return None
    e=cp[i]; return [{"id":x.get("id"),"tok":x.get("token"),"p":x.get("prob")} for x in e.get("top_probs",[])]
res={}
# (1)+(2) baseline
p,lf=start("baseline",OUT+"/server-divergence2-baseline.log")
for n,dv in DIV.items():
    i=dv["i"]
    ptoks=post("/tokenize",{"content":PROMPTS[n]})["tokens"]
    r=post("/completion",dict(GEN,prompt=PROMPTS[n]))
    assert r["tokens"][:i+1]==dv["base_tokens"][:i+1], f"{n}: baseline not reproducible this run"
    pre=post("/completion",dict(GEN,prompt=ptoks+dv["base_tokens"][:i],n_predict=8))
    det=post("/detokenize",{"tokens":[dv["base_tokens"][i],dv["dflash_tokens"][i]]})
    res[n]={"i":i,"prompt_n":len(ptoks),"base_tok":dv["base_tokens"][i],"dflash_tok":dv["dflash_tokens"][i],
            "pieces":{"base":post("/detokenize",{"tokens":[dv["base_tokens"][i]]})["content"],"dflash":post("/detokenize",{"tokens":[dv["dflash_tokens"][i]]})["content"]},
            "context_before":post("/detokenize",{"tokens":dv["base_tokens"][max(0,i-12):i]})["content"],
            "baseline_single_token_top":probs_at(r,i),
            "prefix_test":{"tokens":pre["tokens"],"top_at_i":probs_at(pre,0),"picks_dflash_token":pre["tokens"][0]==dv["dflash_tokens"][i],"picks_base_token":pre["tokens"][0]==dv["base_tokens"][i],
                           "next8_match_dflash":pre["tokens"][:8]==dv["dflash_tokens"][i:i+8],"next8_match_base":pre["tokens"][:8]==dv["base_tokens"][i:i+8]}}
stop(p,lf)
# (3) drafter with debug log
p,lf=start("dflash",OUT+"/server-divergence2-dflash.log")
marks={}
for n,dv in DIV.items():
    i=dv["i"]
    lf.flush(); pos0=os.path.getsize(OUT+"/server-divergence2-dflash.log")
    r=post("/completion",dict(GEN,prompt=PROMPTS[n]))
    lf.flush(); pos1=os.path.getsize(OUT+"/server-divergence2-dflash.log")
    marks[n]=(pos0,pos1)
    same=r["tokens"][:i+1]==dv["dflash_tokens"][:i+1]
    res[n]["dflash_rerun_reproduces"]=same
    res[n]["dflash_verify_batch_top"]=probs_at(r,i)
    res[n]["dflash_timings"]={k:r["timings"].get(k) for k in ("draft_n","draft_n_accepted","predicted_n")}
stop(p,lf)
log=open(OUT+"/server-divergence2-dflash.log","rb").read()
for n,(a,b) in marks.items():
    seg=log[a:b].decode(errors="replace")
    steps=[]
    for m in re.finditer(r"add accepted tokens: sampled=(\d+), ids.size=(\d+), n_draft=(\d+)",seg):
        steps.append({"sampled":int(m.group(1)),"ids":int(m.group(2)),"n_draft":int(m.group(3))})
    acc=[(int(m.group(1)),int(m.group(2)),int(m.group(3))) for m in re.finditer(r"accepted (\d+)/(\d+) draft tokens, new n_tokens = (\d+)",seg)]
    i=res[n]["i"]; cum=1; label=None  # gen index 0 is the token sampled off the prompt pass
    for s_idx,s in enumerate(steps):
        lo,hi=cum,cum+s["ids"]-1
        if lo<=i<=hi:
            k=i-lo; label={"step":s_idx,"step_range":[lo,hi],"offset_in_step":k,"accepted_draft_in_step":s["ids"]-1,"n_draft":s["n_draft"],
                           "token_i_was":"accepted draft token" if k<s["ids"]-1 else "target's own sampled token (first mismatch or end of block)",
                           "accept_line":acc[s_idx] if s_idx<len(acc) else None}
            break
        cum+=s["ids"]
    res[n]["dflash_step_log_at_i"]=label; res[n]["dflash_steps_total"]=len(steps)
json.dump(res,open(OUT+"/divergence2.json","w"),indent=1)
for n,x in res.items():
    b=x["baseline_single_token_top"] or []; f=x["dflash_verify_batch_top"] or []; pt=x["prefix_test"]
    def top2(l): return " | ".join(f"{e['id']}{e['tok']!r} {e['p']:.4f}" for e in l[:3])
    print(f"\n{n}: i={x['i']} prompt_n={x['prompt_n']} base={x['base_tok']}{x['pieces']['base']!r} dflash={x['dflash_tok']}{x['pieces']['dflash']!r}  ...{x['context_before']!r}")
    print(f"  baseline single-token top3 : {top2(b)}")
    print(f"  prefix-test (batched, no drafter) top3: {top2(pt['top_at_i'] or [])}  -> picks dflash={pt['picks_dflash_token']} base={pt['picks_base_token']} next8=dflash:{pt['next8_match_dflash']} base:{pt['next8_match_base']}")
    print(f"  drafter verify-batch top3  : {top2(f)}  rerun reproduces={x['dflash_rerun_reproduces']}")
    print(f"  drafter step log at i      : {x['dflash_step_log_at_i']}")
