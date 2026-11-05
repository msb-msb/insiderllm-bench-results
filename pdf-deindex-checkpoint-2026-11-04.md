# PDF de-index checkpoint — GSC exports of 2026-11-04

Follows `pdf-deindex-checkpoint-2026-10-21.md`. The criterion, the 31-PDF list and the history are
in `pdf-deindex-checkpoint-2026-10-07.md`. Marker: `dated-markers.md`, "PDF de-index checkpoint",
due 2026-11-04. Every figure below comes from the export in `docs/GSC_cvs/2026-11-04/` (gitignored,
like the earlier folders).

**Criterion (approved by Mark 2026-10-07):** landed = no de-indexed PDF left in the Indexed list AND
/pdfs/ impression share under 5% for two consecutive weeks. The share half landed on 10-21.

**Result: NOT RESOLVED. 4 of the 31 are still in the Indexed list, down from 31. Proposed next read:
2026-11-18.**

## Inputs

| Export | Folder | Contents | zip sha256 |
|---|---|---|---|
| Indexed pages | `Coverage-Valid-2026-11-04/` | 832 URLs, each with its last-crawled date; daily indexed chart to 10-22 | `c07a1d27` |

- The zip was loose in `docs/GSC_cvs/`. It was moved to `docs/GSC_cvs/2026-11-04/` and unzipped there.
- **Staleness check passed.** The Page indexing report said "Last update 10/22/26", which is after
  10-21. The chart's last row is 2026-10-22 (833 indexed). The table has 832 URLs, one short of the
  chart, the same one-URL gap as on 10-07 (838 vs 839).
- **No noindex-excluded drilldown was pulled**, so the PDF-only excluded count (183 on 10-07) is not
  updated here.

## 1. The 31: 27 left the Indexed list, 4 remain

Cross-referenced by URL against the 10-07 `Coverage-Valid` table. All 31 were in that list.

| PDF | Last crawled | Exception removed | Live header 11-04 |
|---|---|---|---|
| running-llms-mac-m-series | 07-03 | (never an exception) | `x-robots-tag: noindex` |
| rtx-3060-vs-3060ti-vs-3070-local-ai | 07-16 | (never an exception) | `x-robots-tag: noindex` |
| mycoswarm-wifi-laptop-borrowed-gpu | 08-02 | 10-07 | `x-robots-tag: noindex` |
| newsletter-2026-05-03 | 09-28 | 10-07 | `x-robots-tag: noindex` |

**None of the four is a failure of the mechanism.** Each one's last-crawled date is the same as on
10-07, and each comes before the header applied to it. The first two were last crawled before the
header shipped on 07-20. The two former exceptions were last crawled before their exceptions were
removed on 10-07. Google hasn't fetched any of them since it could have seen `noindex`.

The other 27 are gone, including the top four by impressions (best-anime-stylized-checkpoints…,
comfyui-vs-automatic1111-vs-fooocus, open-webui-setup-guide, wsl2-local-ai-windows-guide).
`running-llms-mac-m-series` (628 impressions, Jun 1 – Oct 6) is now the largest left.

## 2. PDFs in the Indexed list: 33 → 6

| | 10-07 (data to 10-03) | 11-04 (data to 10-22) |
|---|---:|---:|
| Indexed URLs, all types (chart) | 839 | 833 |
| /pdfs/ URLs in the Indexed table | 33 | **6** |
| …of the 31 de-indexed | 31 | **4** |
| …the 2 remaining exceptions | 2 | 2 |

The two exceptions are still listed and still serve no header, as intended:
`ai-market-panic-capability-dissipation-gap.pdf` (crawled 10-12) and
`h-neurons-why-llms-hallucinate.pdf` (crawled 09-05). They don't count against the criterion.

## 3. Hub-experiment note: the control's PDF left on its own

`llamacpp-vs-ollama-vs-vllm.pdf` is one of the 27 that left. It was held out of the request list
because its HTML page is a control in the hub experiment. Nothing was requested for it (GSC refuses
noindex URLs anyway), so this was Google's own recrawl, which the 10-07 doc classes as noise rather
than a change we made. It left sometime between 10-03 and 10-22, so it may fall inside the
experiment's pre-window, which opened 10-14. Worth a line in the experiment's notes when its
readout is written; no action before 2026-12-15.

## 4. Next read: proposed 2026-11-18

Why two weeks: the report updated 10-11 and then 10-22, about every 11 days, so a read on 11-18
should see data to early November. A shorter gap risks pulling the same snapshot again.

**At 2026-11-18:**
1. Check that the Page indexing report's "Last update" is **after 2026-10-22**. If it isn't,
   re-date rather than read a repeat snapshot.
2. Export Indexing → Pages → "View data about indexed pages".
3. Look for the four above. **Zero → resolve the marker.** If any remain, give their last-crawled
   dates. A date still at or before the one in section 1 means not recrawled, not a failure.
4. Optional: the Excluded by 'noindex' drilldown, for a fresh PDF-only excluded count.

If a laggard has still not been recrawled after two more reads, the criterion may be waiting on
Googlebot rather than measuring anything. That's the point at which to consider calling it landed
with named laggards. Not proposed now.

## Reproduction

From `docs/GSC_cvs/2026-11-04/` (local only): grep each `https://insiderllm.com/pdfs/<slug>.pdf` of
the 31 in `Coverage-Valid-2026-11-04/Table.csv` and in `../2026-10-07/…Coverage-Valid…/Table.csv`.
Headers: `curl -sI https://insiderllm.com/pdfs/<slug>.pdf`, checked 2026-11-04.
