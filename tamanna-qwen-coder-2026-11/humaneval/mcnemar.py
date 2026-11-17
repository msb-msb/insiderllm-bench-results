#!/usr/bin/env python3
"""Exact two-sided McNemar for the lock's HumanEval pairs (P5/P6), from summary-<ARM>.json per-problem vectors.
usage: python3 mcnemar.py [DIR] [SUFFIX]   (DIR defaults to this directory; used by audit-exploratory too)"""
import json, os, sys
from math import comb
D = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
PAIRS = [("C30", "A36"), ("CN", "A36"), ("CN3", "CN"), ("A38", "A36"), ("CN", "C30")]


def exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, k) for k in range(min(b, c) + 1)) / 2 ** n)


def vec(arm):
    return json.load(open(os.path.join(D, f"summary-{arm}.json")))["vector"]


if __name__ == "__main__":
    print("| Pair (X vs Y) | X pass@1 | Y pass@1 | only X passes | only Y passes | exact McNemar p (two-sided) |")
    print("|---|---:|---:|---:|---:|---:|")
    for x, y in PAIRS:
        vx, vy = vec(x), vec(y)
        b = sum(vx[t] and not vy[t] for t in vx); c = sum(vy[t] and not vx[t] for t in vx)
        print(f"| {x} vs {y} | {sum(vx.values())}/164 | {sum(vy.values())}/164 | {b} | {c} | {exact(b, c):.3g} |")
