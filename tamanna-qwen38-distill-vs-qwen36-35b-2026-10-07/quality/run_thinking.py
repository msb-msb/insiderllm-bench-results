#!/usr/bin/env python3
"""SECONDARY, thinking-on pass, docs/candidates/qwen38-35b-distill-vs-qwen36-35b-2026-10.md section 5. No gate.
Same 47 items, same system prompt, same parser and scorer as run_quality.py. Differences, all pre-registered:
enable_thinking true, max_tokens 8192, temperature 0, one pass. The server runs at -c 16384 so prompt + 8,192 fit.
Reasoning tokens = /tokenize count of message.reasoning_content (llama-server lifts the <think> span out of content);
if the server leaves the span in content instead, it is split out here and counted the same way.
The answer scored is content with any <think>...</think> span removed. Items that stop on length are counted (cap hits)."""
import json, sys, os, re, time, argparse, urllib.request
TEN = "/home/minotaur/Desktop/InsiderLLM/docs/bench-results/miu-lora-variance-2026-08-31"
sys.path.insert(0, TEN)
from deployed import INTENT_SYSTEM_PROMPT, SOLO_SHA256
from score_lora import parse_and_sanitise, score
HERE = os.path.dirname(os.path.abspath(__file__))
MAX = 8192
def post(base, path, body, timeout=1800):
    req = urllib.request.Request(base + path, json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))
def ntok(base, text):
    return len(post(base, "/tokenize", {"content": text}, 120)["tokens"]) if text else 0
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("tag"); ap.add_argument("--base", default="http://192.168.x.x:8081")
    a = ap.parse_args()
    items = sorted(json.load(open(os.path.join(TEN, "splits", "test.json"))), key=lambda x: x["idx"])
    props = json.load(urllib.request.urlopen(a.base + "/props", timeout=60))
    out = {"tag": a.tag, "base": a.base, "solo_sha256": SOLO_SHA256, "max_tokens": MAX, "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "server_props": {k: props.get(k) for k in ("model_path", "build_info", "n_ctx", "default_generation_settings", "chat_template") if k in props}, "records": []}
    recs = out["records"]
    for x in items:
        body = {"model": "local", "messages": [{"role": "system", "content": INTENT_SYSTEM_PROMPT}, {"role": "user", "content": x["msg"]}],
                "temperature": 0.0, "max_tokens": MAX, "stream": False, "chat_template_kwargs": {"enable_thinking": True}}
        t = time.perf_counter(); r = post(a.base, "/v1/chat/completions", body); el = time.perf_counter() - t
        m = r["choices"][0]["message"]; content = m.get("content") or ""; reasoning = m.get("reasoning_content") or ""
        mm = re.search(r"<think>(.*?)(</think>|$)", content, re.S)
        if mm and not reasoning: reasoning = mm.group(1)
        answer = re.sub(r"<think>.*?(</think>|$)", "", content, flags=re.S).strip()
        pred = parse_and_sanitise(answer, x["msg"]); ex, ef = score(pred, x["gold"])
        rec = {"idx": x["idx"], "gold": x["gold"], "pred": {f: pred[f] for f in ("tool", "mode", "scope")}, "via": pred["via"], "exact": ex,
               "reasoning_tokens": ntok(a.base, reasoning), "answer_tokens": ntok(a.base, answer), "usage": r.get("usage", {}),
               "finish_reason": r["choices"][0].get("finish_reason"), "wall_s": round(el, 3), "answer": answer, "reasoning": reasoning}
        recs.append(rec)
        print(f"{a.tag} idx {x['idx']:>2}  exact {int(ex)}  reasoning {rec['reasoning_tokens']:>5}  completion {rec['usage'].get('completion_tokens')}  {rec['finish_reason']}  {el:.1f}s", flush=True)
        json.dump(out, open(os.path.join(HERE, f"thinking-{a.tag}.json"), "w"), indent=1)
    rt = sorted(r["reasoning_tokens"] for r in recs)
    out["summary"] = {"exact": sum(r["exact"] for r in recs), "per_field": {f: sum(r["pred"][f] == r["gold"][f] for r in recs) for f in ("tool", "mode", "scope")},
                      "unparseable": sum(r["via"] == "unparseable" for r in recs), "cap_hits": sum(r["finish_reason"] == "length" for r in recs),
                      "reasoning_tokens_median": rt[len(rt) // 2] if len(rt) % 2 else (rt[len(rt)//2 - 1] + rt[len(rt)//2]) / 2,
                      "reasoning_tokens_mean": round(sum(rt) / len(rt), 1), "reasoning_tokens_total": sum(rt),
                      "completion_tokens_total": sum(r["usage"].get("completion_tokens", 0) for r in recs), "wall_s_total": round(sum(r["wall_s"] for r in recs), 1)}
    print(json.dumps(out["summary"]), flush=True)
    json.dump(out, open(os.path.join(HERE, f"thinking-{a.tag}.json"), "w"), indent=1)
if __name__ == "__main__": main()
