#!/usr/bin/env python3
"""Summary tables for the Tamanna Qwen Coder speed record (lock 918e33f8, P4), from the raw files in this directory.

P4 void rules, with amendment A1 (2026-11-17, the stricter prompt_n reading): prompt_n max - min <= 3 across all 6
requests of the cell (primes included); cache_n 0 on all 6; swap-out 0 on the 3 measured; PCIe gen 4 x16 during every
prefill. NVMe reads on a measured request: flag > 64 MiB, void > 1 GiB (counted over the whole request, so they can
only over-state reads during decode). A void cell gets one re-run (rerun-*.json), which replaces it; void twice = void.
No sweep on Tamanna (P4). usage: python3 summarize.py  (prints Markdown)"""
import json, os, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
J = lambda *p: json.load(open(os.path.join(HERE, *p)))


def verdict(cell):
    reqs = [x for pair in cell for x in (pair["prime"], pair["measured"])]
    meas = [p["measured"] for p in cell]
    pn = [x["timings"]["prompt_n"] for x in reqs]
    why, flag = [], []
    if max(pn) - min(pn) > 3: why.append(f"prompt_n spread {max(pn) - min(pn)} ({min(pn)}..{max(pn)})")
    if any(x["timings"]["cache_n"] for x in reqs): why.append("cache_n > 0")
    if any(x["swapout_kib"] > 0 for x in meas): why.append("swap-out " + "/".join(str(x["swapout_kib"]) for x in meas) + " KiB")
    if any(x["prefill_pcie_links"] != [["4", "16"]] for x in reqs): why.append("PCIe not gen 4 x16")
    if any(x["nvme_read_mib"] > 1024 for x in meas): why.append("NVMe > 1 GiB")
    if any(64 < x["nvme_read_mib"] <= 1024 for x in meas): flag.append("NVMe > 64 MiB")
    return ("VOID: " + "; ".join(why)) if why else ("FLAG: " + "; ".join(flag) if flag else "pass")


def cellstats(cell):
    m = [p["measured"]["timings"] for p in cell]
    f = lambda k: (st.mean(x[k] for x in m), min(x[k] for x in m), max(x[k] for x in m))
    return f("predicted_per_second"), f("prompt_per_second")


fmt = lambda t: f"{t[0]:.1f} ({t[1]:.1f}..{t[2]:.1f})"
for model in ("coder30b", "codernext"):
    sg = J(model, "stage.json")
    print(f"\n### {model}\n\nServer stage search (L2, -c 34816, 32,512-token request): "
          f"N = {sg['lowest_ncmoe_that_serves_32512_with_ub4096']}.\n")
    print("| Arm | Prompt | Decode tok/s, mean (min..max) | Prefill tok/s | prompt_n, 6 requests | Swap-out KiB, measured reps | NVMe MiB, measured reps | PCIe | P4 |")
    print("|---|---:|---:|---:|---|---|---|---|---|")
    for arm in ("L1", "L2"):
        R = J(model, f"results-{arm}.json")
        RR = J(model, f"rerun-{arm}.json")["cells"] if os.path.exists(os.path.join(HERE, model, f"rerun-{arm}.json")) else {}
        for n, cell in R["cells"].items():
            for label, c in [("", cell)] + ([(" **re-run**", RR[n])] if n in RR else []):
                tg, pp = cellstats(c); meas = [p["measured"] for p in c]
                pn = [x["timings"]["prompt_n"] for p in c for x in (p["prime"], p["measured"])]
                links = sorted({f"gen {g} x{w}" for x in meas for g, w in x["prefill_pcie_links"]})
                print(f"| {arm}{label} | {int(n):,} | {fmt(tg)} | {fmt(pp)} | {min(pn):,}..{max(pn):,} | "
                      f"{' / '.join(str(x['swapout_kib']) for x in meas)} | {' / '.join(str(x['nvme_read_mib']) for x in meas)} | "
                      f"{', '.join(links)} | {verdict(c)} |")
