# PDF de-index checkpoint — GSC exports of 2026-10-21

Follows `pdf-deindex-checkpoint-2026-10-07.md`, which has the criterion, the 31-PDF list and the
history. Marker: `dated-markers.md`, "PDF de-index checkpoint", due 2026-10-21. Every figure below
comes from the exports in `docs/GSC_cvs/2026-10-21/` (gitignored, like the earlier folders).

**Criterion (approved by Mark 2026-10-07):** landed = no de-indexed PDF left in the Indexed list AND
/pdfs/ impression share under 5% for two consecutive weeks.

**Result: the share half has LANDED. The indexed-list half can't be read yet and is re-dated to
2026-11-04.**

## Inputs

| Export | Folder | Filters.csv | zip sha256 |
|---|---|---|---|
| Performance on Search, unfiltered | `Performance-on-Search-2026-10-21/` | Web, Sep 1 – Oct 21 | `5b0c806c` |
| Performance on Search, PDFs | `Performance-on-Search-2026-10-21_page-pdfs/` | Web, Sep 1 – Oct 21, **Page +/pdfs/** | `f0f44708` |
| Indexing → Pages (overview) | `Coverage-2026-10-21/` | Daily chart to 10-11, plus the reasons for not indexing | `3237d9d7` |
| Performance on Search, Query +.pdf | `Performance-on-Search-2026-10-21_query-pdf/` | Web, Sep 1 – Oct 21, **Query +.pdf** | `500d8080` |

- The zips were loose in `docs/`. All five were moved to `docs/GSC_cvs/2026-10-21/` and unzipped there.
- The Query +.pdf export was downloaded twice (`500d8080` and `b8d30609`). The zip bytes differ, but
  the CSVs inside are identical. **It isn't used here.** That filter matches search queries containing
  ".pdf", not PDF URLs, so it can't measure the PDF share.
- **No indexed-URL export was taken.** GSC's Page indexing report said "Last updated 10/11/26" today,
  and the coverage chart ends on 10-11. An Indexed list pulled today would only repeat the 10-11
  snapshot.

## 1. Weekly /pdfs/ impression share: LANDED

Page +/pdfs/ export against the unfiltered export, same window, from each `Chart.csv`. Weeks start
on Monday.

| Week of | Days | Site impr | /pdfs/ impr | Share | /pdfs/ clicks |
|---|---:|---:|---:|---:|---:|
| 08-31 | 6 (data starts 09-01) | 916 | 206 | 22.5% | 3 |
| 09-07 | 7 | 738 | 123 | 16.7% | 0 |
| 09-14 | 7 | 689 | 79 | 11.5% | 0 |
| 09-21 | 7 | 23,275 | 2,789 | 12.0% | 8 |
| 09-28 | 7 | 52,632 | 2,534 | **4.8%** | 7 |
| 10-05 | 7 | 40,079 | 559 | **1.4%** | 4 |
| 10-12 | 7 | 34,219 | 420 | **1.2%** | 4 |
| 10-19 | 3, partial | 9,682 | 78 | **0.8%** | 3 |

Four consecutive weeks are under 5%, three of them complete, against a requirement of two. Total
/pdfs/ clicks in the window: **29**. `Pages.csv` has 94 PDF URLs, and they add up to 6,788 impressions,
the same as the chart total.

**Read this with the confound below.** The share fell on both sides of the fraction:

- **The denominator grew about 60×.** Site impressions ran at ~100/day through 09-24. They were 1,140
  on 09-25 and 11,239 on 09-26, and have held at roughly 5,000–10,000/day since.
- **The numerator fell by itself.** /pdfs/ impressions rose with the site in the weeks of 09-21 and
  09-28 (2,789 and 2,534), then dropped to 559 and 420, about 80% below that peak, while site
  impressions fell only ~35%. So the PDFs are leaving the index. The share isn't just being diluted.
- In absolute terms, PDF impressions (420/week) are still higher than in early September (79–206/week).
  That's because the whole site has far more impressions now.

## 2. Google impressions jumped ~60× from 2026-09-25 (recorded in open-threads and the timeline 2026-10-21)

The open-threads "Google organic collapse — watching, deliberately not chasing" item was last
re-confirmed with a baseline of about 500–1,500 impressions/week. Site impressions are now
**34,000–53,000/week** (unfiltered export). The step is sharp: 92 on 09-24, 1,140 on 09-25, 11,239 on
09-26 (dates from the Performance export; the Coverage chart's impressions column runs one day early). Site clicks went from single digits a week to **275–357/week**. The top pages are ordinary
`/guides/` HTML pages, for example `cpu-only-llms-what-actually-works` (63 clicks, 2,354 impressions)
and `qwen-models-guide` (8,114 impressions).

That item's own rule applies: **do not read this as evidence that a content change worked.** Check
the backlink profile first. This checkpoint doesn't investigate the jump. It's recorded here because
it changes how section 1 reads, and because the open-threads baseline is now out of date.

## 3. Coverage overview (as of 10-11)

| | 10-07 read (data to 10-03) | 10-21 read (data to 10-11) |
|---|---:|---:|
| Excluded by 'noindex', **all URL types** | 206 | **230** |
| …of which de-indexed PDFs | 183 | not pulled (no drilldown) |
| Indexed (chart) | 839 | 839 |
| Crawled – currently not indexed | 165 | 175 |

- The noindex count grew by 24 across all URL types: 856 → 875 (10-04) → 891 (10-09) not-indexed.
  No drilldown was pulled, so how many of the 24 are PDFs is unknown. The earlier note "230 vs 183"
  compared an all-types count with a PDF-only count. The like-for-like comparison is 230 vs 206.
- Other reasons: Page with redirect 469, Not found (404) 12, Alternate page with proper canonical 4,
  Duplicate / Google chose different canonical 1.

## 4. Indexed-list half: re-dated to 2026-11-04

Still open: how many of the 31 de-indexed PDFs that were in the Indexed list on 10-07 are still
there. (These are the 29 in section 5 of the 10-07 doc, plus `newsletter-2026-05-03.pdf` and
`mycoswarm-wifi-laptop-borrowed-gpu.pdf`.)

**At 2026-11-04:**
1. Check that the Page indexing report's "Last update" is **after 2026-10-21**. If it isn't, the
   export would repeat a stale snapshot, so re-date again rather than read it.
2. Export the indexed URL list: Indexing → Pages → "View data about indexed pages" → export.
3. Count how many of the 31 are still listed. **Zero → resolve the marker** (the share half has
   already landed). More than zero → list them with last-crawled dates. As on 10-07, a PDF with a
   last-crawled date before 07-20 hasn't been recrawled since the header shipped, so it isn't a
   failure of the mechanism.
4. Optional: the Excluded by 'noindex' drilldown, to bring the PDF-only excluded count up to date
   (183 on 10-07).

`llamacpp-vs-ollama-vs-vllm.pdf` is still a hub-experiment control. No request action on it before
2026-12-15. Requests are impossible anyway, because GSC refuses URLs that serve noindex.

## Reproduction

From `docs/GSC_cvs/2026-10-21/` (local only): bucket the daily `Chart.csv` rows of `_page-pdfs` and of
the unfiltered export into Monday-start weeks from 2026-08-31, and divide the impressions. The
coverage figures come from `Coverage-2026-10-21/Chart.csv` and `Critical issues.csv`.
