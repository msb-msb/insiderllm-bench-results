# PDF de-index checkpoint — GSC exports of 2026-10-07

This is the follow-up to `pdf-deindex-checkpoint-2026-09-23.md`, which explains the mechanism and the
history. Marker: `dated-markers.md`, "PDF de-index checkpoint", due 2026-10-07. Every figure below
comes from the exports in `docs/GSC_cvs/2026-10-07/`. That folder is gitignored, like the 09-23 one.

## Inputs

| Export | Folder | Contents |
|---|---|---|
| Indexing → Pages (overview) | `Coverage-2026-10-07/` | Daily indexed and not-indexed counts to 10-03; reasons for not indexing |
| Excluded by 'noindex' tag | `Coverage-Drilldown-2026-10-07/` | 206 URLs, each with its last-crawled date |
| Indexed pages | `Coverage-Valid-2026-10-07/` | 838 URLs, each with its last-crawled date. Matches the chart's 839 indexed, so the list is complete. |
| Performance on Search | `Performance-on-Search-2026-10-07/` | Web, Jun 1 – Oct 6. **Whole site, with no `.pdf` filter.** |

The zips were filed under `docs/GSC_cvs/2026-09-23/`, and a performance zip was loose in `docs/`.
All four were moved to `docs/GSC_cvs/2026-10-07/` and unzipped there. The empty `docs/GSC-cvs/`
folder was removed: GSC exports go in the gitignored `GSC_cvs/`.

GSC's coverage data stops at **10-03**. The noindex-excluded count has been flat at 206 since 09-21,
so this read covers recrawls up to about the last week of September.

**The base is 308 PDFs** (the 09-23 set). There are now 317 PDFs on disk. Five are exceptions, and
the four newest belong to pages published after 09-23 (bonsai-2-27b-vs-qwen3-8-27b-rtx-3090,
strata-vs-llama-cpp-rtx-3060, and the newsletters of 09-28 and 10-05). None of those four appears in
either list.

## 1. Excluded count: 183 of 308, up from 158 on 09-23

| | 09-23 | 10-07 |
|---|---:|---:|
| Noindex-excluded URLs, all types | 181 | 206 |
| …of which de-indexed PDFs | **158** | **183** |
| De-indexed PDFs still in the **Indexed** list | not pulled | **29** |
| De-indexed PDFs in neither list | — | **96** |

- Every PDF that was excluded on 09-23 is still excluded, and 25 more have been added.
- None of the five exceptions is in the excluded list, which is correct.
- 146 of the 183 excluded PDFs were last crawled in September or October.

The daily excluded count (all URL types) climbed in steps: 53 on 08-21, 95 on 08-28, 167 on 09-04,
182 on 09-14, then 206 from 09-21. It hasn't moved since.

**The 29 still-indexed PDFs have not been recrawled since the header shipped.** Their last-crawled
dates run from 06-01 to 07-20. Every other de-indexed PDF that Google crawled after 07-20 is in the
excluded list. That points to recrawl pace as the reason, not a gap in the mechanism.

**The 96 in neither list are mostly already out of the index.**
- 16 belong to pages published after 07-20, so Google may never have indexed them.
- Most of the rest had impressions earlier in the window and dropped out without a noindex recrawl.
  The largest is `lm-studio-tips-and-tricks.pdf`: 2,847 impressions over Jun 1 – Oct 6, zero in
  the 09-23 window, and now neither indexed nor excluded.
- These exports can't show which "not indexed" reason Google gives for them. The overview's largest
  candidate is "Crawled – currently not indexed" (165 URLs), but its drilldown wasn't pulled.

## 2. Weekly /pdfs/ impression share: not readable from this export

The 10-07 Performance export covers the whole site. Its `Chart.csv` has daily totals for the site
only, and `Pages.csv` has one total per URL across Jun 1 – Oct 6. A weekly PDF share needs the same
export filtered to `Page contains .pdf`, as was pulled on 09-23 (`_pdf`). **That export is the one
input missing from this read.**

The only PDF figure available is for the whole window: 38,375 of 154,499 page-basis impressions
(24.8%). That mixes June and July, before the header took effect, with the period after, so it says
nothing about the last two weeks.

## 3. The twelve re-check URLs

| PDF | 10-07 status | Last crawled |
|---|---|---|
| multi-gpu-local-ai | **excluded** | 09-25 |
| replace-github-copilot-local-llms-vscode | **excluded** | 09-26 |
| crane-qwen3-tts-local-voice-cloning | **excluded** | 09-26 |
| local-ai-video-generation | **excluded** | 09-27 |
| open-webui-ollama-connection-fix | **excluded** | 09-25 |
| embedding-models-rag | **excluded** | 09-27 |
| wicked-fast-qwen-3-6-27b-mtp-rtx-3090 | **excluded** | 09-27 |
| best-anime-stylized-checkpoints-local-image-generation | still **indexed** | 06-01 |
| wsl2-local-ai-windows-guide | still **indexed** | 07-03 |
| qwen25-vl-lm-studio-vision-setup | still **indexed** | 07-04 |
| running-llms-mac-m-series | still **indexed** | 07-03 |
| running-ai-offline-complete-guide | still **indexed** | 07-15 |

Seven were recrawled in the last week of September and excluded on that crawl. The other five have
not been recrawled since before the ship date, so they are on the request-indexing list below.

## 4. The five exceptions

| Exception | HTML twin | PDF | Action |
|---|---|---|---|
| newsletter-2026-05-03 | **indexed**, crawled 08-25 | indexed, crawled 09-28 | **Exception removed 2026-10-07**, as the marker says |
| newsletter-2026-07-06 | **indexed**, crawled 07-09 | not indexed | **Exception removed 2026-10-07**, as the marker says |
| mycoswarm-wifi-laptop-borrowed-gpu | **indexed**, crawled 09-17 | indexed, crawled 08-02 | **Exception removed 2026-10-07** on Mark's approval (same rule as the newsletters) |
| ai-market-panic-capability-dissipation-gap | not indexed (4 impressions over the window) | indexed, crawled 07-04 | Keep |
| h-neurons-why-llms-hallucinate | **canonical URL not indexed**. Google indexed a `?utm_source=insiderllm&utm_medium=email&utm_campaign=…` copy instead (crawled 08-02, 8 impressions). | indexed, crawled 09-05 | Keep. Canonical checked (below): the tag is correct. |

**h-neurons canonical, checked 2026-10-07 (report only).**
- Both the clean URL and the `?utm_source=insiderllm&utm_medium=email&utm_campaign=…` copy serve
  `<link rel=canonical href=https://insiderllm.com/blog/h-neurons-why-llms-hallucinate/>`.
- og:url is the clean URL, and the sitemap lists the clean URL.
- No page on the site links to the utm copy. It came from the newsletter email.

So the tag is right and Google indexed the utm copy anyway. Nothing to fix on our side. At the next
read, check whether the clean URL has replaced it.

**.htaccess change, deployed 2026-10-07 (two deploys the same day).**
- Second deploy, approved by Mark: `mycoswarm-wifi-laptop-borrowed-gpu` removed too. Two exceptions
  remain. Checked live: the mycoswarm PDF returns `200` with `x-robots-tag: noindex`, and
  `ai-market-panic-capability-dissipation-gap` and `h-neurons-why-llms-hallucinate` return `200`
  without it.

First deploy:
- `newsletter-2026-05-03` and `newsletter-2026-07-06` were taken out of the exception
  `RewriteCond`. Three exceptions remain.
- Checked live with `curl -sI`:
  - Both newsletter PDFs now return `200` with `x-robots-tag: noindex`.
  - The three remaining exceptions return `200` without the header.
  - `lm-studio-tips-and-tricks.pdf` (control) still has it.

## 5. For Mark: request indexing (URL Inspection → Request indexing)

**Outcome 2026-10-07: nothing was requested.** Mark tried Request indexing on the top 5 and GSC
rejected each attempt, because a URL serving noindex can't be submitted for indexing. The live test
on comfyui-vs-automatic1111-vs-fooocus.pdf confirmed that GSC sees 'noindex' in the X-Robots-Tag.
So the header is reaching Googlebot, but this route can't force a recrawl. **All 31 de-indexed PDFs
still in the Indexed list are on natural recrawl:** the 29 below, plus newsletter-2026-05-03.pdf
and mycoswarm-wifi-laptop-borrowed-gpu.pdf, whose exceptions were removed today. The 10-21 read
doesn't split requested from not-requested. The table is kept as the full list.

These 30 PDFs are de-indexed and still in Google's index. Each needs a recrawl so Google sees the
header. Each was last crawled before the header shipped, except newsletter-2026-05-03, whose
exception was only removed today. The list is ordered by impressions (Jun 1 – Oct 6, page basis).
GSC caps manual requests at about 10 a day, so this is three or four days of requests.

| PDF | Impr | Clicks | Last crawled |
|---|---:|---:|---|
| best-anime-stylized-checkpoints-local-image-generation | 1,774 | 0 | 06-01 |
| comfyui-vs-automatic1111-vs-fooocus | 854 | 0 | 07-04 |
| running-llms-mac-m-series | 628 | 1 | 07-03 |
| open-webui-setup-guide | 591 | 1 | 06-30 |
| wsl2-local-ai-windows-guide | 247 | 0 | 07-03 |
| what-can-you-run-8gb-vram | 243 | 0 | 07-20 |
| llamacpp-vs-ollama-vs-vllm ⚠ | 241 | 0 | 07-04 |
| run-first-local-llm | 228 | 1 | 07-15 |
| liquidai-lfm2-local-setup-guide | 218 | 1 | 07-04 |
| running-ai-offline-complete-guide | 216 | 4 | 07-15 |
| qwen25-vl-lm-studio-vision-setup | 213 | 0 | 07-04 |
| mistral-voxtral-tts-local-voice-ai | 158 | 1 | 07-04 |
| ollama-0-17-new-features | 151 | 0 | 07-04 |
| multi-gpu-worth-it | 125 | 0 | 07-15 |
| rtx-5060-ti-16gb-local-ai-options | 115 | 0 | 07-03 |
| rtx-3060-vs-3060ti-vs-3070-local-ai | 113 | 1 | 07-16 |
| fine-tuning-local-lora-qlora | 105 | 0 | 07-03 |
| deepseek-v4-preview | 105 | 0 | 07-04 |
| used-tesla-p40-local-ai | 69 | 0 | 07-04 |
| smarterrouter-vram-aware-llm-gateway-local-ai | 53 | 0 | 07-03 |
| openclaw-security-guide | 48 | 0 | 07-15 |
| nanollama-train-llama-from-scratch | 42 | 0 | 07-03 |
| best-local-llms-data-analysis | 41 | 0 | 07-15 |
| local-llms-vs-claude | 33 | 0 | 07-04 |
| model-routing-local-ai-guide | 31 | 1 | 07-04 |
| claude-code-source-leak-what-we-learned | 19 | 0 | 07-04 |
| karpathy-autoresearch-local-gpu-guide | 17 | 0 | 07-15 |
| newsletter-2026-06-15 | 13 | 0 | 06-24 |
| newsletter-2026-05-03 (exception removed today) | 10 | 0 | 09-28 |
| intent-engineering-local-ai-guide | 3 | 0 | 07-11 |

⚠ **Hold `llamacpp-vs-ollama-vs-vllm.pdf` until after 2026-12-15.** Its HTML page is a control in the
hub experiment, whose pre-window opens 10-14. A forced recrawl that drops its PDF duplicate could move
impressions onto the control's HTML page in the middle of the windows. A recrawl Google does on its
own is outside our control and would count as noise. A request from us would be a change we made, and
the protocol has no allowance for it. **That leaves 29 to request now.** None of the other seven
frozen pages' PDFs are on the list.

URL to paste for each: `https://insiderllm.com/pdfs/<slug>.pdf`.

## 6. Verdict: NOT LANDED on the stated criterion. Re-dated to 2026-10-21

**Criterion replaced, approved by Mark 2026-10-07:** landed = no de-indexed PDF left in the Indexed
list AND PDF share under 5% for two consecutive weeks. The old ≥ 250-of-308 test is retired. The
reasoning is below. On the new criterion today: 31 de-indexed PDFs are still in the Indexed list,
and the share wasn't readable.


- **Mechanism: landed.** Verified live for the third time.
- **Excluded ≥ 250 of 308: not met.** The count is 183 (59%), up from 158.
- **PDF share under 5% for two consecutive weeks: not readable.** That needs the `.pdf`-filtered
  Performance export, which wasn't pulled this time.

**The count criterion can't be reached as written.** If Google recrawls and excludes all 29
still-indexed PDFs, the count reaches 212. The 96 in neither list are already out of the index, so
they'll never be recrawled into the excluded list. Since the aim is to get the PDFs out of the
index, a criterion that would actually measure it is: **"0 de-indexed PDFs in the Indexed list, and
PDF share under 5% for two consecutive weeks."** Today the first part stands at 29, and those 29 are
exactly the request-indexing list. Mark approved it on 2026-10-07, and the marker now carries it.

## Reproduction

All from `docs/GSC_cvs/2026-10-07/` (local only).
1. Take the de-indexed set: `insiderllm-hugo/public/pdfs/*.pdf`, minus the exceptions, minus the
   four PDFs added after 09-23.
2. Cross-reference it against the `Table.csv` URL lists in `Coverage-Drilldown…` and
   `Coverage-Valid…`.
3. Take impressions from `Performance-on-Search…/Pages.csv`.
4. Check headers live with `curl -sI`.
