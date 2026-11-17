#!/usr/bin/env python3
"""Score MBPP completions inside he-scorer:b10088 (the HumanEval lock's image) with the official human-eval
execution sandbox (human_eval.execution.check_correctness: reliability_guard, 3.0 s timeout per problem).

Program executed per problem = generation prompt + completion + "\\n" + test_imports + test_list (the 3 asserts)
+ "\\ndef check(candidate):\\n    pass\\n" + "check(None)". Passes iff it runs to the end without an exception.
Input /work/<name>.jsonl rows: {"task_id", "prompt", "completion", "test"}; output /work/<name>.jsonl_results.jsonl
with "passed" and "result" added, and the pass count on stdout.
usage (in the container): python3 /work/mbpp_score.py /work/<name>.jsonl
"""
import json, sys
from concurrent.futures import ThreadPoolExecutor
from human_eval.execution import check_correctness

path = sys.argv[1]
rows = [json.loads(l) for l in open(path)]


def one(r):
    prob = {"task_id": r["task_id"], "prompt": r["prompt"], "entry_point": "None",
            "test": r["test"] + "\ndef check(candidate):\n    pass\n"}
    out = check_correctness(prob, r["completion"], 3.0)
    return dict(r, passed=bool(out["passed"]), result=out["result"])


with ThreadPoolExecutor(4) as ex:
    res = list(ex.map(one, rows))
with open(path + "_results.jsonl", "w") as f:
    for r in res:
        f.write(json.dumps(r) + "\n")
n = sum(r["passed"] for r in res)
print(json.dumps({"n": len(res), "passes": n, "pass_at_1": n / len(res)}))
