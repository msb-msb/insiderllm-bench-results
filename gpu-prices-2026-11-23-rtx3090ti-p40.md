# GPU used prices, RTX 3090 Ti and Tesla P40: eBay US sold listings, 2026-11-23

Mark saved two eBay sold-listings pages on 2026-11-23 (the files are named 11-22; both pages carry sales dated 11-23
for the Ti):

| Card | Raw file | sha256 after redaction | sha256 as saved |
|---|---|---|---|
| RTX 3090 Ti | `raw/ebay-rtx3090ti-sold-2026-11-22.txt` | `f1e94355…72b87b1` | `8645749f…cf80b48f` |
| Tesla P40 | `raw/ebay-teslap40-sold-2026-11-22.txt` | `4c39739a…0f762b8` | `57069a82…5d69e5e5` |

This is a price record, not a benchmark. **Applied:** store `mycoSwarm/data/gpu-reference.json` **1.15.0**
(`used_price_updated` 2026-11-23), copied to `insiderllm-hugo/data/gpus.json` (invariant (ad)).

## Method

The method follows `gpu-prices-2026-11-06-rtx3090.md`. Where it differs, the table says so.

| | |
|---|---|
| Source | eBay US, sold listings, Sold Items + Completed Items, Used, US Only, Graphics/Video Cards. Every listing on both pages is "Pre-Owned" and "Located in United States" |
| Search | 3090 Ti: `rtx 3090 ti` ("2,500+ results", 240 on the page). P40: `tesla p40 -m40` ("111 results", all 111 on the page, so the page is the complete result set) |
| Card filter | **By title**, as on 11-06. Ti: the title must say "3090 Ti" or "3090TI". eBay's seller-entered model field says plain "RTX 3090" on 13 of the 17 Ti titles, so it isn't used. P40: the title must name a P40; M40/P4/P100 titles are excluded (there were none) |
| Window | The run of days the page covers completely, the 11-06 rule (there: 10-25..11-06). Ti: **2026-11-15..11-23** (9 days; the page is dense from 11-15, with stragglers before). P40: **2026-08-25..11-22**, eBay's 90-day sold history, which this page holds entirely (P40s sell about once a day). The 2026-09-02 P40 pull also used a ~3-month window |
| Basis | **Sold price excluding shipping.** Ti: 12 of 16 charged shipping. P40: 66 of 106. Every listing has a delivery line |
| Best offer | Kept at the struck-through **list** price eBay shows, as on 11-06, with a without-them sensitivity. Ti: 1 of 16. P40: 21 of 106 |
| Statistic | p25 / median / p75, `statistics.quantiles(method='inclusive')`, **rounded to $5** (half up), as on 11-06 |

Parsing was checked against the 11-06 page: the same parser finds its 240 sold blocks and its 36 "Best offer accepted"
lines (the 11-06 record counts 37 because one of them also shows "1 bid").

## RTX 3090 Ti

The query returns mostly other cards: of 240 sales, 193 are vanilla 3090s (by title), 14 are 4090s, and the rest are
Quadros, K80s, NVLink bridges and the like. **17 carry "3090 Ti" in the title.**

**Excluded (1 of 17):** line 2406, sold 11-12, $1,999.00, EVGA RTX 3090 Ti FTW3 Black: sold outside the window.

No Ti listing was a lot, a parts or non-working card, or an accessory. No title for another card turned out to be a
mislabelled Ti.

**Kept on purpose:**
- line 2474, $1,599.99, ASUS ROG Strix 3090 Ti OC "with Alphacool Waterblock": a working card with a block fitted (11-06
  kept these too);
- line 252, $1,675.00, "READ DESCRIPTION: EVGA … 3090 Ti FTW3": the title marks no fault (11-06 kept defect-noted
  working cards);
- line 2538, $1,700.00, "EVGA GeForce RTX 3090 Ti FTW3 Triple Fan Heatsink GPU w/ LED Lighting": the whole card at
  that price, not a heatsink.

| Window | n | p25 | median | p75 |
|---|---:|---:|---:|---:|
| **11-15..11-23 (band, rounded to $5)** | **16** | **$1,675** | **$1,725** | **$1,800** |
| unrounded | 16 | $1,675.00 | $1,725.00 | $1,799.99 |
| `exclusive` rule | 16 | $1,675.00 | $1,725.00 | $1,799.99 |
| Shipping included (reference) | 16 | $1,692 | $1,747 | $1,800 |
| Without the best-offer sale (line 1549, $1,900) | 15 | $1,675 | $1,700 | $1,775 |

Range $1,550-1,999. Sales 11-16..11-23 (none of the window's first day is a Ti).

**Small sample.** A bootstrap (20,000 resamples) puts the median's 95% interval at **$1,675-1,800**. The band is
usable but loose; a second pull would tighten it.

**Against the 3090.** The store's vanilla 3090 band is $1,500 / $1,580 / $1,625 (2026-11-06). The Ti's whole
interquartile range sits above it: **+$145 at the median**. The 2026-09-02 pull measured both cards on one day and put
the Ti $100 above the 3090 ($1,400 against $1,300), so the Ti has always carried a premium in our data.

**Against 2026-09-02** ($1,300 / $1,400 / $1,499, n=41, Buy It Now only): median **+$325 (+23%)**. Not like-for-like:
09-02 was Buy It Now only and pooled open-box with used; this pull includes auctions (5 of 16 sales) and is the Used
filter only.

**The 3090 may have moved since 11-06.** The same page's 193 vanilla-3090 sales in 11-15..11-23 have a median of
$1,649. They were filtered by title only, not screened to the 11-06 method (no defect, window or lot review), so this
is an indicator, not a band, and it's **not applied**. If it holds, the Ti premium over a same-week 3090 is closer to
$75.

## Tesla P40

**Excluded (5 of 111):**

| Line | Sold | Price | Title (shortened) | Reason |
|---:|---|---:|---|---|
| 430 | 04-09 | $294.00 | NVIDIA Tesla P40 24GB GDDR5 … | sold outside the window |
| 453 | 04-23 | $249.99 | Nvidia Tesla P40 24GB GDDR5 699-2G610-0200-100 | sold outside the window |
| 1069 | 09-13 | $500.00 | LOT of 2 NVIDIA Tesla P40 … | multi-card lot (2) |
| 524 | 11-01 | $649.00 | 2x Tesla P40 24GB GPU Pair Cooled … | multi-card lot (2) |
| 286 | 11-10 | $299.00 | NVIDIA 699-1G610-0300-100 TESLA P41 (P40) 24GB | not a P40 (P41, a different board) |

**Kept on purpose:**
- **Seller model field wrong:** 13 P40 titles carry the model "Tesla P4" and one (line 999) "RTX 2080 Ti". Title rules,
  as on 11-06.
- **Sold with cooling (12):** fan, shroud, blower or Noctua fitted, sometimes with a power adapter. These are complete
  cards. Mark's "blowers or brackets only" exclusion is for accessory-only listings; there were none. Two bracket
  mentions ("with Bracket", lines 857 and 1208) are cards.
- **Low and high tails:** nine sales under $230 (lowest $200, lines 877 and 949) and four over $350 (highest $459, line
  406). No title marks them as junk or new.

| Window | n | p25 | median | p75 |
|---|---:|---:|---:|---:|
| **90 days, 08-25..11-22 (band, rounded to $5)** | **106** | **$250** | **$285** | **$320** |
| unrounded | 106 | $252.25 | $282.50 | $320.00 |
| Shipping included (reference) | 106 | $264 | $294 | $330 |
| Without best-offer-accepted sales | 85 | $250 | $280 | $320 |
| Last 30 days, 10-24..11-22 | 36 | $285 | $330 | $350 |

Range $200-459. Bootstrap 95% interval for the 90-day median: $275-299.

**The price is rising.** Monthly medians: **$270** (08-25..09-30, n=42), **$287** (October, n=35), **$330**
(11-01..11-22, n=29). The 90-day band is the method's window and matches the 09-02 pull, but it trails today's price:
a page quoting $330-350 for a P40 now is current, not wrong. If the store should track the current month instead, the
last-30-day band is $285 / $330 / $350 (n=36).

**The cooling split is retired.** The 09-02 entry found two price modes, bare cards ($230 median) and cards sold with a
fan or shroud ($288), and encoded both in the band (low = bare p25, mid = bare median, high = cooled median). They have
converged:

| | n | p25 | median | p75 |
|---|---:|---:|---:|---:|
| Bare, 90 days | 94 | $250 | $277 | $320 |
| Cooled, 90 days | 12 | $275 | $288 | $330 |
| Bare, last 30 days | 33 | $285 | $329 | $349 |
| Cooled, last 30 days | 3 | $305 | $330 | $340 |

A $10 gap at the 90-day median and none in the last month, so the store carries one plain band. The advice stands
that a bare P40 needs a fan or shroud in a desktop; it's now a cost on top, not a price mode.

**Against 2026-09-02** ($220 / $230 / $288): not like-for-like (split band, Buy It Now only, 06-09..09-02). Against its
bare median of $230, the 90-day median is +$53 and November's is +$100.

## Caveats

- **Exclusion is by title**, as on 11-06. A Ti listed without "Ti" in its title is missed, so the Ti sample
  under-counts, not over-counts.
- **The raw files are eBay page chrome plus results.** In each, line 7 (the account greeting) and the delivery-ZIP line
  (Ti line 51, P40 line 45) are replaced with `[redacted page chrome]`. Line numbers are unchanged, so the references
  above hold. Neither file now matches the mirror's `PII_GATE`.
- **Best offer:** the list price, not the accepted price, as before. It matters little here: the without-them bands
  move the medians by $25 (Ti) and $5 (P40).
