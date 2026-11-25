#!/usr/bin/env python3
"""Lock I7 smoke test against a running server: 5 fixed prompts, temperature 0, max_tokens 2048, scored on the final
answer (content after any thinking block; reasoning_content is kept but not scored).
  smoke.py PORT OUT.json
"""
import json, re, sys, urllib.request

port, out = int(sys.argv[1]), sys.argv[2]


def ask(messages):
    body = {"model": "bench", "messages": messages, "temperature": 0, "top_k": 1, "seed": 1234, "max_tokens": 2048,
            "cache_prompt": False}
    req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=3600) as r:
        o = json.loads(r.read())
    m = o["choices"][0]["message"]; fin = o["choices"][0].get("finish_reason")
    content = m.get("content") or ""
    content = re.sub(r"(?s)^.*</think>", "", content).strip()
    return content, m.get("reasoning_content") or "", fin, o.get("usage")


def code_of(s):
    m = re.search(r"```(?:python)?\n(.*?)```", s, re.S)
    return m.group(1) if m else s


def t_palin(s):
    ns = {}
    try:
        exec(code_of(s), ns)
        f = ns["is_palindrome"]
        return bool(f("A man, a plan, a canal: Panama") and f("") and not f("hello") and f("No 'x' in Nixon") and not f("ab"))
    except Exception:
        return False


def t_json(s):
    try:
        m = re.search(r"\{.*\}", s, re.S); o = json.loads(m.group(0))
        return isinstance(o.get("name"), str) and o.get("year") == 1889 and isinstance(o.get("tags"), list) \
            and len(o["tags"]) == 3 and all(isinstance(t, str) for t in o["tags"])
    except Exception:
        return False


TESTS = [
    ("arith", [{"role": "user", "content": "A shop sells pens at $3 each and notebooks at $7 each. Maria buys 4 pens and 3 notebooks and pays with a $50 note. How much change does she get? Put only the number on the last line."}],
     lambda s: re.sub(r"[^0-9.]", "", (s.strip().splitlines() or [""])[-1]) in ("17", "17.00", "17.0")),
    ("palindrome", [{"role": "user", "content": "Write a Python function `is_palindrome(s)` that ignores case and non-alphanumeric characters. Reply with only the code."}], t_palin),
    ("json", [{"role": "user", "content": "Return only JSON with keys name (string), year (integer) and tags (array of exactly 3 strings) describing the Eiffel Tower's completion."}], t_json),
    ("capital", [{"role": "user", "content": "What is the capital of Australia? Answer in one word."}],
     lambda s: re.sub(r"[^a-z]", "", s.lower()) == "canberra"),
]
R = []
for name, msgs, check in TESTS:
    c, rc, fin, u = ask(msgs)
    capped = fin == "length" and not c
    R.append({"test": name, "pass": (not capped) and check(c), "cap_inside_thinking": capped, "finish": fin, "usage": u,
              "content": c, "reasoning": rc})
# 5: two turns
c1, rc1, f1, u1 = ask([{"role": "user", "content": "My name is Ada and my favourite number is 42."}])
c2, rc2, f2, u2 = ask([{"role": "user", "content": "My name is Ada and my favourite number is 42."}, {"role": "assistant", "content": c1},
                       {"role": "user", "content": "What is my favourite number plus 8? Answer with the number only."}])
capped = f2 == "length" and not c2
R.append({"test": "multiturn", "pass": (not capped) and re.sub(r"[^0-9]", "", c2) == "50", "cap_inside_thinking": capped,
          "finish": f2, "usage": u2, "turn1": c1, "content": c2, "reasoning": rc2})
json.dump(R, open(out, "w"), indent=1)
print(" ".join(f"{r['test']}={'PASS' if r['pass'] else ('CAP' if r['cap_inside_thinking'] else 'FAIL')}" for r in R),
      f"total {sum(r['pass'] for r in R)}/5")
