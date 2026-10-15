# GPU used prices, RTX 5090, RTX 4090 and RTX 3090: eBay US sold listings, 2026-10-15

Pulled by Mark on 2026-10-15. This is a price record, not a benchmark. It feeds `mycoSwarm/data/gpu-reference.json`
(store 1.12.0) and its site mirror `insiderllm-hugo/data/gpus.json`.

## Method

| | |
|---|---|
| Source | eBay US, **sold + completed** listings |
| Search | `_nkw=rtx+5090` and `_nkw=rtx+3090`; `_sacat=27386` (graphics cards); `LH_Sold=1`; `LH_Complete=1`; `LH_ItemCondition=3000` (used); `LH_PrefLoc=1` (US only); `_sop=13` (recently ended first) |
| Excluded | Ti cards, Quadro and other cards, parts, box-only, waterblocks, whole PCs, adapters, eGPU units |
| Basis | **Sold price excluding shipping.** About 70% of sales charged shipping (median $21 on the 3090, $29 on the 5090). Shipping-included quartiles are given below for reference |
| Statistic | Quartiles of sold prices: p25 / median / p75. The store band is low = p25, mid = median, high = p75, **not rounded** |

## RTX 5090

| Window | n | p25 | median | p75 |
|---|---:|---:|---:|---:|
| **14 days, 2026-10-01..10-15 (store band)** | **119** | **$5,899** | **$6,000** | **$6,355** |
| 30 days, 2026-09-17..10-15 | 215 | $5,555 | $5,950 | $6,200 |
| 14 days, shipping included (reference) | 119 | $5,900 | $6,051 | $6,406 |

**Weekly medians**

| Week starting | Median |
|---|---:|
| 09-14 | $5,400 |
| 09-21 | $5,725 |
| 09-28 | $5,929 |
| 10-05 | $6,000 |
| 10-12 (partial week) | $6,399 |

The price is still rising week on week.

**Best offer:** 45 of the 215 sales in the 30-day window were best-offer-accepted. On those, eBay shows the list price, not the price actually accepted. Excluding them, the 30-day median is $5,899 instead of $5,950. So the band leans slightly high, by roughly $50 at the median.

**Previous band:** $3,900 / $4,220 / $4,400 (2026-08-18, used subset, n=61). The median is up 42% in two months.

**Context, reported and not measured:**
- Nvidia has not confirmed or denied the reported RTX 5090 production halt (Tom's Hardware, 2026-10-10).
- Micro Center lists the card as "Not Carried" (Tom's Hardware, 2026-10-15).

## RTX 3090

| Window | n | p25 | median | p75 |
|---|---:|---:|---:|---:|
| 7 days, 2026-10-08..10-15 | 161 | $1,397 | $1,499 | $1,552 |
| 7 days, shipping included (reference) | 161 | $1,407 | $1,500 | $1,579 |

**Previous band:** $1,200 / $1,300 / $1,400 (2026-08-19). That band pooled used cards with eBay Refurbished (n=68). This pull uses eBay's **used** condition filter only, so refurbished units are out. That method change is part of the difference, and its size isn't measured. The 08-19 used-only subset was $1,200 / $1,275 / $1,300, and the median is up $224 against that.

## RTX 4090

**Search:** `rtx 4090` -3090 -3080 -4080 -5090 -4070, used, US location, sold + completed.

**Excluded:**
- parts and box-only listings;
- coolers and heatsinks;
- 48 GB modded cards and the 4090D;
- eGPU, XG Mobile and docks;
- pairs.

| Window | n | p25 | median | p75 |
|---|---:|---:|---:|---:|
| **14 days, 2026-10-02..10-15 (store band)** | **81** | **$2,900** | **$3,000** | **$3,100** |
| 30 days, 2026-09-15..10-15 | 200 | $2,800 | $2,999 | $3,099 |
| 14 days, shipping included (reference) | 81 | $2,905 | $3,016 | $3,123 |

**Weekly medians**

| Week starting | Median |
|---|---:|
| 09-14 | $2,879 |
| 09-21 | $2,950 |
| 09-28 | $3,000 |
| 10-05 | $2,999 |
| 10-12 | $3,025 |

The price is flat to slightly rising. The 4090/3090 median ratio is 3,000 / 1,499 = **2.0x**.

**Previous band:** $2,575 / $2,860 / $3,010 (2026-10-02, n=216). That pull was **delivered price**, i.e. item plus shipping. The like-for-like comparison is the shipping-included median, $3,016 against $2,860: up $156.

## Caveats

- **The cards use different windows** (14 days for the 5090 and 4090 bands, 7 days for the 3090), so they aren't directly comparable across cards.
- **Excluding shipping, unlike earlier pulls.** The store bands from this pull (3090, 5090, 4090) are sold price excluding shipping. The superseded 4090 band (10-02) was delivered price. Compare across bases with the shipping-included rows above.
- **Five other cards are still on delivered-price basis:** rtx-3060-12gb and rx-7800-xt-16gb (2026-09-25), and rtx-3060-ti-8gb, rtx-4060-ti-16gb and rtx-4070-ti-super-16gb (2026-10-02). Each is converted to sold price excluding shipping at its next refresh. Until then the store mixes the two bases, so a cross-card comparison against those five reads them about one shipping charge high.
- **Not rounded.** The 09-25 and 10-02 store convention rounded the IQR to $5; these values are entered exactly as the quartiles came out. In site prose they appear as $1,400–1,550 (3090) and $5,900–6,350 (5090).
- **Exclusions are by title.** Excluding by title catches sellers who name the card correctly. A mislabelled Ti or another model could still be in the sample, and so could a genuine card whose title trips an exclusion.

## Files changed

- `mycoSwarm/data/gpu-reference.json`:
  - `rtx-5090-32gb`, `rtx-3090-24gb` and `rtx-4090-24gb`: `used_price_usd`, `used_price_updated`, `used_price_source` (now "excl. shipping"), `used_price_note`, `ai_notes`;
  - `_meta` version 1.10.0 → 1.12.0 and two dated notes;
  - mirrored to `insiderllm-hugo/data/gpus.json`.
