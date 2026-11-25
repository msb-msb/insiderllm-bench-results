#!/bin/bash
# Voice pipeline install on Tamanna, no sudo. 2026-11-05.
set -euo pipefail
U=~/.local/bin/uv
V=~/voice-pipeline
mkdir -p $V/{bin,tls,src,dl,logs}
echo "== df before"; df -B1 / | tail -1
for e in owui tts ctc; do
  [ -x $V/$e/bin/python ] || $U venv -q --python 3.12 $V/$e
  $U pip install -q --python $V/$e/bin/python torch==2.13.0 --index-url https://download.pytorch.org/whl/cu130
done
$U pip install -q --python $V/owui/bin/python open-webui==0.13.0
$U pip install -q --python $V/tts/bin/python faster-qwen3-tts==0.5.4 fastapi uvicorn python-multipart
$U pip install -q --python $V/ctc/bin/python "transformers>=5.16,<6" fastapi uvicorn soundfile python-multipart
# faster-qwen3-tts examples (openai_server.py) at the release tag
[ -d $V/src/faster-qwen3-tts ] || git clone -q --depth 1 --branch v0.5.4 https://github.com/andimarafioti/faster-qwen3-tts $V/src/faster-qwen3-tts \
  || git clone -q https://github.com/andimarafioti/faster-qwen3-tts $V/src/faster-qwen3-tts
# static ffmpeg (BtbN n9.0, GPL), checksum from the release's checksums.sha256
cd $V/dl
curl -sSfLO https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/checksums.sha256
curl -sSfLO https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n9.0-latest-linux64-gpl-9.0.tar.xz
/usr/bin/grep " ffmpeg-n9.0-latest-linux64-gpl-9.0.tar.xz" checksums.sha256 | sha256sum -c -
tar -xJf ffmpeg-n9.0-latest-linux64-gpl-9.0.tar.xz
cp ffmpeg-n9.0-latest-linux64-gpl-9.0/bin/ffmpeg ffmpeg-n9.0-latest-linux64-gpl-9.0/bin/ffprobe $V/bin/
rm -rf ffmpeg-n9.0-latest-linux64-gpl-9.0
sha256sum ffmpeg-n9.0-latest-linux64-gpl-9.0.tar.xz $V/bin/ffmpeg $V/bin/ffprobe > $V/dl/SHA256SUMS
# self-signed TLS for Open WebUI on 8443
[ -f $V/tls/cert.pem ] || openssl req -x509 -newkey rsa:2048 -nodes -days 365 -subj "/CN=tamanna" \
  -addext "subjectAltName=IP:192.168.x.x,DNS:tamanna" -keyout $V/tls/key.pem -out $V/tls/cert.pem 2>/dev/null
chmod 600 $V/tls/key.pem
echo "== versions"
for e in owui tts ctc; do echo "-- $e"; $U pip list -q --python $V/$e/bin/python 2>/dev/null | /usr/bin/grep -iE "^(torch|transformers|open-webui|faster-qwen3-tts|qwen-tts-hf|fastapi|uvicorn|sentence-transformers) "; done
$V/tts/bin/python -c "import torch;print('torch',torch.__version__,'cuda',torch.version.cuda,'avail',torch.cuda.is_available(),torch.cuda.get_device_name(0))"
$V/bin/ffmpeg -hide_banner -version | head -1; $V/bin/ffmpeg -hide_banner -encoders 2>/dev/null | /usr/bin/grep -i mp3
git -C $V/src/faster-qwen3-tts describe --tags --always; git -C $V/src/faster-qwen3-tts rev-parse HEAD; ls $V/src/faster-qwen3-tts/examples | head -20
openssl x509 -in $V/tls/cert.pem -noout -subject -enddate -fingerprint -sha256
echo "== du"; du -sh $V $V/* ~/.cache/uv; echo "== df after"; df -B1 / | tail -1
