#!/usr/bin/env python3
"""Tamanna Gen 4 baseline beside the Miu rows. Reads the result files; writes comparison.md and comparison.json."""
import json, os, statistics as st
BR = "/home/minotaur/Desktop/InsiderLLM/docs/bench-results"
T = os.path.join(BR, "tamanna-gen4-baseline-2026-09-21")
tam = json.load(open(os.path.join(T, "summary.json")))
tres = json.load(open(os.path.join(T, "results.json")))["results"]
ab = json.load(open(os.path.join(BR, "miu-build-ab-2026-09-07/summary.json")))
ab2 = json.load(open(os.path.join(BR, "miu-build-ab-2026-09-07/block2/summary.json")))
abres = json.load(open(os.path.join(BR, "miu-build-ab-2026-09-07/results.json")))["results"]
ab2res = json.load(open(os.path.join(BR, "miu-build-ab-2026-09-07/block2/results.json")))["results"]
pub = json.load(open(os.path.join(BR, "miu-ornith-abba-2026-08-28/results.json")))["summary"]["depths"]
# 08-28 prefill figures are in that run's README table, not its summary block
pub_pp = {"ornith-1.5-35b-a3b": {0: 3602.94, 4096: 3387.42, 8192: 3263.34}, "qwen3.6-35b-a3b": {0: 3694.22, 4096: 3493.14, 8192: 3362.46}}
MODELS = ["ornith-1.5-35b-a3b", "qwen3.6-35b-a3b"]
NAME = {"ornith-1.5-35b-a3b": "Ornith 1.5-35B-A3B", "qwen3.6-35b-a3b": "Qwen3.6-35B-A3B"}
def pooled(model, kind, depth):
    v = [x["avg_ts"] for r in abres + ab2res if r["model"] == model and r["build"] == "v0.4.0" for x in r["rows"] if x["kind"] == kind and x["depth"] == depth]
    return v
def parse_csv(path):
    rows = []
    with open(path) as f:
        next(f)
        for line in f:
            parts = [x.strip() for x in line.split(",")]
            try: rows.append({"util": int(parts[8]), "pcie_gen": int(parts[1])})
            except (ValueError, IndexError): pass
    return rows
def fmt(x, kind): return f"{x:,.1f}" if kind == "pp" else f"{x:.2f}"
def pct(a, b): return (a - b) / b * 100
out, cj = [], {}
out.append("| model | metric | Tamanna v0.4.0 (n=3) | Miu v0.4.0 09-07 (n=3) | Δ vs Miu v0.4.0 | Miu b10088 09-07 (n=3) | Δ vs Miu b10088 | Miu b10088 08-28 published | Δ vs 08-28 |")
out.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
for m in MODELS:
    for kind in ("tg", "pp"):
        for d in (0, 4096, 8192):
            k = f"{m}|{kind}|{d}"; t = tam[k]
            mv = ab[k]["v0.4.0"]; mb = ab[k]["b10088"]
            p = pub[str(d)][m] if kind == "tg" else pub_pp[m][d]
            label = f"{'tg128' if kind=='tg' else 'pp512'} d={d}"
            row = {"tamanna": t, "miu_v040": mv, "miu_b10088": mb, "miu_0828": p,
                   "delta_vs_miu_v040_pct": pct(t["mean"], mv["mean"]), "delta_vs_miu_b10088_pct": pct(t["mean"], mb["mean"]), "delta_vs_0828_pct": pct(t["mean"], p)}
            if m == "qwen3.6-35b-a3b":
                pv = pooled(m, kind, d); row["miu_v040_pooled_n6"] = {"mean": st.mean(pv), "min": min(pv), "max": max(pv)}; row["delta_vs_miu_v040_pooled_pct"] = pct(t["mean"], st.mean(pv))
            cj[k] = row
            out.append(f"| {NAME[m] if kind=='tg' and d==0 else ''} | {label} | {fmt(t['mean'],kind)} [{fmt(t['min'],kind)}..{fmt(t['max'],kind)}] | {fmt(mv['mean'],kind)} [{fmt(mv['min'],kind)}..{fmt(mv['max'],kind)}] | {row['delta_vs_miu_v040_pct']:+.2f}% | {fmt(mb['mean'],kind)} [{fmt(mb['min'],kind)}..{fmt(mb['max'],kind)}] | {row['delta_vs_miu_b10088_pct']:+.2f}% | {fmt(p,kind)} | {row['delta_vs_0828_pct']:+.2f}% |")
out.append("")
out.append("Qwen against the pooled Miu v0.4.0 figure (blocks 1+2, n=6):")
out.append("")
out.append("| metric | Tamanna | Miu v0.4.0 pooled n=6 | Δ |")
out.append("|---|---:|---:|---:|")
for kind in ("tg", "pp"):
    for d in (0, 4096, 8192):
        r = cj[f"qwen3.6-35b-a3b|{kind}|{d}"]; pv = r["miu_v040_pooled_n6"]
        out.append(f"| {'tg128' if kind=='tg' else 'pp512'} d={d} | {fmt(r['tamanna']['mean'],kind)} | {fmt(pv['mean'],kind)} [{fmt(pv['min'],kind)}..{fmt(pv['max'],kind)}] | {r['delta_vs_miu_v040_pooled_pct']:+.2f}% |")
out.append("")
out.append("Per-rep telemetry (samples with GPU utilisation ≥ 50%):")
out.append("")
out.append("| rep | model | start → max temp | SM clock median (min..max) | mem clock median | power mean (max) | PCIe gen under load | clock-event reasons | VRAM peak | run time |")
out.append("|---|---|---|---|---|---|---|---|---|---|")
for r in tres:
    t = r["telemetry"]
    share = ", ".join(f"gen {g}: {int(s*100)}%" for g, s in t.get("pcie_gen_under_load_share", {}).items())
    out.append(f"| {r['rep']} | {NAME[r['model']]} | {t['temp_start']} → {t['temp_max']} °C | {t['sm_clock']['median']:.0f} ({t['sm_clock']['min']}..{t['sm_clock']['max']}) MHz | {t['mem_clock']['median']:.0f} MHz | {t['power']['mean']:.0f} W ({t['power']['max']:.0f}) | {share} x{t['pcie_width_under_load']} | {' / '.join(t['clock_event_reasons_under_load'])} | {t['vram_peak_mib']:,} MiB | {r['elapsed_s']:.0f} s |")
B2 = os.path.join(T, "block2")
if os.path.exists(os.path.join(B2, "summary.json")):
    tam2 = json.load(open(os.path.join(B2, "summary.json")))
    tres2 = json.load(open(os.path.join(B2, "results.json")))["results"]
    out.append(""); out.append("Block 2 (same design, replication) and Tamanna pooled over both blocks (n=6):"); out.append("")
    out.append("| model | metric | block 1 (n=3) | block 2 (n=3) | Δ block 2 vs 1 | Tamanna pooled n=6 | Miu v0.4.0 09-07 (Qwen pooled n=6) | Δ pooled vs Miu v0.4.0 | Miu b10088 08-28 | Δ pooled vs 08-28 |")
    out.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for m in MODELS:
        for kind in ("tg", "pp"):
            for d in (0, 4096, 8192):
                k = f"{m}|{kind}|{d}"; a = tam[k]; b = tam2[k]; pv = a["reps"] + b["reps"]
                miu = cj[k]["miu_v040_pooled_n6"] if m == "qwen3.6-35b-a3b" else ab[k]["v0.4.0"]
                p = pub[str(d)][m] if kind == "tg" else pub_pp[m][d]
                cj[k]["block2"] = b; cj[k]["tamanna_pooled_n6"] = {"mean": st.mean(pv), "min": min(pv), "max": max(pv), "reps": pv}
                cj[k]["delta_pooled_vs_miu_v040_pct"] = pct(st.mean(pv), miu["mean"]); cj[k]["delta_pooled_vs_0828_pct"] = pct(st.mean(pv), p)
                out.append(f"| {NAME[m] if kind=='tg' and d==0 else ''} | {'tg128' if kind=='tg' else 'pp512'} d={d} | {fmt(a['mean'],kind)} [{fmt(a['min'],kind)}..{fmt(a['max'],kind)}] | {fmt(b['mean'],kind)} [{fmt(b['min'],kind)}..{fmt(b['max'],kind)}] | {pct(b['mean'],a['mean']):+.2f}% | {fmt(st.mean(pv),kind)} [{fmt(min(pv),kind)}..{fmt(max(pv),kind)}] | {fmt(miu['mean'],kind)} | {cj[k]['delta_pooled_vs_miu_v040_pct']:+.2f}% | {fmt(p,kind)} | {cj[k]['delta_pooled_vs_0828_pct']:+.2f}% |")
    out.append(""); out.append("Block 2 per-rep telemetry:"); out.append("")
    out.append("| rep | model | start → max temp | SM clock median (min..max) | mem clock median | power mean (max) | PCIe gen under load | VRAM peak | run time |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    for r in tres2:
        t = r["telemetry"]; share = ", ".join(f"gen {g}: {int(s*100)}%" for g, s in t.get("pcie_gen_under_load_share", {}).items())
        out.append(f"| {r['rep']} | {NAME[r['model']]} | {t['temp_start']} → {t['temp_max']} °C | {t['sm_clock']['median']:.0f} ({t['sm_clock']['min']}..{t['sm_clock']['max']}) MHz | {t['mem_clock']['median']:.0f} MHz | {t['power']['mean']:.0f} W ({t['power']['max']:.0f}) | {share} x{t['pcie_width_under_load']} | {t['vram_peak_mib']:,} MiB | {r['elapsed_s']:.0f} s |")
B3 = os.path.join(T, "block3")
if os.path.exists(os.path.join(B3, "results.json")):
    r3 = json.load(open(os.path.join(B3, "results.json"))); meas, prim = r3["results"], r3["primes"]
    tam3 = json.load(open(os.path.join(B3, "summary.json")))
    out.append(""); out.append("Block 3 (diagnostic): priming run (cold load after the swap, discarded) vs the measured run that followed it (warm):"); out.append("")
    out.append("| rep | model | run | load-phase s (util<50 before first ≥50) | pp512 d=0 samples | pp512 d=0 | pp512 d=4096 | pp512 d=8192 | tg128 d=0 | power mean |")
    out.append("|---|---|---|---:|---|---:|---:|---:|---:|---:|")
    def loadphase(path):
        rows = parse_csv(path); n = 0
        for r in rows:
            if r["util"] >= 50: break
            n += 1
        return n
    for pr, mr in zip(prim, meas):
        for tag, r in (("prime (cold)", pr), ("measured (warm)", mr)):
            pp = {x["depth"]: x for x in r["rows"] if x["kind"] == "pp"}; tg = {x["depth"]: x for x in r["rows"] if x["kind"] == "tg"}
            tp = os.path.join(B3, f"telemetry-{'prime-' if tag.startswith('prime') else ''}{r['model']}-rep{r['rep']}.csv")
            out.append(f"| {r['rep']} | {NAME[r['model']]} | {tag} | {loadphase(tp)} | {' '.join(str(round(x)) for x in pp[0]['samples'])} | {pp[0]['avg_ts']:,.0f} | {pp[4096]['avg_ts']:,.0f} | {pp[8192]['avg_ts']:,.0f} | {tg[0]['avg_ts']:.2f} | {r['telemetry']['power']['mean']:.0f} W |")
    out.append(""); out.append("Block 3 measured (warm) runs, n=3, beside block 1 and the Miu rows:"); out.append("")
    out.append("| model | metric | block 3 warm (n=3) | block 1 (n=3) | Miu v0.4.0 09-07 (Qwen pooled n=6) | Δ block 3 vs Miu v0.4.0 | Miu b10088 08-28 | Δ block 3 vs 08-28 |")
    out.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for m in MODELS:
        for kind in ("tg", "pp"):
            for d in (0, 4096, 8192):
                k = f"{m}|{kind}|{d}"; a = tam[k]; b = tam3[k]
                miu = cj[k]["miu_v040_pooled_n6"] if m == "qwen3.6-35b-a3b" else ab[k]["v0.4.0"]
                p = pub[str(d)][m] if kind == "tg" else pub_pp[m][d]
                cj[k]["block3_warm"] = b; cj[k]["delta_block3_vs_miu_v040_pct"] = pct(b["mean"], miu["mean"]); cj[k]["delta_block3_vs_0828_pct"] = pct(b["mean"], p)
                out.append(f"| {NAME[m] if kind=='tg' and d==0 else ''} | {'tg128' if kind=='tg' else 'pp512'} d={d} | {fmt(b['mean'],kind)} [{fmt(b['min'],kind)}..{fmt(b['max'],kind)}] | {fmt(a['mean'],kind)} [{fmt(a['min'],kind)}..{fmt(a['max'],kind)}] | {fmt(miu['mean'],kind)} | {cj[k]['delta_block3_vs_miu_v040_pct']:+.2f}% | {fmt(p,kind)} | {cj[k]['delta_block3_vs_0828_pct']:+.2f}% |")
open(os.path.join(T, "comparison.md"), "w").write("\n".join(out) + "\n")
json.dump(cj, open(os.path.join(T, "comparison.json"), "w"), indent=1)
print("\n".join(out))
