#!/usr/bin/env python3
"""Phase 2. Same server line as phase 1. Modes:
  choose        single-pass reference (phase-1 schema), one request per item
  twopass       pass 1 tool+mode; pass 2 scope, with "tool: X, mode: Y" appended to the item CONTEXT
  twopass_instr pass 2 with the line appended to the INSTRUCTIONS instead (prefix varies per item)
  twopass_seq   same as twopass, but all 47 pass-1 calls first, then all 47 pass-2 calls, so each pass's
                prefix stays cached (twopass alternates schemas per item and evicts the one cached prefix)
  write_short   system prompt + "Respond with only the three values as tool/mode/scope"  (bare values)
  write_json    phase-1 request re-run in this session (the prompt's own compact JSON)
  write_pretty  system prompt + ask for the JSON pretty-printed one field per line
  write_reason  system prompt + ask for a fourth field "reason", one sentence, ignored by the scorer
"""
import json, sys, os, time, argparse, urllib.request, statistics
TEN = "/home/minotaur/Desktop/InsiderLLM/docs/bench-results/miu-lora-variance-2026-08-31"
P1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, TEN); sys.path.insert(0, P1)
from deployed import INTENT_SYSTEM_PROMPT, INTENT_DEFAULT, SOLO_SHA256
from score_lora import parse_and_sanitise, score
from run_decision import SCHEMA, TOOLS, MODES, SCOPES, post

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_TM = {k: SCHEMA[k] for k in ("tool", "mode")}
SCHEMA_S = {"scope": SCHEMA["scope"]}
FORMAT_SUFFIX = {
    "write_json": "",
    "write_short": "\n\nOUTPUT FORMAT OVERRIDE: respond with ONLY the three values separated by slashes, in the order tool/mode/scope, no JSON, no quotes, no other text. Example: answer/chat/all",
    "write_pretty": "\n\nOUTPUT FORMAT OVERRIDE: write the JSON object pretty-printed, one field per line, two-space indent, no other text.",
    "write_reason": "\n\nOUTPUT FORMAT OVERRIDE: the JSON object has a fourth field, \"reason\", after \"scope\": one sentence explaining the choice. No other text.",
}


def choose_call(msg, schema, instructions=INTENT_SYSTEM_PROMPT):
    body = {"model": "local", "instructions": instructions, "schema": schema, "contexts": [msg], "mode": "tree"}
    r, el = post("/v1/decision", body)
    return r["results"][0], r.get("usage", {}), r.get("timings", {}), el


def write_call(msg, system):
    body = {"model": "local", "messages": [{"role": "system", "content": system}, {"role": "user", "content": msg}],
            "temperature": 0.0, "max_tokens": 160, "stream": False, "chat_template_kwargs": {"enable_thinking": False}}
    r, el = post("/v1/chat/completions", body)
    return (r["choices"][0]["message"].get("content") or ""), r["usage"], r.get("timings", {}), el


def short_to_json(raw):
    parts = [p.strip().strip('"').strip("'") for p in raw.strip().strip("`").split("/")]
    if len(parts) == 3:
        return json.dumps({"tool": parts[0], "mode": parts[1], "scope": parts[2]})
    return raw  # let parse_and_sanitise treat it as unparseable


def fields_of(res):
    return {k: {"value": v["value"], "probability": v["probability"]} for k, v in res["fields"].items()}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("mode"); ap.add_argument("tag"); a = ap.parse_args()
    items = sorted(json.load(open(os.path.join(TEN, "splits", "test.json"))), key=lambda x: x["idx"])
    recs = []
    if a.mode == "twopass_seq":
        p1 = [choose_call(x["msg"], SCHEMA_TM) for x in items]
        lines = [f"tool: {r1['decision']['tool']}, mode: {r1['decision']['mode']}" for r1, _, _, _ in p1]
        p2 = [choose_call(x["msg"] + "\n" + ln, SCHEMA_S) for x, ln in zip(items, lines)]
        for x, (r1, u1, t1, e1), (r2, u2, t2, e2), ln in zip(items, p1, p2, lines):
            decision = {**r1["decision"], **r2["decision"]}
            pred = parse_and_sanitise(json.dumps(decision), x["msg"])
            ex, ef = score(pred, x["gold"])
            recs.append({"decision": decision, "fields": {**fields_of(r1), **fields_of(r2)}, "pass1": {"usage": u1, "timings": t1, "wall_s": round(e1, 4)},
                         "pass2": {"usage": u2, "timings": t2, "wall_s": round(e2, 4), "line": ln}, "wall_s": round(e1 + e2, 4),
                         "idx": x["idx"], "msg": x["msg"], "gold": x["gold"], "pred": {k: pred[k] for k in ("tool", "mode", "scope")},
                         "exact": ex, "effective": ef, "raw_valid": pred["raw_valid"]})
        items = []
    for x in items:
        msg = x["msg"]
        if a.mode == "choose":
            res, usage, tim, el = choose_call(msg, SCHEMA)
            pred = parse_and_sanitise(json.dumps(res["decision"]), msg)
            rec = {"decision": res["decision"], "fields": fields_of(res), "usage": usage, "timings": tim, "wall_s": round(el, 4)}
        elif a.mode in ("twopass", "twopass_instr"):
            r1, u1, t1, e1 = choose_call(msg, SCHEMA_TM)
            line = f"tool: {r1['decision']['tool']}, mode: {r1['decision']['mode']}"
            if a.mode == "twopass":
                r2, u2, t2, e2 = choose_call(msg + "\n" + line, SCHEMA_S)
            else:
                r2, u2, t2, e2 = choose_call(msg, SCHEMA_S, instructions=INTENT_SYSTEM_PROMPT + "\n" + line)
            decision = {**r1["decision"], **r2["decision"]}
            pred = parse_and_sanitise(json.dumps(decision), msg)
            rec = {"decision": decision, "fields": {**fields_of(r1), **fields_of(r2)}, "pass1": {"usage": u1, "timings": t1, "wall_s": round(e1, 4)},
                   "pass2": {"usage": u2, "timings": t2, "wall_s": round(e2, 4), "line": line}, "wall_s": round(e1 + e2, 4)}
        else:
            system = INTENT_SYSTEM_PROMPT + FORMAT_SUFFIX[a.mode]
            content, usage, tim, el = write_call(msg, system)
            raw_for_parse = short_to_json(content) if a.mode == "write_short" else content
            pred = parse_and_sanitise(raw_for_parse, msg)
            rec = {"raw": content, "via": pred["via"], "prompt_tokens": usage["prompt_tokens"],
                   "completion_tokens": usage["completion_tokens"], "timings": tim, "wall_s": round(el, 4)}
        ex, ef = score(pred, x["gold"])
        rec.update({"idx": x["idx"], "msg": msg, "gold": x["gold"], "pred": {k: pred[k] for k in ("tool", "mode", "scope")},
                    "exact": ex, "effective": ef, "raw_valid": pred["raw_valid"]})
        recs.append(rec)
    n = len(recs); walls = sorted(r["wall_s"] for r in recs)
    summ = {"n": n, "exact": sum(r["exact"] for r in recs), "raw_valid": sum(r["raw_valid"] for r in recs),
            "per_field": {f: sum(r["pred"][f] == r["gold"][f] for r in recs) for f in ("tool", "mode", "scope")},
            "wall_mean_s": round(statistics.mean(walls), 4), "wall_p95_s": round(walls[int(round(0.95 * (n - 1)))], 4)}
    if "completion_tokens" in recs[0]:
        summ["completion_tokens_mean"] = round(statistics.mean(r["completion_tokens"] for r in recs), 2)
        summ["unparseable"] = sum(r["via"] == "unparseable" for r in recs)
    out = {"tag": a.tag, "mode": a.mode, "solo_sha256": SOLO_SHA256, "model": "Qwen_Qwen3.6-27B-Q4_K_M.gguf",
           "format_suffix": FORMAT_SUFFIX.get(a.mode), "summary": summ, "records": recs}
    json.dump(out, open(os.path.join(HERE, "raw", f"{a.tag}.json"), "w"), indent=1)
    print(f"{a.tag}: {a.mode} exact {summ['exact']}/{n} per-field {summ['per_field']} raw_valid {summ['raw_valid']} "
          f"wall mean {summ['wall_mean_s']}s p95 {summ['wall_p95_s']}s" + (f" tokens {summ['completion_tokens_mean']}" if 'completion_tokens_mean' in summ else ""))


if __name__ == "__main__":
    main()
