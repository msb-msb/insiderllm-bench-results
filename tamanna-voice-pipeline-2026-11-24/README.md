# Voice pipeline on one RTX 3090 (Tamanna), 2026-11-24: results

Pre-registration `docs/candidates/voice-pipeline-3090-2026-11.md`: lock `c7cf92cc` (sha256 `6c7608fc…2a35`), plus
amendments A1, A2 (`b8d34f65…4b54`), A3 (`bae91cb1…79a5`, commit `5224a479`) and A4 (`81ba932a…d417`, commit
`d8d7ba39`). The file as it stood for the run hashes to
`81ba932a6ff203ef3d9fca27ab248d11420b0610e5e9999b072cd85a18a7d417`, and its public copy matches. What was done before
the first measured pass is in `PRE-RUN.md`. This file reports the locked results against the section 4 predictions.
Anything not pre-registered is labelled **exploratory**.

**Question (section 1).** On Tamanna (RTX 3090 24 GB, Ryzen 7 5700X, 64 GB DDR4-3000), a browser on another LAN
machine, through Open WebUI 0.13.0: how long from the end of a spoken question to the first audio of the answer,
where does the time go, and how is the 24 GB split?

**Short answer.** About **6.2–6.7 s** median from end of speech to first audio for FLEURS in all three STT arms. For
Mark's five real questions the pooled median is **5.1–5.4 s**, but 5–7 of those 15 clips per arm got their answer
audio from Open WebUI's own TTS cache (see Measurement notes); the TTS-served ones alone have a median of
**5.6–6.6 s**. Every E2E prediction missed (bands 2.8–5.5 s). The time splits roughly
in half:
- **~3.2–3.4 s residual.** This is Open WebUI's own: the ~2 s end-of-speech wait, plus its title call (~0.4–0.6 s),
  which runs ahead of the reply on the single LLM slot.
- **~2.5–2.7 s first TTS request.** Open WebUI usually sent the whole two-sentence reply as one TTS request, not one
  sentence.
- **Under 0.6 s for STT plus the LLM's first sentence.**

The STT choice moves E2E by less than 0.5 s. S2 (Granite 5.0 TurboCTC) was the fastest STT on every clip; S1
(Qwen3-ASR) had the lowest WER once its language prefix is stripped. The LLM fitted at `-ncmoe` 10 (S1, S3) and 5
(S2). Peak total VRAM was ~24.1 GB, about 290 MiB over the 23,808 MiB budget the method set, because the TTS process
grew ~700 MiB past its warm-up peak.

## What ran

| Arm | STT | LLM `-ncmoe` | Free VRAM for the LLM (MiB) | Run window (PST) |
|---|---|---:|---:|---|
| S1 | Qwen3-ASR-1.7B Q8_0 GGUF, llama-server | 10 | 17,342 | 15:26–16:18 |
| S2 | Granite Speech 5.0 TurboCTC, our wrapper | 5 | 19,586 | 16:20–17:14 |
| S3 | Granite Speech 4.1-2B-Plus Q8_0 GGUF, llama-server | 10 | 17,286 | 17:14–18:07 |
| R0 | none (typed text, LLM only, fully resident) | 0 | n/a | 18:07–18:32 |

- **Software.** llama.cpp v0.7.0 (`620d222`) for the LLM and the S1/S3 STT servers. The LLM is
  Qwen3.6-35B-A3B UD-Q4_K_M, sha256 `ac0e2c11…31a61`. TTS is Qwen3-TTS-12Hz-0.6B-CustomVoice (voice `ryan`) behind
  `harness/tts_customvoice_server.py`.
- **Model files.** All 35 were re-hashed against LLM_repo on the day (`day0/rehash.log`).
- **GPU.** Before every arm's warm-up the A1 check read `Enabled, 420.00 W` (`<ARM>/a1_check.log`, plus
  `nvidia-smi -q -d POWER` output beside it).
- **Passes.** Each arm ran 1 discarded warm-up pass over all 25 clips, then 3 measured passes.

Exact server command lines (also in each arm's `meta.json` and in the first line of each server log):

```
LLM  llama-server -m ~/bench-models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf --alias qwen3.6-35b-a3b -ngl 99 --n-cpu-moe N
     -c 8192 -np 1 -fa on --jinja --chat-template-kwargs {"enable_thinking":false} --host 0.0.0.0 --port 8080
     (N = 10 S1, 5 S2, 10 S3, 0 R0; default host prompt cache, A4)
S1   llama-server -m qwen3-asr-1.7b-Q8_0.gguf --mmproj mmproj-qwen3-asr-1.7b-f16.gguf -ngl 99 -c 2048 -np 1
     --cache-ram 0 --host 127.0.0.1 --port 8093
S2   ctc/bin/python harness/stt_ctc_server.py --model granite-speech-5.0-470m-turboctc --ffmpeg bin/ffmpeg
     --host 127.0.0.1 --port 8091 --log <ARM>/stt_s2.jsonl
S3   llama-server -m granite-speech-4.1-2b-plus-Q8_0.gguf --mmproj mmproj-model-f16.gguf -ngl 99 -c 2048 -np 1
     --cache-ram 0 --host 127.0.0.1 --port 8093
TTS  tts/bin/python harness/tts_customvoice_server.py --model qwen3-tts-12hz-0.6b-customvoice --speaker ryan
     --language english --ffmpeg bin/ffmpeg --host 0.0.0.0 --port 8092 --log <ARM>/tts.jsonl
     (language set per clip through /v1/voice-pipeline/language, section 3.1)
```

## Results (3 measured passes pooled; median / p90, ms)

| Arm | Set | n ok | E2E | STT | LLM TTFT | LLM to 1st sentence | 1st TTS request | Residual | E2E − residual |
|---|---|---:|---|---|---|---|---|---|---|
| S1 | FLEURS en | 27 | 6,166 / 7,973 | 177 / 205 | 270 / 280 | 340 / 512 | 2,440 / 3,981 | 3,365 / 3,571 | 2,954 |
| S1 | FLEURS de | 30 | 6,433 / 8,647 | 221 / 255 | 285 / 294 | 392 / 667 | 2,552 / 4,394 | 3,426 / 3,634 | 3,112 |
| S1 | FLEURS both | 57 | 6,313 / 8,113 | 193 / 255 | 274 / 293 | 365 / 587 | 2,536 / 4,113 | 3,396 / 3,616 | 3,070 |
| S1 | EN real | 15 | 5,417 / 7,850 | 80 / 140 | 170 / 174 | 295 / 631 | 2,770 / 4,179 | 3,337 / 3,445 | 3,288 |
| S2 | FLEURS en | 27 | 6,656 / 7,799 | 71 / 85 | 147 / 203 | 242 / 501 | 3,107 / 4,091 | 3,159 / 3,486 | 3,430 |
| S2 | FLEURS de | 30 | 6,072 / 7,529 | 68 / 79 | 202 / 208 | 312 / 579 | 2,527 / 3,819 | 3,198 / 3,459 | 2,915 |
| S2 | FLEURS both | 57 | 6,199 / 7,799 | 70 / 82 | 149 / 208 | 273 / 579 | 2,684 / 4,091 | 3,195 / 3,478 | 3,079 |
| S2 | EN real | 15 | 5,060 / 6,074 | 53 / 75 | 137 / 144 | 218 / 424 | 2,093 / 2,675 | 3,180 / 3,266 | 2,418 |
| S3 | FLEURS en | 27 | 6,571 / 8,025 | 193 / 213 | 173 / 210 | 300 / 610 | 2,711 / 3,595 | 3,409 / 3,610 | 3,314 |
| S3 | FLEURS de | 30 | 6,743 / 8,201 | 241 / 277 | 262 / 272 | 409 / 707 | 2,652 / 3,983 | 3,424 / 3,636 | 3,396 |
| S3 | FLEURS both | 57 | 6,679 / 8,238 | 211 / 270 | 178 / 268 | 358 / 682 | 2,695 / 3,948 | 3,415 / 3,637 | 3,386 |
| S3 | EN real | 15 | 5,297 / 7,383 | 95 / 169 | 154 / 165 | 256 / 510 | 2,472 / 4,548 | 3,317 / 3,382 | 2,928 |
| R0 | FLEURS both | 60 | n/a | n/a | 114 / 115 | 231 / 335 | n/a | n/a | n/a |
| R0 | EN real | 15 | n/a | n/a | 110 / 111 | 176 / 276 | n/a | n/a | n/a |

- **Columns.** "E2E − residual" is the median of the per-clip difference. S2's STT figure includes the wrapper's
  file read and ffmpeg decode; its inference-only median is 54–57 ms on FLEURS and 40 ms on EN real. S1/S3 STT is
  llama-server's per-task time, which doesn't include its own audio-file decode.
- **Failures.** In each S arm, en04 failed in all 3 passes (see Failed clips), so FLEURS en has n = 27 there.
- **Per clip.** Every clip is in `<ARM>/per_clip.tsv`; aggregates are in `<ARM>/summary.json` and `tables.json`.

**VRAM peaks over each arm (MiB, 10 Hz sampler, `<ARM>/vram.csv`):**

| Arm | STT | LLM | TTS | Total (per-tick sum) |
|---|---:|---:|---:|---:|
| S1 | 3,532 | 16,898 | 3,666 | 24,096 |
| S2 | 1,268 | 19,204 | 3,624 | 24,096 |
| S3 | 3,430 | 16,884 | 3,784 | 24,098 |
| R0 | – | 21,254 | – | 21,254 |

**WER (pass 1, `harness/wer.py`; q3 excluded as pre-declared; corpus-level per set):**

| Arm | FLEURS en (9 clips) | FLEURS de (10) | EN real (4) |
|---|---:|---:|---:|
| S1, prefix stripped (A3 primary) | 12.5% | 8.0% | 0.0% |
| S1, unstripped (locked scoring, as delivered) | 22.0% | 18.3% | 18.6% |
| S2 | 13.7% | 15.4% | 0.0% |
| S3 | 13.1% | 18.9% | 0.0% |

FLEURS en has 9 clips because en04 has no transcript. en08 alone has a per-clip WER of 68–73% in every arm, because
Open WebUI transcribed only part of it (see Measurement notes).

**S1 prefix through Open WebUI (A3).** The prefix reaches the LLM. In all 72 successful S1 clips, the user turn Open
WebUI sent was the transcription response verbatim, starting `language English<asr_text>` or
`language German<asr_text>` (`s1_prefix_delivered` in `S1/per_clip.tsv`).

## Predictions (section 4)

A prediction holds if the arm's median lands inside the band. Where the lock says GB for VRAM, both MiB and GiB are
given. "Per arm" medians are FLEURS en+de pooled unless a row says otherwise.

**4.1 STT stage**

| Prediction | S1 | S2 | S3 |
|---|---|---|---|
| Process VRAM peak (S1 2.5–4.5, S2 1.5–3.5, S3 3.0–5.0 GB) | 3,532 MiB = 3.45 GiB: **holds** | 1,268 MiB = 1.24 GiB: **misses** (below) | 3,430 MiB = 3.35 GiB: **holds** |
| STT time per clip, median (S1 150–600, S2 30–200, S3 200–800 ms) | 193: **holds** | 70: **holds** | 211: **holds** |
| WER EN (S1 2–8%, S2 2–8%, S3 2–9%) | 12.5%: **misses** | 13.7%: **misses** | 13.1%: **misses** |
| WER DE (S1 3–10%, S2 4–14%, S3 4–12%) | 8.0%: **holds** | 15.4%: **misses** | 18.9%: **misses** |
| S2 faster than S1 and S3 on every clip | | **holds**: 24 of 24 clips (per-clip median over 3 passes; en04 has no STT) | |

S1's unstripped WER (EN 22.0%, DE 18.3%) misses both bands. These WERs come from 9–10 clips per language, a sanity
check as section 3.3 says, not a leaderboard figure.

**4.2 LLM fit and speed**

| Prediction | S1 | S2 | S3 | R0 |
|---|---|---|---|---|
| Free VRAM after STT + TTS + margin, 15.5–19 GB | 17,342 MiB = 16.9 GiB: **holds** | 19,586 MiB = 19.1 GiB: **misses** (above) | 17,286 MiB = 16.9 GiB: **holds** | |
| Chosen `-ncmoe` 6–14 | 10: **holds** | 5: **misses** (below) | 10: **holds** | 0 (fixed) |
| Decode at the chosen `-ncmoe`, 80–125 tok/s | 96.2: **holds** | 113.3: **holds** | 95.2: **holds** | 153.8 (no band) |
| LLM TTFT, voice arms 150–500 ms; R0 80–250 ms | 274: **holds** | 149: **misses** (just below) | 178: **holds** | 114: **holds** |
| LLM to first sentence boundary, 350–900 ms | 365: **holds** | 273: **misses** (below) | 358: **holds** | 231 |

The TTFT prediction assumed a ~300–600-token prompt. The real reply prompt was ~7,400–7,430 tokens, because Open
WebUI 0.13 adds 38 built-in tool definitions (A4). The default host cache restored all but 30–50 of those tokens
for each reply (next table), so TTFT measures 30–50 evaluated tokens plus the cached prefix. llama-server's
slot-selection-to-launch step, which holds the host-cache restore, takes ~134 ms per reply here and isn't in TTFT.
The exploratory tools-off pass, with a ~240-token prompt, shows ~115 ms for the same step. So most of it is
per-request overhead, and the restore of the 7.4K prefix adds only ~20 ms.

Decode is the median of each reply's own rate. German replies decode visibly slower in every arm (lower quartile
30–50 tok/s, slowest on the longest replies). **Exploratory, not verified:** the likely cause is the TTS starting on
the first sentence while the LLM is still decoding, so the two share the GPU.

**A4 per-pass LLM figures (all successful clips per pass; median):**

| Arm | Pass | TTFT (ms) | Evaluated prompt tokens | Cached prompt tokens | Slot select → launch (ms) |
|---|---:|---:|---:|---:|---:|
| S1 | 1 / 2 / 3 | 271.5 / 271.2 / 271.0 | 42 / 42 / 42 | 7,389 / 7,389 / 7,389 | 133.8 / 134.0 / 134.3 |
| S2 | 1 / 2 / 3 | 146.5 / 147.7 / 146.6 | 31.5 / 33.5 / 32 | 7,389 / 7,389 / 7,389 | 134.3 / 133.9 / 134.0 |
| S3 | 1 / 2 / 3 | 174.7 / 174.7 / 173.3 | 34 / 34.5 / 33.5 | 7,389 / 7,389 / 7,389 | 134.0 / 134.1 / 134.0 |
| R0 | 1 / 2 / 3 | 112.6 / 112.3 / 112.3 | 35 / 35 / 35 | 7,208 / 7,208 / 7,208 | 135.5 / 135.3 / 136.0 |

- **No drift from pass 1 to pass 3.** The discarded warm-up pass already put the shared prefix in the host cache, so
  pass 1 behaves like passes 2 and 3. Per reply, the cache restored the shared tool prefix, and the user turn was
  evaluated fresh.
- **Whole-prompt restores.** In 0–3 replies per pass the whole prompt came back (4 evaluated tokens).
- **STT cache stayed off.** STT prompt tokens are the same in every pass (S1 116.5, S3 87.5 median), which confirms
  A3's `--cache-ram 0` on the STT servers.

**4.3 TTS stage and end to end**

| Prediction | S1 | S2 | S3 |
|---|---|---|---|
| TTS process VRAM peak 2.5–5.0 GB | 3,666 MiB: **holds** | 3,624 MiB: **holds** | 3,784 MiB: **holds** |
| First TTS request, 400–1,500 ms | 2,536: **misses** | 2,684: **misses** | 2,695: **misses** |
| Residual 1.8–3.0 s | 3.40 s: **misses** | 3.20 s: **misses** | 3.42 s: **misses** |
| Residual the same across arms within ±0.3 s | spread 0.22 s: **holds** | | |
| E2E median (S1 3.0–5.5, S2 2.8–5.0, S3 3.0–5.5 s) | 6.31 s: **misses** | 6.20 s: **misses** | 6.68 s: **misses** |
| E2E without the residual, 1.0–2.8 s | 3.07 s: **misses** | 3.08 s: **misses** | 3.39 s: **misses** |
| German vs English E2E within ±20% | +4.3%: **holds** | −8.8%: **holds** | +2.6%: **holds** |
| German WER higher than English in all three arms | 8.0 < 12.5: no | 15.4 > 13.7: yes | 18.9 > 13.1: yes → **misses** (not all three) |
| EN real vs EN FLEURS E2E within ±25% | −12.1%: **holds** | −24.0%: **holds** | −19.4%: **holds** (all three also hold on TTS-served EN real clips only: +6.5%, −15.2%, −5.0%) |
| Total VRAM peak ≤ 23.8 GB (the 23,808 MiB budget) | 24,096 MiB: **misses** | 24,096 MiB: **misses** | 24,098 MiB: **misses** |
| p90 E2E within 1.5 s of the median | +1.80 s: **misses** | +1.60 s: **misses** | +1.56 s: **misses** |

**First TTS request.** The prediction assumed one sentence per TTS request. Open WebUI's punctuation splitting
usually sent the whole reply as the first and only TTS request: a median of 1 request per clip, while replies had a
median of 2 sentences (S1 request text median 91 characters). Why the splitting didn't send the first sentence on
its own wasn't investigated.

**Residual.** The residual contains Open WebUI's title-generation call. Open WebUI sends it ~20 ms before the reply
request, and on the single LLM slot it runs first (A4). Median `pre_reply_ms`: S1 593, S2 430, S3 585 (R0 241). The
rest is the end-of-speech wait (~2 s), upload and Open WebUI overhead.

**VRAM.** Total VRAM went over the budget by ~290 MiB. The fit added warm-up peaks (STT + TTS) to the LLM's fit peak:
23,348 / 23,426 / 23,404 MiB, inside the budget. During the run the TTS process grew to 3,624–3,784 MiB, from
2,944–3,098 MiB in warm-up, because it synthesised longer texts than the three warm-up sentences. Nothing ran out of
memory. A school box sized by this method needs a larger margin, or longer TTS warm-up texts.

**p90 per set.** S1 en +1.81, de +2.21, real +2.43 s; S2 en +1.14, de +1.46, real +1.01 s; S3 en +1.45, de +1.46, real
+2.09 s. The pooled p90 misses in all three arms; per set, S2 stays within 1.5 s everywhere.

## Failed clips

- **en04 (FLEURS en_us row 28), all 3 measured passes in S1, S2 and S3.** It also failed in every warm-up pass.
  Open WebUI's voice mode never detected it as speech: no transcription request was sent, and the client's 90 s wait
  for audio timed out (`TimeoutError … 90000ms` in `client-<pass>.jsonl`).
- **Level.** Peak −29.6 dBFS. Only 15 10 ms frames are above −40 dBFS, against 400–800 for en01–en06.
- **Treatment (A4).** It counts as a failed clip in each S arm (3 of 75 per arm) and is not replaced.
- **R0** has no failed clips (it's typed text).

## Measurement notes (reported; no clip is excluded, the lock has no exclusion rule)

- **Open WebUI's TTS cache (found after the run).** Open WebUI's `/api/v1/audio/speech` keys a cache on the SHA-256
  of the request body (text, voice and model; `routers/openai.py` line 525 in 0.13.0). If a reply's first TTS chunk
  is text it has synthesised before, Open WebUI returns the cached mp3 and never calls the TTS server. The cache has
  run since Open WebUI started at 10:26, so it spans passes, the warm-up passes, the voided attempts and the arms
  (`owui-data/cache/audio/speech/`, 1,576 entries by the end).
  - **Which clips.** In the locked arms it hit only EN real, whose short questions often get word-for-word the same
    reply ("The capital of France is Paris."): S1 5 of 15 EN real clips, S2 5, S3 7. These clips have no TTS request
    in their window, so they have no 1st-TTS, residual or E2E − residual figure, and their E2E is ~3.4–3.6 s.
  - **No FLEURS clip** in any locked arm was served from the cache, so the FLEURS figures are not affected.
  - **EN real E2E, pooled vs TTS-served only (median):** S1 5,417 vs 6,569 ms (n 15 vs 10), S2 5,060 vs 5,642
    (15 vs 10), S3 5,297 vs 6,245 (15 vs 8). The split is **exploratory**; the pre-registered figure is the pooled
    one.
  - **For a school deployment**, a repeated reply is played straight from the cache, so a common question answered
    the same way gets faster.

- **en08 is partly heard.** en08 is quiet (most frames between −45 and −30 dBFS). In every arm and pass Open WebUI
  sent only its middle, "…adult children did not leave a big impression", so it lost both the opening name and the
  ending. Its E2E is measured from the clip's real speech end (6.25 s), while Open WebUI acted on an utterance that
  ended earlier. That understates its E2E: one value is 1.3 s (S1 pass 1). Its WER is 68–73% in every arm.
  **Exploratory:** without en08, the pooled FLEURS en WER would be lower in all three arms. That isn't computed here
  as a result.
- **S3 en08 pass 2: E2E 25.5 s, residual 21.7 s.** Open WebUI didn't close the recording until much later on this
  quiet clip. It's included in S3's figures (it is the p90 tail's largest value).
- **Long first TTS requests.** Most other values over 10 s come from first TTS requests of 6–10 s, when the reply's
  first chunk is long: S1 de01 (passes 1 and 3), en03 (pass 2), de09 (pass 3); S3 de08 (pass 1), q3 (pass 2).
- **Speech end at end of file (limitation, A3).** For en01 and en10 the last frame above −40 dBFS is the last frame
  of the file, so their E2E is measured from the end of the file.
- **Silent primer.** The silent `data:` audio primer Open WebUI plays when Voice mode is clicked is logged and
  ignored, by rule (A3).

## Limitations (A2 known cost, A3 section 3)

- **No speaker IDs.** FLEURS publishes no speaker IDs, so A2's distinct-speaker count can't be given. FLEURS sentence
  ids and gender labels are in `clips/clips.tsv` instead.
- **All male.** All 20 selected FLEURS clips are labelled MALE.
- **Few distinct sentences.** de_de covers 7 distinct sentences (ids 1885, 1724 and 1674 each appear twice). en_us
  covers 10.
- **Loud English only.** English comes from the loudest ~quarter of FLEURS en_us test clips (A2), so the English
  latency results may not carry over to quiet input. FLEURS en_us audio is quiet as a set. Even within the selection,
  en04 (not detected at all) and en08 (partly heard) show the effect directly: Open WebUI's voice mode needs input
  above roughly −30 dBFS to segment speech reliably. That threshold is **exploratory**, from these two clips.

## Deviations and voided attempts

- **S1.void-1** (15:07–15:18). Stopped by hand in its discarded warm-up pass; no measured clip. It led to A4. Voided
  and re-run under A1 item 1 (`S1.void-1/VOID.md`).
- **S2.void-1** (16:18–16:20). Stopped before READY: a `-ncmoe` fit trial at 4 ran out of CUDA memory while loading,
  and `serve.py` treated the exited server as fatal. Fixed in harness commit `8210d177`, before the re-run: a trial
  that fails to load counts as "does not fit". Voided and re-run (`S2.void-1/VOID.md`). On the re-run, `-ncmoe` 4
  loaded and peaked at 19,668 MiB against 19,586 free, so 5 was chosen.
- **Harness changes after the first lock, all committed before the measured passes they affect.**
  - A3: `--cache-ram 0` and the S1 strip rule (`97a0fb9d`).
  - A4: LLM back on the default host cache; the reply matched by its stored timings; per-pass cache figures;
    exploratory tools-off option (`9880767c`).
  - The fit-trial fix (`8210d177`).
- **benchmarks.json rows pending article; rows prepared at
  `docs/bench-results/tamanna-voice-pipeline-2026-11-24/benchmarks-rows-pending.json`** (one per arm's `-ncmoe`,
  section 5). They go into `insiderllm-hugo/static/benchmarks.json`, with `source_article` set, when the explainer
  publishes (Mark, 2026-11-24).

## Wall time

- **Locked arms.** First warm-up attempt at 15:07, re-run from 15:26, last locked arm done at 18:32. About 3 h 25 min
  in all, including the two voided attempts and the A4 work in between.
- **Per arm.** About 52–54 min per S arm (≈6 min set-up and fit, 5 min idle, 4 × ~11.6 min passes), and 25 min for
  R0.

## Files

- **Per arm, `S1/`, `S2/`, `S3/`, `R0/`:**
  - Client logs: `client-warmup.jsonl` (discarded) and `client-{1,2,3}.jsonl`.
  - Server logs: `llm.log`, `stt.log` / `stt_s2.jsonl`, `tts.jsonl`, `tts.log`.
  - Run state: `vram.csv`, `meta.json` (fit trials, warm-ups, A1 reading, command lines), `owui_config.json`
    (keys redacted), `clock.json`, `a1_check.log`.
  - Analysis: `per_clip.tsv`, `summary.json`; for the S arms also `refs.tsv`, `hyps.tsv` and the `wer_*` files
    (S1 also `hyps-unstripped.tsv` and `wer-unstripped_*`).
- **Shared:**
  - `tables.json`, from `harness/tables.py`.
  - `clips/` (the clip list and the padded FLEURS clips; Mark's audio is not here).
  - `day0/` and `install/`: install script and log, copied from Tamanna.
  - `run_all.log`.
- **Exploratory tools-off pass (A4 item 4):** `X-S1/` … `X-R0/` and `tables-exploratory.json`; see the next section.

## Exploratory, not pre-registered: Open WebUI built-in tools off (A4 item 4)

**Set-up.** Same four arms, same harness and flags, run 18:32–21:30 straight after the locked arms. The one change:
`capabilities.builtin_tools = false` on the voice-bench model, so the reply request carries no tool definitions. The
reply prompt drops from ~7,430 to ~240 tokens. `-ncmoe` came out the same (10 / 5 / 10 / 0). Open WebUI's TTS cache
was still warm from the locked arms. This is not part of the locked results.

| Arm | FLEURS E2E median, tools off (locked) | p90 | LLM TTFT | 1st TTS request | Residual | Reply tokens | FLEURS WER en / de |
|---|---|---|---|---|---|---|---|
| X-S1 | 6,223 (6,313) | 7,142 | 272 (274) | 2,337 (2,536) | 3,384 (3,396) | 22.5 (26) | 12.5 / 8.0% |
| X-S2 | 5,789 (6,199) | 7,509 | 147 (149) | 2,259 (2,684) | 3,203 (3,195) | 26 (35) | 13.7 / 16.0% |
| X-S3 | 6,062 (6,679) | 7,357 | 247 (178) | 2,329 (2,695) | 3,383 (3,415) | 24 (32) | 11.9 / 19.4% |
| X-R0 | n/a | n/a | 56 (114) | n/a | n/a | 44.5 (36) | n/a |

What it shows:
- **TTFT barely moves in the voice arms.** With the host cache on (A4), the 7.4K tool prefix was already restored
  for each reply, so removing it saves no prefill. X-S3's FLEURS TTFT median is higher (247 vs 178 ms) because its
  English and German halves sit at different levels and the pooled median falls between them. Per set it's
  unchanged: en 170 vs 173, de 260 vs 262. In X-R0, TTFT halves (56 vs 114 ms).
- **E2E drops 0.1–0.6 s**, mostly through a shorter first TTS request (0.2–0.4 s less). The replies came out shorter
  (median 22–26 tokens vs 26–35), which shortens the TTS chunk. Whether removing the tools causes that wasn't tested.
- **Residual and title call unchanged** (the title call is ~0.4–0.6 s either way).
- **Restore step.** Slot select → launch is ~115 ms per reply, against ~134 ms with the 7.4K prefix (see 4.2).
- **TTS cache.** Cache-served clips rose to 11 / 7 / 11 of 72–73 per S arm: EN real (6–10 of 15), plus 1–2 FLEURS
  clips. EN real pooled E2E is therefore not comparable with the locked arms.
- **en04 was detected once:** X-S1 pass 3, with E2E 463 ms and a negative residual (−1,476 ms). The answer audio
  started 0.46 s after the clip's speech end, quicker than the stages add up to. That doesn't fit a normal
  detection, and it wasn't investigated. It failed in the other 11 exploratory voice passes.

## After the run (2026-11-24, 21:35–21:38)

- **voice-bench tools restored.** The voice-bench model's built-in tools were set back to the locked default (on).
  The exploratory pass had set `meta.capabilities = {"builtin_tools": false}`; it's now `null`, so Open WebUI's
  default applies, the same state as the locked arms. Before and after: `post-run-voice-bench-restore.json`.
- **Everything stopped.** Open WebUI (uvicorn, running since 10:26) was stopped by PID. Afterwards no Open WebUI,
  llama-server, STT/TTS wrapper or sampler process remained on Tamanna. Ports 8443, 8080, 8091, 8092 and 8093 were
  closed, and the GPU had no compute process (1 MiB used; persistence Enabled, 420.00 W).
- **Display.** `display_active` read Disabled.

## Handling for any follow-up run (Open WebUI pitfalls found here)

Fix each of these in the pre-registration before the first warm-up:

1. **Clear Open WebUI's TTS cache before each arm.** Delete `owui-data/cache/audio/speech/*`, or decide to keep it
   and say so. `/api/v1/audio/speech` caches on sha256(text, voice, model) and the cache persists across passes,
   arms and restarts. A reply whose text was synthesised before never reaches the TTS server, so it gets no TTS time
   and a ~3.5 s E2E. In this run that hit 5–7 of 15 EN real clips per arm.
2. **Decide on Open WebUI's built-in tools.** 0.13 defaults to native function calling and adds 38 tool definitions
   (~7,400 prompt tokens) to every reply request. Set it per model with `meta.capabilities.builtin_tools`.
3. **Decide on the LLM's host prompt cache.** With `-np 1`, Open WebUI's title, follow-up and tag calls replace the
   slot's contents between clips, so only llama-server's host cache (`--cache-ram`, default 8192 MiB) keeps a shared
   prefix. `--cache-ram 0` makes every reply re-prefill the whole prompt (7.3 s with the tool prefix). The warm-up
   pass also seeds the host cache, so pass 1 behaves like later passes.
4. **Account for the title call.** Open WebUI sends title generation ~20 ms before the reply. On a single slot it
   runs first, inside the E2E window (~0.4–0.6 s here). Either keep it and report it, or turn title generation off
   and say so. Follow-up and tag generation run after the reply; the client must wait for the slot to go idle before
   the next clip.
5. **Match the reply by its stored timings.** The assistant message stores llama.cpp's `timings` as `usage`
   (`prompt_n`, `cache_n`, `prompt_ms`, `predicted_n`). Use them to find the reply task in the server log, not "the
   first task after STT", which is the title call.
6. **Check clip levels against voice mode's speech detection.** Voice mode didn't detect en04 (peak −29.6 dBFS) at
   all, and only partly heard en08 (mostly −45 to −30 dBFS). Either pick clips that Open WebUI's detection
   segments reliably, or record each clip's level and report misses as failures, as here.
7. **Expect the first TTS request to be the whole reply.** With Punctuation splitting, Open WebUI usually sent a
   short reply as one TTS request. Predictions for the first TTS request should be based on whole-reply length.
8. **Size VRAM with realistic TTS input.** The TTS process grew ~700 MiB past its three-sentence warm-up peak, so the
   fit's total went ~290 MiB over budget. Warm the TTS on reply-length text, or widen the margin.
9. **Keep the S1 prefix in mind.** llama.cpp v0.7.0's Qwen3-ASR transcription starts `language <Name><asr_text>`, and
   Open WebUI passes it to the LLM verbatim. Score WER with the A3 strip rule.
