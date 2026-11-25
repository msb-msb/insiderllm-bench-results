#!/usr/bin/env python3
"""Lock I6 void rules + I9 cell values for every results-*.json in rec/arms.  summarize.py ARMS_DIR > summary.txt"""
import glob, json, os, re, statistics, sys

D = sys.argv[1]


def med(v):
    v = [x for x in v if x is not None]
    return (statistics.median(v), min(v), max(v)) if v else (None, None, None)


def fmt(t, nd=1):
    m, lo, hi = t
    if m is None:
        return "-"
    return f"{m:.{nd}f}" if lo == hi else f"{m:.{nd}f} [{lo:.{nd}f}..{hi:.{nd}f}]"


def looping(text):
    toks = text.split()
    if not toks:
        return True
    top = max(toks.count(t) for t in set(toks))
    return top > len(toks) / 2 and len(toks) > 20


def void_reasons(cell, target):
    why = []
    reqs = cell["reqs"]
    pn = [(r["timings"] or {}).get("prompt_n") or (r["usage"] or {}).get("prompt_tokens") for r in reqs]
    pn = [p for p in pn if p is not None]
    if any(r["error"] for r in reqs):
        why.append("request error: " + "; ".join(r["error"] for r in reqs if r["error"]))
    if pn and max(pn) - min(pn) > 3:
        why.append(f"prompt_n spread {min(pn)}..{max(pn)}")
    if pn and any(abs(p - target) > 0.01 * target for p in pn):
        why.append(f"prompt_n off target {pn} vs {target}")
    cn = [(r["timings"] or {}).get("cache_n") for r in reqs]
    if any(c not in (None, 0) and c > 64 for c in cn):
        why.append(f"cache_n {cn}")
    if cell["pswpout_delta"] > 0 or any(r["swapout_kib"] > 0 for r in reqs):
        why.append(f"swap-out (pswpout +{cell['pswpout_delta']})")
    for r in reqs:
        if any((g, w) != (os.environ.get("PCIE_GEN", "3"), "16") for g, w in r["prefill_pcie_links"]) and r["prefill_pcie_links"]:  # A1.5: PCIE_GEN=4 on Tamanna
            why.append(f"PCIe {r['prefill_pcie_links']}")
        if (r["nvme_read_decode_mib"] or 0) > 1024:
            why.append(f"NVMe decode read {r['nvme_read_decode_mib']} MiB")
        if looping(r["answer_full"]):
            why.append("empty/looping answer")
    return why


rows = []
for f in sorted(glob.glob(os.path.join(D, "results-*.json"))):
    R = json.load(open(f))
    arm = R["arm"]
    if R.get("error"):
        print(f"{arm}: {R['error']} (load {R.get('load_s')} s, load peak {R.get('load_peak_mib')} MiB)")
        continue
    print(f"{arm}: load {R['load_s']} s, card after load {R['card_after_load_mib']} MiB, arm peak {R['arm_peak_mib']} MiB, "
          f"min MemAvailable {R['min_avail_mib']} MiB, avail after load {R.get('avail_after_load_mib')} MiB, "
          f"rss after load {R.get('proc_after_load', {}).get('RssAnon')}/{R.get('proc_after_load', {}).get('RssFile')}")
    for name, c in R["cells"].items():
        reqs = c["reqs"]
        T = [r["timings"] or {} for r in reqs]
        tg = med([t.get("predicted_per_second") for t in T])
        pp = med([t.get("prompt_per_second") for t in T])
        ttft = med([r["ttft_s"] for r in reqs])
        dn = sum((t.get("draft_n") or 0) for t in T); da = sum((t.get("draft_n_accepted") or 0) for t in T)
        acc = f" draft {da}/{dn} = {da / dn:.0%}" if dn else ""
        why = void_reasons(c, c["prompt_target"])
        pn = [t.get("prompt_n") for t in T]
        print(f"  {name:6s} n={len(reqs)} prompt_n {pn} decode {fmt(tg, 2)} prefill {fmt(pp, 1)} ttft {fmt(ttft, 1)} s "
              f"peak card {c['peak_card_mib']} MiB min avail {c['min_avail_mib']} MiB pswpout +{c['pswpout_delta']}{acc}"
              f"{'  VOID: ' + '; '.join(sorted(set(why))) if why else ''}")
