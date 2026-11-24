#!/usr/bin/env python3
"""Lock 03361fb7 N6 (void rules), N8 (scoring) and N7 (predictions), from results-<arm>.json in the run folder.
  summarize.py RUNDIR   -> prints the tables and writes summary.json
A re-run of a void cell (N6) is read from results-<arm>-rerun<len>.json when present and replaces that cell.
Answer quality (empty / looping) is flagged by a heuristic here; NariQ answers are also read by eye against the IQ3
answer to the same prompt (N6 addition), in the record.
"""
import json, os, re, statistics, sys

D = sys.argv[1]
ARMS = ["M-IQ3", "F-IQ3", "F-N3", "F-N25"]
LENGTHS = ["512", "4096"]
COMMIT = {"mainline": "a946eb5", "fork": "9d5c990"}   # N3 /props check (build_info suffix; record N5 gate note)


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
    return {"ratio": round(ratio, 3), "verdict": verdict, "ranges_overlap": overlap}


def build_ok(r):
    bi = (r.get("props_build") or {}).get("build_info") if isinstance(r.get("props_build"), dict) else None
    return bool(bi) and COMMIT[r["build"]] in bi, bi


def daemon_delta(arm):  # N5: > 5 CPU-seconds during an arm flags it (not a void)
    p = os.path.join(D, f"state-{arm}.txt")
    if not os.path.exists(p):
        return None
    s = open(p).read()
    def kv(tag):
        m = re.search(rf"^{tag} (.*)$", s, re.M)
        return dict(x.split("=") for x in m.group(1).split()) if m and m.group(1).strip() else {}
    b, a = kv("daemons-before"), kv("daemons-after")
    return {k: round(float(a[k]) - float(b.get(k, 0)), 2) for k in a}


R = {a: load(a) for a in ARMS}
S = {"cells": {}, "arms": {}, "scores": {}, "predictions": {}, "probe": {}}
print("| arm | len | decode t/s median (min..max) | prompt t/s median (min..max) | prompt_n | peak MiB | void |")
print("|---|---:|---|---|---|---:|---|")
for a in ARMS:
    if not R[a] or not R[a].get("cells"):
        continue
    ok, bi = build_ok(R[a])
    for n in LENGTHS:
        c = R[a]["cells"].get(n)
        if not c:
            continue
        tg, pp = stat(c, "predicted_per_second"), stat(c, "prompt_per_second")
        v = voids(c) + ([] if ok else [f"build_info {bi!r}"])
        S["cells"][f"{a}-{n}"] = {"tg": tg, "pp": pp, "void": v, "flags": flags(c), "peak": R[a].get(f"cell_{n}_peak_mib"),
                                 "prompt_n": [q["timings"]["prompt_n"] for q in c],
                                 "ttft_s": [round(q["ttft_s"], 3) for q in c if q.get("ttft_s")]}
# N6: prompt_n differing by more than 3 tokens between arms at the same length
for n in LENGTHS:
    pns = {a: S["cells"][f"{a}-{n}"]["prompt_n"] for a in ARMS if f"{a}-{n}" in S["cells"]}
    allv = [x for v in pns.values() for x in v]
    if allv and max(allv) - min(allv) > 3:
        med = statistics.median(allv)
        for a, v in pns.items():
            if any(abs(x - med) > 3 for x in v):
                S["cells"][f"{a}-{n}"]["void"].append(f"prompt_n {v} vs other arms (median {med})")
for a in ARMS:
    for n in LENGTHS:
        x = S["cells"].get(f"{a}-{n}")
        if x:
            tg, pp = x["tg"], x["pp"]
            print(f"| {a} | {n} | {tg['median']:.2f} ({tg['min']:.2f}..{tg['max']:.2f}) | {pp['median']:.1f} ({pp['min']:.1f}..{pp['max']:.1f}) "
                  f"| {x['prompt_n']} | {x['peak']} | {'; '.join(x['void']) or 'no'} |")

print()
for a in ARMS:
    r = R[a]
    if not r:
        print(f"{a}: no results file"); continue
    ok, bi = build_ok(r); dd = daemon_delta(a)
    flag = dd is not None and any(v > 5 for v in dd.values())
    S["arms"][a] = {"load_s": r.get("load_s"), "load_peak_mib": r.get("load_peak_mib"), "arm_peak_mib": r.get("arm_peak_mib"),
                    "min_avail_mib": r.get("min_avail_mib"), "build_info": bi, "build_ok": ok, "daemon_cpu_s": dd,
                    "daemon_flag": flag, "error": r.get("error"), "rerun": r.get("rerun", [])}
    cold = r.get("cold", {}).get("timings") or {}
    print(f"{a}: load {r.get('load_s')}s, load peak {r.get('load_peak_mib')} MiB, arm peak {r.get('arm_peak_mib')} MiB, "
          f"min MemAvailable {r.get('min_avail_mib')} MiB, cold tg {cold.get('predicted_per_second')} pp {cold.get('prompt_per_second')}, "
          f"build_info {bi} ({'ok' if ok else 'WRONG'}), daemons {dd}{' FLAG >5 s' if flag else ''}{' ERROR ' + r['error'] if r.get('error') else ''}")


def cell(a, n, k="tg"):
    x = S["cells"].get(f"{a}-{n}")
    return None if x is None or x["void"] else x[k]


print()
for k in ("tg", "pp"):
    for n in LENGTHS:
        out = {}
        for name, x, y in (("F-N3/M-IQ3 (vs what a user runs)", "F-N3", "M-IQ3"), ("F-N3/F-IQ3 (format alone)", "F-N3", "F-IQ3"),
                           ("F-IQ3/M-IQ3 (fork on stock file; F2)", "F-IQ3", "M-IQ3"), ("F-N25/F-N3", "F-N25", "F-N3"),
                           ("F-N25/M-IQ3", "F-N25", "M-IQ3")):
            cx, cy = cell(x, n, k), cell(y, n, k)
            if cx and cy:
                out[name] = compare(cx, cy)
        S["scores"][f"{k}-{n}"] = out
        for name, v in out.items():
            print(f"{k} {n}: {name} = {v['ratio']:.3f}  {v['verdict']}  (ranges overlap: {v['ranges_overlap']})")

print()
for n in LENGTHS:
    x, y = cell("F-N3", n), cell("M-IQ3", n)
    if x and y:
        c = compare(x, y); h = c["verdict"] == "slower"
        S["scores"][f"F1-{n}"] = {**c, "holds": h}
        print(f"F1 @{n}: F-N3 decode vs M-IQ3 = {c['ratio']:.3f} ({c['verdict']}) -> {'HOLDS' if h else 'FAILS'}")
    for k in ("tg", "pp"):
        x, y = cell("F-IQ3", n, k), cell("M-IQ3", n, k)
        if x and y:
            c = compare(x, y); h = c["verdict"] == "no difference shown" or 0.97 <= c["ratio"] <= 1.03
            S["scores"][f"F2-{k}-{n}"] = {**c, "holds": h}
            print(f"F2 @{n} {k}: F-IQ3/M-IQ3 = {c['ratio']:.3f} ({c['verdict']}) -> {'HOLDS' if h else 'FAILS (' + c['verdict'] + ')'}")

print()
for n in LENGTHS:
    for name, k, x, y, lo, hi in (("P-a F-N3/M-IQ3 decode", "tg", "F-N3", "M-IQ3", 0.50, 0.85),
                                  ("P-b F-N25/F-N3 decode", "tg", "F-N25", "F-N3", 1.05, 1.20),
                                  ("P-c F-N3/M-IQ3 prompt", "pp", "F-N3", "M-IQ3", 0.30, 0.80)):
        cx, cy = cell(x, n, k), cell(y, n, k)
        if cx and cy:
            r = cx["median"] / cy["median"]; hit = lo <= r <= hi
            S["predictions"][f"{name} @{n}"] = {"ratio": round(r, 3), "band": [lo, hi], "hit": hit}
            print(f"{name} @{n}: {r:.3f}, predicted {lo}-{hi} -> {'HIT' if hit else 'MISS'}")
    for k in ("tg", "pp"):
        cx, cy = cell("F-IQ3", n, k), cell("M-IQ3", n, k)
        if cx and cy:
            c = compare(cx, cy); hit = c["verdict"] == "no difference shown"
            S["predictions"][f"P-d F-IQ3 vs M-IQ3 {k} @{n}"] = {**c, "hit": hit}
            print(f"P-d F-IQ3 vs M-IQ3 {k} @{n}: {c['verdict']} -> {'HIT' if hit else 'MISS'}")

print()
print("Fit probe (N5, reported only): -c, loads, answers, cold tg, card peak")
for a in ("F-N3", "F-N25", "M-IQ3"):
    for c in ("16384", "32768"):
        p = os.path.join(D, f"results-P-{a}-{c}.json")
        if not os.path.exists(p):
            S["probe"][f"{a}-{c}"] = None; print(f"{a} @{c}: no results file"); continue
        r = json.load(open(p))
        cold = r.get("cold") or {}
        loads = not r.get("error")
        t = cold.get("timings") or {}   # a full answer = timings present and all 256 tokens out (a mid-stream crash leaves none)
        answers = loads and not cold.get("error") and (t.get("predicted_n") or 0) >= 256
        S["probe"][f"{a}-{c}"] = {"loads": loads, "answers": answers, "peak_mib": r.get("arm_peak_mib"),
                                 "n_ctx": r.get("props_n_ctx"), "cold_tg": (cold.get("timings") or {}).get("predicted_per_second"),
                                 "answer_head": (cold.get("answer_head") or "")[:80]}
        print(f"{a} @{c}: loads {loads}, answers {answers}, n_ctx {r.get('props_n_ctx')}, tg {S['probe'][f'{a}-{c}']['cold_tg']}, peak {r.get('arm_peak_mib')} MiB")
pr = S["probe"]
def ok(k):
    return bool(pr.get(k) and pr[k]["answers"])
for name, hit in (("F-N3 loads at 16K and not at 32K", ok("F-N3-16384") and not ok("F-N3-32768")),
                  ("F-N25 loads at 32K", ok("F-N25-32768")),
                  ("M-IQ3 behaves like F-N3", ok("M-IQ3-16384") == ok("F-N3-16384") and ok("M-IQ3-32768") == ok("F-N3-32768"))):
    S["predictions"][f"fit: {name}"] = {"hit": hit}
    print(f"Prediction fit: {name} -> {'HIT' if hit else 'MISS'}")
json.dump(S, open(os.path.join(D, "summary.json"), "w"), indent=1)
