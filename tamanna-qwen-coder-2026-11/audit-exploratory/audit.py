#!/usr/bin/env python3
"""POST-HOC, exploratory failure audit (deviation D1, 2026-11-17). Not confirmatory; changes no locked score.

Step 1 (default): read ../humaneval/gen-<ARM>.json and eval/he_<ARM>.jsonl_results.jsonl, parse prompt+completion,
  write all.json (per item: verdict, syntax check, finish reason, fence present), cf/cf_<ARM>.jsonl (each
  completion cut at its first ```), and print the headline counts.
Step 2 (after scoring cf/ in the sandbox, see README): `audit.py classify` writes cls.json and final.json, the class
  per failed item:
  c  = finish_reason "length" (512 tokens);
  b1 = has ``` and passes once cut there;  b2 = has ``` and still fails when cut;
  b3 = no ``` but still a SyntaxError after the cut (non-code tokens after the body);
  b4 = NameError on a non-module name (a helper the model meant to define after, removed by the \\ndef stop);
  d  = NameError on a stdlib module (missing import), or timed out;  a = the rest (assertion / runtime error).
Needs the `datasets` copy of openai_humaneval the generator used (lucebox venv, as he_gen.py)."""
import ast, collections, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); H = os.path.join(HERE, "..", "humaneval")
ARMS = ["A36", "A38", "C30", "CN", "CN3"]
MODS = {"math", "re", "hashlib", "heapq", "string", "itertools", "collections", "functools"}


def prompts():
    sys.path.insert(0, "/home/minotaur/Desktop/lucebox-hub/dflash/.venv/lib/python3.12/site-packages")
    from datasets import load_dataset
    return {s["task_id"]: s for s in load_dataset("openai_humaneval", split="test")}


def parses(src):
    try:
        ast.parse(src); return "ok"
    except SyntaxError as e:
        return f"SyntaxError: {e.msg} line {e.lineno}"


def step1():
    ds, out = prompts(), {}
    os.makedirs(os.path.join(HERE, "cf"), exist_ok=True)
    for a in ARMS:
        g = json.load(open(os.path.join(H, f"gen-{a}.json")))["results"]
        rs = [json.loads(l) for l in open(os.path.join(H, "eval", f"he_{a}.jsonl_results.jsonl"))]
        out[a] = []
        with open(os.path.join(HERE, "cf", f"cf_{a}.jsonl"), "w") as f:
            for r in rs:
                t, c = r["task_id"], r["completion"]
                out[a].append(dict(task=t, passed=r["passed"], result=r["result"], syn=parses(ds[t]["prompt"] + c),
                                   finish=g[t]["finish_reason"], ntok=g[t]["completion_tokens"], fence="```" in c,
                                   completion=c, entry=ds[t]["entry_point"]))
                f.write(json.dumps({"task_id": t, "completion": c.split("```", 1)[0]}) + "\n")
        fl = [x for x in out[a] if not x["passed"]]
        print(a, len(fl), "failed; syntax errors", sum(x["syn"] != "ok" for x in fl), "; completions with ```",
              sum(x["fence"] for x in out[a]))
    json.dump(out, open(os.path.join(HERE, "all.json"), "w"), indent=1)


def classify():
    ds, d = prompts(), json.load(open(os.path.join(HERE, "all.json")))
    cls, final = {}, {}
    for a in ARMS:
        cf = {json.loads(l)["task_id"]: json.loads(l)
              for l in open(os.path.join(HERE, "cf", f"cf_{a}.jsonl_results.jsonl"))}
        rows, fin = [], []
        for x in d[a]:
            if x["passed"]:
                continue
            t, c = x["task"], x["completion"]
            syn2 = parses(ds[t]["prompt"] + c.split("```", 1)[0])
            syn2 = "ok" if syn2 == "ok" else syn2.split(": ", 1)[1].rsplit(" line", 1)[0]
            if x["finish"] == "length": k = "c"
            elif x["fence"] and cf[t]["passed"]: k = "b-fixed"
            elif x["syn"] != "ok" and syn2 != "ok": k = "?syntax-after-cut"
            elif x["fence"]: k = "b-but-still-fails"
            else: k = "?"
            rows.append(dict(task=t, k=k, res=x["result"][:90], cfres=cf[t]["result"][:90], syn=x["syn"], syn2=syn2))
            m = re.search(r"name '(\w+)' is not defined", x["result"])
            if k == "c": f = "c truncation (max_tokens)"
            elif k == "b-fixed": f = "b1 trailing fence+prose (passes if cut)"
            elif k == "b-but-still-fails": f = "b2 fence/prose, fails even if cut"
            elif k == "?syntax-after-cut": f = "b3 non-code tokens after body"
            elif m and m.group(1) not in MODS: f = "b4 helper cut by \\ndef stop"
            elif m: f = "d missing import"
            elif "timed out" in x["result"]: f = "d timeout"
            else: f = "a wrong logic"
            fin.append((t, f))
        cls[a], final[a] = rows, fin
        print(a, len(fin), dict(sorted(collections.Counter(f for _, f in fin).items())))
    json.dump(cls, open(os.path.join(HERE, "cls.json"), "w"), indent=1)
    json.dump(final, open(os.path.join(HERE, "final.json"), "w"), indent=1)


if __name__ == "__main__":
    classify() if sys.argv[1:] == ["classify"] else step1()
