# GPU used prices, NVIDIA CMP 170HX (8 GB): eBay US sold listings, 2026-11-16

This is a price record, not a benchmark. It seeds a new tracked card, `cmp-170hx-8gb`, in the store
(`mycoSwarm/data/gpu-reference.json` 1.14.0, mirrored to `insiderllm-hugo/data/gpus.json`). **Data only:**
no content page quotes this card.

## Which card

| | |
|---|---|
| Tracked | CMP 170HX, **8 GB SK Hynix HBM2e** version. Reported to unlock to **64 GB** (as reported to us; InsiderLLM hasn't measured it) |
| Excluded | CMP 170HX, **10 GB Samsung HBM2e** version. A different card: it unlocks to about **40 GB** stable. Its sales are left out of every figure below |

## Method

| | |
|---|---|
| Source | eBay US, sold listings, pulled by Mark on 2026-11-16 |
| Condition | Used |
| Excluded | Parts-only listings, multi-card lots, and the 10 GB Samsung version |
| Statistic | **Median only** for each window, with n. No quartiles were taken |
| Basis | Shipping treatment was not recorded with the pull. The 2026-10-15 and 11-06 records used sold price excluding shipping; this one can't say which it used |
| Raw page | Not saved to the repo. The figures below are Mark's summary of the pull |

**Caveat: best offer.** For "Best offer accepted" sales, eBay shows the struck-through **asking** price, not
the accepted one. Any such sale in these windows counts at its asking price, so a median that includes them
can run high. The pull didn't record how many there were.

## Medians

| Window | Days | n | Median |
|---|---:|---:|---:|
| September 2026 | 30 | 14 | $2,360 |
| October 2026 | 31 | 43 | $2,709 |
| 2026-11-01..11-08 | 8 | 10 | $3,118 |
| **2026-11-09..11-16** | **8** | **47** | **$4,000** |

The median has climbed 69% since September. The two November windows are 8 days each, and the first has
only 10 sales.

## How it's stored

- `used_price_usd` = `{low: null, mid: 4000, high: null}`, status **`unverified`**. The store's rule is that
  a price with no band is `unverified`, even when the data is firsthand. The same goes for `rtx-5070-ti-16gb`
  and `rtx-5080-16gb`. It becomes `verified` once a pull records quartiles.
- All four windows are in `used_price_history`.
- Specs (chip, bandwidth, compute, power) are **null**. TechPowerUp, the store's spec source, refused our
  fetch on 2026-11-16, and they aren't filled in from memory.

## Watch

`price_watch` on the card: **buy below $2,000** on a 14-day median. $2,000 / 64 GB is about **$31/GB**,
roughly half a used RTX 3090's price per GB ($1,580 / 24 GB ≈ $66/GB, store 1.13.0). That's the signal to
consider buying one to measure. The morning brief checks it against the latest `used_price_history` entry
and says when that window isn't 14 days. Today: $4,000 on an 8-day window, so no signal.
