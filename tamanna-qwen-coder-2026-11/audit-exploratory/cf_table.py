#!/usr/bin/env python3
"""POST-HOC, exploratory (deviation D1, 2026-11-17). Not a confirmatory result; the locked scores are the primary ones.
Fence-cut counterfactual: each completion cut at its first ``` (same rule for every arm; cf/cf_<ARM>.jsonl, written by
audit.py), re-scored in the same he-scorer:b10088 sandbox with the lock's docker flags
(cf/cf_<ARM>.jsonl_results.jsonl). Prints pass@1 locked vs cut, and exact McNemar on the lock's pairs under the cut."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "humaneval"))
from mcnemar import PAIRS, exact
H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "humaneval")
C = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cf")
ARMS = ["A36", "A38", "C30", "CN", "CN3"]
locked = {a: json.load(open(os.path.join(H, f"summary-{a}.json")))["vector"] for a in ARMS}
cut = {a: {json.loads(l)["task_id"]: json.loads(l)["passed"] for l in open(os.path.join(C, f"cf_{a}.jsonl_results.jsonl"))}
       for a in ARMS}
print("| Arm | Locked (primary) | Fence-cut (post-hoc) | Change |\n|---|---:|---:|---:|")
for a in ARMS:
    l, c = sum(locked[a].values()), sum(cut[a].values())
    print(f"| {a} | {l}/164 ({100*l/164:.2f}%) | {c}/164 ({100*c/164:.2f}%) | {c-l:+d} |")
print("\n| Pair, fence-cut (post-hoc) | only X | only Y | exact McNemar p |\n|---|---:|---:|---:|")
for x, y in PAIRS:
    b = sum(cut[x][t] and not cut[y][t] for t in cut[x]); c = sum(cut[y][t] and not cut[x][t] for t in cut[x])
    print(f"| {x} vs {y} | {b} | {c} | {exact(b, c):.3g} |")
