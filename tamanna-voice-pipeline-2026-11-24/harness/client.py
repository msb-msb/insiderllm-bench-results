"""Miu-side Playwright client for the voice-pipeline run (pre-registration section 3.2; amendments A1-A4).

One fresh Chromium per clip, launched with
  --use-fake-ui-for-media-stream --use-fake-device-for-media-stream --use-file-for-fake-audio-capture=<padded clip>
  --ignore-certificate-errors
so the microphone is the 12 s-padded test clip. An init script stamps performance.now() when the first audio
getUserMedia resolves (clip start) and when a media element first fires `playing` with a source that is not a data:
URI (first TTS audio). Open WebUI plays a ~10 ms silent data:audio/wav primer when Voice mode is clicked, to unlock
browser audio; that event is logged and excluded.
  E2E = first playing - (clip start + speech-end offset)        [speech-end offset from clips.tsv]
The page is https://tamanna:8443/?models=voice-bench; the harness clicks Open WebUI's "Voice mode" button and waits.
The browser closes as soon as the first `playing` is seen. Before each clip the client waits until the LLM server
reports no slot processing and the TTS wrapper's log has stopped growing, each for 3 s (Open WebUI's title, tag and
follow-up generation run in the background after a reply and would otherwise queue in front of the next clip). It then
posts the clip's language to the TTS wrapper (section 3.1), outside the timed path. After the clip it reads the chat
back from Open WebUI's API (the user turn is the STT transcript as delivered; the assistant turn is the reply) and
counts the reply's first-sentence tokens with the LLM server's /tokenize, for the time-to-first-sentence figure.

R0 (text chat, no voice): the same 25 utterances are typed as text (the FLEURS raw transcription, or the questions.txt
line for EN real) into the chat box and sent with Enter; only server-side LLM timing is used.

Usage: client.py ARM PASS clips.tsv CLIPDIR OUTDIR [--tamanna-dir NAME] [--only clip_id,...]
  PASS: warmup | 1 | 2 | 3   (warmup is discarded). Appends one JSON line per clip to OUTDIR/client-<PASS>.jsonl.
"""
import argparse, asyncio, csv, json, pathlib, re, ssl, subprocess, time, urllib.request

from playwright.async_api import async_playwright

ap = argparse.ArgumentParser()
ap.add_argument("arm"); ap.add_argument("pass_"); ap.add_argument("clips"); ap.add_argument("clipdir"); ap.add_argument("outdir")
ap.add_argument("--tamanna-dir", default=None)
ap.add_argument("--only", default=None)
ap.add_argument("--host", default="tamanna")
ap.add_argument("--token", default=str(pathlib.Path.home() / "voice-pipeline-client/owui-admin.token"))
a = ap.parse_args()
H = a.host
OWUI = f"https://{H}:8443"
TDIR = f"voice-pipeline/run-2026-11-24/{a.tamanna_dir or a.arm}"
TOKEN = pathlib.Path(a.token).read_text().strip()
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
SSH = ["ssh", "-o", "ControlMaster=auto", "-o", "ControlPath=~/.ssh/cm-vp-%r@%h:%p", "-o", "ControlPersist=900", H]
OUT = pathlib.Path(a.outdir); OUT.mkdir(parents=True, exist_ok=True)
LOG = OUT / f"client-{a.pass_}.jsonl"

INIT_JS = """
window.__vp = {gum: null, playing: []};
(() => {
  const md = navigator.mediaDevices;
  if (md && md.getUserMedia) {
    const og = md.getUserMedia.bind(md);
    md.getUserMedia = async (c) => {
      const s = await og(c);
      if (c && c.audio && window.__vp.gum === null) window.__vp.gum = performance.now();
      return s;
    };
  }
  const op = HTMLMediaElement.prototype.play;
  HTMLMediaElement.prototype.play = function () {
    if (!this.__vpL) {
      this.__vpL = 1;
      this.addEventListener('playing', () => window.__vp.playing.push([performance.now(), 'el', String(this.currentSrc || this.src).slice(0, 40)]));
    }
    return op.apply(this, arguments);
  };
  document.addEventListener('playing', (e) => window.__vp.playing.push([performance.now(), 'doc', String(e.target.currentSrc || e.target.src).slice(0, 40)]), true);
})();
"""


def http(url, data=None, timeout=30, auth=False):
    h = {"Content-Type": "application/json"}
    if auth:
        h["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None, headers=h)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX if url.startswith("https") else None) as r:
        return json.loads(r.read())


def tts_log_size():
    r = subprocess.run(SSH + [f"stat -c %s {TDIR}/tts.jsonl 2>/dev/null || echo 0"], capture_output=True, text=True)
    return int((r.stdout.strip() or "0").split()[-1])


def wait_idle(voice, cap=180):
    """LLM slot idle and TTS log unchanged, both for 3 consecutive seconds."""
    t0, stable, last = time.time(), 0, None
    while time.time() - t0 < cap:
        busy = any(s.get("is_processing") for s in http(f"http://{H}:8080/slots"))
        size = tts_log_size() if voice else 0
        stable = stable + 1 if (not busy and size == last) else 0
        last = size
        if stable >= 3:
            return round(time.time() - t0, 1)
        time.sleep(1)
    raise RuntimeError("server did not go idle within cap")


SENT_END = re.compile(r"(?<=[.!?])\s+")  # Open WebUI's punctuation splitting, first boundary


def first_sentence(text):
    parts = SENT_END.split(text.strip(), maxsplit=1)
    return parts[0] if parts else ""


def chat_turns(chat_id):
    c = http(f"{OWUI}/api/v1/chats/{chat_id}", auth=True)
    msgs = c["chat"].get("history", {}).get("messages", {})
    user = [m for m in msgs.values() if m.get("role") == "user"]
    asst = [m for m in msgs.values() if m.get("role") == "assistant"]
    user.sort(key=lambda m: m.get("timestamp", 0)); asst.sort(key=lambda m: m.get("timestamp", 0))
    return user, asst


async def one_clip(pw, row, clipdir):
    voice = a.arm != "R0"
    rec = {"arm": a.arm, "pass": a.pass_, "clip_id": row["clip_id"], "set": row["set"], "language": row["language"],
           "speech_end_s": float(row["speech_end_s"])}
    rec["idle_wait_s"] = wait_idle(voice)
    if voice:
        http(f"http://{H}:8092/v1/voice-pipeline/language", {"language": row["language"]})
    sub = "fleurs" if row["set"].startswith("fleurs") else "real"
    args = ["--ignore-certificate-errors"]
    if voice:
        args += ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
                 f"--use-file-for-fake-audio-capture={pathlib.Path(clipdir) / sub / (row['clip_id'] + '.wav')}"]
    b = await pw.chromium.launch(args=args)
    try:
        ctx = await b.new_context(ignore_https_errors=True, viewport={"width": 1280, "height": 900})
        await ctx.add_init_script(f"localStorage.setItem('token', {json.dumps(TOKEN)});" + INIT_JS)
        pg = await ctx.new_page()
        await pg.goto(f"{OWUI}/?models=voice-bench", wait_until="load")
        # Open WebUI shows a one-off "What's New" release-notes modal after a version's first login; it covers the
        # page. Dismissing it is outside the timed path (clip start is getUserMedia, which happens after the click).
        okay = pg.get_by_role("button", name="Okay, Let's Go!")
        try:
            await okay.wait_for(state="visible", timeout=4000)
            await okay.click()
            rec["dismissed_whats_new"] = True
        except Exception:
            pass
        if voice:
            btn = pg.get_by_role("button", name="Voice mode", exact=True)
            await btn.wait_for(state="visible", timeout=30000)
            rec["wall_click"] = time.time()
            await btn.click()
            await pg.wait_for_function("window.__vp.playing.some(p => !p[2].startsWith('data:'))", timeout=90000, polling=20)
            rec["wall_playing"] = time.time()
            v = await pg.evaluate("window.__vp")
            rec["t_gum_ms"] = v["gum"]
            rec["t_playing_ms"] = min(t for t, _, src in v["playing"] if not src.startswith("data:"))
            rec["playing_events"] = v["playing"][:6]
            rec["e2e_ms"] = round(rec["t_playing_ms"] - (rec["t_gum_ms"] + rec["speech_end_s"] * 1e3), 1)
        else:
            box = pg.locator("#chat-input")
            await box.wait_for(state="visible", timeout=30000)
            await box.click()
            await box.fill(row["reference"])
            rec["wall_send"] = time.time()
            await pg.keyboard.press("Enter")
            await pg.wait_for_url(re.compile(r"/c/"), timeout=60000)
            await pg.wait_for_timeout(1500)
        await pg.wait_for_url(re.compile(r"/c/"), timeout=60000)
        rec["chat_id"] = pg.url.rsplit("/c/", 1)[-1].split("?")[0]
    finally:
        await b.close()
        rec["wall_closed"] = time.time()
    rec["idle_after_s"] = wait_idle(voice)
    user, asst = chat_turns(rec["chat_id"])
    rec["n_user_turns"], rec["n_assistant_turns"] = len(user), len(asst)
    rec["transcript"] = user[0]["content"] if user else None
    reply = asst[0]["content"] if asst else ""
    rec["reply"] = reply
    # A4: llama-server's `timings` for the reply as Open WebUI stored them (prompt_n, cache_n, prompt_ms, predicted_n).
    rec["reply_usage"] = asst[0].get("usage") if asst else None
    rec["reply_meta"] = asst[0].get("meta") if asst else None
    fs = first_sentence(reply)
    rec["first_sentence"] = fs
    rec["first_sentence_tokens"] = len(http(f"http://{H}:8080/tokenize", {"content": fs})["tokens"]) if fs else 0
    rec["reply_tokens"] = len(http(f"http://{H}:8080/tokenize", {"content": reply})["tokens"]) if reply else 0
    return rec


async def main():
    rows = list(csv.DictReader(open(a.clips), delimiter="\t"))
    if a.only:
        keep = a.only.split(",")
        rows = [r for r in rows if r["clip_id"] in keep]
    async with async_playwright() as pw:
        for row in rows:
            t = time.time()
            try:
                rec = await one_clip(pw, row, a.clipdir)
                rec["ok"] = True
            except Exception as e:  # a failed clip is logged, not retried silently
                rec = {"arm": a.arm, "pass": a.pass_, "clip_id": row["clip_id"], "set": row["set"], "ok": False,
                       "error": repr(e)[:500]}
            rec["wall_clip_start"] = t
            with open(LOG, "a") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(rec["clip_id"], rec.get("ok"), rec.get("e2e_ms"), (rec.get("transcript") or "")[:50], "|",
                  (rec.get("reply") or rec.get("error", ""))[:60], flush=True)


asyncio.run(main())
