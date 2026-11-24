#!/usr/bin/env python3
"""Tamanna-side server control for the voice-pipeline run (pre-registration section 3; amendments A1, A2, A3).

  serve.py up ARM      ARM in S1 S2 S3 R0. Starts the 10 Hz VRAM sampler, the arm's STT server and the TTS wrapper
                       (voice arms only), runs 3 warm-up requests through each, records each process's VRAM peak,
                       computes free VRAM = 24,576 - (STT peak + TTS peak) - 768 MiB, fits the LLM's --n-cpu-moe by
                       the section 3.1 rule over a 4K-token prompt, starts the LLM at that value, points Open WebUI
                       at the three servers, idles 300 s, then runs the A1 GPU check. Prints one READY json line.
  serve.py down ARM    Stops the arm's servers and the sampler.
  serve.py check ARM   A1 check only (before a re-run under A1 item 1).

Standard library only (Tamanna's system python3). Everything goes to ~/voice-pipeline/run-2026-11-24/<ARM>/.
Fixed across arms (section 3.1): llama-server -c 8192 -np 1 -fa on --jinja, thinking off. STT llama-servers (S1, S3)
run with -ngl 99 -c 2048 -np 1, set before the first warm-up: llama-server's default context (65,536 x 4 slots for
Qwen3-ASR) reserves ~10 GB of KV for clips that use ~100-300 tokens. The lock fixes the STT models and route, not
these flags. Amendment A3: the LLM and the S1/S3 STT llama-servers run with --cache-ram 0 (no host-RAM prompt cache;
per-slot common-prefix reuse stays at its default). Warm-up audio is the TTS-generated smoke-test audio (smoke-2026-11-19/{en,de}.mp3), never a measured clip.
"""
import json, os, pathlib, signal, subprocess, sys, time, urllib.request, ssl

HOME = pathlib.Path.home()
VP = HOME / "voice-pipeline"
RUN = VP / "run-2026-11-24"
M = HOME / "bench-models" / "voice-pipeline"
LLAMA = HOME / "llama-v0.7.0" / "build" / "bin" / "llama-server"
LLM_GGUF = HOME / "bench-models" / "Qwen3.6-35B-A3B-UD-Q4_K_M.gguf"
CARD_MIB, MARGIN_MIB = 24576, 768
OWUI = "https://127.0.0.1:8443"
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE

STT = {
    "S1": [str(LLAMA), "-m", f"{M}/qwen3-asr-1.7b-gguf/qwen3-asr-1.7b-Q8_0.gguf",
           "--mmproj", f"{M}/qwen3-asr-1.7b-gguf/mmproj-qwen3-asr-1.7b-f16.gguf",
           "-ngl", "99", "-c", "2048", "-np", "1", "--cache-ram", "0", "--host", "127.0.0.1", "--port", "8093"],
    "S3": [str(LLAMA), "-m", f"{M}/granite-speech-4.1-2b-plus-gguf/granite-speech-4.1-2b-plus-Q8_0.gguf",
           "--mmproj", f"{M}/granite-speech-4.1-2b-plus-gguf/mmproj-model-f16.gguf",
           "-ngl", "99", "-c", "2048", "-np", "1", "--cache-ram", "0", "--host", "127.0.0.1", "--port", "8093"],
    "S2": [str(VP / "ctc/bin/python"), str(VP / "harness/stt_ctc_server.py"),
           "--model", f"{M}/granite-speech-5.0-470m-turboctc", "--ffmpeg", str(VP / "bin/ffmpeg"),
           "--host", "127.0.0.1", "--port", "8091", "--log", "{D}/stt_s2.jsonl"],
}
STT_URL = {"S1": "http://127.0.0.1:8093/v1", "S3": "http://127.0.0.1:8093/v1", "S2": "http://127.0.0.1:8091/v1"}
TTS = [str(VP / "tts/bin/python"), str(VP / "harness/tts_customvoice_server.py"),
       "--model", f"{M}/qwen3-tts-12hz-0.6b-customvoice", "--speaker", "ryan", "--language", "english",
       "--ffmpeg", str(VP / "bin/ffmpeg"), "--host", "0.0.0.0", "--port", "8092", "--log", "{D}/tts.jsonl"]
LLM_ALIAS = "qwen3.6-35b-a3b"


def llm_cmd(ncmoe):
    return [str(LLAMA), "-m", str(LLM_GGUF), "--alias", LLM_ALIAS, "-ngl", "99", "--n-cpu-moe", str(ncmoe),
            "-c", "8192", "-np", "1", "--cache-ram", "0", "-fa", "on", "--jinja", "--chat-template-kwargs", '{"enable_thinking":false}',
            "--host", "0.0.0.0", "--port", "8080"]


SYSTEM_PROMPT = "Answer in two or three short sentences."
PARAMS = {"temperature": 0.7, "max_tokens": 256}
WARM_TTS = ["Plants use sunlight to turn water and air into food.", "The library opens at nine in the morning.",
            "Water boils at one hundred degrees Celsius at sea level."]


def http(url, data=None, headers=None, timeout=300, method=None):
    h = {"Content-Type": "application/json"} | (headers or {})
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX if url.startswith("https") else None) as r:
        raw = r.read()
    try:
        return json.loads(raw)
    except Exception:
        return raw


def multipart(url, path, fields):
    b = "----vpbench"
    parts = []
    for k, v in fields.items():
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
                 f'Content-Type: audio/mpeg\r\n\r\n'.encode() + path.read_bytes() + b"\r\n")
    parts.append(f"--{b}--\r\n".encode())
    req = urllib.request.Request(url, data=b"".join(parts), headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def start(name, cmd, d):
    log = open(d / f"{name}.log", "a")
    log.write(f"# wall_start {time.time():.3f} cmd {json.dumps(cmd)}\n"); log.flush()
    p = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=VP, start_new_session=True)
    (d / f"{name}.pid").write_text(str(p.pid))
    (d / f"{name}.pid.final").write_text(str(p.pid))  # kept after stop, for VRAM attribution in analyze.py
    return p


def stop(name, d):
    pf = d / f"{name}.pid"
    if not pf.exists():
        return
    pid = int(pf.read_text())
    try:
        os.killpg(pid, signal.SIGTERM)
        for _ in range(100):
            os.kill(pid, 0); time.sleep(0.1)
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    pf.unlink()


def wait_health(url, p, secs=600):
    for _ in range(secs):
        if p.poll() is not None:
            raise SystemExit(f"process for {url} exited with {p.returncode}")
        try:
            http(url, timeout=2); return
        except Exception:
            time.sleep(1)
    raise SystemExit(f"timeout waiting for {url}")


def gpu_apps():
    out = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True).stdout
    return [l for l in out.splitlines() if l.strip()]


def peaks(d, since, until=None):
    """Per-pid peak MiB from the sampler CSV (wall, pid, MiB) in [since, until]."""
    pk = {}
    for line in (d / "vram.csv").read_text().splitlines()[1:]:
        t, pid, mib = line.split(",")
        t, pid, mib = float(t), int(pid), int(mib)
        if t >= since and (until is None or t <= until):
            pk[pid] = max(pk.get(pid, 0), mib)
    return pk


def tree_pids(pid):
    """pid plus descendants (uvicorn wrappers run model code in the same process, but be safe)."""
    out = {pid}
    for c in pathlib.Path(f"/proc/{pid}/task").glob("*/children"):
        for x in c.read_text().split():
            out |= tree_pids(int(x))
    return out


def peak_of(d, pid, since, until=None):
    pk = peaks(d, since, until)
    return max([pk.get(x, 0) for x in tree_pids(pid)] + [0])


def a1_check(d, tag):
    q = subprocess.run(["nvidia-smi", "--query-gpu=persistence_mode,power.limit", "--format=csv,noheader"],
                       capture_output=True, text=True).stdout.strip()
    power = subprocess.run(["nvidia-smi", "-q", "-d", "POWER"], capture_output=True, text=True).stdout
    with open(d / "a1_check.log", "a") as f:
        f.write(f"# {tag} wall {time.time():.3f} {time.strftime('%Y-%m-%dT%H:%M:%S%z')}\n{q}\n")
    (d / f"nvidia-smi-q-power-{tag}.txt").write_text(power)
    ok = q.replace(" ", "") == "Enabled,420.00W"
    return ok, q


def owui_token():
    return (RUN / "owui-admin.token").read_text().strip()


def owui_configure(arm, d):
    T = {"Authorization": f"Bearer {owui_token()}"}
    http(f"{OWUI}/openai/config/update", {"ENABLE_OPENAI_API": True, "OPENAI_API_BASE_URLS": ["http://127.0.0.1:8080/v1"],
                                          "OPENAI_API_KEYS": ["none"], "OPENAI_API_CONFIGS": {}}, T)
    cfg = http(f"{OWUI}/api/v1/audio/config", headers=T)
    cfg["tts"].update({"ENGINE": "openai", "OPENAI_API_BASE_URL": "http://127.0.0.1:8092/v1", "OPENAI_API_KEY": "none"})
    if arm in STT_URL:
        cfg["stt"].update({"ENGINE": "openai", "OPENAI_API_BASE_URL": STT_URL[arm], "OPENAI_API_KEY": "none",
                           "MODEL": "whisper-1"})
    http(f"{OWUI}/api/v1/audio/config/update", {"tts": cfg["tts"], "stt": cfg["stt"]}, T)
    models = http(f"{OWUI}/api/models?refresh=true", headers=T)
    ids = [m["id"] for m in models.get("data", [])]
    assert LLM_ALIAS in ids, ids
    # A workspace model carries the fixed system prompt and sampling (section 3.1), applied server-side by Open WebUI.
    body = {"id": "voice-bench", "base_model_id": LLM_ALIAS, "name": "voice-bench",
            "meta": {"description": "voice-pipeline run 2026-11-24"},
            "params": {"system": SYSTEM_PROMPT, **PARAMS}, "access_control": None, "is_active": True}
    try:
        http(f"{OWUI}/api/v1/models/model/update?id=voice-bench", body, T)
    except Exception:
        http(f"{OWUI}/api/v1/models/create", body, T)
    after = {"audio": http(f"{OWUI}/api/v1/audio/config", headers=T), "openai": http(f"{OWUI}/openai/config", headers=T),
             "model": http(f"{OWUI}/api/v1/models/model?id=voice-bench", headers=T),
             "tasks": http(f"{OWUI}/api/v1/tasks/config", headers=T)}
    for k in ("audio",):
        for s in ("tts", "stt"):
            for kk in list(after[k][s]):
                if "KEY" in kk:
                    after[k][s][kk] = "<redacted>" if after[k][s][kk] else ""
    after["openai"]["OPENAI_API_KEYS"] = ["<redacted>"]
    (d / "owui_config.json").write_text(json.dumps(after, indent=2))


def fit_ncmoe(d, free):
    """Smallest --n-cpu-moe whose llama-server peak over a 4K-token prompt stays below `free` MiB (section 3.1)."""
    prompt = (VP / "harness" / "fit_prompt.txt").read_text()
    # Start from the Miu sweep's prediction (b10088: ncmoe 6 -> 18,898 MiB, 16 -> 14,260 MiB at small context;
    # ~463.8 MiB per step) and search: down while it fits, up while it doesn't.
    pred = max(0, min(40, 6 + -(-(18898 - free) // 464))) if free < 18898 else max(0, 6 - (free - 18898) // 464)
    tried = {}

    def trial(n):
        name = f"fit_ncmoe{n}"
        t0 = time.time()
        p = start(name, llm_cmd(n), d)
        try:
            wait_health("http://127.0.0.1:8080/health", p)
            ntok = len(http("http://127.0.0.1:8080/tokenize", {"content": prompt})["tokens"])
            r = http("http://127.0.0.1:8080/v1/chat/completions",
                     {"model": LLM_ALIAS, "messages": [{"role": "user", "content": prompt}], "max_tokens": 8,
                      "temperature": 0.7})
            time.sleep(0.5)
            pk = peak_of(d, p.pid, t0)
        finally:
            stop(name, d)
            time.sleep(2)
        tried[n] = {"peak_mib": pk, "prompt_tokens": ntok, "fits": pk < free,
                    "usage": r.get("usage") if isinstance(r, dict) else None}
        return pk < free

    n = pred
    if trial(n):
        while n > 0 and trial(n - 1):
            n -= 1
        chosen = n
    else:
        chosen = None
        while n < 24:
            n += 1
            if trial(n):
                chosen = n
                break
    return pred, chosen, tried


def up(arm, dirname=None, idle=300, force_ncmoe=None):
    d = RUN / (dirname or arm)
    d.mkdir(parents=True, exist_ok=True)
    meta = {"arm": arm, "wall_up": time.time()}
    assert not gpu_apps(), f"GPU not empty: {gpu_apps()}"
    start("sampler", [sys.executable, str(VP / "harness/sampler.py"), str(d / "vram.csv")], d)
    time.sleep(1)
    stt_peak = tts_peak = 0
    if arm != "R0":
        t0 = time.time()
        sp = start("stt", [a.replace("{D}", str(d)) for a in STT[arm]], d)
        tp = start("tts", [a.replace("{D}", str(d)) for a in TTS], d)
        base = STT_URL[arm].rsplit("/v1", 1)[0]
        wait_health(base + "/health", sp)
        wait_health("http://127.0.0.1:8092/health", tp)
        warm = []
        for f in ("en", "de", "en"):
            ts = time.time()
            r = multipart(STT_URL[arm] + "/audio/transcriptions", VP / "smoke-2026-11-19" / f"{f}.mp3", {"model": "whisper-1"})
            warm.append({"kind": "stt", "audio": f, "ms": round((time.time() - ts) * 1e3, 1), "text": r.get("text")})
        for i, s in enumerate(WARM_TTS):
            ts = time.time()
            n = len(http("http://127.0.0.1:8092/v1/audio/speech", {"input": s, "voice": "alloy"}))
            warm.append({"kind": "tts", "chars": len(s), "ms": round((time.time() - ts) * 1e3, 1), "bytes": n})
        time.sleep(1)
        stt_peak, tts_peak = peak_of(d, sp.pid, t0), peak_of(d, tp.pid, t0)
        meta.update(stt_cmd=STT[arm], tts_cmd=TTS, warmups=warm, stt_peak_mib=stt_peak, tts_peak_mib=tts_peak)
        free = CARD_MIB - (stt_peak + tts_peak) - MARGIN_MIB
        if force_ncmoe is not None:  # functional tests only (FUNC* folders); never in an arm
            pred, chosen, tried = None, force_ncmoe, {}
        else:
            pred, chosen, tried = fit_ncmoe(d, free)
        meta.update(free_mib=free, ncmoe_predicted_start=pred, ncmoe=chosen, fit_trials=tried)
        if chosen is None:
            meta["result"] = "no --n-cpu-moe <= 24 fits; recorded as the result (section 4.3)"
            (d / "meta.json").write_text(json.dumps(meta, indent=2))
            print("NOFIT " + json.dumps({"free_mib": free, "trials": tried})); return
    else:
        meta.update(ncmoe=0, free_mib=None)
    lp = start("llm", llm_cmd(meta["ncmoe"]), d)
    wait_health("http://127.0.0.1:8080/health", lp)
    meta["llm_cmd"] = llm_cmd(meta["ncmoe"])
    owui_configure(arm, d)
    meta["idle_start"] = time.time()
    time.sleep(idle)  # section 3.1: 5 minutes idle before each arm (300 s; FUNC tests may pass less)
    ok, q = a1_check(d, "pre-warmup")
    meta.update(a1_reading=q, a1_ok=ok, gpu_apps_ready=gpu_apps(), wall_ready=time.time())
    (d / "meta.json").write_text(json.dumps(meta, indent=2))
    if not ok:
        print("ABORT_A1 " + q); return
    print("READY " + json.dumps({"arm": arm, "ncmoe": meta["ncmoe"], "free_mib": meta["free_mib"],
                                 "stt_peak_mib": stt_peak, "tts_peak_mib": tts_peak, "a1": q}))


def down(arm, dirname=None):
    d = RUN / (dirname or arm)
    for n in ("llm", "stt", "tts"):
        stop(n, d)
    time.sleep(2)
    stop("sampler", d)
    print("DOWN", arm, "gpu apps:", gpu_apps())


if __name__ == "__main__":
    cmd, arm = sys.argv[1], sys.argv[2]
    assert arm in ("S1", "S2", "S3", "R0"), arm
    opt = dict(a.split("=", 1) for a in sys.argv[3:])  # FUNC tests: dir=FUNCn idle=S ncmoe=N
    if any(k in opt for k in ("idle", "ncmoe")):
        assert opt.get("dir", "").startswith("FUNC"), "idle/ncmoe overrides are for FUNC* folders only"
    if cmd == "up":
        up(arm, opt.get("dir"), int(opt.get("idle", 300)), int(opt["ncmoe"]) if "ncmoe" in opt else None)
    elif cmd == "down":
        down(arm, opt.get("dir"))
    elif cmd == "check":
        ok, q = a1_check(RUN / arm, f"rerun-{int(time.time())}")
        print(("OK " if ok else "ABORT_A1 ") + q)
