#!/usr/bin/env python3
"""Observation, not a result (Mark 2026-11-24): does server RssAnon growth per request come from the host prompt
cache (--cache-ram, default 8192 MiB)? M-IQ3 command (lock N2) + EXTRA args, 5 requests of the 512 prompt, same
request shape as bench_nariq.py (fresh nonce, thinking off, temperature 0, cache_prompt false, ignore_eos, 256 tokens).
  ramcheck.py OUTDIR LABEL [EXTRA ARGS...]
"""
import json, os, random, subprocess, sys, time, urllib.request
W = os.path.expanduser("~/nariq-2026-11"); H = os.path.dirname(os.path.abspath(__file__))
out, label, extra = sys.argv[1], sys.argv[2], sys.argv[3:]
cmd = [f"{W}/mainline/build/bin/llama-server", "-m", f"{W}/model/Qwen3.8-27B-UD-IQ3_XXS.gguf", "-ngl", "99", "-fa", "on",
       "-c", "8192", "-np", "1", "--fit", "off", "-lm", "mmap", "-t", "4", "--port", "8081"] + extra
prompt = open(f"{H}/prompt-512.txt", encoding="utf-8").read()

def rss(pid):
    d = {}
    for l in open(f"/proc/{pid}/status"):
        k = l.split(":")[0]
        if k in ("VmRSS", "RssAnon", "RssFile"):
            d[k] = int(l.split()[1]) // 1024
    return d

def post(path, body):
    r = urllib.request.Request(f"http://127.0.0.1:8081{path}", json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=600))

log = open(f"{out}/ramcheck-{label}-server.log", "w")
p = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
for _ in range(600):
    try:
        if json.load(urllib.request.urlopen("http://127.0.0.1:8081/health", timeout=2)).get("status") == "ok":
            break
    except Exception:
        pass
    time.sleep(1)
rows = [{"after": "load", **rss(p.pid)}]
for i in range(1, 6):
    nonce = "%08x" % random.getrandbits(32)
    r = post("/v1/chat/completions", {"temperature": 0, "cache_prompt": False, "ignore_eos": True, "max_tokens": 256,
             "chat_template_kwargs": {"enable_thinking": False},
             "messages": [{"role": "user", "content": f"request {nonce}\n{prompt}\n\nSummarise what this code does."}]})
    t = r.get("timings", {})
    time.sleep(1)
    rows.append({"after": f"req{i}", "prompt_n": t.get("prompt_n"), "cache_n": t.get("cache_n"),
                 "predicted_n": t.get("predicted_n"), **rss(p.pid)})
p.terminate(); p.wait(30)
res = {"label": label, "cmd": cmd, "rows": rows}
json.dump(res, open(f"{out}/ramcheck-{label}.json", "w"), indent=1)
for r in rows:
    print(label, r)
