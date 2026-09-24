#!/usr/bin/env python3
"""Three-way: Miu b10088 / Tamanna gen 3 / Tamanna gen 4, and the gen 3 -> gen 4 delta on the same box.
Tamanna figures are the warm measured runs of the priming design (n=3 each). Writes comparison.md / comparison.json."""
import json, os, statistics as st
BR = "/home/minotaur/Desktop/InsiderLLM/docs/bench-results"
G3 = os.path.join(BR, "tamanna-gen3-baseline-2026-09-21"); G4 = os.path.join(BR, "tamanna-gen4-baseline-2026-09-21", "block3")
g3 = json.load(open(os.path.join(G3, "summary.json"))); g4 = json.load(open(os.path.join(G4, "summary.json")))
g3r = json.load(open(os.path.join(G3, "results.json"))); g4r = json.load(open(os.path.join(G4, "results.json")))
ab = json.load(open(os.path.join(BR, "miu-build-ab-2026-09-07/summary.json")))
pub = json.load(open(os.path.join(BR, "miu-ornith-abba-2026-08-28/results.json")))["summary"]["depths"]
pub_pp = {"ornith-1.5-35b-a3b": {0: 3602.94, 4096: 3387.42, 8192: 3263.34}, "qwen3.6-35b-a3b": {0: 3694.22, 4096: 3493.14, 8192: 3362.46}}
MODELS = ["ornith-1.5-35b-a3b", "qwen3.6-35b-a3b"]; NAME = {"ornith-1.5-35b-a3b": "Ornith 1.5-35B-A3B", "qwen3.6-35b-a3b": "Qwen3.6-35B-A3B"}
def fmt(x, k): return f"{x:,.1f}" if k == "pp" else f"{x:.2f}"
def pct(a, b): return (a - b) / b * 100
out, cj = [], {}
out.append("| model | metric | Miu b10088 08-28 published | Miu b10088 09-07 (n=3) | Tamanna gen 3 (n=3) | Tamanna gen 4 (n=3) | gen 3 vs 4, same box | gen 3 vs Miu 08-28 | gen 4 vs Miu 08-28 |")
out.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
for m in MODELS:
    for kind in ("tg", "pp"):
        for d in (0, 4096, 8192):
            k = f"{m}|{kind}|{d}"; a = g3[k]; b = g4[k]; mb = ab[k]["b10088"]; p = pub[str(d)][m] if kind == "tg" else pub_pp[m][d]
            row = {"miu_0828": p, "miu_b10088_0907": mb, "gen3": a, "gen4": b, "gen3_vs_gen4_pct": pct(a["mean"], b["mean"]),
                   "gen3_vs_0828_pct": pct(a["mean"], p), "gen4_vs_0828_pct": pct(b["mean"], p), "gen3_vs_b10088_0907_pct": pct(a["mean"], mb["mean"]),
                   "spread_gen3": a["max"] - a["min"], "spread_gen4": b["max"] - b["min"], "gap_tok_s": a["mean"] - b["mean"]}
            row["resolvable"] = abs(row["gap_tok_s"]) > max(row["spread_gen3"], row["spread_gen4"])
            cj[k] = row
            out.append(f"| {NAME[m] if kind=='tg' and d==0 else ''} | {'tg128' if kind=='tg' else 'pp512'} d={d} | {fmt(p,kind)} | {fmt(mb['mean'],kind)} [{fmt(mb['min'],kind)}..{fmt(mb['max'],kind)}] | {fmt(a['mean'],kind)} [{fmt(a['min'],kind)}..{fmt(a['max'],kind)}] | {fmt(b['mean'],kind)} [{fmt(b['min'],kind)}..{fmt(b['max'],kind)}] | **{row['gen3_vs_gen4_pct']:+.2f}%** ({'resolvable' if row['resolvable'] else 'inside spread'}) | {row['gen3_vs_0828_pct']:+.2f}% | {row['gen4_vs_0828_pct']:+.2f}% |")
out.append(""); out.append("Gen 3 vs gen 4 on the same box: gap in tok/s against the larger of the two same-config repeat spreads (the 08-28 resolvability rule):"); out.append("")
out.append("| model | metric | gen 3 − gen 4 (tok/s) | gen 3 spread | gen 4 spread | verdict |"); out.append("|---|---|---:|---:|---:|---|")
for m in MODELS:
    for kind in ("tg", "pp"):
        for d in (0, 4096, 8192):
            r = cj[f"{m}|{kind}|{d}"]
            out.append(f"| {NAME[m] if kind=='tg' and d==0 else ''} | {'tg128' if kind=='tg' else 'pp512'} d={d} | {r['gap_tok_s']:+.2f} | {r['spread_gen3']:.2f} | {r['spread_gen4']:.2f} | {'RESOLVABLE' if r['resolvable'] else 'UNRESOLVABLE'} |")
def under_load(path):
    rows = []
    for line in open(path).read().splitlines()[1:]:
        f = [x.strip() for x in line.split(",")]
        try:
            if int(f[8]) >= 50: rows.append((int(f[1]), int(f[2]), int(f[3]), int(f[4]), int(f[5]), int(f[6]), float(f[7]), f[10]))
        except (ValueError, IndexError): pass
    return rows
out.append(""); out.append("Gen 3 run telemetry, every run including primes (samples with utilisation ≥ 50%):"); out.append("")
out.append("| run | model | PCIe gen (host view / GPU view) x width | under-load samples | SM clock median (min..max) | mem clock | power mean (max) | temp start → max | reasons |"); out.append("|---|---|---|---:|---|---|---|---|---|")
allgens = set(); n_all = 0
for r in sorted(g3r["results"] + g3r["primes"], key=lambda r: r["started"]):
    tag = "prime-" if r.get("tag") == "prime" else ""
    ul = under_load(os.path.join(G3, f"telemetry-{tag}{r['model']}-rep{r['rep']}.csv"))
    gens = sorted(set((x[0], x[1]) for x in ul)); widths = sorted(set(x[2] for x in ul)); allgens |= set(gens); n_all += len(ul)
    sm = [x[4] for x in ul]; t = r["telemetry"]
    out.append(f"| {r.get('tag','measured')} rep {r['rep']} | {NAME[r['model']]} | {', '.join(f'{h}/{g}' for h, g in gens)} x{widths} | {len(ul)} | {st.median(sm):.0f} ({min(sm)}..{max(sm)}) | {st.median([x[5] for x in ul]):.0f} | {st.mean([x[6] for x in ul]):.0f} W ({max(x[6] for x in ul):.0f}) | {t['temp_start']} → {t['temp_max']} °C | {' / '.join(sorted(set(x[7] for x in ul)))} |")
out.append(""); out.append(f"All under-load samples across the 12 gen 3 runs: {n_all} samples, PCIe gen (host/GPU) values seen = {sorted(allgens)}.")
cj["_pcie_gen_under_load_all_runs"] = {"samples": n_all, "gens_seen": sorted(allgens)}
open(os.path.join(G3, "comparison.md"), "w").write("\n".join(out) + "\n"); json.dump(cj, open(os.path.join(G3, "comparison.json"), "w"), indent=1)
print("\n".join(out))
