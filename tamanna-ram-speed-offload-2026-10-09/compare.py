"""3000 vs 2133 per cell, against the pre-registered ranges (docs/candidates/tamanna-ram-speed-offload-2026-10.md)."""
import json, os
D = os.path.dirname(os.path.abspath(__file__))
a = json.load(open(os.path.join(D, "3000", "summary.json")))
b = json.load(open(os.path.join(D, "2133", "summary.json")))
# predicted decode gain ranges (percent), pp512 ranges, resident control
PRED = {("A", 40, "tg"): (15, 30), ("A", 20, "tg"): (5, 20), ("A", 0, "tg"): (-1, 1), ("B", 29, "tg"): (5, 25),
        ("A", 40, "pp"): (-5, 5), ("A", 20, "pp"): (-5, 5), ("A", 0, "pp"): (-1, 1)}
print("| arm | -ncmoe | metric | DDR4-2133 | DDR4-3000 | gain | ranges overlap? | predicted | inside? |")
print("|---|---:|---|---|---|---:|---|---|---|")
for key in a:
    arm, n, kind, d = key.split("|"); n = int(n)
    x, y = b[key], a[key]
    g = (y["mean"] / x["mean"] - 1) * 100
    overlap = not (y["min"] > x["max"] or y["max"] < x["min"])
    lo, hi = PRED[(arm, n, kind)]
    f = (lambda v: f"{v:,.1f}") if kind == "pp" else (lambda v: f"{v:.2f}")
    print(f"| {arm} | {n} | {'tg128' if kind == 'tg' else 'pp512'} d={d} | {f(x['mean'])} [{f(x['min'])}..{f(x['max'])}] | "
          f"{f(y['mean'])} [{f(y['min'])}..{f(y['max'])}] | {g:+.1f}% | {'yes, within noise' if overlap else 'no'} | "
          f"{lo:+d}% to {hi:+d}% | {'inside' if lo <= g <= hi else 'OUTSIDE'} |")
