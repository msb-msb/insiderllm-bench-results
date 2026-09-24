#!/usr/bin/env python3
"""PAIR phase-1 load generator.

Fires N independent chat requests concurrently at one base URL, records per-request
wall time and token counts, and writes a JSON-lines record per rep.

usage: bench.py --base http://127.0.0.1:11434 --label direct --rep 1 --model qwen3.5:9b
"""
import argparse, json, time, urllib.request, urllib.error, concurrent.futures as cf, statistics, sys, os

TOPICS = [
    "how a network router decides where to send a packet",
    "why DDR4 memory bandwidth limits CPU inference speed",
    "what quantization does to a language model's weights",
    "how PCIe lane count affects a GPU used for compute",
    "why the KV cache grows with context length",
    "how mDNS discovers services on a home network",
    "what a LoRA adapter changes inside a transformer",
    "why a used RTX 3090 is popular for local AI",
    "how speculative decoding speeds up token generation",
    "what the difference is between a dense and a mixture-of-experts model",
    "how a reverse proxy differs from a load balancer",
    "why greedy decoding is deterministic",
    "how mutual TLS authenticates both ends of a connection",
    "what happens when a GPU runs out of VRAM during inference",
    "how a page cache affects model load time from disk",
    "why prompt processing is faster than token generation on a GPU",
    "how a systemd timer differs from a cron job",
    "what a tokenizer does before a model sees text",
    "how flash attention reduces memory use",
    "why two machines cannot pool their GPU memory over Ethernet",
]

def one(base, model, i, max_tokens, timeout):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": f"Explain, in about 250 words and without a title, {TOPICS[i % len(TOPICS)]}."}],
        "max_tokens": max_tokens,
        "temperature": 0.0,
        "stream": False,
    }
    req = urllib.request.Request(base + "/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            hdrs = dict(r.headers)
        d = json.loads(raw)
        u = d.get("usage", {})
        return {"i": i, "ok": True, "wall_s": round(time.time() - t0, 3),
                "completion_tokens": u.get("completion_tokens"), "prompt_tokens": u.get("prompt_tokens"),
                "finish": d["choices"][0].get("finish_reason"),
                "hdr": {k: v for k, v in hdrs.items() if k.lower().startswith("x-")}}
    except urllib.error.HTTPError as e:
        return {"i": i, "ok": False, "wall_s": round(time.time() - t0, 3), "status": e.code, "err": e.read()[:200].decode(errors="replace")}
    except Exception as e:
        return {"i": i, "ok": False, "wall_s": round(time.time() - t0, 3), "err": repr(e)[:200]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--rep", type=int, required=True)
    ap.add_argument("--model", default="qwen3.5:9b")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--max-tokens", type=int, default=200)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--out", default=os.path.expanduser("~/pair-bench/results.jsonl"))
    a = ap.parse_args()
    t_start = time.time()
    started_at = time.strftime("%H:%M:%S", time.localtime(t_start))
    with cf.ThreadPoolExecutor(max_workers=a.n) as ex:
        res = list(ex.map(lambda i: one(a.base, a.model, i, a.max_tokens, a.timeout), range(a.n)))
    wall = time.time() - t_start
    oks = [r for r in res if r["ok"]]
    toks = [r["completion_tokens"] for r in oks if r.get("completion_tokens") is not None]
    rec = {"label": a.label, "rep": a.rep, "model": a.model, "base": a.base, "n": a.n,
           "started_at": started_at, "wall_s": round(wall, 3), "ok": len(oks), "failed": len(res) - len(oks),
           "completion_tokens_total": sum(toks), "completion_tokens_mean": round(statistics.mean(toks), 1) if toks else None,
           "per_request_wall_s": [r["wall_s"] for r in res],
           "agg_tok_per_s": round(sum(toks) / wall, 1) if toks else None,
           "requests": res}
    with open(a.out, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(json.dumps({k: rec[k] for k in ("label", "rep", "started_at", "wall_s", "ok", "failed", "completion_tokens_total", "completion_tokens_mean", "agg_tok_per_s")}))
    print("per-request wall_s:", sorted(rec["per_request_wall_s"]))
    errs = [r for r in res if not r["ok"]]
    if errs:
        print("errors:", errs[:3])

if __name__ == "__main__":
    main()
