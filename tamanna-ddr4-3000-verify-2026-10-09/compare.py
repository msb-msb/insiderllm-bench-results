import json, os
BR="/home/minotaur/Desktop/InsiderLLM/docs/bench-results"
ref=json.load(open(f"{BR}/tamanna-gen4-verify-2026-09-23/summary.json"))
new=json.load(open(f"{BR}/tamanna-ddr4-3000-verify-2026-10-09/summary.json"))
newr=json.load(open(f"{BR}/tamanna-ddr4-3000-verify-2026-10-09/results.json"))
NAME={"ornith-1.5-35b-a3b":"Ornith 1.5-35B-A3B","qwen3.6-35b-a3b":"Qwen3.6-35B-A3B"}
def fmt(x,k): return f"{x:,.1f}" if k=="pp" else f"{x:.2f}"
rows=[]; worst=0; fails=[]
print("| model | metric | 09-23 gen 4, DDR4-2133, 31 GiB (n=3) | 10-09 gen 4, DDR4-3000, 64 GB (n=3) | delta | within 1% |")
print("|---|---|---:|---:|---:|---|")
for m in NAME:
    for k in ("tg","pp"):
        for d in (0,4096,8192):
            key=f"{m}|{k}|{d}"; a=ref[key]; b=new[key]; delta=(b["mean"]-a["mean"])/a["mean"]*100; ok=abs(delta)<1.0; worst=max(worst,abs(delta))
            if not ok: fails.append(key)
            print(f"| {NAME[m] if k=='tg' and d==0 else ''} | {'tg128' if k=='tg' else 'pp512'} d={d} | {fmt(a['mean'],k)} [{fmt(a['min'],k)}..{fmt(a['max'],k)}] | {fmt(b['mean'],k)} [{fmt(b['min'],k)}..{fmt(b['max'],k)}] | {delta:+.2f}% | {'PASS' if ok else 'FAIL'} |")
gens=set()
for r in newr["results"]+newr["primes"]:
    gens|=set(r["telemetry"].get("pcie_gen_under_load",[]))
print(f"\nworst |delta| = {worst:.2f}%  ->  {'PASS' if not fails else 'FAIL: '+', '.join(fails)}")
print(f"PCIe gen under load across all 12 runs: {sorted(gens)}")
