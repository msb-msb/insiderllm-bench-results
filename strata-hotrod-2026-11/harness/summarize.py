#!/usr/bin/env python3
"""Strata HotRod lock (c06003fc): score our cells and print the tables for the record README.

  summarize.py RECDIR        (RECDIR = this folder: reads rushuna/ARM/ and tamanna/ARM/)

Void rules, H6 (Rule P4 with A1's reading), per cell over all 6 requests (3 priming + 3 measured):
  prompt_n spread > 3; cache_n > 16 (the template header, ~0); swap-out > 0 KiB; PCIe link below gen 3 x16 (Rushuna)
  or gen 4 x16 (Tamanna) during any prefill; Tamanna only: NVMe reads > 1 GiB during a measured decode (flag > 64 MiB).
A void cell is re-run once (results-ARM-rerunLENGTH.json); the re-run's value replaces it when valid, else "void".
Value = mean of the 3 measured requests (min..max).
"""
import glob, json, os, statistics as st, sys

REC = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINK = {"rushuna": ("3", "16"), "tamanna": ("4", "16")}


def score(rig, reps):
    reqs = [r[k] for r in reps for k in ("prime", "measured")]
    pn = [q["timings"]["prompt_n"] for q in reqs]
    cn = [q["timings"]["cache_n"] for q in reqs]
    so = [q["swapout_kib"] for q in reqs]
    links = {tuple(l) for q in reqs for l in q["prefill_pcie_links"]}
    void, flags = [], []
    if max(pn) - min(pn) > 3: void.append(f"prompt_n spread {max(pn) - min(pn)}")
    if max(cn) > 16: void.append(f"cache_n {max(cn)}")
    if max(so) > 0: void.append(f"swap-out {max(so)} KiB")
    if any(l != LINK[rig] for l in links): void.append(f"PCIe {sorted(links)}")
    if any(q["error"] for q in reqs): void.append("request error")
    if rig == "tamanna":
        dec = [r["measured"].get("nvme_read_decode_mib") for r in reps]
        if any(d is None for d in dec): void.append("decode NVMe not recorded")
        elif max(dec) > 1024: void.append(f"decode NVMe {max(dec)} MiB")
        elif max(dec) > 64: flags.append(f"decode NVMe {max(dec)} MiB (flag)")
    empty = sum(1 for q in reqs if not q["answer_head"].strip())
    if empty: flags.append(f"{empty} empty answer(s)")
    m = [r["measured"]["timings"] for r in reps]
    pp = [x["prompt_per_second"] for x in m]; tg = [x["predicted_per_second"] for x in m]
    dn = sum(x.get("draft_n", 0) for x in m); da = sum(x.get("draft_n_accepted", 0) for x in m)
    return {"pp": (st.mean(pp), min(pp), max(pp)), "tg": (st.mean(tg), min(tg), max(tg)), "void": void, "flags": flags,
            "spread": max(pn) - min(pn), "accept": da / dn if dn else None,
            "nvme": [r["measured"]["nvme_read_mib"] for r in reps]}


def arm(rig, a):
    d = os.path.join(REC, rig, a)
    f = os.path.join(d, f"results-{a}.json")
    if not os.path.exists(f):
        return None
    out = {}
    for L, reps in json.load(open(f))["cells"].items():
        s = score(rig, reps); s["src"] = "first pass"
        if s["void"]:
            rf = os.path.join(d, f"results-{a}-rerun{L}.json")
            if os.path.exists(rf):
                r = score(rig, json.load(open(rf))["cells"][L]); r["src"] = "re-run"; r["first_void"] = s["void"]
                if r["void"]:
                    r["void"] = ["void twice: " + "; ".join(s["void"]) + " / " + "; ".join(r["void"])]
                s = r
        out[int(L)] = s
    return out


def fmt(t):
    return f"{t[0]:.1f} ({t[1]:.1f}–{t[2]:.1f})"


def cmp(h, u):
    """H7: faster/slower only when means differ and min..max ranges don't overlap."""
    if h[1] > u[2]: return "faster"
    if h[2] < u[1]: return "slower"
    return "no difference shown"


for rig in ("rushuna", "tamanna"):
    R = {a: arm(rig, a) for a in "UHB"}
    print(f"\n## {rig}\n\n| arm | length | prefill tok/s | decode tok/s | accept | spread | source | void / flags |\n|---|---|---|---|---|---|---|---|")
    for a in "UHB":
        if not R[a]:
            print(f"| {a} | – | – | – | – | – | – | no results file |"); continue
        for L, s in sorted(R[a].items()):
            v = "; ".join(s["void"]) or "valid"
            if s.get("first_void"): v += f" (first pass void: {'; '.join(s['first_void'])})"
            if s["flags"]: v += "; " + "; ".join(s["flags"])
            acc = f"{s['accept']:.2f}" if s["accept"] is not None else "–"
            print(f"| {a} | {L} | {fmt(s['pp'])} | {fmt(s['tg'])} | {acc} | {s['spread']} | {s['src']} | {v} |")
    U, H = R["U"], R["H"]
    if U and H:
        print("\nH vs U per length (H7 rule): decode, prefill, prefill ratio")
        for L in sorted(set(U) & set(H)):
            if U[L]["void"] or H[L]["void"]:
                print(f"  {L}: void cell, not scored"); continue
            print(f"  {L}: decode {cmp(H[L]['tg'], U[L]['tg'])}, prefill {cmp(H[L]['pp'], U[L]['pp'])}, "
                  f"H/U prefill {H[L]['pp'][0] / U[L]['pp'][0]:.2f}, H/U decode {H[L]['tg'][0] / U[L]['tg'][0]:.2f}")
