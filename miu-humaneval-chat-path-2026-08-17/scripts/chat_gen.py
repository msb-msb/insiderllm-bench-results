#!/usr/bin/env python3
"""HumanEval generation over the CHAT path, for one (model, run) pair.

New arm. The published raw-completion result stands and is not touched by this.

Design decisions, stated because they change the number:
  * The user message is the HumanEval prompt VERBATIM, with no added
    instruction. Any wording I invented ("complete this function") would be a
    second difference between this arm and the raw arm, and the chat path is
    supposed to be the only one.
  * --reasoning-format deepseek-legacy keeps <think></think> in message.content
    AND fills reasoning_content. That is an output-format flag; it does not
    touch sampling, the template, or reasoning effort. It is needed so an
    UNTERMINATED thinking block is visible to us rather than left to the
    server parser's undefined behaviour.
  * reasoning effort is NOT set. 3.8's template defaults it to 'xhigh'
    (tpl line 59, reasoning_effort|default('xhigh')); 3.6 has no such
    parameter. That asymmetry is the thing under test.
"""
import json, os, sys, time, urllib.request

URL = "http://127.0.0.1:8099/v1/chat/completions"
TOK = "http://127.0.0.1:8099/tokenize"

LABEL, OUT, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3])

PINNED = {
    "temperature": 1.0,
    "top_p": 0.95,
    "top_k": 20,
    # Raised from 16384 after the 20-problem pilot: HumanEval/2 reached 14,953
    # tokens, 91.3% of the old ceiling, on one draw in twenty. Scaling to 164
    # problems makes a truncation likely, and a truncated problem is
    # unscoreable rather than a fail. 32000 + a ~400-token prompt fits inside
    # -c 32768 (n_ctx_slot=32768, kv_unified=true), so it costs no VRAM.
    "max_tokens": 32000,
    "seed": SEED,
    "stream": False,
    # NO stop sequences: the raw-arm list ("\nclass", "\ndef", "\n#", ...)
    # would fire inside a thinking block and truncate mid-reasoning.
}

sys.path.insert(0, "/home/minotaur/Desktop/lucebox-hub/dflash/.venv/lib/python3.12/site-packages")
from datasets import load_dataset  # noqa: E402


def post(url, body, timeout=3600):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def ntok(s):
    if not s:
        return 0
    try:
        return len(post(TOK, {"content": s}, timeout=120).get("tokens", []))
    except Exception:
        return -1


ds = load_dataset("openai_humaneval", split="test")
# Pilot mode: the FIRST N problems in canonical dataset order, never a sample,
# so the subset is reproducible and comparable against the same 20 elsewhere.
LIMIT = int(os.environ.get("CHAT_LIMIT", "0"))
if LIMIT:
    ds = ds.select(range(LIMIT))
    print(f"  PILOT: first {LIMIT} problems in canonical order "
          f"({ds[0]['task_id']} .. {ds[LIMIT-1]['task_id']})", flush=True)
N = len(ds)
res, t0 = {}, time.time()
for i, s in enumerate(ds):
    body = dict(PINNED)
    body["messages"] = [{"role": "user", "content": s["prompt"]}]
    t1 = time.time()
    d = post(URL, body)
    ch = d["choices"][0]
    msg = ch.get("message", {}) or {}
    content = msg.get("content") or ""
    reasoning = msg.get("reasoning_content") or ""
    usage = d.get("usage") or {}
    res[s["task_id"]] = {
        "content": content,
        "reasoning_content": reasoning,
        "finish_reason": ch.get("finish_reason"),
        "completion_tokens": usage.get("completion_tokens"),
        "prompt_tokens": usage.get("prompt_tokens"),
        "reasoning_tokens": ntok(reasoning) if reasoning else None,
        "elapsed_s": round(time.time() - t1, 2),
    }
    if (i + 1) % 5 == 0 or i + 1 == N:
        el = time.time() - t0
        gen = sum(v["completion_tokens"] or 0 for v in res.values())
        print(f"  {i+1:3d}/{N}  {el:6.0f}s  {gen:8d} tok  "
              f"{gen/el:5.1f} tok/s  eta {el/(i+1)*(N-i-1)/60:5.1f} min", flush=True)

el = time.time() - t0
gen = sum(v["completion_tokens"] or 0 for v in res.values())
rtok = sum(v["reasoning_tokens"] or 0 for v in res.values())
ceil = sum(1 for v in res.values() if v["finish_reason"] == "length")
json.dump({"label": LABEL, "seed": SEED, "pinned": PINNED, "elapsed_s": el,
           "gen_tokens": gen, "reasoning_tokens": rtok,
           "hit_ceiling": ceil, "results": res}, open(OUT, "w"), indent=1)
print(f"{LABEL}: {N} prompts in {el:.0f}s, {gen} completion tokens "
      f"({rtok} reasoning), {gen/el:.1f} tok/s, {ceil} hit the 32000 ceiling -> {OUT}")
