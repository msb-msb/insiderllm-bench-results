#!/usr/bin/env python3
"""llama.cpp v1.0.0 vs 0.9 builds, Qwen3.5-27B MTP on/off, Tamanna. Lock a39c4818 (llamacpp-v1-mtp-3090-2026-11.md).

Request body, prompts and token caps are the homebrewserver.club bench.py (selfhosted@9ea02603, llama-cpp-v1/,
sha256 06fdc812...): /v1/chat/completions, streamed, temperature 0, seed 42, enable_thinking false; short = the
bicycle essay prompt, max_tokens 512; long = long-context.txt + the five-bullet tail, max_tokens 256.
Changes from it (lock M2/M4): 8-hex nonce instead of a uuid; (priming, measured) pairs; 3 rounds rotated over 6
setups; per-request void metrics (prompt_n, cache_n, swap, NVMe reads during decode, PCIe during prefill, peak MiB).
Run inside `bwrap --dev-bind / / --unshare-net`.
"""
import json, os, secrets, subprocess, sys, threading, time, urllib.request

HOME = os.path.expanduser("~")
B = f"{HOME}/llamacpp-v1-mtp-2026-11"
MODEL = f"{HOME}/bench-models/qwen3.5-27b-mtp/Qwen3.5-27B-Q4_K_M.gguf"
OUT = f"{B}/results.jsonl"
PORT = 8081
URL = f"http://127.0.0.1:{PORT}"
NVME = "nvme0n1"
SHORT = "Write a long, detailed essay of at least 2000 words about the history of the bicycle, with many sections."
LONG_TAIL = "\n\nSummarize the text above in five bullet points."
LONG_CTX = open(f"{B}/long-context.txt").read()
SPEC = ["--spec-type", "draft-mtp", "--spec-draft-n-max", "6"]
SETUPS = ["V-mtp", "Z-mtp", "O-mtp", "V-off", "Z-off", "O-off"]
COOL = 50


def smi(q):
    return subprocess.check_output(["nvidia-smi", f"--query-gpu={q}", "--format=csv,noheader,nounits"]).decode().strip()


def gpu_mib():
    return int(smi("memory.used"))


def gpu_temp():
    return int(smi("temperature.gpu"))


def vmstat():
    d = {}
    for line in open("/proc/vmstat"):
        k, v = line.split()
        if k in ("pswpin", "pswpout"):
            d[k] = int(v)
    return d


def nvme_read_bytes():
    return int(open(f"/sys/block/{NVME}/stat").read().split()[2]) * 512


class Sampler(threading.Thread):
    """Samples PCIe gen/width while `prefill` is set, and peak card MiB throughout."""
    def __init__(self):
        super().__init__(daemon=True)
        self.stop = threading.Event(); self.prefill = threading.Event(); self.prefill.set()
        self.pcie = []; self.peak = 0

    def run(self):
        while not self.stop.is_set():
            out = smi("memory.used,pcie.link.gen.current,pcie.link.width.current").split(", ")
            self.peak = max(self.peak, int(out[0]))
            if self.prefill.is_set():
                self.pcie.append((int(out[1]), int(out[2])))
            time.sleep(0.1)


def prompt(kind):
    nonce = f"Request id {secrets.token_hex(4)}.\n"
    return nonce + (SHORT if kind == "short" else LONG_CTX + LONG_TAIL)


def request(kind, n, log_path):
    body = {"messages": [{"role": "user", "content": prompt(kind)}], "max_tokens": n, "temperature": 0, "seed": 42,
            "stream": True, "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(URL + "/v1/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    log_before = len(open(log_path, errors="replace").read().splitlines())
    vm0, rd0, t_start = vmstat(), nvme_read_bytes(), gpu_temp()
    s = Sampler(); s.start()
    t0 = time.perf_counter(); ttft = None; timings = None; text = []; rd_first = None
    with urllib.request.urlopen(req, timeout=900) as r:
        for raw in r:
            line = raw.decode().strip()
            if not line.startswith("data: ") or line == "data: [DONE]":
                continue
            d = json.loads(line[6:])
            ch = d.get("choices") or [{}]
            c = (ch[0].get("delta") or {}).get("content")
            if c:
                if ttft is None:
                    ttft = time.perf_counter() - t0; s.prefill.clear(); rd_first = nvme_read_bytes()
                text.append(c)
            if "timings" in d:
                timings = d["timings"]
    wall = time.perf_counter() - t0
    s.stop.set(); s.join()
    vm1, rd1 = vmstat(), nvme_read_bytes()
    time.sleep(0.5)
    new_log = open(log_path, errors="replace").read().splitlines()[log_before:]
    acc = [l for l in new_log if "draft acceptance" in l]
    t = timings or {}
    return {"ttft_s": ttft, "wall_s": wall, "prompt_n": t.get("prompt_n"), "cache_n": t.get("cache_n"),
            "pp_tps": t.get("prompt_per_second"), "predicted_n": t.get("predicted_n"),
            "tg_tps": t.get("predicted_per_second"), "draft_n": t.get("draft_n"),
            "draft_n_accepted": t.get("draft_n_accepted"), "acceptance_log": acc[-1] if acc else None,
            "swap_in_kib": (vm1["pswpin"] - vm0["pswpin"]) * 4, "swap_out_kib": (vm1["pswpout"] - vm0["pswpout"]) * 4,
            "nvme_read_total_b": rd1 - rd0, "nvme_read_decode_b": (rd1 - rd_first) if rd_first is not None else None,
            "pcie_prefill": sorted(set(s.pcie)), "pcie_min_gen": min((g for g, _ in s.pcie), default=None),
            "pcie_min_width": min((w for _, w in s.pcie), default=None), "peak_mib": s.peak,
            "temp_start": t_start, "temp_end": gpu_temp(), "text200": "".join(text)[:200]}


def wait_idle_card():
    for _ in range(600):
        apps = subprocess.check_output(["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"]).decode().strip()
        if not apps and gpu_mib() < 50:
            return gpu_mib()
        time.sleep(1)
    raise SystemExit("card not idle")


def start(setup, tag):
    arm, mode = setup.split("-")
    exe = f"{B}/llama-{arm}/build/bin/llama-server"
    args = [exe, "-m", MODEL, "-c", "32768", "-np", "1", "--host", "127.0.0.1", "--port", str(PORT)]
    if mode == "mtp":
        args += SPEC
    log_path = f"{B}/logs/{tag}.log"
    os.makedirs(f"{B}/logs", exist_ok=True)
    lf = open(log_path, "w")
    p = subprocess.Popen(args, stdout=lf, stderr=subprocess.STDOUT)
    for _ in range(1200):
        try:
            if urllib.request.urlopen(URL + "/health", timeout=2).status == 200:
                return p, log_path, args
        except Exception:
            pass
        if p.poll() is not None:
            raise SystemExit(f"server exited: {tag}")
        time.sleep(0.5)
    raise SystemExit(f"server never healthy: {tag}")


def stop(p):
    p.terminate()
    try:
        p.wait(30)
    except subprocess.TimeoutExpired:
        p.kill(); p.wait()


def run_setup(setup, rnd, suffix=""):
    idle = wait_idle_card()
    tag = f"r{rnd}-{setup}{suffix}"
    p, log_path, args = start(setup, tag)
    try:
        request("short", 32, log_path)  # warm-up, discarded (the report's)
        for kind, n in (("short", 512), ("long", 256)):
            for role in ("prime", "measured"):
                if role == "measured":
                    while gpu_temp() > COOL:
                        time.sleep(2)
                r = request(kind, n, log_path)
                row = {"round": rnd, "setup": setup, "arm": setup.split("-")[0], "mode": setup.split("-")[1],
                       "prompt": kind, "n": n, "role": role, "tag": tag, "idle_mib_before_start": idle,
                       "argv": args[1:], "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **r}
                with open(OUT, "a") as f:
                    f.write(json.dumps(row) + "\n")
                print(f"{tag} {kind} {role} tg={r['tg_tps']:.2f} pp={r['pp_tps']:.1f} prompt_n={r['prompt_n']} "
                      f"cache_n={r['cache_n']} pcie={r['pcie_min_gen']}x{r['pcie_min_width']}", flush=True)
    finally:
        stop(p)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rerun":  # rerun <setup> : void-cell re-run, appended (lock M5)
        for rnd in (1, 2, 3):
            run_setup(sys.argv[2], rnd, suffix="-rerun")
    else:
        for rnd in (1, 2, 3):
            for k in range(6):
                run_setup(SETUPS[(k + 2 * (rnd - 1)) % 6], rnd)
    print("ALL DONE", flush=True)
