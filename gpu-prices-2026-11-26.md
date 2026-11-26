# GPU used prices, six cards: eBay US sold listings, 2026-11-26

Mark saved six eBay sold-listings pages on 2026-11-26 (`raw/ebay-*-sold-2026-11-26.txt`). In each file, line 7 (the
account greeting) and the "Shipping to <ZIP>" line (43–46) are replaced with `[redacted page chrome]`, so line numbers
are unchanged. This is a price record, not a benchmark. The parser is `gpu-prices-2026-11-26.py`, and its full output
(every kept and excluded block, with the reason) is `gpu-prices-2026-11-26-parse.txt`.

| File | sha256 as saved | sha256 after redaction | Sold blocks | Page |
|---|---|---|---:|---|
| `ebay-r9700-sold-2026-11-26.txt` | `44cf72d5…4c748ad0` | `cc7ba5bb…f46551c6` | 55 | complete ("47 results", plus eBay's own extras) |
| `ebay-teslap100-16gb-sold-2026-11-26.txt` | `be98a19b…4e224a34` | `4c02e68c…48977cb3` | 62 | complete ("62 results") |
| `ebay-rtx5090-sold-2026-11-26.txt` | `70886f23…312c037c` | `5b769941…489c1227` | 240 | capped ("1,100+ results") |
| `ebay-rtx3060-sold-2026-11-26.txt` | `636160e6…4d283dba` | `017859f3…af41bb44` | 240 | capped ("2,400+ results") |
| `ebay-rx7800xt-sold-2026-11-26.txt` | `6016f33e…ab1f0ba1` | `c4f777d5…00d43ca2` | 240 | capped ("272 results") |
| `ebay-rtx5060ti-16gb-sold-2026-11-26.txt` | `eb1a4bc9…01cf7ced` | `03900ba3…27b771da` | 240 | capped ("433 results") |

## Method

As in `gpu-prices-2026-11-24-teslav100.md` (and the 11-06 and 11-23 records before it). The differences are in this
table.

| | |
|---|---|
| Source | eBay US, sold listings: Sold Items + Completed Items, US Only, Graphics/Video Cards. Queries as on each page: `R9700 32GB -ryzen -9700x`, `Tesla P100 16GB PCIe -SXM2 -12GB`, `RTX 5090 -laptop -5090D -box -waterblock`, `RTX 3060 12GB -Ti -laptop -8GB`, `RX 7800 XT 16GB -7800X3D`, `RTX 5060 Ti 16GB -8GB -laptop` |
| Card filter | **By title.** Kept titles name the card and are located in the United States. Excluded: parts (condition "Parts Only", or a title saying for parts / not working / no core / broken / as-is / artifacts / damaged), accessories (brackets, connectors, thermal pads, water blocks sold alone, boxes), whole systems and laptops (a CPU, SSD/NVMe/DDR, screen size, refresh rate or laptop model in the title), external GPU boxes (XG Mobile, AORUS AI Box), multi-card lots and bundles, and the wrong card or variant (3060 Ti / 8 GB, 5060 Ti 8 GB, 5090D, R9700S, P100 SXM2 / 12 GB). OEM cards (Dell, HP, Lenovo "from Legion") and cards sold *with* a cable or water block are kept |
| Conditions | **Used = Pre-Owned.** New = Brand New + New (Other). Open Box and refurbished are reported on their own and are in neither band |
| Window | **Complete pages (R9700, P100):** every sale, which is eBay's 90-day history. **Capped 240-listing pages:** the run of days the page covers continuously, from the newest sale back to the first gap of more than 3 days with no sale. Older stragglers are excluded and listed. The 3060 and 5090 pages cover 10 and 20 days, so for those two the "last 30 days" band is the same as the window band |
| Basis | **Sold price excluding shipping.** A "$sale$was" pair uses the first (sold) price. Multi-variation listings shown as a price range are excluded (the one on the 5060 Ti page, line 316, is a whole PC and falls out as "other card" first) |
| Best offer | "Best offer accepted" sales are kept at the price shown, with a without-them sensitivity row |
| Statistic | p25 / median / p75, `statistics.quantiles(method='inclusive')`, **rounded to $5** (half up) |

## Result (used, rounded $5)

| Card | Window | n | p25 (low) | median | p75 (high) | range | Last 30 days (10-27..11-26) |
|---|---|---:|---:|---:|---:|---|---|
| **Radeon AI PRO R9700 32GB** | 08-31..11-26 (90-day history) | 26 | **$1,765** | **$2,000** | **$2,135** | $1,400–2,381 | n=12: $2,000 / $2,125 / $2,265 |
| **Tesla P100 16GB PCIe** | 09-02..11-25 (90-day history) | 52 | **$100** | **$140** | **$195** | $78–279 | n=29: $145 / $180 / $200 |
| **RTX 5090 32GB** | 11-06..11-25 (20 days) | 111 | **$5,660** | **$6,000** | **$6,200** | $700–7,500 | same as window |
| **RTX 3060 12GB** | 11-17..11-26 (10 days) | 209 | **$310** | **$330** | **$350** | $90–500 | same as window |
| **RX 7800 XT 16GB** | 09-06..11-25 (81 days) | 218 | **$485** | **$525** | **$560** | $390–800 | n=82: $520 / $575 / $600 |
| **RTX 5060 Ti 16GB** | 10-05..11-25 (52 days) | 181 | **$650** | **$700** | **$740** | $450–850 | n=110: $680 / $700 / $750 |

Sensitivities (rounded $5):

| Card | Shipping included | Without best-offer-accepted sales | Monthly used medians |
|---|---|---|---|
| R9700 | $1,770 / $2,005 / $2,145 | n=19: $1,715 / $1,950 / $2,175 | Sep $1,712.50 (n=4), Oct $1,800, Nov $2,124.50 |
| P100 | $105 / $145 / $200 | n=43: $100 / $145 / $200 | Sep $80, Oct $135, Nov $193 |
| 5090 | $5,695 / $6,020 / $6,205 | n=84: $5,275 / $6,000 / $6,115 | (window inside November) |
| 3060 | $320 / $340 / $360 | n=190: $310 / $330 / $350 | (window inside November) |
| 7800 XT | $495 / $530 / $575 | n=186: $485 / $525 / $560 | Sep $500, Oct $520, Nov $585 |
| 5060 Ti | $665 / $705 / $740 | n=150: $650 / $695 / $730 | Oct $677.50, Nov $710 |

**New and other conditions:**
- **R9700, new (Brand New + New (Other)), n=13:** $1,750 / $2,200 / $2,300 ($1,050–2,500). Last 30 days n=6: $2,200
  / $2,250 / $2,335. **Open Box, n=8:** $1,800 / $1,925 / $2,045. The early new sales ($1,050 on 09-03, best offer;
  $1,300 on 09-04; $1,500 on 09-17) sit near the $1,299 launch price. Every new sale since 10-21 was at $2,090 or more.
- **5060 Ti, new: none.** The saved page holds no new-condition sale (only 1 factory-refurbished card, $749.99 on
  10-26), so **no new band can be given** from this file. It would need a separate pull with the New filter.
- P100: one new sale ($449, 10-23) and 3 refurbished ($125–170), in neither band.

## Against the store (1.17.0)

| Card | Store before | Now (used) | Change |
|---|---|---|---|
| R9700 | none | $1,765 / $2,000 / $2,135 | new entry |
| P100 16GB PCIe | none (page `used-server-gpus-local-ai` says "~$200-350") | $100 / $140 / $195; last 30 days $145 / $180 / $200 | new entry; the page figure is high |
| RTX 5090 | $5,899 / $6,000 / $6,355 (10-15, n=119, verified) | $5,660 / $6,000 / $6,200 | median unchanged, band wider at the low end |
| RTX 3060 12GB | $275 / $300 / $325 (09-25, verified) | $310 / $330 / $350 | up $30 at the median (+10%) |
| RX 7800 XT | $465 / $500 / $535 (09-25, verified) | $485 / $525 / $560; last 30 days $520 / $575 / $600 | up $25 over the window, rising: November median $585 |
| RTX 5060 Ti 16GB | $475 / $600 / $720 (05-19, researched) | $650 / $700 / $740 | up $100 at the median; first firsthand pull |

## Exclusions (counts; every row is in the parse output)

| Card | Excluded | By reason |
|---|---:|---|
| R9700 | 8 | outside the US 8 (Canada 4, China 2, Germany 1, Austria 1). No R9700S title appeared |
| P100 | 6 | multi-card lots 5 (three lots of 4 and two pairs, $259–350), parts 1 ($6,000 "Parts Only") |
| 5090 | 129 | parts 73, systems and laptops 43 (laptop "RTX 5090" is a 24 GB mobile chip), accessories 5, external GPU boxes 2, lot 1 (5 cards), other card 2, stragglers 3 (05-14 $11,428.54; 10-12; 11-01) |
| 3060 | 31 | parts 17, systems 8, box only 1, stragglers 5 (one at $2,369.99) |
| 7800 XT | 22 | parts 17, systems 4, straggler 1 |
| 5060 Ti | 58 | systems 31, AORUS AI Box eGPU 10, parts 11, lot 1, box only 1, other 1 (a PC with a price range), stragglers 3; plus 1 refurbished |

**Kept on purpose:**
- **5090, line 2251, $699.54**, "MSI Vanguard GeForce RTX 5090 32GB GDDR7 Graphics Card - Excellent", Pre-Owned. This
  is far below any other card (next $2,000), but no title word marks it as faulty. It's kept, as low 1-bid sales were
  on 11-06/11-23. It can't move the quartiles. Also kept: line 826 $2,000 (PNY) and line 236 $2,500 (Gigabyte),
  line 1105 $2,750 "Non tested … See details" (Pre-Owned, not marked for parts), and line 1303 $3,999 "… Triple Fan
  SHROUD" (priced as a whole card).
- **5090 OEM cards** (HP OMEN V530 / "HP OEM", Dell THGGW, $5,499–6,050) are desktop cards, so they're kept.
- **P100, line 526, $93**, "… Heatsink Only": read as the card with its passive heatsink and no fan, so kept by hand.
  Line 749, $79.97, carries "$71.97/ea (4)", a multi-quantity listing sold as one card, so it's kept.
- **3060, line 422, $89.79**, "used. in good cond.": a low auction, kept. Cards "From Lenovo Legion" and HP/Dell OEM
  3060s are kept as cards.
- **3060 / 5060 Ti titles that call VRAM "RAM"** ("16GB RAM Graphics Card") are kept as cards. A title that adds
  system RAM ("PLUS 16Gb DDR5 Ram", "and 16 gbs of DDR4") is a bundle, so it's excluded.

## Notes

- **P100 nearly doubled in 90 days:** monthly medians were $80 → $135 → $193. The 90-day band trails today's price;
  the last-30-day band ($145–200, median $180) is the current one.
- **R9700 used is above its $1,299 launch price** and rising: September $1,712.50, November $2,124.50. Used and new
  now overlap (used median $2,000, new median $2,200).
- The 5090 page is mostly parts and laptops (116 of 240 blocks). Its 111 desktop cards fill only 20 days.
