#!/usr/bin/env python3
"""Same-request benchmark for Ollama (/api/chat) and llama-server (/v1/chat/completions).

Each run starts with a random nonce so neither server can reuse a cached prompt.
Speeds come from each server's own timing fields; time to first token is measured
by this client from request start to the first non-empty content chunk.
"""
import argparse, json, statistics, subprocess, time, urllib.request, uuid, sys

SHORT = "Write a long, detailed essay of at least 2000 words about the history of the bicycle, with many sections."
LONG_TAIL = "\n\nSummarize the text above in five bullet points."


def prompt(kind):
    nonce = f"Request id {uuid.uuid4().hex}.\n"
    if kind == "short":
        return nonce + SHORT
    return nonce + open("long-context.txt").read() + LONG_TAIL


def stream(req):
    with urllib.request.urlopen(req, timeout=900) as r:
        for line in r:
            yield line.decode().strip()


def run_ollama(url, model, p, n, ctx, gpu):
    body = {"model": model, "messages": [{"role": "user", "content": p}], "think": False, "stream": True,
            "options": {"temperature": 0, "seed": 42, "num_predict": n}}
    if ctx:
        body["options"]["num_ctx"] = ctx
    if not gpu:
        body["options"]["num_gpu"] = 0
    req = urllib.request.Request(url + "/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"})
    t0 = time.perf_counter(); ttft = None
    for line in stream(req):
        if not line:
            continue
        d = json.loads(line)
        if ttft is None and d.get("message", {}).get("content"):
            ttft = time.perf_counter() - t0
        if d.get("done"):
            return {"ttft_s": ttft, "wall_s": time.perf_counter() - t0,
                    "prompt_tokens": d["prompt_eval_count"], "pp_tps": d["prompt_eval_count"] / (d["prompt_eval_duration"] / 1e9),
                    "gen_tokens": d["eval_count"], "tg_tps": d["eval_count"] / (d["eval_duration"] / 1e9),
                    "load_s": d.get("load_duration", 0) / 1e9}


def run_llama(url, model, p, n, ctx, gpu):
    body = {"messages": [{"role": "user", "content": p}], "max_tokens": n, "temperature": 0, "seed": 42,
            "stream": True, "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(url + "/v1/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json"})
    t0 = time.perf_counter(); ttft = None; timings = None
    for line in stream(req):
        if not line.startswith("data: ") or line == "data: [DONE]":
            continue
        d = json.loads(line[6:])
        ch = d.get("choices") or [{}]
        if ttft is None and (ch[0].get("delta") or {}).get("content"):
            ttft = time.perf_counter() - t0
        if "timings" in d:
            timings = d["timings"]
    t = timings
    return {"ttft_s": ttft, "wall_s": time.perf_counter() - t0, "prompt_tokens": t["prompt_n"], "pp_tps": t["prompt_per_second"],
            "gen_tokens": t["predicted_n"], "tg_tps": t["predicted_per_second"], "load_s": 0}


ap = argparse.ArgumentParser()
ap.add_argument("engine", choices=["ollama", "llama"])
ap.add_argument("--url", required=True)
ap.add_argument("--model", default="")
ap.add_argument("--prompt", choices=["short", "long"], default="short")
ap.add_argument("-n", type=int, default=512)
ap.add_argument("--ctx", type=int, default=8192)
ap.add_argument("--runs", type=int, default=5)
ap.add_argument("--cpu", action="store_true")
ap.add_argument("--label", default="")
ap.add_argument("--out", default="results.jsonl")
ap.add_argument("--cool", type=int, default=0, help="wait until GPU temp <= this before each run")
a = ap.parse_args()
fn = run_ollama if a.engine == "ollama" else run_llama
fn(a.url, a.model, prompt(a.prompt), 32, a.ctx, not a.cpu)  # warm-up, not recorded
rows = []
def gpu_temp():
    return int(subprocess.check_output(["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"]).decode().strip())


for i in range(a.runs):
    while a.cool and gpu_temp() > a.cool:
        time.sleep(2)
    t_start = gpu_temp()
    r = fn(a.url, a.model, prompt(a.prompt), a.n, a.ctx, not a.cpu)
    r["temp_start"] = t_start
    r["temp_end"] = gpu_temp()
    rows.append(r)
    print(json.dumps({"run": i + 1, **{k: round(v, 3) if isinstance(v, float) else v for k, v in r.items()}}), file=sys.stderr)
med = {k: round(statistics.median(r[k] for r in rows), 3) for k in ["ttft_s", "wall_s", "prompt_tokens", "pp_tps", "gen_tokens", "tg_tps"]}
out = {"label": a.label, "engine": a.engine, "prompt": a.prompt, "n": a.n, "ctx": a.ctx, "cpu": a.cpu, "runs": a.runs, "median": med, "all": rows}
print(json.dumps(out))
with open(a.out, "a") as f:
    f.write(json.dumps(out) + "\n")
