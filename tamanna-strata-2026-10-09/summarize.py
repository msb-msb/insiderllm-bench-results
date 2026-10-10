"""Tables for one file's run: python3 summarize.py coder|iq3xxs. Mean of 3 measured requests, [min..max]."""
import json, os, sys, statistics as st
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), sys.argv[1])
ARMS = ["S1", "S2-2048", "S2-4096", "S2-8192", "S3", "L1", "L2", "L3"]
R = {}
for a in ARMS:
    p = os.path.join(D, f"results-{a}.json")
    if os.path.exists(p): R[a] = json.load(open(p))["cells"]


def stat(a, n, key):
    v = [c["measured"]["timings"][key] for c in R[a].get(str(n), []) if c["measured"].get("timings")]
    return (st.mean(v), min(v), max(v)) if v else None


def f(x, d=1):
    return "—" if x is None else f"{x[0]:,.{d}f} ({x[1]:,.{d}f}..{x[2]:,.{d}f})"


L = [4096, 16384, 32512]
print("### Prefill, tok/s\n\n| prompt | S1 Strata | L1 (ub 512) | L2 (ub 4096) | L3 (ub 4096 + pinned) | S1÷L1 | S1÷L2 | S1÷L3 | S1 vs best llama.cpp ranges |")
print("|---:|---:|---:|---:|---:|---:|---:|---:|---|")
for n in L:
    s = stat("S1", n, "prompt_per_second"); ls = [stat(a, n, "prompt_per_second") if a in R else None for a in ("L1", "L2", "L3")]
    rat = [f"{s[0] / x[0]:.1f}×" if s and x else "—" for x in ls]
    best = max((x for x in ls if x), key=lambda x: x[0], default=None)
    sep = "no overlap" if s and best and s[1] > best[2] else "overlap"
    print(f"| {n:,} | **{f(s)}** | {f(ls[0])} | {f(ls[1])} | {f(ls[2])} | {' | '.join(rat)} | {sep} |")
print("\n### Decode, tok/s\n\n| prompt | S1 as shipped (MTP + prompt lookup) | draft acceptance | S3 engine speed, no drafts | S3 draft_n | L1 | L2 | L3 | S3 ÷ best llama.cpp |")
print("|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for n in L:
    s1 = stat("S1", n, "predicted_per_second"); s3 = stat("S3", n, "predicted_per_second") if "S3" in R else None
    acc = [c["measured"]["timings"]["draft_n_accepted"] / c["measured"]["timings"]["draft_n"] for c in R["S1"][str(n)] if c["measured"]["timings"].get("draft_n")]
    dn = [c["measured"]["timings"].get("draft_n", 0) for c in R.get("S3", {}).get(str(n), [])]
    ls = [stat(a, n, "predicted_per_second") if a in R else None for a in ("L1", "L2", "L3")]
    best = max((x[0] for x in ls if x), default=None)
    print(f"| {n:,} | {f(s1)} | {100 * st.mean(acc):.0f}% | **{f(s3)}** | {dn} | {f(ls[0])} | {f(ls[1])} | {f(ls[2])} | {s3[0] / best:.1f}× |" if s3 and best else f"| {n:,} | {f(s1)} | | | | | | | |")
print("\n### S2 chunk sweep, 32,512 prompt\n\n| arm | prefill tok/s | prefill rx GB/s mean |\n|---|---:|---:|")
for a in ("S2-2048", "S2-4096", "S2-8192", "S1"):
    if a not in R: continue
    rx = [c["measured"].get("prefill_rx_mb_s_mean") for c in R[a]["32512"] if c["measured"].get("prefill_rx_mb_s_mean")]
    print(f"| {a} | {f(stat(a, 32512, 'prompt_per_second'))} | {st.mean(rx) / 1000:.2f} |" if rx else f"| {a} | {f(stat(a, 32512, 'prompt_per_second'))} | — |")
print("\n### Every measured request: checks\n\n| arm | prompt | prompt_n | cache_n | swap-in / out KiB | NVMe MiB | peak card MiB | PCIe |")
print("|---|---:|---|---|---|---|---|---|")
for a in R:
    for n, cells in R[a].items():
        m = [c["measured"] for c in cells]
        print(f"| {a} | {int(n):,} | {[x['timings']['prompt_n'] for x in m]} | {[x['timings']['cache_n'] for x in m]} | "
              f"{[x.get('swapin_kib') for x in m]} / {[x.get('swapout_kib') for x in m]} | {[x.get('nvme_read_mib') for x in m]} | "
              f"{max(x.get('peak_card_mib') or 0 for x in m)} | {sorted({tuple(l) for x in m for l in (x.get('prefill_pcie_links') or [])})} |")
