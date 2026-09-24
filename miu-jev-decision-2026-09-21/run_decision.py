#!/usr/bin/env python3
"""Phase 1 of the Jev-mode test: choose (POST /v1/decision) vs write (/v1/chat/completions)
on the frozen 47-item ten-seeds test split, same server, same session.

Choose: instructions = the deployed intent system prompt, unchanged; schema = the three
fields with their deployed label sets (order as listed in the prompt), descriptions = the prompt's own
field-header phrases (the endpoint requires one);
one context per request so each item has its own wall-clock. The decision object goes
through the same parse_and_sanitise() as the written answer (past-reference override,
docs/web_and_rag override), then score() exact match.
Write: identical to score_lora.py's call() -- temperature 0, max_tokens 100, thinking off.
"""
import json, sys, os, time, argparse, urllib.request, statistics
TEN = "/home/minotaur/Desktop/InsiderLLM/docs/bench-results/miu-lora-variance-2026-08-31"
sys.path.insert(0, TEN)
from deployed import (INTENT_SYSTEM_PROMPT, INTENT_DEFAULT, VALID_TOOLS, VALID_MODES,
                      VALID_SCOPES, SOLO_SHA256)
from score_lora import parse_and_sanitise, score

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "http://127.0.0.1:8081"
TOOLS = ["answer", "web_search", "rag", "web_and_rag"]
MODES = ["recall", "explore", "execute", "chat"]
SCOPES = ["session", "docs", "facts", "all"]
assert set(TOOLS) == VALID_TOOLS and set(MODES) == VALID_MODES and set(SCOPES) == VALID_SCOPES
# The endpoint rejects a field without a description (HTTP 400 "field \"tool\" needs a description",
# 2026-09-21). These are the three field-header phrases from the system prompt, verbatim, so the
# instructions stay unchanged and the catalogue adds nothing the write path did not see.
SCHEMA = {"tool": {"type": "enum", "choices": TOOLS, "description": "what tools are needed"},
          "mode": {"type": "enum", "choices": MODES, "description": "what kind of thinking"},
          "scope": {"type": "enum", "choices": SCOPES,
                    "description": "where to search (only matters when tool is rag or web_and_rag)"}}
for _f, _d in (("tool", "tool — what tools are needed"), ("mode", "mode — what kind of thinking"),
               ("scope", "scope — where to search (only matters when tool is rag or web_and_rag)")):
    assert _d in INTENT_SYSTEM_PROMPT, _d


def post(path, body, timeout=900):
    req = urllib.request.Request(BASE + path, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    t = time.perf_counter()
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    return r, time.perf_counter() - t


def choose(msg, mode):
    body = {"model": "local", "instructions": INTENT_SYSTEM_PROMPT, "schema": SCHEMA,
            "contexts": [msg], "mode": mode}
    r, el = post("/v1/decision", body)
    res = r["results"][0]
    return res, r.get("usage", {}), r.get("timings", {}), el


def write(msg):
    body = {"model": "local",
            "messages": [{"role": "system", "content": INTENT_SYSTEM_PROMPT},
                         {"role": "user", "content": msg}],
            "temperature": 0.0, "max_tokens": 100, "stream": False,
            "chat_template_kwargs": {"enable_thinking": False}}
    r, el = post("/v1/chat/completions", body)
    return (r["choices"][0]["message"].get("content") or ""), r["usage"], r.get("timings", {}), el


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", choices=["choose", "write"])
    ap.add_argument("tag")
    ap.add_argument("--mode", default="tree")
    a = ap.parse_args()
    items = sorted(json.load(open(os.path.join(TEN, "splits", "test.json"))), key=lambda x: x["idx"])
    recs = []
    for x in items:
        if a.path == "choose":
            res, usage, tim, el = choose(x["msg"], a.mode)
            raw = json.dumps(res["decision"])
            pred = parse_and_sanitise(raw, x["msg"])
            ex, ef = score(pred, x["gold"])
            fields = {k: {"value": v["value"], "probability": v["probability"],
                          "scored_nodes": v.get("scored_nodes"), "tree": v.get("tree")}
                      for k, v in res["fields"].items()}
            recs.append({"idx": x["idx"], "msg": x["msg"], "gold": x["gold"],
                         "decision": res["decision"], "fields": fields,
                         "pred": {k: pred[k] for k in ("tool", "mode", "scope")},
                         "exact": ex, "effective": ef, "raw_valid": pred["raw_valid"],
                         "min_prob": min(v["probability"] for v in fields.values()),
                         "prod_prob": fields["tool"]["probability"] * fields["mode"]["probability"] * fields["scope"]["probability"],
                         "usage": usage, "timings": tim, "wall_s": round(el, 4)})
        else:
            content, usage, tim, el = write(x["msg"])
            pred = parse_and_sanitise(content, x["msg"])
            ex, ef = score(pred, x["gold"])
            recs.append({"idx": x["idx"], "msg": x["msg"], "gold": x["gold"], "raw": content,
                         "pred": {k: pred[k] for k in ("tool", "mode", "scope")},
                         "exact": ex, "effective": ef, "raw_valid": pred["raw_valid"], "via": pred["via"],
                         "prompt_tokens": usage["prompt_tokens"], "completion_tokens": usage["completion_tokens"],
                         "timings": tim, "wall_s": round(el, 4)})
    n = len(recs); walls = sorted(r["wall_s"] for r in recs)
    summ = {"n": n, "exact": sum(r["exact"] for r in recs), "effective": sum(r["effective"] for r in recs),
            "raw_valid": sum(r["raw_valid"] for r in recs),
            "per_field": {f: sum(r["pred"][f] == r["gold"][f] for r in recs) for f in ("tool", "mode", "scope")},
            "wall_mean_s": round(statistics.mean(walls), 4), "wall_median_s": round(statistics.median(walls), 4),
            "wall_p95_s": round(walls[int(round(0.95 * (n - 1)))], 4), "wall_min_s": walls[0], "wall_max_s": walls[-1]}
    summ["exact_pct"] = round(100 * summ["exact"] / n, 2)
    out = {"tag": a.tag, "path": a.path, "mode": a.mode if a.path == "choose" else None,
           "schema": SCHEMA if a.path == "choose" else None, "solo_sha256": SOLO_SHA256,
           "model": "Qwen_Qwen3.6-27B-Q4_K_M.gguf", "summary": summ, "records": recs}
    os.makedirs(os.path.join(HERE, "raw"), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, "raw", f"{a.tag}.json"), "w"), indent=1)
    print(f"{a.tag}: {a.path} exact {summ['exact']}/{n} ({summ['exact_pct']}%) per-field {summ['per_field']} "
          f"raw_valid {summ['raw_valid']} wall mean {summ['wall_mean_s']}s p95 {summ['wall_p95_s']}s")


if __name__ == "__main__":
    main()
