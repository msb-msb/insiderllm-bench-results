# Voice pipeline on one RTX 3090: day-0 record, before the first warm-up (2026-11-24)

Pre-registration: `docs/candidates/voice-pipeline-3090-2026-11.md`, lock `c7cf92cc` (sha256 `6c7608fc…2a35`),
Amendment A1 (file sha256 `711bf08d…1570`), Amendment A2 (commit `a8712dca`, file sha256
`b8d34f650fc31559bf83ca1a1bb0314c0b682258697a769390413d66e15b4b54`, public copy checked byte-identical). This file
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

## Open questions for Mark before the first warm-up

1. **llama-server's host prompt cache.** v0.7.0 defaults to `--cache-ram 8192` (keeps past prompts in RAM and
   restores them). Each clip is asked once per pass, so passes 2 and 3 repeat pass 1's prompts and their prefill
   could be served from cache. TTFT would then fall after pass 1. In the functional test, a repeated prompt
   evaluated only 4 new tokens. The lock's fixed flags don't mention it, and the harness as committed runs the
   defaults. Options: run as is and report TTFT per pass; or add `--cache-ram 0` to the LLM server in every arm,
   which needs your call since it's a flag outside the locked list.
2. **S1's transcript carries Qwen3-ASR's prefix.** llama.cpp v0.7.0 returns `language English<asr_text>Plants use…`.
   Open WebUI passes that verbatim to the LLM as the user's message. The run measures it as is, since that's the
   route the lock names. Pre-registered WER is computed on the text as delivered, so the prefix counts as inserted
   words. A prefix-stripped WER can be reported beside it, labelled exploratory.
