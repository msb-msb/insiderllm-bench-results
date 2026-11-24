# Pre-registration: voice pipeline on one RTX 3090, through Open WebUI over the LAN, 2026-11

**LOCKED on commit, 2026-11-19, before any measured run. The run is on 2026-11-24.** The sha256 of this file is in
the lock commit message and in `voice-pipeline-3090-2026-11.md.sha256` next to it. Anything added later is appended
after section 8 as a dated amendment or deviation; nothing above that changes. Drafted 2026-11-05; Mark's decisions
are in section 8. Model facts were read on 2026-11-05 from the Hugging Face API (`/api/models/<repo>?blobs=true`),
the model cards and the project READMEs, and re-checked on 2026-11-19 when every file was downloaded and hash-verified
(section 6). Nothing has been measured. The only things run before the lock were functional smoke tests of the two
wrappers (section 6), with cold servers and TTS-generated audio. They showed a few VRAM and timing numbers, and the
predictions in section 4 were not changed after seeing them.

Serves dated-markers.md "Explainer candidate: a local AI lab for education", open item (a), and
`docs/candidates/school-lab-explainer-scope-2026-10.md` scope item 1 (the reader's top priority). It also closes
the two gaps the 2026-09-25 concurrency record left: Open WebUI in the path, and LAN latency.

## 1. Question

On one school box (Tamanna: RTX 3090 24 GB, Ryzen 7 5700X, 64 GB DDR4-3000), with commercially licensed models
only, how long does a student wait from the end of their spoken question to the first audio of the answer, in a
browser on another machine on the LAN, through Open WebUI? Where does the time go, and how is the 24 GB split
between speech-to-text, the LLM and text-to-speech?

## 2. Components (all commercial-use licences)

| Stage | Model | Repo @ sha (2026-11-05, re-checked 2026-11-19) | Licence | Download | Serving route |
|---|---|---|---|---:|---|
| STT, arm S1 | Qwen3-ASR-1.7B | `Qwen/Qwen3-ASR-1.7B` @ `7278e1e7` | Apache-2.0 | 4,703,114,308 B | Converted to GGUF (Q8_0 + f16 mmproj) with llama.cpp v0.7.0's converter (section 6); second `llama-server`, `/v1/audio/transcriptions`. Fallback: `qwen-asr-serve` (transformers backend) |
| STT, arm S2 | Granite Speech 5.0 TurboCTC (470M CTC) | `ibm-granite/granite-speech-5.0-470m-turboctc` @ `1dd23f46` (main moved to `91dcb060` on 2026-11-06, a README-only change; weights identical) | Apache-2.0 (**not** the `-nc` sibling) | 949,341,648 B | transformers `AutoModelForCTC` behind our own FastAPI `/v1/audio/transcriptions` wrapper, `harness/stt_ctc_server.py` (no OpenAI endpoint upstream; llama.cpp support is draft PR #29446 only) |
| STT, arm S3 | Granite Speech 4.1 2B Plus (v2610), official GGUF | `ibm-granite/granite-speech-4.1-2b-plus-GGUF` @ `39543e0c` | Apache-2.0 | Q8_0 1,737,793,312 + mmproj-f16 1,167,743,488 = 2,905,536,800 B | `llama-server` `/v1/audio/transcriptions` (mtmd granite-speech merged #22101, Plus #24818, conversion fix #30628) |
| LLM | Qwen3.6-35B-A3B UD-Q4_K_M (our measured 24 GB pick) | `unsloth/Qwen3.6-35B-A3B-GGUF`; canonical copy `LLM_repo/from-miu/bench-models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf`, 22,134,528,992 B, sha256 `ac0e2c11…31a61` (working copy already on Tamanna) | Apache-2.0 | none | `llama-server`, llama.cpp v0.7.0 (`~/llama-v0.7.0`, b11669, sm_86), thinking off |
| TTS | Qwen3-TTS-12Hz-0.6B-CustomVoice | `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice` @ `85e237c1` (bundles the 12 Hz speech tokenizer) | Apache-2.0 | 2,498,388,392 B | `faster-qwen3-tts` 0.5.4 (MIT) `generate_custom_voice`, behind our own FastAPI `/v1/audio/speech` wrapper, `harness/tts_customvoice_server.py`, mp3 out (Open WebUI cannot play PCM). The package's `examples/openai_server.py` only does voice cloning, so it can't serve presets (Mark, 2026-11-19) |
| Front end | Open WebUI v0.13.0 (2026-11-03, tag `c38885a1`) | PyPI `open-webui` | Open WebUI License: BSD-3 plus a branding clause with a 50-user threshold (quoted below) | ~2–3 GB of wheels | uvicorn with TLS in a Python 3.12 venv, port 8443 (section 3.2) |

**Open WebUI's licence, re-read 2026-11-05** from `LICENSE` in the repo at tag v0.13.0. It's byte-identical to
`main` that day (2,819 B, sha256 `5f1bd74c…a47fc232`). Clauses 1–3 are standard BSD-3. The branding clause and the
user threshold, exactly:

> 4. Notwithstanding any other provision of this License, and as a material condition of the rights granted herein,
> licensees are strictly prohibited from altering, removing, obscuring, or replacing any "Open WebUI" branding,
> including but not limited to the name, logo, or any visual, textual, or symbolic identifiers that distinguish the
> software and its interfaces, in any deployment or distribution, except in the following circumstances: (i)
> deployments or distributions where the total number of end users (defined as individual natural persons with
> direct access to the application) does not exceed fifty (50) within any rolling thirty (30) day period; (ii) the
> licensee has obtained specific prior written permission from the copyright holder; or (iii) where the licensee has
> obtained a duly executed enterprise license expressly permitting such modification. For all other cases, any
> removal or alteration of the "Open WebUI" branding shall constitute a material breach of license.

The file also says: "Materials governed by prior licenses retain those original license terms, as specified in
LICENSE_HISTORY." What this means for a school: using it unchanged, with the Open WebUI name and logo left in
place, is allowed at any number of users. The 50-user limit only applies to *removing or changing the branding*
(re-skinning it as "School AI", for example). Above 50 people with access in any rolling 30 days, that needs
written permission or an enterprise licence. A school lab passes 50 users easily, so the explainer should say:
keep the branding.

Why these choices:
- **CustomVoice, not Base.** The school wants preset voices. Base exists for voice cloning, which brings consent
  questions for minors (the same issue the Fish Audio check found) and isn't needed here.
- **S3 stays (Mark, 2026-11-05).** It is the only Granite model with a turnkey route into Open WebUI today: an
  official, signed GGUF served by llama-server's transcription endpoint. S2 is probably faster and more accurate in
  English (a 470M CTC model against a 2B autoregressive one; English Open ASR average WER 5.51 vs 6.10 on different
  test sets), but it needs our own wrapper until #29446 merges. A school admin will copy whichever has the simpler
  install, so we measure both.
- **Granite Speech 5.0 2B: noted, no arm.** `ibm-granite/granite-speech-5.0-2b` (Apache-2.0, German, official GGUF
  and ONNX repos, 2026-10-07) may supersede 4.1-2B-Plus. llama.cpp support for its architecture is unchecked, so it
  stays out of this run. It's a candidate for the follow-up.
- **Nemotron 3.5 Transcribe: dropped from this run (Mark, 2026-11-05), follow-up only.** The plan was to serve it
  through the NeMo-Speech.cpp v0.3.0 prebuilt CUDA archive, which reportedly works on 3090s (issue #61, 0.1/0.2
  archives), though nobody reports Transcribe itself there. It needs ~20 GB of VRAM and ~21 GB of disk
  (`nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B` @ `c1766764`, OpenMDW-1.1, IQ4_NL GGUF), so the LLM would sit
  almost entirely on the CPU. That makes it a separate STT-only record, not an arm of this one.
- **faster-qwen3-tts, not vLLM-Omni.** vLLM-Omni's 0.6B recipe idles at ~13.5 GiB at its defaults on a 4090 (≈5 GiB
  idle / ≈10 GiB peak at `gpu_memory_utilization 0.15`), which doesn't leave room for the LLM. llama.cpp's
  `llama-tts` handles Qwen3-TTS (#26254, #28231), but llama-server has no `/v1/audio/speech`.
- **Our own TTS wrapper (Mark, 2026-11-19).** faster-qwen3-tts 0.5.4's `examples/openai_server.py` only calls
  `generate_voice_clone` with a reference WAV (its default model is 1.7B-Base), and its mp3 path needs pydub, which
  isn't installed. The library itself has `generate_custom_voice(speaker=…)`, so a ~100-line FastAPI wrapper serves
  the CustomVoice preset, the same approach as S2. That keeps CustomVoice and avoids the cloning consent question
  above.
- **One llama.cpp build for the LLM.** v0.7.0 is the build our 2026-11-03 Tamanna rows used (162.24
  tok/s resident at d0). Check on day 0 that it also has Qwen3-ASR mtmd (#19441, conversion fix #23081),
  granite-speech Plus (#24818, #30628) and llama-server `/v1/audio/transcriptions` (#21863). If any is missing, the
  STT servers use a newer pinned llama.cpp build in a separate directory, and the LLM stays on v0.7.0.

## 3. Design

### 3.1 The VRAM budget decides the LLM's offload

The LLM fully resident takes 21,586 MiB (Tamanna v0.7.0, 2026-11-03) of the card's 24,576 MiB. STT plus TTS will
not fit beside it. So we fix the STT and TTS processes first and fit the LLM to what is left:

1. Start the STT server for the arm and the TTS server. Run 3 warm-up requests through each. Record each
   process's VRAM (nvidia-smi `--query-compute-apps`, sampled at 10 Hz) at its peak.
2. Free VRAM = 24,576 MiB − (STT peak + TTS peak) − **768 MiB margin**.
3. Choose the smallest `--n-cpu-moe` (`-ncmoe`) at which llama-server, with `-c 8192 -np 1 -fa on`, peaks below the
   free VRAM over a 4K-token prompt. Search upward from the value our Miu sweep predicts (section 4.2).
4. That `-ncmoe` is fixed for the arm. It is reported with every number.

**Reference arm R0, LLM only:** the same llama-server, fully resident (`-ncmoe 0`), with Open WebUI text chat and
no voice. This shows what the voice stages cost the LLM.

Fixed across arms: llama-server `-c 8192 -np 1 -fa on --jinja`, thinking off
(`chat_template_kwargs {"enable_thinking": false}`), temperature 0.7, `max_tokens 256`, system prompt "Answer in two
or three short sentences." Open WebUI Voice Mode defaults (Standard mode, Response Splitting = Punctuation).
No STT language hint in any arm: Open WebUI's STT language setting stays empty, and S2's wrapper forces none.

**TTS voice (Mark, 2026-11-19): `ryan` for both languages.** The rule: the first English preset in the model card's
"Supported Speakers" table (Vivian, Serena, Uncle_Fu, Dylan, Eric, **Ryan**, Aiden, Ono_Anna, Sohee). For a language
with no native preset, use that same voice. None of the nine is German (their native languages: Chinese ×5,
English ×2, Japanese, Korean), so German is also spoken by Ryan, with `language="german"`. Keeping the voice the same
means any EN/DE difference comes from the language, not the voice. The language is always set explicitly, never
"auto". The Playwright harness posts it to the TTS wrapper (`/v1/voice-pipeline/language`) before each clip, outside
the timed path. The `voice` value Open WebUI sends is logged and ignored. Generation uses the library defaults
(sampling on, temperature 0.9, top_k 50, top_p 1.0, repetition_penalty 1.05, non-streaming), and the output is mp3 at
128 kb/s, 24 kHz, encoded by the pinned ffmpeg.

Power limit 420 W (default), persistence mode on, nothing else on the GPU, 5 minutes idle before each arm. Ambient
noted.

### 3.2 Client and timing

- **Client:** Miu, on the LAN, in Chromium driven by Playwright. Chromium is launched with
  `--use-fake-ui-for-media-stream --use-fake-device-for-media-stream --use-file-for-fake-audio-capture=<clip>.wav`,
  so the microphone input is the test clip, the same every run.
- **HTTPS is required.** Browsers allow the microphone only on HTTPS or localhost. The Miu smoke test confirms
  this: on a non-HTTPS page, Playwright's Chromium has no `navigator.mediaDevices` at all. Open WebUI is served
  over TLS with a self-signed certificate made with openssl (no sudo, port 8443), and the test browser accepts it
  with `--ignore-certificate-errors`. This is also what a school would have to do, and the explainer should say
  so.
- **How it's launched.** `open-webui serve` takes only `--host` and `--port`, with no TLS options. So we run the
  same app under uvicorn with TLS. This needs two environment variables that `serve` normally sets itself:
  `FROM_INIT_PY=true`, so it finds the bundled frontend, and `WEBUI_SECRET_KEY`, from a file. Open WebUI calls a
  direct uvicorn launch "unsupported". The supported alternative is `open-webui serve` on 127.0.0.1 behind a TLS
  reverse proxy, which adds a component. We use the direct launch and record the command:
  `FROM_INIT_PY=true WEBUI_SECRET_KEY=$(cat tls/webui_secret_key) DATA_DIR=owui-data PATH=bin:$PATH
  owui/bin/uvicorn open_webui.main:app --host 0.0.0.0 --port 8443 --ssl-keyfile tls/key.pem --ssl-certfile
  tls/cert.pem --forwarded-allow-ips "*"`.
- **Clips** are padded with 12 s of trailing silence. Chromium's fake capture loops the file, and the padding stops
  the question repeating before Open WebUI detects the end of speech.
- **Timing, client side:** an init script records `performance.now()` when `getUserMedia` resolves (clip start) and
  when the first TTS audio element fires `playing`. **E2E = first `playing` − (clip start + speech-end offset)**,
  where the speech-end offset is the end of speech in the clip, set once with a −40 dBFS energy threshold.
- **Timing, server side (Tamanna's clock only, durations so no clock sync is needed):** STT request received →
  response sent; LLM request received → first token (TTFT) → first sentence boundary; first TTS request received →
  response sent. Taken from each server's request log; for the two llama-servers, from `timings` in the response.
- **Residual** = E2E − STT − LLM to first sentence − first TTS request. It holds Open WebUI's end-of-speech wait
  (documented at about 2 s of silence), browser upload and decode, and Open WebUI's own overhead. We report it as
  one number; we don't try to split it further.
- **VRAM:** per-process peak over each arm, and the total, from the 10 Hz nvidia-smi sampler.

### 3.3 Clips

- **E2E and per-stage timing:** 10 English (`en_us`) and 10 German (`de_de`) utterances from the FLEURS test split
  (CC-BY-4.0), 4–10 s of speech each. Chosen by a fixed rule before any run: the first 10 test utterances per
  language between 4 and 10 s, in file order. "File order" means row order in `data/<lang>/test.tsv`, and the length
  is the file duration, `num_samples` / 16,000. The files are `google/fleurs` @ `70bb2e84` in
  `LLM_repo/datasets/fleurs-en_us-de_de-test/`. FLEURS sentences aren't questions; with the system prompt above the LLM
  still answers in 2–3 sentences, and the reply length is logged.
- **STT accuracy (secondary):** WER on the same 20 clips against the FLEURS `raw transcription` column, plus EN real
  (below). With 10 clips per language this is a sanity check, not a leaderboard figure, and the write-up says so.
  - **Normalisers (Mark, 2026-11-19), from `openai-whisper==20250625`, applied to both reference and hypothesis.**
    English (FLEURS `en_us` and EN real) uses `EnglishTextNormalizer`. German uses `BasicTextNormalizer`, Whisper's
    own choice for languages other than English. WER is jiwer 4.0.0 over the normalised strings, per clip and
    corpus-level (all words pooled) per arm × set, from the first measured pass. Scorer: `harness/wer.py`.
  - **q3 is excluded from WER, declared here before any run (Mark, 2026-11-19).** "their, there, and they're" are
    homophones that can't be told apart from the audio. q3 stays in every timing measurement, and its transcript is
    reported verbatim.
- **Real questions (Mark, 2026-11-05): 5 short spoken English questions recorded by Mark**, the kind a student
  would ask, each answerable in 2–3 sentences. They go through the same E2E and per-stage timing as FLEURS and are
  reported as their own row ("EN real"), because FLEURS is read speech and these are how people actually talk.
  Their WER is computed against Mark's written transcript, but it is reported separately and not pooled with FLEURS
  WER. **The audio stays private (Mark, 2026-11-19).** Only the transcripts and the timings are published.
  - **Format Mark sends:** WAV, mono, 16-bit PCM, 48 kHz (anything from 16 kHz up is fine; I convert with the
    pinned ffmpeg and keep the original). A phone voice memo (m4a) works too, though WAV is preferred.
  - **Length:** 2–8 s of speech per question (changed from 3–8 s by Mark on 2026-11-19, with q1–q5 kept as
    recorded), with no more than 0.5 s of silence before the first word. Trailing
    silence doesn't matter, because we pad 12 s ourselves.
  - **Conditions:** one question per file, normal speaking pace, a quiet room, the mic at normal laptop or phone
    distance.
  - **Files:** named `q1.wav` … `q5.wav`, with a `questions.txt` holding the exact words spoken, one line per file.
  - **Received 2026-11-19, converted on Tamanna with the pinned ffmpeg (section 6, n9.0.2-47-gb204e94e90).**
    What Mark sent: 5 phone recordings, `q1.mp3` … `q5.mp3`, MP3 128 kb/s, 44.1 kHz, mono. The originals stay
    untouched in Mark's `~/Documents` on Miu. Byte-identical copies are kept in the private inputs folder's `orig/`
    (see "Where they are"). In q2 the
    last MP3 frame fails to decode ("Header missing"), and the same happens to the last frame of q5 and the last two
    of q4: 26–52 ms at the very end of the file, well after the speech ends, so those frames are lost. That's the
    usual truncated tail from a phone recorder.
    - **Conversion:** `ffmpeg -i qN.mp3 -ac 1 -ar 48000 -c:a pcm_s16le -map_metadata -1 -fflags +bitexact` gives a
      48 kHz, mono, 16-bit WAV, the format above. The 44.1 kHz source is upsampled to 48 kHz with the default
      swresample. Then a sample-exact `atrim` with the same flags.
    - **Trim rule:** speech is every 10 ms frame with RMS above −40 dBFS, the same threshold as the speech-end offset
      in section 3.2. Above-threshold runs that sit entirely inside the first or last 0.25 s of the file are the
      recorder's start and stop transients (a ~−42 dB bump at 0.15–0.25 s and the stop-tap click in the last
      ≤ 0.17 s), so they're ignored. Each end keeps at most 0.5 s of silence before the first and after the last
      speech frame; only silence beyond that is cut. Script `bounds.py`; sample bounds in `bounds.tsv`.
    - **Result:** every clip has exactly 0.500 s of silence before its first and after its last speech frame. So the
      speech-end offset, for the timing in section 3.2, is clip duration − 0.500 s.

      | File | Clip duration (s) | Speech (s) | sha256 |
      |---|---:|---:|---|
      | `q1.wav` | 3.610 | 2.610 | `9444870f47fed9ede9a0e95f087eda95c65ded245d692f393d12effb049521e8` |
      | `q2.wav` | 3.090 | 2.090 | `fe3a8e29b34b0b36284dbdf9c19566c24b7d08fa3ac63c693560ca3924f2ce2f` |
      | `q3.wav` | 4.310 | 3.310 | `d35b7088cf1aebaf2e0bc725d385ce3ef6995d363b3420d04199a48b24c80414` |
      | `q4.wav` | 5.480 | 4.480 | `c9027862707ba12f5f884c68fe28b6eed8a76b216c5f539ffd8417512a9fd461` |
      | `q5.wav` | 6.090 | 5.090 | `9445d643a50c93b7b8d5a774d4dc9572a5ca20bf104c0d29ebd312214da7beaa` |
      | `questions.txt` (5 lines, LF) | | | `599c479dcce81fa4bc719c18d6d79493b3c9e466b162a3329628fb230297ebac` |

      Original MP3 sha256s: q1 `8da80a28…83bc40`, q2 `351e2b13…d383b2`, q3 `531d7ba0…d09cd7`, q4 `0ec491dc…04436f`,
      q5 `f098cd15…1a71d`. Full hashes are in `orig/SHA256SUMS`.
    - **Length check:** all five clips are 3.09–6.09 s long, and all five have 2.09–5.09 s of speech, inside the
      2–8 s spec. q1 (2.61 s) and q2 (2.09 s) are the reason the spec moved from 3–8 s.
    - **Where they are:** private, in `docs/candidates/voice-pipeline-3090-2026-11-inputs/` (the WAVs,
      `questions.txt`, `SHA256SUMS`, `orig/`, `bounds.py`, `bounds.tsv`). Not under `docs/bench-results/`, because
      every git-tracked file there goes to the public mirror. Working copies, hash-checked: Miu (the client, which
      plays them through Chromium's fake capture) `~/voice-pipeline-client/clips/real/`, and Tamanna
      `~/voice-pipeline/clips/real/`, where they were converted. The run itself doesn't need them on Tamanna. The 12 s
      trailing-silence padding (section 3.2) is applied on the day to copies, never to these files. The audio (`*.wav`,
      `orig/*.mp3`) is not committed to git, even to this private repo, because that would put Mark's voice on GitHub;
      a `.gitignore` in the folder keeps it out. The hashes, `questions.txt`, `bounds.py` and `bounds.tsv` are committed.
- Each arm: 1 discarded warm-up pass over all 25 clips (20 FLEURS + 5 real), then 3 measured passes. Report the
  median and p90 per language, and for EN real separately.

## 4. Arms and predictions (set before any number exists)

A prediction **holds** if the arm's median lands inside the band.

### 4.1 STT stage alone (per clip of 4–10 s, server time)

| Arm | Process VRAM peak | STT time per clip, median | WER, EN / DE (sanity only) |
|---|---|---|---|
| S1 Qwen3-ASR-1.7B, Q8_0 GGUF via llama-server | 2.5–4.5 GB | 150–600 ms | EN 2–8% / DE 3–10% |
| S2 Granite 5.0 TurboCTC, transformers | 1.5–3.5 GB | 30–200 ms | EN 2–8% / DE 4–14% |
| S3 Granite 4.1-2B-Plus Q8_0 GGUF via llama-server | 3.0–5.0 GB | 200–800 ms | EN 2–9% / DE 4–12% |

S2 faster than S1 and S3 on every clip length: predicted. Nobody publishes 3090 figures for any of the three, so
these bands are wide on purpose.

### 4.2 LLM fit and speed

- Free VRAM after STT + TTS + margin: 15.5–19 GB, depending on the STT arm.
- Chosen `-ncmoe`: **6–14**. From the Miu sweep (b10088, DDR4-2667): `-ncmoe` 6 → 18,898 MiB, 8 → 17,970 MiB,
  16 → 14,260 MiB at small context; `-c 8192` adds KV on top.
- Decode at the chosen `-ncmoe`: **80–125 tok/s**. Miu measured 106.56 (ncmoe 6), 94.54 (8) and 66.96 (16) at
  DDR4-2667. Tamanna at DDR4-3000 ran ncmoe 20 at 69.3 tok/s (v0.7.0, 2026-11-03), about 15% above where Miu's
  curve would put ncmoe 20, so Tamanna should sit above Miu at the same `-ncmoe`.
- LLM TTFT (Open WebUI prompt, ~300–600 tokens): **150–500 ms** in the voice arms; **80–250 ms** in R0.
- LLM time to first sentence boundary (TTFT + ~15–30 tokens): **350–900 ms**.

### 4.3 TTS stage and end to end

- TTS process VRAM peak: **2.5–5.0 GB**.
- First TTS request (one sentence, mp3, non-streamed): **400–1,500 ms**. faster-qwen3-tts reports TTFA 156 ms and
  4.78× real time on a 4090 with CUDA graphs; a whole first sentence of ~2–4 s of audio, on a 3090, through mp3
  encoding, is the request we time.
- Residual (end-of-speech wait + browser + Open WebUI): **1.8–3.0 s**, the same across arms within ±0.3 s.
- **E2E, speech end → first audio, median:** S1 **3.0–5.5 s**; S2 **2.8–5.0 s**; S3 **3.0–5.5 s**. Without the
  residual (the part we control): **1.0–2.8 s**.
- German vs English E2E: within ±20%. German WER higher than English in all three arms.
- EN real vs EN FLEURS E2E: within ±25%. Real questions are shorter and less fluent, and the replies are
  probably longer. Reply length is logged so we can tell those effects apart.
- Total VRAM peak: ≤ 23.8 GB by construction. If an arm cannot fit with `-ncmoe` ≤ 24, that is the result: we
  record it and don't relax the margin.
- p90 E2E within 1.5 s of the median in every arm.

### 4.4 O1 (Nemotron 3.5 Transcribe): dropped from this run

Mark, 2026-11-05: follow-up only (see section 2). No predictions are set for it here.

## 5. What gets written down

`docs/bench-results/tamanna-voice-pipeline-2026-11-24/`: the lock hash, every command line, versions and shas of
every model file (hashed on the day against LLM_repo), per-request server logs, the Playwright timing log, the
nvidia-smi sampler CSV, the clip list with speech-end offsets, WER per clip, and a README with the tables in
section 4 filled in. benchmarks.json rows only for the LLM fit (one row per arm's `-ncmoe`), with
`display_attached false` and the DDR4-3000 note.

Committed with this lock, in `harness/`:

| File | sha256 |
|---|---|
| `stt_ctc_server.py` (S2 wrapper) | `68ad583dcc564211d4f7b5f609330ef47256af87dfa6554ccdfeee31f82b1871` |
| `tts_customvoice_server.py` (TTS wrapper) | `41940d2f90b1cb97119fd5500338075cd8272e318a797f093328fbb7a7828638` |
| `wer.py` (WER scorer) | `1723893fd52856558891514692c5485791804e94acd97b45b7984585ebfc4575` |

The `harness/env/` folder holds `uv pip freeze` output for the Tamanna `tts`, `ctc` and `convert` venvs and the
Miu client venv. That folder is published through the mirror. **The audio isn't**, whether Mark's recordings or any
copy of them: it stays in `docs/candidates/voice-pipeline-3090-2026-11-inputs/` (private) and in the working copies.
Per-request logs in this record will contain the EN real transcripts and the STT hypotheses, which is allowed. They
must never contain audio.

## 6. Install list

**Installed 2026-11-05, 20:47–20:52 PST, no sudo** (script `~/vp_install.sh`, log `~/vp_install.log` on Tamanna;
both get copied into the record). Before that, none of it was present: no Open WebUI, no ffmpeg, no docker, and the
system Python was 3.14.4, which Open WebUI doesn't support.

**On Tamanna, under `~/voice-pipeline/`:**
- **Python:** uv 0.13.0 (already in `~/.local/bin`) with its managed CPython 3.12.15 (already in
  `~/.local/share/uv/python`, so not the voice-01 copy). All three venvs use it.
- **torch 2.13.0+cu130 in every venv, not the cu124 build planned earlier.** That exact wheel was already in
  Tamanna's uv cache, and uv hardlinks it, so the three venvs share one copy on disk. The driver is 580.178.04
  (CUDA 13.0), and faster-qwen3-tts asks only for `torch>=2.5.1`. In the tts venv, `torch.cuda.is_available()`
  is True on the RTX 3090.
- **`owui`:** open-webui 0.13.0, which pins transformers 5.5.4 and sentence-transformers 5.5.1.
- **`tts`:** faster-qwen3-tts 0.5.4 (pulls qwen-tts-hf 0.1.1.post1), plus fastapi 0.162.0, uvicorn 0.54.0 and
  python-multipart. Its repo at tag v0.5.4, commit `1094aabd83b367b1b29942769141b0524bed245d`, is in
  `src/faster-qwen3-tts`. **transformers was pinned down from 5.22.1 to 5.16.1 on 2026-11-19.** The smoke test found
  that qwen-tts-hf 0.1.1.post1 (which allows transformers ≥5.15.1,<6) can't load the model on newer versions. On
  5.21.x–5.22.x it fails with `property 'upsample' of 'Qwen3TTSTokenizerV2Encoder' object has no setter`; on
  5.17.0–5.20.2 it fails with `'MimiConfig' object has no attribute 'rope_theta'`. 5.16.1 is the newest version that
  loads and generates (5.15.1 works too). torchaudio is 2.11.1 (the newest release; nothing is built for torch 2.13).
- **`ctc`:** transformers 5.22.1 (meets ≥5.16), fastapi, uvicorn, soundfile and python-multipart. **torchaudio 2.11.1
  added on 2026-11-19** with `--no-deps`, which leaves torch untouched. `GraniteSpeech5FeatureExtractor` needs it,
  and the smoke test failed without it.
- **`convert`** (added 2026-11-19, used only to make S1's GGUF): built from llama.cpp v0.7.0's
  `requirements/requirements-convert_hf_to_gguf.txt` (torch 2.11.0+cpu, transformers 4.57.6, sentencepiece 0.2.3,
  numpy 2.2.6). It's kept apart so the arms' venvs stay unchanged. It also pulled regex 2026.11.19, released a day
  earlier; that only matters for the conversion, which is already done and hashed.
- **Wrapper smoke test, 2026-11-19 (functional only; no clips from section 3.3 touched, no numbers recorded):** both
  wrappers started on the 3090. TTS (Ryan) made one English and one German sentence as mp3, and S2 transcribed both
  back word for word. Script `~/voice-pipeline/smoke-2026-11-19.sh`.
- **ffmpeg + ffprobe** in `bin/`: the static BtbN build `ffmpeg-n9.0-latest-linux64-gpl-9.0.tar.xz`
  (n9.0.2-47-gb204e94e90-20261105, GPL). Its sha256 checked out against the release's `checksums.sha256`, and the
  hashes of the tarball and both binaries are in `dl/SHA256SUMS`. It has the libmp3lame encoder.
- **TLS** in `tls/`: a self-signed RSA-2048 certificate, CN `tamanna`, SAN Tamanna's LAN address and `DNS:tamanna`, valid to
  2027-11-06. SHA-256 fingerprint `3A:0E:57:E7:…:3A:96:4B:C9`. Also `webui_secret_key` (mode 600).
- **Open WebUI smoke test, 20:53–20:55 PST:** launched with the section 3.2 command. `/health` returned `{"status":
  true}` over HTTPS from Miu about 75 s after start, `/api/version` returned 0.13.0, and `/` returned 200. Then I
  stopped it, with no account created. **On first start it downloads `sentence-transformers/all-MiniLM-L6-v2` @
  `1110a243` from Hugging Face, 887 MB as a full repo snapshot, for its document-search embeddings.** A school
  installing offline has to pre-seed that cache or change the embedding setting. The explainer should say so.
- **llama.cpp v0.7.0** (`~/llama-v0.7.0`, commit 620d222, a shallow clone, so PRs can't be checked by number). From
  the source: the server has `/v1/audio/transcriptions`, mtmd has the Qwen3-ASR projector (`qwen3a`) and
  `models/granite-speech.cpp`. Whether it loads the 4.1-2B-**Plus** GGUF is checked on day 0, by loading it. If
  that fails, the STT servers get a newer pinned build in a separate directory, as section 2 says.
- **Not installed:** `qwen-asr` (only the fallback if S1's GGUF route fails) and NeMo-Speech.cpp (O1 dropped).
- **Disk:** the installs plus Open WebUI's first-start download took Tamanna from 24.6 GB to 15 GB free.

**On Miu (the client), `~/voice-pipeline-client/.venv`:** uv-managed Python 3.12, playwright 1.64.1 with its own
Chromium 156.0.8078.4 (`~/.cache/ms-playwright`, 681 MB; this avoids the snap Chromium's /tmp restriction), jiwer
4.0.0, soundfile and numpy. The launch smoke test passed. **Added 2026-11-19:** `openai-whisper==20250625`, installed
with `--no-deps`, plus `regex==2026.11.7` and `more-itertools==11.2.1`. `wer.py` loads only `whisper.normalizers`, so
torch is never needed there. Mark's own browser is the manual check: one English and one German question by voice
from another machine, judged by ear, after the timed runs.

**Downloads, done 2026-11-19.** All 46 files (11.92 GB) were downloaded on Tamanna, where HF pulls run at 12–13 MiB/s
against Miu's ~2 MiB/s, and its disk now has room. Files over 64 MB came in 8 ranged curl segments. Each file was
checked against its Hugging Face LFS sha256 oid (weights, archives) or its git blob sha1 (small files) at the pinned
revision: 46/46 match. They were then rsynced into LLM_repo, re-checked there (46/46), and given a README and
SHA256SUMS per folder. Script, manifest and log: `LLM_repo/voice-pipeline-dl-2026-11-19.{sh,manifest.psv,log}`.
Tamanna's working copies, in `~/bench-models/voice-pipeline/` (8.6 GB), were copied from LLM_repo and pass
`sha256sum -c` against each folder's SHA256SUMS. The ASR safetensors and FLEURS stay on Miu only.

| What | Bytes | sha256 of the main files | In LLM_repo |
|---|---:|---|---|
| Qwen3-ASR-1.7B safetensors @ `7278e1e7` | 4,703,114,308 | shards `a4cd1f1a…08d6`, `6e0b9d9e…ccfc` | `qwen3-asr-1.7b/` |
| Its GGUF conversion, made on Tamanna with llama.cpp v0.7.0 (620d222) `convert_hf_to_gguf.py` in the `convert` venv: `--outtype q8_0`, and `--mmproj --outtype f16` | 2,165,035,040 + 641,774,112 = 2,806,809,152 | Q8_0 `44f5f919de1852120bae01cae1f2e96c8adfad40096cbef006e58befa1bbbe33`, mmproj `9910d2cbba7ad7fe0fd64493a0a2a90aeceee65b28a9ae7f7e19195b0edf43b4` | `qwen3-asr-1.7b-gguf/` (with `convert.log`, venv freeze) |
| Granite 5.0 TurboCTC @ `1dd23f46` | 949,339,712 (every file except .gitattributes) | model.safetensors `5b569c37…` (LFS oid) | `granite-speech-5.0-470m-turboctc/` |
| Granite 4.1-2B-Plus GGUF @ `39543e0c`, Q8_0 + mmproj-f16 (+ their .sig) | 2,905,536,800 | Q8_0 `71f93e9912e63ecf4e1b302af2bf5730a5f9945ae584982c2f7343494c1e08a2`, mmproj `50a504753e9c5365f1f2e0257585b8c825d56db2cb0bec94e403e0b10999708f` | `granite-speech-4.1-2b-plus-gguf/` |
| Qwen3-TTS-12Hz-0.6B-CustomVoice @ `85e237c1` | 2,498,388,392 | model `bc3c7e785eb961179c25450d1acff03f839e0002f2f3a5aeb67b5735c0fa2adb`, speech tokenizer `836b7b357f5ea43e889936a3709af68dfe3751881acefe4ecf0dbd30ba571258` | `qwen3-tts-12hz-0.6b-customvoice/` |
| FLEURS `google/fleurs` @ `70bb2e84`: `data/{en_us,de_de}/test.tsv` + `audio/test.tar.gz` (CC-BY-4.0) | 859,513,321 | archives = LFS oids `d9c2e37b…` (en_us), `e86b42df…` (de_de) | `datasets/fleurs-en_us-de_de-test/` |

Full per-file hashes are in each folder's SHA256SUMS. On the day, the record re-hashes the working copies against
those files.

**Needs Mark's sudo: nothing.** Everything above went in without it: ufw is disabled on Tamanna, ports above 1024
need no privilege, and ffmpeg is a static build.

## 7. Disk

Tamanna's root is 468 GB. It had **15 GB free after the installs** (23–24.6 GB before them). On 2026-11-19 it had
47 GB free before the downloads and **37 GB after** the 8.6 GB of working copies and the `convert` venv. On 2026-11-05 every file in `~/bench-models` was hashed
and checked against LLM_repo: the recorded sha256s, plus a fresh re-hash of each matching store copy (all 15
store copies still match their records). 12 working copies, 164.1 GB, are verified exact duplicates of LLM_repo
files. Mark has the `rm` list; nothing is deleted. `Qwen3.6-35B-A3B-UD-Q4_K_M.gguf` is also an exact duplicate, but
it's this run's LLM, so it stays. Deleting is Mark's call; this draft deletes nothing.

## 8. Decisions (Mark, 2026-11-05 and 2026-11-19)

Decided:
1. Arms: S1, S2, S3 all kept. Granite Speech 5.0 2B is noted, with no arm (section 2).
2. O1 (Nemotron 3.5 Transcribe): dropped from this run, follow-up only.
3. Clips: FLEURS `en_us` + `de_de` for WER and timing, plus 5 real English questions recorded by Mark (section 3.3).
4. Open WebUI licence: re-read and quoted (section 2). Unmodified use has no user limit; changing the branding
   needs ≤ 50 users per rolling 30 days, written permission, or an enterprise licence.
5. Install everything without sudo: done (section 6).

2026-11-19:
6. Real-question length spec changed to 2–8 s of speech. q1–q5 kept as recorded (section 3.3).
7. TTS voice: Ryan for English and for German, by the rule in section 3.1. The model has no German preset.
8. TTS served by our own CustomVoice wrapper, since the stock example server only clones voices (section 2).
9. WER normalisers: `openai-whisper==20250625`, `EnglishTextNormalizer` for English and `BasicTextNormalizer` for
   German, on reference and hypothesis. q3 is excluded from WER by pre-declaration and stays in all timing
   (section 3.3).
10. Mark's audio stays private: only transcripts and timings are published.
11. Run date: 2026-11-24. No measured run before then.
12. No LAN addresses in this document; machines are named.

Done before locking (2026-11-19): recordings converted and hashed (section 3.3), all downloads verified in LLM_repo
and on Tamanna (section 6), S1 GGUF converted, both wrappers and the WER scorer written, smoke-tested and hashed
(section 5).

Left for day 0 (2026-11-24), as already specified above: the llama.cpp v0.7.0 load checks for the S1 and S3 GGUFs
(section 2), the FLEURS clip selection by the fixed rule (section 3.3), and the Playwright timing harness that applies
section 3.2. This lock fixes that harness's method and definitions, not its code. The harness's code and the 12 s
padded copies of the clips go into the record before the first warm-up pass.

## Amendment A1 (2026-11-23, Mark): interrupted arms, and a pre-run GPU check

**Written 2026-11-23, the day before the run, before any warm-up or measured pass.** Nothing has been measured. Why:
a power outage on 2026-11-23 (about 09:17 PT) rebooted Tamanna, and the reboot turned GPU persistence mode off. The
lock above has no rule for an interrupted run and no check that the GPU settings in section 3 still hold.

1. **Interrupted arms.** An arm interrupted mid-pass (power loss, crash, OOM) is voided and re-run once from its
   discarded warm-up; a second interruption voids that arm, reported as void.
2. **Pre-run GPU check.** Before the first warm-up pass, and again before any re-run under item 1, the harness reads
   `nvidia-smi --query-gpu=persistence_mode,power.limit --format=csv,noheader` on Tamanna. If persistence mode is not
   Enabled or the power limit is not 420.00 W, the run aborts before that arm, and the reading goes into the record.
3. **Persistence on Tamanna** is set by a systemd drop-in since 2026-11-23:
   `/etc/systemd/system/nvidia-persistenced.service.d/persistence.conf` replaces the stock
   `--no-persistence-mode` ExecStart with `--persistence-mode` and sets `StopWhenUnneeded=false`, and the unit is
   wanted by `multi-user.target`. Verified on 2026-11-23 with `systemctl cat nvidia-persistenced` (the drop-in is
   loaded) and nvidia-smi (Enabled, 420.00 W). Item 2 still runs; the drop-in makes an abort unlikely, not impossible.

### Amendment A2 (2026-11-24, before any run, pre-results)

**Why.** Applying the locked FLEURS rule on the run day showed that it conflicts with the locked −40 dBFS speech-end threshold on English. Of 359 en_us test rows of 4-10 s, only 83 (23%) have any 10 ms frame above −40 dBFS (median peak ~−50 dBFS). Nine of the first ten selected English rows never cross the threshold, so no speech-end point can be found and end-to-end latency can't be measured. One selected clip peaks at −53 dBFS, close to Open WebUI's −55 dB voice-activity floor. German is unaffected: all 313 qualifying de_de rows cross −40 dBFS. Mark's q1-q5 sit around −15 to −18 dBFS.

**Change.** FLEURS selection, both languages: "the first 10 test rows per language between 4 and 10 s **that contain at least one 10 ms frame above −40 dBFS**." No audio is altered. The −40 dBFS threshold and every other method detail are unchanged.

**Resulting sets** (recorded here before the run): en_us rows 7, 23, 28, 42, 58, 60, 66, 68, 74, 80; de_de rows 4, 8, 11, 14, 15, 16, 17, 26, 29, 30 (identical to the original rule).

**Known cost, reported with the results.** English is drawn from the loudest ~quarter of FLEURS en_us test clips. The record lists each selected clip's FLEURS speaker ID and the number of distinct speakers, and states that the English latency results may not carry over to quiet input. The low level of FLEURS en_us audio is reported as a finding in its own right.

**Fallback.** If a selected clip still yields no speech-end point at run time, it is voided (logged with the reason) and replaced by the next qualifying row in order. The replacement is listed in the record.

### Amendment A3 (2026-11-24, before any warm-up or measured pass, pre-results)

#### 1. Host prompt cache off

**Change.** The LLM llama-server gets `--cache-ram 0` in every arm (S1, S2, S3, R0), and so do the S1 and S3 STT
llama-servers. Per-slot common-prefix reuse (`cache_prompt`) stays at llama.cpp's default.

**Why.** llama.cpp v0.7.0 defaults to `--cache-ram 8192`: it keeps past prompts in host RAM and restores them. Each
clip is asked once per pass, so passes 2 and 3 repeat pass 1's prompts exactly. In the functional test a repeated LLM
prompt evaluated 4 new tokens. A day-0 check on the S1 STT server (11-19 smoke audio, sequence en, de, en, de)
evaluated 80, 84, 1, 1 prompt tokens with the default, and 80, 84, 71, 84 with `--cache-ram 0` (logs in
`docs/bench-results/tamanna-voice-pipeline-2026-11-24/day0/cache-check/`). A cached prompt makes time to first
token, and STT time, unrepresentative of real use, where nobody repeats a question word for word. Common-prefix reuse within a slot (system prompt, chat template, the audio
prompt's fixed head) is what a real deployment gets, so it stays.

**Record.** The exact server command lines (LLM, STT, TTS) are written per arm to `meta.json` and to the first line
of each server log, and are reproduced in the record.

#### 2. S1 transcript prefix

**Finding.** With llama.cpp v0.7.0, Qwen3-ASR's transcription response carries the model's language tag before the
text. The two S1 outputs from the day-0 load check (11-19 smoke audio, `day0/loadcheck/S1-responses.jsonl` in the
same record), and again from the cache check, are:

    language English<asr_text>Plants use sunlight to turn water and air into food.
    language German<asr_text>Pflanzen nutzen Sonnenlicht, um aus Wasser und Luft Nahrung zu machen.

**Strip rule (S1 only, applied to each hypothesis before `wer.py`, nothing else changed):**

    re.sub(r"^\s*language [A-Za-z]+<asr_text>", "", hyp, count=1)

That is: at the start of the string, optional whitespace, the literal `language `, one or more ASCII letters, the
literal `<asr_text>`; removed once. A hypothesis without that prefix at its start is left unchanged. Applied to the
two outputs above:

    Plants use sunlight to turn water and air into food.
    Pflanzen nutzen Sonnenlicht, um aus Wasser und Luft Nahrung zu machen.

**Primary S1 WER** is computed on the stripped hypotheses. The WER under the locked scoring on the hypotheses as
delivered (prefix included) is reported beside it, labelled "unstripped, locked scoring". The hypothesis is whatever
Open WebUI delivered as the user turn; the record states, from the S1 arm's chats, whether the prefix reached the
LLM. Latency is measured on the pipeline as is; the strip rule touches WER only.

#### 3. Limitations (reported with the results; not method changes)

- FLEURS publishes no speaker IDs (`test.tsv` columns: id, file, raw and normalised transcription, characters,
  `num_samples`, gender), so the record gives FLEURS sentence IDs and gender labels instead of A2's speaker count.
- All 20 selected FLEURS clips are labelled MALE.
- The 10 de_de clips cover 7 distinct sentences (ids 1885, 1724 and 1674 each appear twice, in separate recordings).
  The 10 en_us clips are 10 distinct sentences.
- For en01 and en10 the last 10 ms frame above −40 dBFS is the last frame of the file (background noise), so their
  speech-end offset is the end of the file.
- Clicking Voice mode makes Open WebUI play a ~10 ms silent `data:audio/wav` primer. By rule, a `playing` event whose
  source is a `data:` URI is logged and ignored; first TTS audio is the first `playing` from any other source.
