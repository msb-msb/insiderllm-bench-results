# PDF de-index checkpoint — GSC export of 2026-09-23

Marker: `dated-markers.md` "PDF de-index checkpoint", due 2026-09-17 (re-dated from 08-17, from 08-07).
Every figure below is from the exports in `docs/GSC_cvs/2026-09-23/` (folder kept out of the repo via
`.gitignore`, added today). Nothing here is carried over from notes except where labelled "08-07 marker".

## What was done, and when (stated before analysing)

| | |
|---|---|
| Mechanism | `X-Robots-Tag: noindex` response header on every `/pdfs/*.pdf`, set in `static/.htaccess` via a `RewriteCond`/env-var pair and `Header set … env=PDF_NOINDEX`. A header on a 200, not a redirect; `robots.txt` untouched (it allows everything); no removal requests filed; no per-file `noindex` meta (PDFs cannot carry one). |
| Shipped | 2026-07-20, commit `02707355` "SEO: noindex /pdfs/*.pdf via X-Robots-Tag (5 temp exceptions where PDF is sole indexed copy)". |
| Scope | all `/pdfs/` PDFs except five, excluded because at 07-20 the PDF was the only indexed copy: `ai-market-panic-capability-dissipation-gap`, `newsletter-2026-05-03`, `mycoswarm-wifi-laptop-borrowed-gpu`, `newsletter-2026-07-06`, `h-neurons-why-llms-hallucinate`. `/downloads/` lead magnets deliberately untouched. |
| Verified live | 2026-08-07 (marker) and again 2026-09-23: `agent-skill-compilation-tested.pdf`, `lm-studio-tips-and-tricks.pdf`, `unsloth-studio-setup-guide.pdf` return `200` + `x-robots-tag: noindex`; the excepted `h-neurons-why-llms-hallucinate.pdf` returns `200` with no header. |
| 08-07 baseline (from the 08-07 export, per the marker) | 251 PDFs indexed of 255; PDF impressions 17,550 = 60.5% of site over Jun 22 – Aug 7; the noindex "has not taken effect yet, and that is expected". |
| Today's set | 313 PDFs on disk, so **308 de-indexed** (313 − 5 exceptions). |

## Inputs found

| named in the brief | found | note |
|---|---|---|
| full-site performance, 08-07 → today | `Performance-on-Search-2026-09-23/` | Web, Aug 7 – Sep 23 2026, 48 days; Chart, Pages, Queries, Countries, Devices |
| performance filtered to `.pdf` | `Performance-on-Search-2026-09-23_pdf/` | same window, filter `Page contains .pdf` |
| Indexing → Pages, noindex-excluded | `Coverage-Drilldown-2026-09-23_Excluded/` | Issue "Excluded by 'noindex' tag", all known pages; 181 URLs with last-crawled date; daily affected-page count from 06-29 |
| screenshots | none | |
| also present, not used | two identical `Performance-on-Search-2026-02-26` zips | Jan 28 – Feb 24 2026, "last 28 days" at the time; predate everything here |

Two caveats that apply throughout. GSC lags 2–3 days, so 09-21 to 09-23 are incomplete (the last week has six
days and its final day reads 80 impressions against a 416 spike the day before). And the Pages view and the
Chart view disagree, as they did on 08-07: over the same window Pages.csv sums to 13,403 impressions and
Chart.csv to 6,790, because Pages counts an impression once per URL and Chart once per query. The weekly series
below is Chart-basis; the per-URL lists are Pages-basis; shares are stated with their basis.

## 1. PDF impressions and clicks, week by week since 08-07

Weeks are seven-day bins from 08-07 (a Thursday). Chart basis. "PDF share" is PDF impressions over site
impressions for the same bin.

| week from | days | site clicks | site impr | **PDF clicks** | **PDF impr** | PDF share | PDF position (impr-weighted) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-08-07 | 7 | 12 | 1,027 | 1 | 195 | 19.0% | 11.6 |
| 2026-08-14 | 7 | 19 | 1,015 | 5 | 198 | 19.5% | 13.1 |
| 2026-08-21 | 7 | 14 | 964 | 3 | 177 | 18.4% | 10.1 |
| 2026-08-28 | 7 | 15 | 1,388 | 6 | 236 | 17.0% | 9.5 |
| 2026-09-04 | 7 | 3 | 929 | 1 | 169 | 18.2% | 5.1 |
| 2026-09-11 | 7 | 6 | 671 | 0 | 88 | 13.1% | 3.3 |
| 2026-09-18 | 6 | 4 | 796 | 0 | 50 | 6.3% | 3.0 |

**The curve dropped, and it dropped in the week of 09-11.** PDF impressions held at 170–240 a week for five
weeks, then 88, then 50 in six days (a 7-day pace of ~58): a fall of about 70% from the August level, and the
PDF share of site impressions went from 19% to 6%. PDF clicks were 1–6 a week through 09-04 and zero since.
The daily series shows the break between 09-11 and 09-13 (…29 13 18 **3** 23 5 16 10 6 9 10 16 6 3). The
remaining PDF impressions sit at a mean position of 3, which is what a few still-indexed PDFs on branded or
`site:` queries look like (`site:insiderllm.com/pdfs` alone is 31 of the window's PDF impressions).

Against the 08-07 baseline: PDF share 60.5% (Jun 22 – Aug 7, Pages basis) → 16.4% over this whole window
(Chart basis; 8.3% Pages basis) → 6% in the latest week.

**How many PDF URLs, week by week: not answerable from these exports.** The Pages export is a single
aggregate over the 48 days; GSC does not export per-URL-per-day. Over the whole window **132 PDF URLs
received at least one impression and 11 received at least one click** (16 clicks total, 1,113 impressions,
Pages basis). Four of the 132 are `#page=` fragments of one URL.

## 2. The noindex-excluded list against what we de-indexed

The Coverage export lists 181 URLs excluded by noindex: **158 are `/pdfs/` URLs**, 23 are tag pages and two
old guide URLs excluded for their own reasons. All 158 are in our de-indexed set; none of the five exceptions
appears, which is correct.

| | count |
|---|---:|
| PDFs we de-indexed (on disk minus 5 exceptions) | 308 |
| in the noindex-excluded list | **158 (51%)** |
| **de-indexed but missing from the excluded list** | **150** |
| …of which received impressions in the window (so were indexed at some point in it) | 55 |
| …of which received no impressions in the window (likely never indexed, or crawled before 07-20 and not since) | 95 |

Google's recognition ramped late. The daily affected-page count in the Coverage chart (all noindex-excluded
URLs, PDFs and tag pages together):

| date | excluded pages | event |
|---|---:|---|
| 06-29 → 07-09 | 6 | pre-ship (tag pages) |
| 07-10 | 15 | pre-ship |
| 07-24 | 47 | four days after the 07-20 ship |
| 08-05 → 08-27 | 49 → 53 | the 08-07 read sat here: 18 days in, ~35 PDFs recognised |
| 08-28 | 95 | |
| 09-04 | 167 | the big step |
| 09-14 → 09-20 | 182 | |

Of the 158 excluded PDFs, 121 were last crawled in September, 14 in August and 23 in July: Google has been
working through the set at roughly its own recrawl pace, and the 09-04 step is what produced the impression
drop a week later.

**De-indexed PDFs missing from the excluded list and still receiving impressions (Pages basis, top 20 of
59; the full list of 150 is in the session record and is reproducible from the exports):**

| PDF | clicks | impr | position |
|---|---:|---:|---:|
| multi-gpu-local-ai | 1 | 99 | 4.4 |
| best-anime-stylized-checkpoints-local-image-generation | 0 | 42 | 10.0 |
| replace-github-copilot-local-llms-vscode | 0 | 38 | 4.6 |
| wsl2-local-ai-windows-guide | 0 | 36 | 23.4 |
| local-ai-video-generation | 0 | 34 | 2.9 |
| crane-qwen3-tts-local-voice-cloning | 0 | 32 | 6.5 |
| open-webui-ollama-connection-fix | 0 | 26 | 14.6 |
| qwen25-vl-lm-studio-vision-setup | 0 | 19 | 4.8 |
| embedding-models-rag | 0 | 18 | 11.9 |
| running-llms-mac-m-series | 0 | 18 | 17.6 |
| wicked-fast-qwen-3-6-27b-mtp-rtx-3090 | 0 | 17 | 5.1 |
| running-ai-offline-complete-guide | 1 | 16 | 10.0 |
| fine-tuning-mac-lora-mlx | 0 | 13 | 12.8 |
| ouro-2b-thinking-looped-language-model-local | 1 | 11 | 5.1 |
| pi-agent-local-models-ollama | 0 | 9 | 3.0 |
| turboquant-kv-cache-compression-local-ai | 0 | 9 | 6.7 |
| ollama-0-17-new-features | 0 | 8 | 3.6 |
| used-tesla-p40-local-ai | 0 | 8 | 6.0 |
| structured-output-local-llms | 0 | 8 | 6.1 |
| multi-gpu-worth-it | 0 | 8 | 7.3 |

The other 39 have 1–7 impressions each. Of the 132 PDFs with impressions in the window, 71 are already in the
excluded list (their impressions predate their exclusion) and 61 are not (59 de-indexed, 2 exceptions).

## 3. Did the site total move?

**Around the 07-20 de-index date: not computable from these exports.** The performance window opens 08-07,
eighteen days after the ship. The only pre-ship series on record is the 08-07 marker's, from the 08-07
export: weekly impressions from wk 06-22 of 9,659 / 6,425 / 1,432 / 1,016 / 1,493 / 1,039 / 497, with the
78% break between wk 06-29 and wk 07-06, two weeks before the noindex. That finding stands and is not
re-derived here.

**Around the event this export does contain, the 09-04 mass exclusion**, using the six full weeks:

| | first 3 full weeks (08-07 → 08-27) | last 3 full weeks (08-28 → 09-17) | weekly noise (population sd, 6 weeks) |
|---|---:|---:|---:|
| site impressions / week | 1,002 | 996 | 211 |
| site clicks / week | 15.0 | 8.0 | 5.4 |
| PDF impressions / week | 190 | 164 | 45 |
| non-PDF impressions / week | 812 | 832 | — |

Site impressions did not move (a 6-impression difference against a 211 band). Site clicks fell from 15 to 8 a
week, which is 1.3 sd and rests on single digits; the PDF clicks that stopped account for about 3 of the 7.
Non-PDF impressions did not rise as PDF impressions fell: **the PDF impressions left the site rather than
moving to the HTML twins**, which is the marker's original question answered in the same direction it was
answered on 08-07. Per-URL: of the twelve most-impressed PDFs, seven have an HTML twin with zero impressions in
the window; `lm-studio-tips-and-tricks.pdf`, the 08-07 example at 2,603 impressions, has **zero** now, and
its HTML twin has 274 at position 33.4 (against 144 at 12.7 over the 47 days to 08-07) — more impressions,
far worse position.

## 4. Verdict: PARTIALLY LANDED

- **Mechanism: landed and verified live twice.** Every non-excepted PDF serves the header; the exception
  does not.
- **Effect: landed on about half the set.** 158 of 308 de-indexed PDFs are recognised as noindex-excluded,
  PDF impressions are down ~70% and PDF clicks are zero for two weeks, with the break in the week of 09-11.
- **Not landed on 150 PDFs**, 59 of which still draw impressions. The likely reason is **not yet recrawled
  since 07-20**, not a mechanism gap: the excluded list's last-crawled dates show Google reaching the set at
  its own pace (23 in July, 14 in August, 121 in September, still climbing on 09-14), every spot-checked URL
  serves the header, and nothing links the PDFs except each page's own download button, which the header
  covers. "Cached" cannot be distinguished from "not recrawled" without an Indexed-pages export, which was
  not pulled; the 95 de-indexed PDFs with neither an exclusion entry nor an impression are most likely PDFs
  published after 07-20 that Google has never indexed at all (the PDF count grew from 255 to 313).
- **The five exceptions.** Impressions prove indexing: `/blog/newsletter-2026-05-03/` has 63 impressions and
  `/blog/newsletter-2026-07-06/` has 1, so both HTML twins are indexed and **those two exceptions can be
  removed**. `ai-market-panic-capability-dissipation-gap`, `mycoswarm-wifi-laptop-borrowed-gpu` and
  `h-neurons-why-llms-hallucinate` have HTML twins absent from Pages.csv (zero impressions), so their status
  still needs the Indexing report; their PDFs carry 1, 0 and 7 impressions. Removing an exception is an
  `.htaccess` edit and a deploy — not done today.

## Re-check on 2026-10-07

Pull the same three exports plus **Indexing → Pages → Indexed** (the list, not just the excluded one).
Re-check the 20 URLs in section 2's table first; if `multi-gpu-local-ai.pdf` is still not in the excluded
list, run it through URL Inspection and request indexing (which forces the recrawl that applies the header).
Remove the `newsletter-2026-05-03` and `newsletter-2026-07-06` exceptions from the `RewriteCond` in the same
pass. Landed = excluded count ≥ 250 of 308 and PDF share under 5% for two consecutive weeks.

## Reproduction

`docs/GSC_cvs/2026-09-23/` (local only). Weekly bins: 7-day from 08-07 over `Chart.csv` of the site and
`_pdf` exports; cross-reference: `public/pdfs/*.pdf` on disk minus the five `.htaccess` exceptions, against
`Coverage-Drilldown…/Table.csv` URLs and `_pdf/Pages.csv`; live header check with `curl -sI`.
