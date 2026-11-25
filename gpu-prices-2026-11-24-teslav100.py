#!/usr/bin/env python3
"""Parse raw/ebay-teslav100-16gb-sold-2026-11-24.txt (eBay US sold, Used, US Only, 16 GB + PCI facets).
Method of gpu-prices-2026-11-06-rtx3090.md / 11-23: card filter by title, sold price excluding shipping,
p25/median/p75 with statistics.quantiles(method='inclusive'), rounded to $5 (half up).
  python3 gpu-prices-2026-11-24-teslav100.py
"""
import json, re, statistics, sys
from datetime import datetime

RAW = "raw/ebay-teslav100-16gb-sold-2026-11-24.txt"
L = open(RAW, encoding="utf-8").read().split("\n")
FEWER = next(i for i, l in enumerate(L) if l.strip() == "Results matching fewer words")
idx = [i for i, l in enumerate(L) if re.match(r"^Sold [A-Z][a-z]{2} \d+, \d{4}$", l)]
# PCIe evidence when the title doesn't say PCIe: PCIe board IDs (PG500 / 699-2G500 / 900-2G500), HPE PCIe SKUs, FHHL
PCIE_ID = re.compile(r"PCI[- ]?E|PCIE|PG500|699-2G500|900-2G500|Q2N68A|876908-001|876340-001|FHHL", re.I)
SXM = re.compile(r"SXM", re.I)
LOT = re.compile(r"\b(LOT|TWO|THREE|FOUR|PAIR)\b|^\(?\d+\s*x\s|\(\d+ ?pack\)", re.I)   # not "(2x 8-pin)"
MULTIMON = re.compile(r"Multi-Monitor", re.I)

rows = []
for k, i in enumerate(idx):
    end = idx[k + 1] - 1 if k + 1 < len(idx) else len(L)
    blk = L[i:end]
    title = blk[1].replace("Opens in a new window or tab", "").strip()
    price_s = next(x for x in blk if x.startswith("$"))
    price = float(price_s.split("$")[1].replace(",", ""))   # a "$sale$was" pair: the first (sold) price
    deliv = next((x for x in blk if "delivery" in x), "")
    ship = 0.0 if deliv.startswith("Free") or not deliv else float(re.search(r"\$([\d,.]+)", deliv).group(1).replace(",", ""))
    rows.append({"line": i + 1, "sold": datetime.strptime(L[i][5:], "%b %d, %Y").date().isoformat(), "price": price,
                 "ship": ship, "cond": next((x for x in blk if x in ("Pre-Owned", "Parts Only")), "?"),
                 "fmt": "or Best Offer" if any(x == "or Best Offer" for x in blk) else "Buy It Now",
                 "loc": next((x for x in blk if x.startswith("Located in")), "?").replace("Located in ", ""),
                 "title": title, "spec": blk[2] if len(blk) > 2 else "", "section": "fewer words" if i > FEWER else "main"})


def classify(r):
    t = r["title"]
    if r["loc"] != "United States":
        return "excluded", f"located in {r['loc']}"
    if r["cond"] != "Pre-Owned":
        return "excluded", f"condition {r['cond']}"
    if "CMP 100-210" in t:
        return "excluded", "not a Tesla V100 (CMP 100-210 mining card; seller's model field says Tesla V100)"
    if not re.search(r"V100", t, re.I):
        if re.search(r"Tesla 16GB HBM2 PCIe.*Volta", t, re.I):
            return "kept", "title omits 'V100' but says Tesla 16GB HBM2 PCIe + Volta (only the V100 PCIe fits)"
        return "excluded", "other card (" + (re.search(r"P100|P40|T4|T10|P4\b", t, re.I) or re.search(r"\S+", t)).group(0) + ")"
    if re.search(r"32\s*GB", t, re.I) and not re.search(r"16G/32G|16GB 32GB", t, re.I):
        return "excluded", "32 GB"
    if re.match(r"SXM2 to PCIe", t, re.I):
        return "excluded", "adapter board only"
    if SXM.search(t):
        return ("sxm2-lot" if LOT.search(t) else "sxm2"), "SXM2 (module, or converted with a PCIe adapter)"
    if LOT.search(t):
        return "excluded", "multi-card lot"
    if not PCIE_ID.search(t):
        return "excluded", "form factor not stated (no PCIe / SXM2 marker or PCIe board ID in the title)"
    return "kept", ""


for r in rows:
    r["class"], r["why"] = classify(r)
q = lambda v: statistics.quantiles(v, n=4, method="inclusive")
r5 = lambda x: int(x / 5 + 0.5) * 5


def band(sel, key="price"):
    v = sorted(r[key] + (r["ship"] if key == "total" else 0) for r in sel) if key == "total" else sorted(r["price"] for r in sel)
    if len(v) < 2:
        return {"n": len(v)}
    a = q(v)
    return {"n": len(v), "p25": round(a[0], 2), "median": round(a[1], 2), "p75": round(a[2], 2), "min": v[0], "max": v[-1]}


kept = [r for r in rows if r["class"] == "kept"]
sx = [r for r in rows if r["class"] in ("sxm2",) and r["loc"] == "United States"]
sxl = [r for r in rows if r["class"] == "sxm2-lot" and r["loc"] == "United States"]
out = {
    "kept": band(kept),
    "kept_shipping_included": band([dict(r, price=r["price"] + r["ship"]) for r in kept]),
    "kept_main_section_only": band([r for r in kept if r["section"] == "main"]),
    "kept_without_multimonitor_wording": band([r for r in kept if not MULTIMON.search(r["title"])]),
    "kept_without_untested": band([r for r in kept if not re.search(r"untested", r["title"], re.I)]),
    "kept_last_30_days": band([r for r in kept if r["sold"] >= "2026-10-26"]),
    "sxm2_us_single": band(sx), "sxm2_us_lots": [(r["line"], r["price"], r["title"]) for r in sxl],
    "dates_kept": [min(r["sold"] for r in kept), max(r["sold"] for r in kept)],
    "or_best_offer_kept": sum(r["fmt"] == "or Best Offer" for r in kept),
}
print(json.dumps(out, indent=1))
print("\nKEPT"); [print(r["line"], r["sold"], r["price"], r["ship"], r["section"], r["title"][:80], "|", r["why"]) for r in sorted(kept, key=lambda r: r["price"])]
print("\nSXM2 (US)"); [print(r["line"], r["sold"], r["price"], r["title"][:80]) for r in sorted(sx + sxl, key=lambda r: r["price"])]
print("\nEXCLUDED (V100-related or US)"); [print(r["line"], r["sold"], r["price"], r["loc"], r["title"][:70], "|", r["why"]) for r in rows
                                          if r["class"] == "excluded" and ("V100" in r["title"].upper() or "CMP" in r["title"] or "form factor" in r["why"])]
print("\nCOUNTS", {c: sum(r["class"] == c for r in rows) for c in ("kept", "sxm2", "sxm2-lot", "excluded")}, "total sold blocks", len(rows))
for r5v in ("kept", "kept_shipping_included", "kept_main_section_only", "kept_last_30_days"):
    b = out[r5v]; print(r5v, "rounded $5:", b["n"], r5(b["p25"]), r5(b["median"]), r5(b["p75"]))
