#!/usr/bin/env python3
"""Parse Mark's six eBay US sold pulls saved 2026-11-26 (raw/ebay-*-sold-2026-11-26.txt).
Method of gpu-prices-2026-11-24-teslav100.py (itself 11-06 / 11-23): card filter BY TITLE, US-located only,
sold price EXCLUDING shipping, "$sale$was" pairs use the first (sold) price, best-offer-accepted sales kept at the
price shown (sensitivity without them), p25/median/p75 with statistics.quantiles(method='inclusive'), rounded to
$5 half up. Conditions: Used = Pre-Owned. New = Brand New + New (Other); Open Box and refurbished are reported on
their own and are in neither band; Parts Only is excluded.
Window: a page that holds the complete result set (R9700 47 results, P100 62) uses every sale, as eBay's 90-day
history. A capped 240-listing page uses the run of days it covers continuously (the newest sale back to the first
gap of more than 3 days with no sale); older stragglers are excluded and listed.
  python3 gpu-prices-2026-11-26.py [card ...]      # cards: r9700 p100 rtx5090 rtx3060 rx7800xt rtx5060ti
Prints JSON bands, then every kept and excluded block with its reason.
"""
import json, re, statistics, sys
from datetime import date, datetime, timedelta

PULL = date(2026, 11, 26)
LAST30 = PULL - timedelta(days=30)          # 2026-10-27..11-26
CONDS = ("Pre-Owned", "Brand New", "New (Other)", "Open Box", "Parts Only")
LOT = re.compile(r"\b(LOT|LOTS|PAIR|BUNDLE)\b|^\(?\d+\s*x\s|\b\d+\s*x\s+(nvidia|rtx|amd|tesla|radeon|xfx|asus|asrock|msi|gigabyte|zotac|pny|evga)|\b[2-9]\s*(pcs|pieces|units|cards)\b|\(\d+ ?pack\)|\bTWO\b|\bthree\b|\bfour\b", re.I)
PARTS = re.compile(r"for parts|parts only|not working|no core|no vram|no display|untested.*parts|broken|as[- ]is|\bdead\b|artifact|repair|damaged|no gpu|pcb only", re.I)
NOTCARD = re.compile(r"\b(box only|empty box|backplate only|cooler only|heatsink only|fan only|shroud only|waterblock|water block|bracket|riser|cable|adapter only|bridge|fan shroud|replacement fan|cooling fan)\b", re.I)
# Whole systems / laptops: a CPU, storage, screen or refresh-rate marker in the title.
SYSTEM = re.compile(r"\b(gaming pc|desktop pc|desktop computer|workstation pc|ai workstation|prebuilt|pre-built|tower|laptop|notebook|server with|computer w|desktop:|gaming desktop|PC Specifications)\b"
                    r"|\b(\d+\s?TB\s?(SSD|NVMe)?|SSD|NVMe|DDR5|DDR4)\b|\b\d{2,3}\s?Hz\b|\d{3}HX\b|\bHX \d{3}\b|Ultra [579] \d{3}|Ryzen AI 9|Ryzen [3579] \d{4}|\bi[3579]-\d{4,5}|Core i[3579]\b"
                    r"|\d{2}(\.\d)?\s?(\"|”|''|-inch)", re.I)
SYSTEM_BRAND = re.compile(r"\b(ThinkPad|Legion|Alienware|Razer Blade|Raider|Titan 18|Stealth A1\d|Strix Scar|ProArt 16|Sager|BIMBOX|OMEN|Zephyrus|Predator Helios|Aurora|XPS|CyberPowerPC|Skytech|PowerSpec)\b", re.I)
EXTERNAL = re.compile(r"XG[- ]?Mobile|eGPU|AI Box|External Graphics", re.I)
ACCESSORY = re.compile(r"retention|x-bracket|thermal pad|\bconnector\b|\bcable\b|\bbracket\b|\bscrews\b|backplate only|fan only|cooler only|heatsink only|box only|empty box|\bbridge\b|riser", re.I)


def card_r9700(t):
    if not re.search(r"R\s?9700", t, re.I) or re.search(r"9700X|9700 X\b|Ryzen", t, re.I):
        return "other card (no R9700 in title, or Ryzen 9700X)"
    if re.search(r"R9700S\b", t, re.I):
        return "R9700S (a different SKU name)"
    return None


def card_p100(t):
    if not re.search(r"P100", t, re.I):
        m = re.search(r"P40|V100|T4\b|K80|M40|P4\b|A100|M10|P6000", t, re.I)
        return "other card (" + (m.group(0) if m else "no P100") + ")"
    if re.search(r"SXM", t, re.I):
        return "SXM2"
    if re.search(r"12\s*GB", t, re.I) and not re.search(r"16\s*GB", t, re.I):
        return "12 GB"
    return None


def card_rtx5090(t):
    if not re.search(r"5090", t) or re.search(r"5090\s?D\b|5080|4090|5070", t, re.I) and not re.search(r"RTX\s?5090\b(?!\s?D)", t, re.I):
        return "other card"
    if re.search(r"5090\s?D\b", t, re.I):
        return "RTX 5090D (China model)"
    return None


def card_rtx3060(t):
    if not re.search(r"3060", t):
        return "other card"
    if re.search(r"3060\s?Ti|3060Ti|\bTi\b", t, re.I):
        return "RTX 3060 Ti"
    if re.search(r"\b8\s?GB\b", t, re.I) and not re.search(r"12\s?GB", t, re.I):
        return "RTX 3060 8GB"
    if re.search(r"3060\s?M\b|mobile|laptop", t, re.I):
        return "laptop/mobile"
    return None


def card_rx7800xt(t):
    if not re.search(r"7800\s?XT", t, re.I):
        return "other card (no 7800 XT)"
    if re.search(r"7800X3D", t, re.I):
        return "Ryzen 7800X3D"
    return None


def card_rtx5060ti(t):
    if not re.search(r"5060\s?Ti", t, re.I):
        return "other card (no 5060 Ti)"
    if re.search(r"\b8\s?GB\b", t, re.I) and not re.search(r"16\s?GB", t, re.I):
        return "RTX 5060 Ti 8GB"
    return None


CARDS = {
    "r9700": ("ebay-r9700-sold-2026-11-26.txt", card_r9700, "complete"),
    "p100": ("ebay-teslap100-16gb-sold-2026-11-26.txt", card_p100, "complete"),
    "rtx5090": ("ebay-rtx5090-sold-2026-11-26.txt", card_rtx5090, "capped"),
    "rtx3060": ("ebay-rtx3060-sold-2026-11-26.txt", card_rtx3060, "capped"),
    "rx7800xt": ("ebay-rx7800xt-sold-2026-11-26.txt", card_rx7800xt, "capped"),
    "rtx5060ti": ("ebay-rtx5060ti-16gb-sold-2026-11-26.txt", card_rtx5060ti, "capped"),
}


def blocks(path):
    L = open("raw/" + path, encoding="utf-8").read().split("\n")
    idx = [i for i, l in enumerate(L) if re.match(r"^Sold [A-Z][a-z]{2} \d+, \d{4}$", l)]
    out = []
    for k, i in enumerate(idx):
        blk = L[i:(idx[k + 1] - 1 if k + 1 < len(idx) else len(L))]
        title = blk[1].replace("Opens in a new window or tab", "").strip()
        price_s = next(x for x in blk if x.startswith("$"))
        rng = " to " in price_s                 # multi-variation listing: "$649.95 to $699.95", sold price unknown
        price = float(price_s.split("$")[1].replace(",", "").replace(" to ", ""))
        deliv = next((x for x in blk if "delivery" in x), "")
        ship = 0.0 if deliv.startswith("Free") or not deliv else float(re.search(r"\$([\d,.]+)", deliv).group(1).replace(",", ""))
        cond = next((x for x in blk[2:6] if x in CONDS or "Refurbished" in x), "?")
        spec = blk[2] if blk[2] != cond and not blk[2].startswith("$") else ""
        out.append({"line": i + 1, "sold": datetime.strptime(L[i][5:], "%b %d, %Y").date(), "price": price, "ship": ship,
                    "cond": cond, "range": rng, "boa": any(x == "Best offer accepted" for x in blk),
                    "loc": next((x for x in blk if x.startswith("Located in")), "?").replace("Located in ", ""),
                    "title": title, "spec": spec})
    return out


def run_window(rows):
    ds = sorted({r["sold"] for r in rows}, reverse=True)
    start = ds[0]
    for a, b in zip(ds, ds[1:]):
        if (a - b).days > 4:          # a gap of more than 3 empty days
            break
        start = b
    return start, ds[0]


# Hand decisions after reading the title (key: card, line). Each is listed in the record.
OVERRIDE = {
    ("p100", 526): ("used", "kept by hand: 'Heatsink Only' reads as the card with its passive heatsink and no fan ($93)"),
}


def classify(r, cardfn, wstart, card=None):
    t = r["title"]
    if (card, r["line"]) in OVERRIDE:
        return OVERRIDE[(card, r["line"])]
    if r["loc"] != "United States":
        return "excluded", f"located in {r['loc']}"
    why = cardfn(t)
    if why:
        return "excluded", why
    if r["cond"] == "Parts Only" or PARTS.search(t):
        return "excluded", "parts / not working" + ("" if r["cond"] == "Parts Only" else " (by title)")
    if re.search(r"box only|empty box|\bbox\b.{0,15}\bonly\b", t, re.I):
        return "excluded", "box only, no card"
    if ACCESSORY.search(t) and not re.search(r"(no|missing|without)\s+(end\s+)?bracket", t, re.I) and not re.search(r"(?:^|\s|\b)(with|w/|\+|incl\.?|includes?)\s*(\S+\s){0,5}(cable|bracket|connector|riser|cables)", t, re.I) or NOTCARD.search(t) and not re.search(r"graphics card|gpu|video card|\b\d+\s?GB\b", t, re.I):
        return "excluded", "accessory or box, not a card"
    if EXTERNAL.search(t):
        return "excluded", "external GPU enclosure (eGPU / XG Mobile)"
    if SYSTEM.search(t) or SYSTEM_BRAND.search(t) and not re.search(r"graphics card|\bGPU\b|video card", t, re.I):
        return "excluded", "whole system or laptop"
    if LOT.search(t):
        return "excluded", "multi-card lot or bundle"
    if r["range"]:
        return "excluded", "multi-variation listing (price shown as a range)"
    if r["sold"] < wstart:
        return "excluded", "sold before the window (straggler)"
    if "Refurbished" in r["cond"]:
        return "refurb", r["cond"]
    if r["cond"] == "Open Box":
        return "openbox", ""
    if r["cond"] in ("Brand New", "New (Other)"):
        return "new", r["cond"]
    if r["cond"] == "Pre-Owned":
        return "used", ""
    return "excluded", f"condition {r['cond']}"


q = lambda v: statistics.quantiles(v, n=4, method="inclusive")
r5 = lambda x: int(x / 5 + 0.5) * 5


def band(sel, ship=False):
    v = sorted(r["price"] + (r["ship"] if ship else 0) for r in sel)
    if len(v) < 2:
        return {"n": len(v), "values": v}
    a = q(v)
    return {"n": len(v), "p25": round(a[0], 2), "median": round(a[1], 2), "p75": round(a[2], 2),
            "r5": [r5(a[0]), r5(a[1]), r5(a[2])], "min": v[0], "max": v[-1]}


def main(card):
    path, fn, kind = CARDS[card]
    rows = blocks(path)
    us = [r for r in rows if r["loc"] == "United States" and fn(r["title"]) is None]
    wstart, wend = (min(r["sold"] for r in rows), max(r["sold"] for r in rows)) if kind == "complete" else run_window(us)
    for r in rows:
        r["class"], r["why"] = classify(r, fn, wstart, card)
    by = lambda c: [r for r in rows if r["class"] == c]
    used, new = by("used"), by("new")
    out = {"card": card, "file": path, "blocks": len(rows), "window": [str(wstart), str(wend)], "kind": kind,
           "used": band(used), "used_ship_incl": band(used, True), "used_without_boa": band([r for r in used if not r["boa"]]),
           "used_last30": band([r for r in used if r["sold"] >= LAST30]),
           "new": band(new), "new_last30": band([r for r in new if r["sold"] >= LAST30]),
           "openbox": band(by("openbox")), "refurb": band(by("refurb")),
           "boa_used": sum(r["boa"] for r in used), "ship_charged_used": sum(r["ship"] > 0 for r in used),
           "counts": {c: len(by(c)) for c in ("used", "new", "openbox", "refurb", "excluded")}}
    out["monthly_used_median"] = {m: statistics.median([r["price"] for r in used if r["sold"].strftime("%Y-%m") == m])
                                  for m in sorted({r["sold"].strftime("%Y-%m") for r in used})}
    print(json.dumps(out, indent=1, default=str))
    for c in ("used", "new", "openbox", "refurb"):
        print(f"\n{c.upper()}")
        for r in sorted(by(c), key=lambda r: r["price"]):
            print(r["line"], r["sold"], f"${r['price']:,.2f}", f"+{r['ship']:.2f}", "BOA" if r["boa"] else "", r["title"][:90])
    print("\nEXCLUDED")
    for r in sorted(by("excluded"), key=lambda r: (r["why"], r["sold"])):
        print(r["line"], r["sold"], f"${r['price']:,.2f}", r["cond"], "|", r["why"], "|", r["title"][:90])


for c in (sys.argv[1:] or CARDS):
    print("=" * 30, c)
    main(c)
