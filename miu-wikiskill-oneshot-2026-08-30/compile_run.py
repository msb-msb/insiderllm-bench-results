#!/usr/bin/env python3
"""The 20 compilation calls. claude-opus-5, effort high, cache ttl 1h.

Deliberate deviation from house default: NO server-side refusal fallbacks.
A fallback would silently substitute a different model mid-run and corrupt the
compiler-noise measurement, which is the whole point. A refusal is recorded as
a failure instead. No retries -- a compiler that sometimes produces nothing is
a property worth publishing, and a silent retry would erase it.
"""
import json, os, sys, time, hashlib, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_common import load_env, request_shape, MODEL
import anthropic

load_env()
client = anthropic.Anthropic()
PLAN = [(24, 10), (16, 5), (8, 5)]
OUT = "compile_calls.json"
records = []

def flush():
    json.dump({"model": MODEL, "effort": "high", "thinking": "adaptive (default)",
               "ttl": "1h", "fallbacks": "disabled (would corrupt the measurement)",
               "plan": PLAN, "records": records}, open(OUT, "w"), indent=1)

print(f"{'call':>14} {'in':>6} {'cw':>7} {'cr':>7} {'tot_in':>8} {'out':>7} {'s':>6}  status")
for group, n in PLAN:
    b = json.load(open(f"bundles/bundle_{group}.json"))
    shape = request_shape(b, ttl="1h")
    for i in range(n):
        tag = f"g{group}_{i:02d}"
        t0 = time.time()
        rec = {"tag": tag, "group": group, "call_index": i,
               "started": time.strftime("%H:%M:%S")}
        try:
            with client.messages.stream(
                model=MODEL, max_tokens=16000,
                system=shape["system"], messages=shape["messages"],
                thinking={"type": "adaptive"},
                output_config={"effort": "high"},
            ) as stream:
                msg = stream.get_final_message()
            el = time.time() - t0
            u = msg.usage
            ci = getattr(u, "cache_creation_input_tokens", 0) or 0
            cr = getattr(u, "cache_read_input_tokens", 0) or 0
            it = u.input_tokens or 0
            text = "".join(blk.text for blk in msg.content if blk.type == "text")
            think_blocks = [b_ for b_ in msg.content if b_.type == "thinking"]
            rec.update({
                "status": "ok" if msg.stop_reason != "refusal" else "refusal",
                "stop_reason": msg.stop_reason,
                "model_returned": msg.model,
                "request_id": getattr(msg, "_request_id", None),
                "input_tokens": it,
                "cache_creation_input_tokens": ci,
                "cache_read_input_tokens": cr,
                "total_input_tokens": it + ci + cr,
                "output_tokens": u.output_tokens,
                "elapsed_s": round(el, 2),
                "n_thinking_blocks": len(think_blocks),
                "skill_chars": len(text), "skill_lines": text.count("\n") + 1 if text else 0,
                "skill_sha256": hashlib.sha256(text.encode()).hexdigest(),
            })
            if msg.stop_reason == "refusal":
                rec["stop_details"] = str(getattr(msg, "stop_details", None))
            if not text.strip():
                rec["status"] = "empty_output"
            path = f"skills/skill_{tag}.md"
            open(path, "w").write(text)
            rec["skill_path"] = path
            print(f"{tag:>14} {it:>6} {ci:>7} {cr:>7} {rec['total_input_tokens']:>8} "
                  f"{u.output_tokens:>7} {el:>6.1f}  {rec['status']}", flush=True)
        except Exception as e:
            rec.update({"status": "error", "error_type": type(e).__name__,
                        "error": str(e)[:400], "elapsed_s": round(time.time()-t0, 2)})
            print(f"{tag:>14} {'-':>6} {'-':>7} {'-':>7} {'-':>8} {'-':>7} "
                  f"{rec['elapsed_s']:>6.1f}  ERROR {type(e).__name__}", flush=True)
        records.append(rec); flush()
flush()
ok = [r for r in records if r.get("status") == "ok"]
print(f"\n{len(ok)}/{len(records)} ok -> {OUT}")
