"""STT arm S2: Granite Speech 5.0 TurboCTC (470M CTC) behind an OpenAI-style /v1/audio/transcriptions.

Pre-registration: docs/candidates/voice-pipeline-3090-2026-11.md (section 2, arm S2). Upstream has no OpenAI
endpoint and llama.cpp support is a draft PR, so this is the ~60-line wrapper the pre-registration calls for.

Run in the `ctc` venv on Tamanna (transformers 5.22.1, torch 2.13.0+cu130):
  ctc/bin/python stt_ctc_server.py --model ~/bench-models/voice-pipeline/granite-speech-5.0-470m-turboctc \
      --ffmpeg ~/voice-pipeline/bin/ffmpeg --port 8091 --log logs/stt_s2.jsonl

Any audio container Open WebUI uploads (webm, wav, mp3, ...) is decoded with the pinned ffmpeg to 16 kHz mono
float32, the model's input rate. No language is forced (the model is multilingual CTC). Greedy CTC decoding via
model.generate, as on the model card. One JSON line per request: wall-clock receive time, then durations (ms) for
decode, inference and the whole request (receive -> response ready), plus the audio length and the text.
"""
import argparse, json, subprocess, time

import numpy as np
import torch
import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from transformers import AutoModelForCTC, AutoProcessor

p = argparse.ArgumentParser()
p.add_argument("--model", required=True)
p.add_argument("--ffmpeg", required=True)
p.add_argument("--host", default="0.0.0.0")
p.add_argument("--port", type=int, default=8091)
p.add_argument("--log", required=True)
args = p.parse_args()

processor = AutoProcessor.from_pretrained(args.model)
model = AutoModelForCTC.from_pretrained(args.model).to("cuda").eval()  # no device_map: that needs accelerate
SR = processor.feature_extractor.sampling_rate  # 16000
app = FastAPI()


def decode(data: bytes) -> np.ndarray:
    out = subprocess.run([args.ffmpeg, "-v", "error", "-i", "pipe:0", "-ac", "1", "-ar", str(SR), "-f", "f32le",
                          "pipe:1"], input=data, capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32)


@torch.inference_mode()
def transcribe(audio: np.ndarray) -> str:
    inputs = processor([audio], sampling_rate=SR, device=model.device)
    inputs.to(model.device, dtype=model.dtype)
    out = model.generate(**inputs)
    return processor.batch_decode(out, skip_special_tokens=True)[0].strip()


@app.post("/v1/audio/transcriptions")
async def transcriptions(file: UploadFile = File(...), model_name: str = Form("granite-turboctc", alias="model"),
                         response_format: str = Form("json")):
    t0, wall = time.perf_counter(), time.time()
    data = await file.read()
    t1 = time.perf_counter()
    audio = decode(data)
    t2 = time.perf_counter()
    text = transcribe(audio)
    torch.cuda.synchronize()
    t3 = time.perf_counter()
    rec = {"wall_recv": wall, "file": file.filename, "bytes": len(data), "audio_s": round(len(audio) / SR, 3),
           "read_ms": round((t1 - t0) * 1e3, 1), "decode_ms": round((t2 - t1) * 1e3, 1),
           "infer_ms": round((t3 - t2) * 1e3, 1), "total_ms": round((t3 - t0) * 1e3, 1), "text": text}
    with open(args.log, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return text if response_format == "text" else {"text": text}


@app.get("/health")
def health():
    return {"status": "ok", "model": args.model}


if __name__ == "__main__":
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
