#!/usr/bin/env python3
"""Quality half of the pre-registered Bonsai 2 27B vs Qwen3.8-27B comparison (docs/candidates/bonsai-2-27b-2026-09-23.md A5).
The 47-item frozen ten-seeds test split, WRITE path only, byte-identical to run_decision.write() from the Jev-mode work:
POST /v1/chat/completions, system = the deployed intent prompt (solo.py, sha256 asserted), user = the message,
temperature 0, max_tokens 100, thinking off via chat_template_kwargs. Parsed with parse_and_sanitise(), scored exact-match.
Runs from Miu (where solo.py lives) against a llama-server on Tamanna. Two passes per model to show determinism."""
import json, sys, os, time, argparse, urllib.request
TEN = "/home/minotaur/Desktop/InsiderLLM/docs/bench-results/miu-lora-variance-2026-08-31"
sys.path.insert(0, TEN)
from deployed import INTENT_SYSTEM_PROMPT, SOLO_SHA256
from score_lora import parse_and_sanitise, score
HERE = os.path.dirname(os.path.abspath(__file__))
def write(base, msg):
    body = {"model": "local", "messages": [{"role": "system", "content": INTENT_SYSTEM_PROMPT}, {"role": "user", "content": msg}],
            "temperature": 0.0, "max_tokens": 100, "stream": False, "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(base + "/v1/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json"})
    t = time.perf_counter(); r = json.load(urllib.request.urlopen(req, timeout=900)); el = time.perf_counter() - t
    return (r["choices"][0]["message"].get("content") or ""), r.get("usage", {}), r.get("timings", {}), el
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("tag"); ap.add_argument("--base", default="http://192.168.x.x:8081"); ap.add_argument("--passes", type=int, default=2)
    a = ap.parse_args()
    items = sorted(json.load(open(os.path.join(TEN, "splits", "test.json"))), key=lambda x: x["idx"])
    props = json.load(urllib.request.urlopen(a.base + "/props", timeout=60))
    out = {"tag": a.tag, "base": a.base, "solo_sha256": SOLO_SHA256, "split": "ten-seeds splits/test.json (47)", "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "server_props": {k: props.get(k) for k in ("model_path", "build_info", "n_ctx", "default_generation_settings", "chat_template") if k in props}, "passes": []}
    for p in range(a.passes):
        recs = []
        for x in items:
            content, usage, timings, el = write(a.base, x["msg"])
            pred = parse_and_sanitise(content, x["msg"]); ex, ef = score(pred, x["gold"])
            recs.append({"idx": x["idx"], "msg": x["msg"], "gold": x["gold"], "raw": content, "pred": {f: pred[f] for f in ("tool", "mode", "scope")}, "via": pred["via"], "raw_valid": pred["raw_valid"],
                         "exact": ex, "effective": ef, "usage": usage, "wall_s": round(el, 3), "thinking_leak": "<think>" in content})
        n = sum(r["exact"] for r in recs)
        out["passes"].append({"pass": p + 1, "exact": n, "effective": sum(r["effective"] for r in recs), "per_field": {f: sum(r["pred"][f] == r["gold"][f] for r in recs) for f in ("tool", "mode", "scope")},
                              "schema_valid": sum(r["raw_valid"] for r in recs), "unparseable": sum(r["via"] == "unparseable" for r in recs), "thinking_leaks": sum(r["thinking_leak"] for r in recs),
                              "mean_wall_s": round(sum(r["wall_s"] for r in recs) / len(recs), 3), "records": recs})
        print(f"{a.tag} pass {p+1}: exact {n}/47  effective {out['passes'][-1]['effective']}  fields {out['passes'][-1]['per_field']}  valid {out['passes'][-1]['schema_valid']}  unparseable {out['passes'][-1]['unparseable']}  think-leaks {out['passes'][-1]['thinking_leaks']}  wall {out['passes'][-1]['mean_wall_s']} s", flush=True)
    if a.passes > 1:
        p1, p2 = out["passes"][0]["records"], out["passes"][1]["records"]
        out["determinism"] = {"identical_preds": sum(x["pred"] == y["pred"] for x, y in zip(p1, p2)), "identical_raw": sum(x["raw"] == y["raw"] for x, y in zip(p1, p2))}
        print(f"  determinism: {out['determinism']}")
    json.dump(out, open(os.path.join(HERE, f"raw-{a.tag}.json"), "w"), indent=1)
if __name__ == "__main__": main()
