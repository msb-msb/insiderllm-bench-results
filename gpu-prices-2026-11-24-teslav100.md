# GPU used prices, Tesla V100 16GB (PCIe): eBay US sold listings, 2026-11-24

Mark saved the eBay sold-listings page on 2026-11-24: `raw/ebay-teslav100-16gb-sold-2026-11-24.txt` (sha256
`e0e71e42…ec326edbfc` after redaction; as saved `62da3475…ecef4e3bf1`). Line 7 (account greeting) and line 45 (delivery
ZIP) are replaced with `[redacted page chrome]`; line numbers are unchanged. This is a price record, not a benchmark.
**Not applied:** no store entry and no page change. Mark decides on a store entry and a V100 16GB section for
`used-server-gpus-local-ai`. Parser: `gpu-prices-2026-11-24-teslav100.py` (prints every kept and excluded line).

## Method

As `gpu-prices-2026-11-06-rtx3090.md` and `gpu-prices-2026-11-23-rtx3090ti-p40.md`; differences in the table.

| | |
|---|---|
| Source | eBay US, sold listings: Sold Items + Completed Items, Used, US Only, Graphics/Video Cards, plus the **16 GB** and **PCI** (Compatible Slot) facets |
| Search | `tesla v100 16gb pcie` ("38 results"), then eBay's "Results matching fewer words" section (P100, T4, T10, P40 and more V100s). 132 sold blocks on the page |
| Card filter | **By title**: must name a V100 (one exception below), be located in the US, Pre-Owned, PCIe. PCIe = the title says PCIe/PCI-E, or carries a PCIe board ID (PG500, 699-2G500, 900-2G500, HPE Q2N68A / 876908-001 / 876340-001, FHHL). SXM2 titles (modules, and SXM2 cards converted with a PCIe adapter) are counted separately |
| Window | 2026-08-26..11-24, eBay's 90-day sold history. V100 16GB sales are sparse (about one every two days), so the whole page is used, as for the P40 |
| Basis | **Sold price excluding shipping.** 16 of 42 kept sales charged shipping |
| Best offer | No sale on this page shows "Best offer accepted". 30 of the 42 kept sales show "or Best Offer"; the price shown is used |
| Statistic | p25 / median / p75, `statistics.quantiles(method='inclusive')`, rounded to $5 (half up) |

## Result

| | n | p25 (low) | median | p75 (high) | range |
|---|---:|---:|---:|---:|---|
| **V100 16GB PCIe, 90 days, 08-26..11-24 (rounded $5)** | **42** | **$250** | **$300** | **$335** | $200-459 |
| unrounded | 42 | $252.49 | $298.99 | $337.12 | |
| Shipping included (reference) | 42 | $260 | $300 | $345 | |
| Last 30 days, 10-26..11-24 | 19 | $310 | $340 | $375 | $299-459 |
| eBay's 38 exact results only (no "fewer words" section) | 32 | $245 | $290 | $330 | |
| Without the three "Multi-Monitor" titles (lines 227, 336, 386) | 39 | $255 | $299 | $345 | |
| Without the "Untested" PNY (line 261) | 41 | $250 | $299 | $340 | |

**Rising:** medians by 30-day block: 08-26..09-24 $232.50 (n=4), 09-25..10-24 $264.99 (n=19), 10-25..11-24 **$339.50**
(n=19). The 90-day band understates today's price; the last-30-day band is the current one. Every sale in the last 30
days was at $299 or more.

## SXM2 (counted separately, not in the band)

**9 single US sales, $140-460** (p25 $195, median $260, p75 $325): bare modules at $140 (line 650) and $195 (848, with
heatsink) and $325 (1000); SXM2 cards sold with a PCIe adapter board at $180-460 (808, 241, 251, 306, 491, 533; 533
includes a water block). Plus **one lot**: two SXM2 + adapter kit, $700 (line 543). Not included: China-located
SXM2 adapter boards alone (1409, 1421, 1432) and one China-located SXM2 kit (1477).

## Excluded (V100-related or ambiguous)

| Line | Sold | Price | Title (shortened) | Reason |
|---:|---|---:|---|---|
| 619 | 11-16 | $1,500.00 | 4x NVIDIA TESLA V100 GPU … 16GB HBM2 | multi-card lot (4) |
| 629 | 08-27 | $205.99 | Nvidia Tesla V100 16GB Graphics Card - Tested & Working | form factor not stated (no PCIe/SXM2 word or board ID) |
| 1031 | 10-03 | $219.99 | Nvidia CMP 100-210 16GB Mining GPU | not a Tesla V100 (V100-based mining card; the seller's model field says "Tesla V100") |
| 1443, 1453, 1464, 1488, 1499, 1510, 1521 | 09-29..11-19 | $299-460 | V100 16GB PCIe (and one "PCIe … SXM2 Driver") | located in China |

No 32 GB, no parts-only and no other lots among V100 16GB PCIe titles. Of the 80 excluded blocks, 66 are other cards by
title (P100 44, T4 18, T10 3, P40 2 — the P100 count includes 2 lots), 11 are China-located (7 V100 cards, 4 SXM2
adapter boards or kits), plus the three rows above.

**Kept on purpose:**
- line 670, $230, "NVIDIA Tesla 16GB HBM2 PCIe x16 GPU + 12" NVidia Volta …": the title omits "V100", but a Tesla with
  16 GB HBM2 on PCIe and Volta is only the V100 PCIe;
- lines 899 and 1246, $394.99, "V100 FHHL 16GB HPE Q8Z50A": the full-height half-length PCIe V100 (150 W variant), a
  PCIe card;
- lines 227, 336, 386 ("PCIe x16 GPU … Multi-Monitor (Heatsink)", $200-269): the same wording as SXM2 conversion line
  491 ("SXM 2 Converted PCIe x16 GPU Card, CUDA, Multi-Monitor"), and a V100 has no display outputs, so these may be
  conversions. The titles say PCIe and nothing else, so they're kept, with a sensitivity row;
- line 261, $260, PNY "Untested": sold Pre-Owned, not for parts.

## Against the page

`used-server-gpus-local-ai` quotes only the **32 GB** V100 at "~$300-500". The 16 GB PCIe card sells at **$250-335
over 90 days, $310-375 in the last 30 days (median $340)**. A converted SXM2 16 GB with an adapter sells for about
$180-460, but needs the adapter, cooling, and (for most kits) more case room.
