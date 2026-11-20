#!/usr/bin/env python3
"""Summarize results.jsonl for lock a39c4818 (llamacpp-v1-mtp-3090-2026-11.md), M5 void rules read per A1.

Usage: summarize.py results.jsonl
"""
import json, re, statistics, sys
from collections import defaultdict

GIB, FLAG = 1 << 30, 64 << 20
rows = [json.loads(l) for l in open(sys.argv[1])]
cells = defaultdict(list)
for r in rows:
    cells[(r["arm"], r["mode"], r["prompt"], r["tag"].endswith("-rerun"))].append(r)


def void_reasons(rs):
    why = []
    pn = [r["prompt_n"] for r in rs]
    if max(pn) - min(pn) > 3:
        why.append(f"prompt_n spread {min(pn)}..{max(pn)}")
    if any((r["cache_n"] or 0) > 0 for r in rs):
        why.append(f"cache_n {sorted(set(r['cache_n'] for r in rs))}")
    if any(r["swap_out_kib"] > 0 for r in rs):
        why.append("swap-out")
    for r in rs:  # A1: must reach gen 4 x16 during prefill, no width below x16
        gens = [g for g, _ in r["pcie_prefill"]]; widths = [w for _, w in r["pcie_prefill"]]
        if not gens or max(gens) < 4 or min(widths) < 16:
            why.append(f"pcie {r['pcie_prefill']} ({r['role']} r{r['round']})")
    for r in rs:
        if r["role"] == "measured" and (r["nvme_read_decode_b"] or 0) > GIB:
            why.append(f"nvme decode reads {r['nvme_read_decode_b']}")
    return why


def flags(rs):
    out = []
    for r in rs:
        if r["role"] == "measured" and (r["nvme_read_decode_b"] or 0) > FLAG:
            out.append(f"nvme {r['nvme_read_decode_b'] / 2**20:.0f} MiB r{r['round']}")
        t = r["text200"]
        if len(t.strip()) < 20 or re.search(r"(.{8,})\1\1\1", t):
            out.append(f"sanity r{r['round']} {t[:40]!r}")
    return out


def stat(vals):
    return statistics.mean(vals), min(vals), max(vals)


summary = {}
print(f"{'cell':18} {'decode tok/s mean (min..max)':32} {'prefill':>9} {'TTFT s':>7} {'accept':>7} {'peakMiB':>8}  void/flags")
for arm in "VZO":
    for mode in ("off", "mtp"):
        for prompt in ("short", "long"):
            key = (arm, mode, prompt)
            base = cells.get(key + (False,), [])
            rr = cells.get(key + (True,), [])
            why = void_reasons(base) if base else ["missing"]
            used, rerun = base, False
            if why and rr:
                used, rerun = rr, True
                why = void_reasons(rr)
            meas = [r for r in used if r["role"] == "measured"]
            tg = stat([r["tg_tps"] for r in meas]); pp = stat([r["pp_tps"] for r in meas])
            ttft = statistics.mean(r["ttft_s"] for r in meas)
            acc = [r["draft_n_accepted"] / r["draft_n"] for r in meas if r.get("draft_n")]
            peak = max(r["peak_mib"] for r in used)
            summary[key] = {"tg": tg, "pp": pp, "ttft": ttft, "void": bool(why), "rerun": rerun,
                            "acc": statistics.mean(acc) if acc else None, "peak": peak, "n": len(meas)}
            note = ("VOID: " + "; ".join(why) if why else "ok") + (" (rerun)" if rerun else "")
            fl = flags(used)
            print(f"{arm}-{mode}-{prompt:6} {tg[0]:8.2f} ({tg[1]:.2f}..{tg[2]:.2f}){'':8} {pp[0]:9.1f} {ttft:7.3f} "
                  f"{(summary[key]['acc'] or 0):7.3f} {peak:8d}  {note}{' | ' + ', '.join(fl) if fl else ''}")


def within3(a, b):
    return 0.97 <= a / b <= 1.03


def faster(a, b, lo=None, hi=None):
    ok = a["tg"][0] > b["tg"][0] and a["tg"][1] > b["tg"][2]
    if lo is not None:
        ok = ok and lo <= a["tg"][0] / b["tg"][0] <= hi
    return ok


print("\nPredictions (decode, both prompts must hold; void cells can't score):")
for name, mode, other, test in (
        ("P1 off: V within ±3% of O", "off", "O", "w"), ("P1 off: V within ±3% of Z", "off", "Z", "w"),
        ("P2 mtp: V faster than O, V/O in [1.30,1.70]", "mtp", "O", "f"), ("P3 mtp: V within ±3% of Z", "mtp", "Z", "w")):
    parts = []; results = []
    for prompt in ("short", "long"):
        v, o = summary[("V", mode, prompt)], summary[(other, mode, prompt)]
        if v["void"] or o["void"]:
            parts.append(f"{prompt}: void"); results.append(None); continue
        ratio = v["tg"][0] / o["tg"][0]
        ok = within3(v["tg"][0], o["tg"][0]) if test == "w" else faster(v, o, 1.30, 1.70)
        overlap = "ranges overlap" if v["tg"][1] <= o["tg"][2] and o["tg"][1] <= v["tg"][2] else "ranges apart"
        parts.append(f"{prompt}: V/{other} = {ratio:.3f} ({overlap}) {'holds' if ok else 'MISSES'}")
        results.append(ok)
    # M6: holds only if it holds at both prompts; a miss at either prompt is a miss, void cells can't hold
    verdict = "MISSES" if False in results else ("UNSCORED (void)" if None in results else "HOLDS")
    print(f"  {name}: {verdict}\n      " + "\n      ".join(parts))

print("\nDescriptive: MTP on / MTP off, per arm (decode):")
for arm in "VZO":
    print("  " + arm + ": " + ", ".join(
        f"{p} {summary[(arm, 'mtp', p)]['tg'][0] / summary[(arm, 'off', p)]['tg'][0]:.3f}x" for p in ("short", "long")))
print("Descriptive: prefill V/O and V/Z (long prompt):")
for mode in ("off", "mtp"):
    v = summary[("V", mode, "long")]["pp"][0]
    print(f"  {mode}: V/O {v / summary[('O', mode, 'long')]['pp'][0]:.3f}, V/Z {v / summary[('Z', mode, 'long')]['pp'][0]:.3f}")
print("Descriptive: peak MiB, mtp − off:", {a: summary[(a, 'mtp', 'long')]['peak'] - summary[(a, 'off', 'long')]['peak'] for a in "VZO"})
