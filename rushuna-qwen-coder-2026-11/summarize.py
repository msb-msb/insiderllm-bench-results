#!/usr/bin/env python3
"""Summary tables for the Rushuna Qwen Coder record (lock 918e33f8, P4), from the raw files in this directory.

P4 void rules, applied per cell to its 3 measured requests (as in the Strata records): prompt_n within +-3 tokens
of the cell's median over all 6 requests (primes included; the reading the Tamanna Strata record used when it passed
a 4,123..4,127 cell; a spread of 4 is flagged, since a strict pairwise reading would void it), cache_n 0, swap-out 0, PCIe gen 3 x16 during every prefill.
NVMe reads: flag > 64 MiB, void > 1 GiB. The harness counts NVMe reads over the whole request (prefill + decode),
which can only over-state reads during decode. A void cell gets one re-run (rerun-*.json); void twice = void.
usage: python3 summarize.py  (prints Markdown)"""
import json, os, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
J = lambda *p: json.load(open(os.path.join(HERE, *p)))


def verdict(cell):
    reqs = [x for pair in cell for x in (pair["prime"], pair["measured"])]
    meas = [p["measured"] for p in cell]
    pn = [x["timings"]["prompt_n"] for x in reqs]
    why, flag = [], []  # (prompt_n read as +-3 of the cell median, as the Tamanna Strata record passed 4,123..4,127)
    med = st.median(pn)
    if any(abs(x - med) > 3 for x in pn): why.append(f"prompt_n off the cell median by > 3 ({min(pn)}..{max(pn)})")
    elif max(pn) - min(pn) > 3: flag.append(f"prompt_n spread {max(pn) - min(pn)} ({min(pn)}..{max(pn)}): void only under a strict pairwise reading")
    if any(x["timings"]["cache_n"] for x in reqs): why.append("cache_n > 0")
    if any(x["swapout_kib"] > 0 for x in meas): why.append("swap-out " + "/".join(str(x["swapout_kib"]) for x in meas) + " KiB")
    if any(x["prefill_pcie_links"] != [["3", "16"]] for x in reqs): why.append("PCIe not gen 3 x16")
    if any(x["nvme_read_mib"] > 1024 for x in meas): why.append("NVMe > 1 GiB")
    if any(64 < x["nvme_read_mib"] <= 1024 for x in meas): flag.append("NVMe > 64 MiB")
    return ("VOID: " + "; ".join(why)) if why else ("FLAG: " + "; ".join(flag) if flag else "pass")


def cellstats(cell):
    m = [p["measured"]["timings"] for p in cell]
    f = lambda k: (st.mean(x[k] for x in m), min(x[k] for x in m), max(x[k] for x in m))
    return f("predicted_per_second"), f("prompt_per_second")


fmt = lambda t: f"{t[0]:.1f} ({t[1]:.1f}..{t[2]:.1f})"
for model in ("coder30b", "codernext"):
    print(f"\n### {model}\n")
    sw, sg = J(model, "sweep.json"), J(model, "stage.json")
    print(f"Sweep (llama-bench, -ncmoe N): lowest fitting N = {sw['lowest_fit']}, first failure {sw['first_fail']}. "
          f"Server stage search (L2, -c 34816, 32,512-token request): N = {sg['lowest_ncmoe_that_serves_32512_with_ub4096']}.\n")
    by = {}
    for p in sw["points"]:
        if p["rc"] == 0: by.setdefault(p["ncmoe"], []).append(p)
    print("| -ncmoe N | tg128 d=0, tok/s | tg128 d=4096, tok/s | peak VRAM MiB |\n|---:|---:|---:|---:|")
    for n in sorted(by, reverse=True):
        r = by[n]; d = lambda k: st.mean(x["rows"][k]["avg_ts"] for x in r)
        print(f"| {n} | {d(0):.2f} | {d(1):.2f} | {max(x['peak_vram_mib'] for x in r)} |")
    print("\n| Arm | Prompt | Decode tok/s, mean (min..max) | Prefill tok/s | Swap-out KiB, measured reps | NVMe MiB, measured reps | PCIe | P4 |")
    print("|---|---:|---:|---:|---|---|---|---|")
    for arm in ("L1", "L2"):
        R = J(model, f"results-{arm}.json")
        RR = J(model, f"rerun-{arm}.json")["cells"] if os.path.exists(os.path.join(HERE, model, f"rerun-{arm}.json")) else {}
        for n, cell in R["cells"].items():
            for label, c in [("", cell)] + ([(" **re-run**", RR[n])] if n in RR else []):
                tg, pp = cellstats(c); meas = [p["measured"] for p in c]
                links = sorted({f"gen {g} x{w}" for x in meas for g, w in x["prefill_pcie_links"]})
                print(f"| {arm}{label} | {int(n):,} | {fmt(tg)} | {fmt(pp)} | {' / '.join(str(x['swapout_kib']) for x in meas)} | "
                      f"{' / '.join(str(x['nvme_read_mib']) for x in meas)} | {', '.join(links)} | {verdict(c)} |")
