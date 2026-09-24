#!/usr/bin/env python3
"""Run one arm of the WikiSkill one-shot experiment against llama-server.

Replicates solo.intent_classify()'s post-model pipeline EXACTLY -- fence strip,
per-field sanitise to the default, then the two overrides (past-reference forces
scope=session; docs+web_and_rag -> rag). Scoring raw model output instead of the
system's output would misrepresent what production does; scoring only the system
would hide schema defects. Both are recorded.

Usage: run_arm.py <tag> <split[,split...]> <reps> [--think] [--skill FILE]
"""
import json, sys, time, urllib.request, urllib.error, argparse, os, hashlib
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
    # override 1: regex past-reference forces session scope
    if detect_past_reference(query):
        result["scope"] = "session"
    # override 2: docs scope never needs web search
    if result["scope"] == "docs" and result["tool"] == "web_and_rag":
        result["tool"] = "rag"
    rec.update(result)
    return rec

def score(pred, gold):
    exact = all(pred[f] == gold[f] for f in ("tool", "mode", "scope"))
    # 'effective' ignores scope unless gold tool actually uses retrieval
    if gold["tool"] in ("rag", "web_and_rag"):
        eff = exact
    else:
        eff = pred["tool"] == gold["tool"] and pred["mode"] == gold["mode"]
    return exact, eff

def call(system, msg, think, maxtok):
    body = {"model": "local",
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": msg}],
            "temperature": 0.0, "max_tokens": maxtok, "stream": False}
    if not think:
        body["chat_template_kwargs"] = {"enable_thinking": False}
    t = time.time()
    req = urllib.request.Request(URL, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=900))
    el = time.time() - t
    m = r["choices"][0]["message"]
    return (m.get("content") or ""), (m.get("reasoning_content") or ""), r["usage"], el

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tag"); ap.add_argument("splits"); ap.add_argument("reps", type=int)
    ap.add_argument("--think", action="store_true")
    ap.add_argument("--skill", default=None)
    ap.add_argument("--maxtok", type=int, default=None)
    ap.add_argument("--outdir", default="baseline")
    a = ap.parse_args()

    system = INTENT_SYSTEM_PROMPT
    skill_sha = None
    if a.skill:
        sk = open(a.skill).read()
        skill_sha = hashlib.sha256(sk.encode()).hexdigest()
        system = INTENT_SYSTEM_PROMPT + "\n\n" + sk
    maxtok = a.maxtok if a.maxtok else (2048 if a.think else 100)

    items = []
    for s in a.splits.split(","):
        items += json.load(open(os.path.join(HERE, "splits", f"{s}.json")))
    items.sort(key=lambda x: x["idx"])

    runs = []
    for rep in range(a.reps):
        recs, t0 = [], time.time()
        for x in items:
            content, reasoning, usage, el = call(system, x["msg"], a.think, maxtok)
            pred = parse_and_sanitise(content, x["msg"])
            ex, ef = score(pred, x["gold"])
            recs.append({"idx": x["idx"], "msg": x["msg"], "gold": x["gold"],
                         "pred": {k: pred[k] for k in ("tool", "mode", "scope")},
                         "raw": content, "raw_valid": pred["raw_valid"],
                         "via": pred["via"], "exact": ex, "effective": ef,
                         "reasoning_chars": len(reasoning),
                         "prompt_tokens": usage["prompt_tokens"],
                         "completion_tokens": usage["completion_tokens"],
                         "elapsed_s": round(el, 3)})
        n = len(recs)
        summ = {"rep": rep, "n": n,
                "exact": sum(r["exact"] for r in recs),
                "effective": sum(r["effective"] for r in recs),
                "raw_valid": sum(r["raw_valid"] for r in recs),
                "unparseable": sum(r["via"] == "unparseable" for r in recs),
                "prompt_tokens": sum(r["prompt_tokens"] for r in recs),
                "completion_tokens": sum(r["completion_tokens"] for r in recs),
                "wall_s": round(time.time() - t0, 1)}
        summ["exact_pct"] = round(100 * summ["exact"] / n, 2)
        summ["effective_pct"] = round(100 * summ["effective"] / n, 2)
        runs.append({"summary": summ, "records": recs})
        print(f"  rep {rep}: exact {summ['exact']}/{n} = {summ['exact_pct']}%  "
              f"eff {summ['effective_pct']}%  raw_valid {summ['raw_valid']}/{n}  "
              f"tok(p/c) {summ['prompt_tokens']}/{summ['completion_tokens']}  "
              f"{summ['wall_s']}s", flush=True)

    out = {"tag": a.tag, "splits": a.splits, "reps": a.reps, "think": a.think,
           "max_tokens": maxtok, "skill": a.skill, "skill_sha256": skill_sha,
           "solo_sha256": SOLO_SHA256, "model": "Qwen3.6-27B-Q4_K_M",
           "server": "llama-server -ngl 99 -fa on -c 4096 --jinja --no-mmap",
           "runs": runs}
    os.makedirs(os.path.join(HERE, a.outdir), exist_ok=True)
    path = os.path.join(HERE, a.outdir, f"{a.tag}.json")
    json.dump(out, open(path, "w"), indent=1)
    ex = [r["summary"]["exact_pct"] for r in runs]
    print(f"  -> {os.path.relpath(path, HERE)}  exact across reps: {ex}")

if __name__ == "__main__":
    main()
