"""TTS: Qwen3-TTS-12Hz-0.6B-CustomVoice preset voice behind an OpenAI-style /v1/audio/speech (mp3 out).

Pre-registration: docs/candidates/voice-pipeline-3090-2026-11.md (section 2, TTS). faster-qwen3-tts 0.5.4's
examples/openai_server.py only serves voice cloning (generate_voice_clone + a reference WAV, Base model) and its
mp3 path needs pydub, so it cannot serve CustomVoice presets. This wrapper calls the library's
generate_custom_voice instead (Mark, 2026-11-19).

Run in the `tts` venv on Tamanna (faster-qwen3-tts 0.5.4, torch 2.13.0+cu130):
  tts/bin/python tts_customvoice_server.py --model ~/bench-models/voice-pipeline/qwen3-tts-12hz-0.6b-customvoice \
      --speaker ryan --language english --ffmpeg ~/voice-pipeline/bin/ffmpeg --port 8092 --log logs/tts.jsonl

Voice: one preset for every language, Ryan (the first English voice in the model card's speaker table; the model has
no German preset). Whatever `voice` Open WebUI sends is logged and ignored. Language: explicit, never "auto". The
Playwright harness sets it before each clip with POST /v1/voice-pipeline/language {"language": "english"|"german"},
outside the timed path. Generation uses the library defaults (sampling on, temperature 0.9, top_k 50, top_p 1.0,
repetition_penalty 1.05, non-streaming). The whole utterance is generated, then encoded to mp3 with the pinned ffmpeg
(libmp3lame, 128 kb/s, the model's 24 kHz), because Open WebUI cannot play PCM. One JSON line per request: wall-clock
receive time, then durations (ms) for generation, mp3 encoding and the whole request, plus audio length and text.
"""
import argparse, json, subprocess, threading, time

import numpy as np
import torch
import uvicorn
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

p = argparse.ArgumentParser()
p.add_argument("--model", required=True)
p.add_argument("--speaker", default="ryan")
p.add_argument("--language", default="english")
p.add_argument("--ffmpeg", required=True)
p.add_argument("--host", default="0.0.0.0")
p.add_argument("--port", type=int, default=8092)
p.add_argument("--log", required=True)
args = p.parse_args()

from faster_qwen3_tts import FasterQwen3TTS  # noqa: E402

tts = FasterQwen3TTS.from_pretrained(args.model, device="cuda", dtype=torch.bfloat16)
state = {"language": args.language}
lock = threading.Lock()
app = FastAPI()


class SpeechRequest(BaseModel):
    input: str
    model: str = "tts-1"
    voice: str = ""
    response_format: str = "mp3"
    speed: float = 1.0


class LanguageRequest(BaseModel):
    language: str


def to_mp3(audio: np.ndarray, sr: int) -> bytes:
    pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes()
    return subprocess.run([args.ffmpeg, "-v", "error", "-f", "s16le", "-ar", str(sr), "-ac", "1", "-i", "pipe:0",
                           "-c:a", "libmp3lame", "-b:a", "128k", "-f", "mp3", "pipe:1"],
                          input=pcm, capture_output=True, check=True).stdout


@app.post("/v1/audio/speech")
def speech(req: SpeechRequest):
    if not req.input.strip():
        raise HTTPException(400, "'input' is empty")
    if req.response_format.lower() != "mp3":
        raise HTTPException(400, "only mp3 is served")
    t0, wall = time.perf_counter(), time.time()
    lang = state["language"]
    with lock:
        audios, sr = tts.generate_custom_voice(text=req.input, speaker=args.speaker, language=lang)
        torch.cuda.synchronize()
    t1 = time.perf_counter()
    audio = np.asarray(audios[0], dtype=np.float32)
    mp3 = to_mp3(audio, sr)
    t2 = time.perf_counter()
    rec = {"wall_recv": wall, "voice_requested": req.voice, "speaker": args.speaker, "language": lang,
           "chars": len(req.input), "audio_s": round(len(audio) / sr, 3), "gen_ms": round((t1 - t0) * 1e3, 1),
           "mp3_ms": round((t2 - t1) * 1e3, 1), "total_ms": round((t2 - t0) * 1e3, 1), "text": req.input}
    with open(args.log, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return Response(content=mp3, media_type="audio/mpeg")


@app.post("/v1/voice-pipeline/language")
def set_language(req: LanguageRequest):
    lang = req.language.lower()
    if lang not in ("english", "german"):
        raise HTTPException(400, "language must be english or german")
    state["language"] = lang
    return {"language": lang}


@app.get("/health")
def health():
    return {"status": "ok", "speaker": args.speaker, "language": state["language"]}


if __name__ == "__main__":
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
