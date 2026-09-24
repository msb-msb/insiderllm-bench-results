#!/usr/bin/env python3
"""Fan the same 20 requests out through mycoSwarm's task API on Miu's daemon.

Each request is one POST /task (task_type=inference, chat payload, max_tokens=200,
temperature 0.0). The daemon routes each task locally or to a peer. We poll
GET /task/{id} on Miu until completed and record node_id and duration.
"""
import argparse, json, os, time, uuid, urllib.request, urllib.error, concurrent.futures as cf, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench import TOPICS

BASE = "http://127.0.0.1:7890"
TOKEN = open(os.path.expanduser("~/.config/mycoswarm/swarm-token")).read().strip()
NODE_ID = open(os.path.expanduser("~/.config/mycoswarm/node_id")).read().strip()
H = {"Content-Type": "application/json", "X-Swarm-Token": TOKEN}

def call(method, path, body=None, base=BASE, timeout=30):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None, headers=H, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def one(i, model, max_tokens, timeout):
    tid = f"pairbench-{uuid.uuid4().hex[:8]}"
    task = {"task_id": tid, "task_type": "inference",
            "payload": {"model": model, "max_tokens": max_tokens, "temperature": 0.0, "think": False,
                        "messages": [{"role": "user", "content": f"Explain, in about 250 words and without a title, {TOPICS[i % len(TOPICS)]}."}]},
            "source_node": NODE_ID, "priority": 5, "timeout_seconds": timeout}
    t0 = time.time()
    try:
        sub = call("POST", "/task", task)
    except urllib.error.HTTPError as e:
        return {"i": i, "ok": False, "wall_s": round(time.time() - t0, 3), "status": e.code, "err": e.read()[:200].decode(errors="replace")}
    except Exception as e:
        return {"i": i, "ok": False, "wall_s": round(time.time() - t0, 3), "err": repr(e)[:200]}
    target = (sub.get("target_ip"), sub.get("target_port"))
    deadline = t0 + timeout
    while time.time() < deadline:
        time.sleep(0.5)
        try:
            d = call("GET", f"/task/{tid}")
        except Exception:
            continue
        st = d.get("status")
        if st == "completed":
            res = d.get("result") or {}
            return {"i": i, "ok": True, "wall_s": round(time.time() - t0, 3), "node_id": d.get("node_id"),
                    "duration_s": d.get("duration_seconds"), "tok_per_s": res.get("tokens_per_second"),
                    "model": res.get("model"), "eval_count": res.get("eval_count"), "submit_target": target,
                    "resp_chars": len(res.get("response", "") or "")}
        if st == "failed":
            return {"i": i, "ok": False, "wall_s": round(time.time() - t0, 3), "err": str(d.get("error"))[:200], "node_id": d.get("node_id")}
    return {"i": i, "ok": False, "wall_s": round(time.time() - t0, 3), "err": "client poll timeout"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rep", type=int, required=True)
    ap.add_argument("--model", default="qwen3.5:9b")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--max-tokens", type=int, default=200)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--out", default=os.path.expanduser("~/pair-bench/results-myco.jsonl"))
    a = ap.parse_args()
    t0 = time.time(); started = time.strftime("%H:%M:%S", time.localtime(t0))
    with cf.ThreadPoolExecutor(max_workers=a.n) as ex:
        res = list(ex.map(lambda i: one(i, a.model, a.max_tokens, a.timeout), range(a.n)))
    wall = time.time() - t0
    oks = [r for r in res if r["ok"]]
    split = {}
    for r in oks: split[r.get("node_id")] = split.get(r.get("node_id"), 0) + 1
    rec = {"label": "myco", "rep": a.rep, "model": a.model, "n": a.n, "started_at": started, "wall_s": round(wall, 3),
           "ok": len(oks), "failed": len(res) - len(oks), "split": split,
           "per_request_wall_s": [r["wall_s"] for r in res], "requests": res}
    with open(a.out, "a") as f: f.write(json.dumps(rec) + "\n")
    print(json.dumps({k: rec[k] for k in ("label", "rep", "started_at", "wall_s", "ok", "failed", "split")}))
    print("per-request wall_s:", sorted(rec["per_request_wall_s"]))
    for n in split:
        ds = [r["duration_s"] for r in oks if r.get("node_id") == n and r.get("duration_s") is not None]
        tps = [r["tok_per_s"] for r in oks if r.get("node_id") == n and r.get("tok_per_s")]
        if ds: print(f"  {n}: n={len(ds)} service mean={statistics.mean(ds):.2f}s tok/s mean={statistics.mean(tps):.1f}" if tps else f"  {n}: n={len(ds)}")
    errs = [r for r in res if not r["ok"]]
    if errs: print("errors:", errs[:3])

if __name__ == "__main__":
    main()
