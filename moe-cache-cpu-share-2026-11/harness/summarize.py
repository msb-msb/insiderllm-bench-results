#!/usr/bin/env python3
"""Lock c22ff41b M6 (void rules) and M8 (scoring), from results-<arm>.json in the record folder.
  summarize.py RECDIR   -> prints the tables and writes summary.json
A re-run of a void cell (M6) is read from results-<arm>-rerun<len>.json when present and replaces that cell.
Answer quality (empty / looping / garbled) is flagged by a heuristic here and checked by eye in the record.
"""
import json, os, statistics, sys

D = sys.argv[1]
ARMS = ["a24", "a27", "b27", "c"]
LENGTHS = ["512", "4096"]


def load(arm):
    p = os.path.join(D, f"results-{arm}.json")
    if not os.path.exists(p):
        return None
    r = json.load(open(p))
    for n in LENGTHS:
        q = os.path.join(D, f"results-{arm}-rerun{n}.json")
        if os.path.exists(q):
            r["cells"][n] = json.load(open(q))["cells"][n]; r.setdefault("rerun", []).append(n)
    return r


def looping(text):
    if not text.strip():
        return "empty"
    t = text[:600]
    for k in (8, 12, 20, 40):
        for i in range(0, max(0, len(t) - 4 * k)):
            s = t[i:i + k]
            if s.strip() and t.count(s) >= 6:
                return f"repeats {s!r}"
    return None


def voids(cell):
    why = []
    pn = [q["timings"]["prompt_n"] for q in cell]
    if max(pn) - min(pn) > 3:
        why.append(f"prompt_n spread {min(pn)}..{max(pn)}")
    for q in cell:
        t = q["timings"]
        if q.get("error"):
            why.append(f"error {q['error'][:60]}")
        if (t.get("cache_n") or 0) > 0:
            why.append(f"cache_n {t['cache_n']}")
        if q["swapout_kib"] > 0:
            why.append(f"swap-out {q['swapout_kib']} KiB")
        if any(int(g) < 3 or int(w) < 16 for g, w in q["prefill_pcie_links"]):
            why.append(f"PCIe {q['prefill_pcie_links']}")
        if (q["nvme_read_decode_mib"] or 0) > 1024:
            why.append(f"decode NVMe {q['nvme_read_decode_mib']} MiB")
        l = looping(q["answer_head"])
        if l:
            why.append(f"answer {l}")
    return why


def flags(cell):
    return [f"{q['tag']} decode NVMe {q['nvme_read_decode_mib']} MiB" for q in cell if (q["nvme_read_decode_mib"] or 0) > 64]


def stat(cell, key):
    v = [q["timings"][key] for q in cell]
    return {"median": statistics.median(v), "min": min(v), "max": max(v), "values": v}


def compare(x, y):  # x vs y: faster / slower / no difference shown (HotRod H7)
    ratio = x["median"] / y["median"]
    overlap = not (x["min"] > y["max"] or x["max"] < y["min"])
    verdict = "no difference shown" if overlap or x["median"] == y["median"] else ("faster" if ratio > 1 else "slower")
    h0 = "rejected" if (ratio <= 0.95 or ratio >= 1.05) and not overlap else "not rejected"
    return {"ratio": round(ratio, 3), "verdict": verdict, "ranges_overlap": overlap, "H0": h0}


R = {a: load(a) for a in ARMS}
S = {"cells": {}, "void": {}, "scores": {}}
print("| arm | len | decode t/s median (min..max) | prompt t/s median (min..max) | prompt_n | peak MiB | void |")
print("|---|---:|---|---|---|---:|---|")
for a in ARMS:
    if not R[a]:
        continue
    for n in LENGTHS:
        c = R[a]["cells"].get(n)
        if not c:
            continue
        tg, pp = stat(c, "predicted_per_second"), stat(c, "prompt_per_second")
        v = voids(c)
        S["cells"][f"{a}-{n}"] = {"tg": tg, "pp": pp, "void": v, "flags": flags(c), "peak": R[a].get(f"cell_{n}_peak_mib"),
                                 "prompt_n": [q["timings"]["prompt_n"] for q in c]}
        print(f"| {a} | {n} | {tg['median']:.2f} ({tg['min']:.2f}..{tg['max']:.2f}) | {pp['median']:.1f} ({pp['min']:.1f}..{pp['max']:.1f}) "
              f"| {S['cells'][f'{a}-{n}']['prompt_n']} | {R[a].get(f'cell_{n}_peak_mib')} | {'; '.join(v) or 'no'} |")

print()
for a in ARMS:
    if R[a]:
        r = R[a]
        print(f"{a}: load {r.get('load_s')}s, load peak {r.get('load_peak_mib')} MiB, arm peak {r.get('arm_peak_mib')} MiB, "
              f"min MemAvailable {r.get('min_avail_mib')} MiB, cold tg {r['cold']['timings']['predicted_per_second']:.2f} "
              f"pp {r['cold']['timings']['prompt_per_second']:.1f}, build {r.get('props_build')}")

def cell(a, n, k="tg"):
    x = S["cells"].get(f"{a}-{n}")
    return None if x is None or x["void"] else x[k]

print()
for k in ("tg", "pp"):
    for n in LENGTHS:
        out = {}
        for name, x, y in (("b27/a27 (cache alone; C2)", "b27", "a27"), ("b27/a24", "b27", "a24"), ("c/a24", "c", "a24"),
                           ("a27/a24 (3 layers to host)", "a27", "a24"), ("c/b27", "c", "b27")):
            cx, cy = cell(x, n, k), cell(y, n, k)
            if cx and cy:
                out[name] = compare(cx, cy)
        S["scores"][f"{k}-{n}"] = out
        for name, v in out.items():
            print(f"{k} {n}: {name} = {v['ratio']:.3f}  {v['verdict']}  (ranges overlap: {v['ranges_overlap']}; H0 {v['H0']})")

print()
for n in LENGTHS:
    b, c, a = cell("b27", n), cell("c", n), cell("a24", n)
    if b and c and a:
        best, nm = (b, "b27") if b["median"] >= c["median"] else (c, "c")
        cmp = compare(best, a)
        c1 = cmp["ratio"] >= 1.5 and cmp["verdict"] == "faster"
        S["scores"][f"C1-{n}"] = {"better": nm, **cmp, "holds": c1}
        print(f"C1 @{n}: better arm {nm}, {nm}/a24 = {cmp['ratio']:.3f} ({cmp['verdict']}) -> {'HOLDS' if c1 else 'FAILS'}")
    b, a27 = cell("b27", n), cell("a27", n)
    if b and a27:
        cmp = compare(b, a27); c2 = cmp["verdict"] == "slower"
        S["scores"][f"C2-{n}"] = {**cmp, "holds": c2}
        print(f"C2 @{n}: b27/a27 = {cmp['ratio']:.3f} ({cmp['verdict']}) -> {'HOLDS' if c2 else 'FAILS'}")
    c, a = cell("c", n), cell("a24", n)
    if c and a:
        r = c["median"] / a["median"]; hit = 1.1 <= r <= 1.3
        S["scores"][f"P1-{n}"] = {"ratio": round(r, 3), "hit": hit}
        print(f"Prediction 1 @{n}: c/a24 = {r:.3f}, predicted 1.1-1.3 -> {'HIT' if hit else 'MISS'}")
    b, a = cell("b27", n), cell("a24", n)
    if b and a:
        cmp = compare(b, a); hit = cmp["verdict"] in ("slower", "no difference shown")
        S["scores"][f"P2-{n}"] = {**cmp, "hit": hit}
        print(f"Prediction 2 @{n}: b27 vs a24 = {cmp['ratio']:.3f} ({cmp['verdict']}), predicted slower or no difference -> {'HIT' if hit else 'MISS'}")
json.dump(S, open(os.path.join(D, "summary.json"), "w"), indent=1)
