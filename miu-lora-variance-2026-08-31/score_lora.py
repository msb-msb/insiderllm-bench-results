#!/usr/bin/env python3
"""Score adapters through llama-server using PER-REQUEST adapter selection.

This is the same deployed pipeline as run_arm.py (fence strip, per-field
sanitise, both overrides) -- the only difference is HOW the skill is installed.
run_arm.py appends text to the system prompt; this sends the stock prompt and
selects a LoRA with the per-request `lora` field:

    {"lora": [{"id": N, "scale": 1.0}], ...}

Adapters not listed default to scale 0, so one id selects exactly one adapter.
That is the Mixture-of-LoRA routing primitive, and whether it works as
documented is a finding in its own right -- pass --id -1 to score with every
adapter at scale 0, which must reproduce the no-adapter baseline exactly.
"""
import json, sys, time, urllib.request, argparse, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deployed import (INTENT_SYSTEM_PROMPT, INTENT_DEFAULT, VALID_TOOLS,
                      VALID_MODES, VALID_SCOPES, detect_past_reference, SOLO_SHA256)

URL = "http://127.0.0.1:8081/v1/chat/completions"
HERE = os.path.dirname(os.path.abspath(__file__))


def parse_and_sanitise(raw, query):
    """Mirror of solo.intent_classify() from the raw string onward."""
    rec = {"raw_valid": False, "via": "model"}
    r = raw.strip().strip("`").strip()
    if r.startswith("json"):
        r = r[4:].strip()
    try:
        data = json.loads(r)
        if not isinstance(data, dict):
            raise ValueError("not an object")
    except (json.JSONDecodeError, ValueError):
        result = dict(INTENT_DEFAULT)
        low = r.lower()
        for cat in ("web_and_rag", "web_search", "rag", "answer"):
            if cat in low:
                result["tool"] = cat
                break
        rec.update(result); rec["via"] = "unparseable"
        return rec
    result = dict(INTENT_DEFAULT)
    ok = True
    for field, valid in (("tool", VALID_TOOLS), ("mode", VALID_MODES),
                         ("scope", VALID_SCOPES)):
        v = data.get(field, INTENT_DEFAULT[field])
        if v in valid:
            result[field] = v
        else:
            ok = False
    rec["raw_valid"] = ok
    if detect_past_reference(query):
        result["scope"] = "session"
    if result["scope"] == "docs" and result["tool"] == "web_and_rag":
        result["tool"] = "rag"
    rec.update(result)
    return rec


def score(pred, gold):
    exact = all(pred[f] == gold[f] for f in ("tool", "mode", "scope"))
    if gold["tool"] in ("rag", "web_and_rag"):
        eff = exact
    else:
        eff = pred["tool"] == gold["tool"] and pred["mode"] == gold["mode"]
    return exact, eff


def call(msg, lora_id, maxtok=100):
    body = {"model": "local",
            "messages": [{"role": "system", "content": INTENT_SYSTEM_PROMPT},
                         {"role": "user", "content": msg}],
            "temperature": 0.0, "max_tokens": maxtok, "stream": False,
            "chat_template_kwargs": {"enable_thinking": False}}
    if lora_id is not None and lora_id >= 0:
        body["lora"] = [{"id": lora_id, "scale": 1.0}]
    elif lora_id is not None:            # -1 => all adapters explicitly off
        body["lora"] = []
    t = time.time()
    req = urllib.request.Request(URL, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=900))
    m = r["choices"][0]["message"]
    return (m.get("content") or ""), r["usage"], time.time() - t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("--id", type=int, default=None,
                    help="adapter id for per-request selection; -1 = all off")
    ap.add_argument("--split", default="test")
    ap.add_argument("--outdir", default="scored")
    a = ap.parse_args()

    items = json.load(open(os.path.join(HERE, "splits", f"{a.split}.json")))
    items.sort(key=lambda x: x["idx"])

    recs, t0 = [], time.time()
    for x in items:
        content, usage, el = call(x["msg"], a.id)
        pred = parse_and_sanitise(content, x["msg"])
        ex, ef = score(pred, x["gold"])
        recs.append({"idx": x["idx"], "msg": x["msg"], "gold": x["gold"],
                     "pred": {k: pred[k] for k in ("tool", "mode", "scope")},
                     "raw": content, "raw_valid": pred["raw_valid"],
                     "via": pred["via"], "exact": ex, "effective": ef,
                     "prompt_tokens": usage["prompt_tokens"],
                     "completion_tokens": usage["completion_tokens"],
                     "elapsed_s": round(el, 3)})
    n = len(recs)
    summ = {"n": n, "lora_id": a.id,
            "exact": sum(r["exact"] for r in recs),
            "effective": sum(r["effective"] for r in recs),
            "raw_valid": sum(r["raw_valid"] for r in recs),
            "unparseable": sum(r["via"] == "unparseable" for r in recs),
            "prompt_tokens": sum(r["prompt_tokens"] for r in recs),
            "completion_tokens": sum(r["completion_tokens"] for r in recs),
            "wall_s": round(time.time() - t0, 1)}
    summ["exact_pct"] = round(100 * summ["exact"] / n, 2)
    summ["effective_pct"] = round(100 * summ["effective"] / n, 2)
    os.makedirs(os.path.join(HERE, a.outdir), exist_ok=True)
    path = os.path.join(HERE, a.outdir, f"{a.tag}.json")
    json.dump({"tag": a.tag, "lora_id": a.id, "split": a.split,
               "solo_sha256": SOLO_SHA256, "model": "Qwen3.6-27B-Q4_K_M",
               "summary": summ, "records": recs}, open(path, "w"), indent=1)
    print(f"  {a.tag}: lora_id={a.id} exact {summ['exact']}/{n} = {summ['exact_pct']}%  "
          f"eff {summ['effective_pct']}%  raw_valid {summ['raw_valid']}/{n}  "
          f"tok(p/c) {summ['prompt_tokens']}/{summ['completion_tokens']}  {summ['wall_s']}s")


if __name__ == "__main__":
    main()
