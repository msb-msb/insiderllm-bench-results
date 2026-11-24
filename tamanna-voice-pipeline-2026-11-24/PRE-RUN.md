# Voice pipeline on one RTX 3090: day-0 record, before the first warm-up (2026-11-24)

Pre-registration: `docs/candidates/voice-pipeline-3090-2026-11.md`, lock `c7cf92cc` (sha256 `6c7608fc…2a35`),
Amendment A1 (file sha256 `711bf08d…1570`), Amendment A2 (commit `a8712dca`, file sha256
`b8d34f650fc31559bf83ca1a1bb0314c0b682258697a769390413d66e15b4b54`, public copy checked byte-identical), Amendment A3
(commit `5224a479`, file sha256 `bae91cb1…79a5`). This file
lists what was done on the run day before any warm-up or measured pass, and the harness decisions the lock leaves
open (section 8: "This lock fixes that harness's method and definitions, not its code"). Nothing here is a result.

## Checks done

- **Inputs.** Mark's 11-19 set, as locked: `q1.wav`…`q5.wav`, `questions.txt` and the five original MP3s all match
  the locked sha256s (`sha256sum -c` on both SHA256SUMS files in the private inputs folder).
- **Model working copies on Tamanna, re-hashed against LLM_repo** (section 6): 35 of 35 files match, including the
  LLM (`ac0e2c11…31a61`). `day0/llmrepo-voice.SHA256SUMS` is the list built from LLM_repo's per-folder SHA256SUMS;
  `day0/rehash.log` is the `sha256sum -c` output. No re-download.
- **FLEURS dataset in LLM_repo:** its SHA256SUMS checks out (both `test.tsv` files and both audio archives).
- **llama.cpp v0.7.0 load checks** (section 2): both the S1 (Qwen3-ASR Q8_0 + mmproj) and S3 (Granite 4.1-2B-Plus
  Q8_0 + mmproj) GGUFs load in `~/llama-v0.7.0` (620d222) and answer `/v1/audio/transcriptions`, tested on the 11-19
  TTS smoke-test audio only. No newer llama.cpp build is needed. Logs: `day0/loadcheck/`.
- **GPU (A1 item 2)**, read at 10:16 and again after the functional tests: persistence mode Enabled, power limit
  420.00 W, no compute process. The harness re-reads it before each arm's warm-up and aborts on any other value.
- **Disk:** Tamanna 69 GB free.

## Clips (A2 rule)

`harness/select_clips.py` applies A2 and asserts the A2 row lists: en_us rows 7, 23, 28, 42, 58, 60, 66, 68, 74, 80;
de_de rows 4, 8, 11, 14, 15, 16, 17, 26, 29, 30. It reproduces both exactly. Next qualifying rows (the A2 fallback
order): en_us 82, 83, 84, 86, 87; de_de 31, 34, 40, 43, 44. `clips/clips.tsv` has, per clip: source row and file,
source sha256, duration, speech-end offset, padded-copy sha256, FLEURS gender label and the reference text.

- **Format.** FLEURS audio is 16 kHz mono **32-bit float** WAV. Padded copies keep that format: the source samples,
  bit-identical, then 12 s of exact zeros (`clips/fleurs/`, in this record). Mark's clips stay 48 kHz 16-bit PCM;
  their padded copies are in the private inputs folder (`padded/`, not in git), and their sha256s are in
  `clips/clips.tsv`.
- **Speech-end offsets.** FLEURS: end of the last 10 ms frame above −40 dBFS. For en01 and en10 that is the end of
  the file (their background noise stays above −40 dBFS to the last frame), so for those two E2E is measured from
  the end of the file. EN real: clip duration − 0.500 s, as locked.
- **Speaker IDs (A2 "known cost").** FLEURS's `test.tsv` has no speaker ID column. Its columns are sentence id, file
  name, raw transcription, transcription, characters, `num_samples` and gender. The record can give the gender label
  and the sentence ids instead: **all 20 selected clips are labelled MALE**. The 10 English clips are 10 different
  sentences. The 10 German clips are 7 sentences (ids 1885, 1724 and 1674 each appear twice, read in separate
  recordings). The number of distinct speakers can't be established from the dataset.

## Harness decisions (fixed before the first warm-up)

| Decision | Why |
|---|---|
| Arm order **S1, S2, S3, R0** | The lock lists the arms but not an order; this is table order with the reference arm last. |
| STT llama-servers (S1, S3) run with `-ngl 99 -c 2048 -np 1` | At llama-server's defaults (4 slots × 65,536 context) S1 took 10.5 GB in the load check, nearly all of it KV cache for clips that use ~100–300 tokens. The lock fixes the STT models and route, not these flags. |
| STT and TTS warm-ups (3 each, section 3.1) use the 11-19 TTS smoke-test audio and 3 fixed sentences | So no measured clip is heard before the warm-up pass. |
| Fit prompt: `harness/fit_prompt.txt`, 4,048 tokens by the LLM's own tokenizer | The section 3.1 "4K-token prompt". The search starts at the value the Miu sweep predicts for the free VRAM (~464 MiB per `-ncmoe` step from 18,898 MiB at 6) and goes down while the LLM fits and up while it doesn't, so the chosen value is the smallest that fits. |
| System prompt, temperature 0.7 and `max_tokens 256` are set on an Open WebUI workspace model, `voice-bench`, based on the llama-server model | Open WebUI applies these server-side. Checked on a functional run: the llama-server slot reported temperature 0.7, `n_predict` 256. Thinking off is the server flag `--chat-template-kwargs {"enable_thinking":false}`. |
| Open WebUI settings otherwise untouched: Voice Mode defaults, `SPLIT_ON` punctuation, voice-mode prompt on, title / tag / follow-up generation on | Section 3.1 says defaults. The background generations run after each reply, so before each clip the client waits until the LLM slot is idle and the TTS log has stopped growing, each for 3 s. |
| First TTS audio = first `playing` whose source is not a `data:` URI | Clicking Voice mode makes Open WebUI play a ~10 ms silent `data:audio/wav` primer to unlock browser audio. It fires `playing` before the microphone opens; it's logged and excluded. The answer's audio arrives as a `blob:` URL. |
| Open WebUI's one-off "What's New" release-notes modal is dismissed on first sight | It covers the page after a version's first login, before the Voice mode click and outside the timed path. It was dismissed during the functional test, and the dismissal is saved server-side. |
| One fresh Chromium per clip, closed at the first `playing` | Chromium's fake capture loops the file; a fresh browser per clip restarts it from the beginning. |
| R0 inputs: the same 25 utterances, typed as text (FLEURS raw transcription; `questions.txt` for EN real) | The lock defines R0 as Open WebUI text chat with no voice but doesn't name its inputs. |
| STT server time for S1/S3 = llama-server's per-task `print_timing` total (prompt eval, which includes the audio encoder, plus decode) | The transcription response carries no `timings` object (only token usage), so the logged per-task timing is used, the same figures `timings` reports for chat. It doesn't include the server's audio-file decode. S2's wrapper figure does include its ffmpeg decode, so S2's inference-only time is reported beside it. |
| LLM time to first sentence = TTFT + first-sentence tokens × the reply's mean decode time per token | The server logs prompt and decode totals per task, not per token. First sentence = text up to the first `[.!?]` followed by whitespace (Open WebUI's punctuation split), counted with the server's `/tokenize`. |
| Server logs are matched to clips by Tamanna wall time | A Miu–Tamanna clock offset is measured at each arm's start (`clock.json`, median of 5 ssh round trips). Every duration comes from one machine's clock. |
| Open WebUI runs continuously from 10:26 under the section 3.2 command (log `owui-probe.log` on Tamanna) | Admin account `bench@example.com`, created by API. Password and token are kept on the two machines, mode 600, and are not in this record. Configuration switches per arm by API, and `owui_config.json` (keys redacted) is saved per arm. |

## Functional tests (not results)

Run on the 11-19 TTS smoke-test audio with a fixed `-ncmoe 20` (folder `FUNC1` on Tamanna, not copied here). They
checked that the chain works end to end (fake microphone → Open WebUI → STT → LLM → TTS → `blob:` audio playing),
that the R0 typed path works, and that `analyze.py` parses the logs. No number from them is reported.

## Open questions, resolved by Amendment A3 (before the first warm-up)

Amendment A3 (file sha256 `bae91cb167cb3ff79795d0058074176c0016bc9ba0e6f0541726e0986c0179a5`, commit `5224a479`,
public copy checked byte-identical) settles both questions raised here:

1. **Host prompt cache.** llama-server v0.7.0 defaults to `--cache-ram 8192`. A day-0 check on the S1 STT server
   (smoke audio only, `day0/cache-check/`) showed repeated clips evaluating 1 prompt token, against 71-84 with
   `--cache-ram 0`. A3 sets `--cache-ram 0` on the LLM server and on the S1 and S3 STT servers in every arm;
   per-slot common-prefix reuse stays at its default. `serve.py` was updated to match before the first warm-up.
2. **S1 prefix.** llama.cpp v0.7.0's transcription response for Qwen3-ASR starts `language English<asr_text>`
   (`day0/loadcheck/S1-responses.jsonl`). Whether Open WebUI passes it on to the LLM unchanged was not checked
   before the run; the S1 arm's chats show it, and the results say. A3 fixes a strip rule for S1 WER
   (`analyze.py`, `S1_PREFIX`): stripped WER is primary, unstripped WER under the locked scoring is reported beside it.

## S1.void-1 and Amendment A4 (before any measured pass)

The first S1 attempt was stopped during its discarded warm-up pass and voided (`S1.void-1/`, see `VOID.md` there).
Amendment A4 (file sha256 `81ba932a6ff203ef3d9fca27ab248d11420b0610e5e9999b072cd85a18a7d417`, commit `d8d7ba39`,
public copy checked byte-identical) followed:

- **LLM host cache.** The LLM llama-server is back on llama.cpp's default host cache; the S1/S3 STT servers keep
  `--cache-ram 0`. Reason: every reply carries Open WebUI 0.13's built-in tool definitions (38 tools, ~7,400 prompt
  tokens), and the title, follow-up and tag calls replace the single slot's contents between clips, so only the host
  cache keeps the shared prefix.
- **en04** stays a selected clip; Open WebUI's voice mode didn't detect it in S1.void-1 (no transcription request,
  90 s client timeout). It counts as a failed clip in each S arm and is reported with its level.
- **Pre-reply LLM call identified: title generation.** A logging proxy between Open WebUI and the LLM server
  (`day0/owui-request-probe/`, a typed-chat probe with the LLM only; not a result) shows, per user message: the title
  generation request, then ~20 ms later the reply request (with the 38 tool definitions), then follow-up and tag
  generation after the reply. On the single slot the title call runs before the reply, so it falls inside the
  measured E2E window (~0.6 s; reported per clip as `pre_reply_ms`).
- **Analysis fix.** `analyze.py` matches the reply task by the `timings` Open WebUI stores on the assistant message
  (prompt_n and predicted_n), and reports per reply the evaluated and cached prompt tokens and the slot-selection-to-
  launch gap (where a host-cache restore happens, outside `prompt_ms`; 133 ms on one probe reply). `client.py` now
  saves those stored timings with each clip.
- **Exploratory pass (A4 item 4, not pre-registered):** `run_arm.sh ARM X-ARM tools=off`, built-in tools off on the
  voice-bench model, after the four locked arms if time permits.
