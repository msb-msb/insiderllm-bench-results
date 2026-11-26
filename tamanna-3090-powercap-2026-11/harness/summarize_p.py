#!/usr/bin/env python3
"""Arm P summary: per block, medians of 3 (P3), ratios vs B420a, bands from ../bands-P.md (PP3/PP4). usage: summarize_p.py RECDIR"""
import json, os, statistics as st, sys
D = sys.argv[1]
BANDS = {350: ((0.935, 0.995), (0.924, 1.020)), 320: ((0.885, 0.966), (0.900, 1.020)),
         280: ((0.815, 0.926), (0.900, 1.020)), 250: ((0.760, 0.892), (0.900, 1.020))}
def load(b):
    p = os.path.join(D, f"results-{b}.json")
    return json.load(open(p)) if os.path.exists(p) else None
def med(rs, f): return st.median(f(r) for r in rs)
rows = {}
for b in ("B420a", "B350", "B320", "B280", "B250", "B420b"):
    R = load(b)
    if not R: continue
    c = R["cells"]
    rows[b] = dict(
        lim=R["limits_at_start"][0], void=[r["void"] for k in c for r in c[k]],
        d512=med(c["512"], lambda r: r["timings"]["predicted_per_second"]),
        d4k=med(c["4096"], lambda r: r["timings"]["predicted_per_second"]),
        p4k=med(c["4096"], lambda r: r["timings"]["prompt_per_second"]),
        wd512=med(c["512"], lambda r: r["power_decode"]["w_instant"]),
        wd4k=med(c["4096"], lambda r: r["power_decode"]["w_instant"]),
        wp4k=med(c["4096"], lambda r: r["power_prefill"]["w_instant"]),
        smd=med(c["512"], lambda r: r["power_decode"]["sm_mhz"]),
        smp=med(c["4096"], lambda r: r["power_prefill"]["sm_mhz"]),
        memd=med(c["512"], lambda r: r["power_decode"]["mem_mhz"]),
        capd=med(c["512"], lambda r: r["power_decode"]["sw_power_cap_share"]),
        tmax=max(r["power_decode"]["temp_max"] for k in c for r in c[k]))
b0 = rows["B420a"]
print(f"{'block':6} {'lim':>5} {'dec512':>7} {'dec4k':>7} {'pp4k':>7} {'Wdec':>6} {'Wdec4k':>6} {'Wpf4k':>6} {'J/tok dec':>9} {'J/tok pf':>8} {'SMdec':>6} {'SMpf':>5} {'MEM':>5} {'cap%':>5} {'Tmax':>4}  ratios d512/d4k/pp4k  verdicts")
for b, r in rows.items():
    rd, rd4, rp = r["d512"] / b0["d512"], r["d4k"] / b0["d4k"], r["p4k"] / b0["p4k"]
    v = ""
    C = round(float(r["lim"]))
    if C in BANDS:
        (pl, ph), (dl, dh) = BANDS[C]
        io = lambda x, l, h: "in" if l <= x <= h else "OUT"
        v = f"PP3 {io(rp, pl, ph)} PP4 {io(rd, dl, dh)}/{io(rd4, dl, dh)}"
    if b == "B420b":
        v = f"PP6 {'in' if 0.98 <= rd <= 1.02 else 'OUT'}"
    print(f"{b:6} {r['lim']:>5} {r['d512']:7.2f} {r['d4k']:7.2f} {r['p4k']:7.1f} {r['wd512']:6.1f} {r['wd4k']:6.1f} {r['wp4k']:6.1f} "
          f"{r['wd512']/r['d512']:9.2f} {r['wp4k']/r['p4k']:8.3f} {r['smd']:6} {r['smp']:5} {r['memd']:5} {r['capd']:5} {r['tmax']:4}  "
          f"{rd:.3f}/{rd4:.3f}/{rp:.3f}  {v}  void={sum(x is not None for x in r['void'])}")
