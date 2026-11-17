#!/usr/bin/env python3
"""MBPP confirmatory arms (docs/candidates/qwen-coder-mbpp-confirm-2026-11.md), unattended. Derived from the
HumanEval lock's he_run.py: same servers, flags, hashing, order and drift check; differences are the generator
(mbpp_gen.py), CN3's N fixed at 8 (the HumanEval search result; no new search), and scoring twice per arm.

Runs on Miu. Each arm: sha256 the Tamanna working copy -> start llama-server on Tamanna (v0.4.0, bound to its LAN
address, port 8099) -> mbpp_gen.py on Miu -> stop server -> sha256 again -> score in he-scorer:b10088 on Miu with
mbpp_score.py (sandbox flags as P5), twice: CUT (each completion cut at its first ```, primary) and RAW (as
returned, secondary). A pre-load mismatch stops the whole run; a pre/post mismatch voids the arm.

Arms, in order: A36, A38, C30, CN (-ncmoe 28), CN3 (-ncmoe 8), A36 again (completions must be byte-identical).
usage: mbpp_run.py            (all arms; skips an arm whose summary file already exists)
"""
import hashlib, json, os, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
TAM = "192.168.x.x"
PORT = 8099
BASE = f"http://{TAM}:{PORT}"
RBIN = "/home/minotaur/llama-v0.4.0/build/bin"
MD = "/home/minotaur/bench-models/qwen-coder"
TWORK = "/home/minotaur/tamanna-qwen-coder-2026-11/mbpp"
GENPY = "/home/minotaur/Desktop/lucebox-hub/dflash/.venv/bin/python"
GEN = os.path.join(HERE, "mbpp_gen.py")
SCORER = "he-scorer:b10088"

SUMS = {
    "Qwen3.6-27B-UD-Q4_K_XL.gguf": "ff6941ded525b34eb159496762c29dd0ec6e71dc31b74d57e75d871a03eec259",
    "Qwen3.8-27B-UD-Q4_K_XL.gguf": "bee238bbeb3dc0a34bde4d0dedbaee1f98c009e8bb4226f03070054c12fb1372",
    "Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf": "2841aa314d916434860cfb8990347528dcdfe5c350dbcb9d1461dbee88ff2533",
    "Qwen3-Coder-Next-Q4_K_M-00001-of-00004.gguf": "6bcfc9f9c37901eeb92172e2ab871224dab36a453d263bcb2547f737409534da",
    "Qwen3-Coder-Next-Q4_K_M-00002-of-00004.gguf": "817def0691ee9d08bf3dc4444be7aed29c9e52091e8fa9d97901ce7e7f6f01d3",
    "Qwen3-Coder-Next-Q4_K_M-00003-of-00004.gguf": "23aa634d47dca9b4ca3ea249384e6f01951b24c83cdc076f37f6f43d6c99883f",
    "Qwen3-Coder-Next-Q4_K_M-00004-of-00004.gguf": "249c768cc5f130dc731567d6edcbdacc48e14dec9e02c5dbe2b2185d2c5bdb2b",
    "Qwen3-Coder-Next-UD-IQ3_XXS.gguf": "00a9bf4f9dcb6ef4fb78ef810e6b5dbd13cc604ceb0fa10f56c9ae2529c0ade4",
}
CN_SHARDS = [f"Qwen3-Coder-Next-Q4_K_M-0000{i}-of-00004.gguf" for i in range(1, 5)]
ARMS = [  # (slot label, files to hash (first one is -m), ncmoe or None or "search")
    ("A36", ["Qwen3.6-27B-UD-Q4_K_XL.gguf"], None),
    ("A38", ["Qwen3.8-27B-UD-Q4_K_XL.gguf"], None),
    ("C30", ["Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf"], None),
    ("CN", CN_SHARDS, 28),
    ("CN3", ["Qwen3-Coder-Next-UD-IQ3_XXS.gguf"], 8),
    ("A36-drift", ["Qwen3.6-27B-UD-Q4_K_XL.gguf"], None),
]
SEQ = os.path.join(HERE, "sequence.log")


def log(s):
    line = f"{time.strftime('%H:%M:%S')} {s}"
    print(line, flush=True)
    open(SEQ, "a").write(line + "\n")


def ssh(cmd, timeout=3600):
    return subprocess.run(["ssh", "-o", "BatchMode=yes", TAM, cmd], capture_output=True, text=True, timeout=timeout)


def tam_sha(files):
    r = ssh("cd " + MD + " && sha256sum " + " ".join(files), timeout=3600)
    got = dict(reversed(l.split(None, 1)) for l in r.stdout.splitlines())
    return {f: got.get(f) for f in files}


def server_cmd(model, ncmoe, logname):
    flags = f"-m {MD}/{model} -ngl 99 -fa on -c 4096 --no-jinja --no-mmap --host {TAM} --port {PORT}"
    if ncmoe is not None:
        flags += f" -ncmoe {ncmoe}"
    # The braces keep '&' on the server alone; backgrounding the whole && list held the ssh channel open (11-17).
    return (f"mkdir -p {TWORK} && cd {TWORK} && {{ LD_LIBRARY_PATH={RBIN} setsid nohup {RBIN}/llama-server {flags} "
            f"> {logname} 2>&1 < /dev/null & }}; echo started"), flags


def stop_server():
    ssh("pkill -TERM -x llama-server; sleep 5; pkill -KILL -x llama-server; true")
    time.sleep(3)


def wait_ready(timeout=900):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(BASE + "/health", timeout=3) as r:
                if r.status == 200 and b"loading" not in r.read().lower():
                    return True, time.time() - t0
        except Exception:
            pass
        if ssh("pgrep -x llama-server >/dev/null && echo up || echo down").stdout.strip() == "down":
            return False, time.time() - t0
        time.sleep(3)
    return False, time.time() - t0


def answers():
    body = {"prompt": "def fibonacci(n):", "max_tokens": 16, "temperature": 0}
    req = urllib.request.Request(BASE + "/v1/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        d = json.load(urllib.request.urlopen(req, timeout=300))
        return bool(d["choices"][0]["text"])
    except Exception as e:
        log(f"  answer check failed: {e}")
        return False


def search_cn3(model):
    trail = []
    for n in range(0, 50, 2):
        stop_server()
        cmd, _ = server_cmd(model, n, f"server-CN3-search-ncmoe{n}.log")
        ssh(cmd)
        ok, t = wait_ready(600)
        a = answers() if ok else False
        trail.append({"ncmoe": n, "loaded": ok, "answered": a})
        log(f"  CN3 search: -ncmoe {n} loaded={ok} answered={a}")
        stop_server()
        if ok and a:
            json.dump({"lowest_even_ncmoe_loads_and_answers_c4096": n, "trail": trail},
                      open(os.path.join(HERE, "cn3-search.json"), "w"), indent=1)
            return n
    json.dump({"lowest_even_ncmoe_loads_and_answers_c4096": None, "trail": trail},
              open(os.path.join(HERE, "cn3-search.json"), "w"), indent=1)
    return None


def out_sha16(results):
    return hashlib.sha256(json.dumps({k: v["text"] for k, v in sorted(results.items())}).encode()).hexdigest()[:16]


def cut(text):
    return text.split("```", 1)[0]


def score(label, genout):
    """Score twice; returns ({variant: vector}, out_sha16)."""
    evaldir = os.path.join(HERE, "eval")
    os.makedirs(evaldir, exist_ok=True); os.chmod(evaldir, 0o777)
    subprocess.run(["cp", os.path.join(HERE, "mbpp_score.py"), evaldir], check=True)
    d = json.load(open(genout))
    vecs = {}
    for variant, fn in (("cut", cut), ("raw", lambda t: t)):
        name = f"mbpp_{label}_{variant}.jsonl"
        with open(os.path.join(evaldir, name), "w") as f:
            for tid, r in d["results"].items():
                f.write(json.dumps({"task_id": tid, "prompt": r["prompt"], "completion": fn(r["text"]),
                                    "test": r["test"]}) + "\n")
        os.chmod(os.path.join(evaldir, name), 0o666)
        sc = subprocess.run(f"docker run --rm --network none --cap-drop ALL --security-opt no-new-privileges "
                            f"--memory 4g --pids-limit 256 -v {evaldir}:/work --entrypoint python3 {SCORER} "
                            f"/work/mbpp_score.py /work/{name}", shell=True, capture_output=True, text=True)
        open(os.path.join(HERE, f"scorer-{label}-{variant}.txt"), "w").write(sc.stdout + sc.stderr)
        rf = os.path.join(evaldir, name + "_results.jsonl")
        vecs[variant] = {json.loads(l)["task_id"]: bool(json.loads(l)["passed"]) for l in open(rf)} if os.path.exists(rf) else {}
    return vecs, out_sha16(d["results"])


PAIRS = [("C30", "A36"), ("CN", "A36"), ("CN3", "CN"), ("A38", "A36"), ("CN", "C30")]


def mcnemar_p(b, c):
    from math import comb
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, k) for k in range(min(b, c) + 1)) / 2 ** n)


def paired():
    out = {}
    for variant in ("cut", "raw"):
        v = {}
        for a in ("A36", "A38", "C30", "CN", "CN3"):
            p = os.path.join(HERE, f"summary-{a}.json")
            if os.path.exists(p) and json.load(open(p)).get("status") == "ok":
                v[a] = json.load(open(p))["vector"][variant]
        rows = []
        for x, y in PAIRS:
            if x in v and y in v:
                b = sum(v[x][t] and not v[y][t] for t in v[x]); c = sum(v[y][t] and not v[x][t] for t in v[x])
                rows.append({"x": x, "y": y, "x_pass": sum(v[x].values()), "y_pass": sum(v[y].values()),
                             "only_x": b, "only_y": c, "p": mcnemar_p(b, c)})
        out[variant] = rows
    json.dump(out, open(os.path.join(HERE, "mcnemar.json"), "w"), indent=1)
    for variant, rows in out.items():
        for r in rows:
            log(f"  McNemar {variant}: {r['x']} {r['x_pass']} vs {r['y']} {r['y_pass']}: only {r['only_x']}/{r['only_y']} p={r['p']:.3g}")


def main():
    log("=== MBPP run start")
    ident = ssh(f"sha256sum {RBIN}/llama-server {RBIN}/libggml-cuda.so.0.23.0; LD_LIBRARY_PATH={RBIN} {RBIN}/llama-server --version 2>&1 | head -2; "
                "nvidia-smi --query-gpu=name,driver_version,memory.used --format=csv,noheader; df -h ~ | tail -1").stdout
    open(os.path.join(HERE, "engine-identity.txt"), "w").write(ident)
    log("engine identity:\n" + ident.strip())
    for label, files, ncmoe in ARMS:
        summ = os.path.join(HERE, f"summary-{label}.json")
        if os.path.exists(summ):
            log(f"--- {label}: summary exists, skipping")
            continue
        log(f"--- {label}: {files[0]} ncmoe={ncmoe}")
        pre = tam_sha(files)
        bad = [f for f in files if pre[f] != SUMS[f]]
        if bad:
            log(f"STOP: sha256 mismatch before load: {bad} {pre}")
            sys.exit(2)
        log("  sha256 before load OK")
        if ncmoe == "search":
            ncmoe = search_cn3(files[0])
            if ncmoe is None:
                log(f"STOP: CN3 no even -ncmoe loaded and answered at -c 4096")
                sys.exit(3)
            log(f"  CN3 N = {ncmoe}")
            pre = tam_sha(files)  # re-hash immediately before the measured load
            if any(pre[f] != SUMS[f] for f in files):
                log(f"STOP: sha256 mismatch before CN3 load {pre}"); sys.exit(2)
        stop_server()
        cmd, flags = server_cmd(files[0], ncmoe, f"server-{label}.log")
        ssh(cmd)
        ok, t = wait_ready()
        if not ok:
            log(f"  server not ready ({t:.0f}s); arm FAILED, continuing")
            stop_server()
            json.dump({"label": label, "status": "server failed", "flags": flags}, open(summ, "w"), indent=1)
            continue
        log(f"  server ready in {t:.0f}s: {flags}")
        genout = os.path.join(HERE, f"gen-{label}.json")
        g = subprocess.run([GENPY, GEN, label, genout], capture_output=True, text=True)
        open(os.path.join(HERE, f"gen-{label}.log"), "w").write(g.stdout + g.stderr)
        log("  " + (g.stdout.strip().splitlines() or ["(no output)"])[-1])
        stop_server()
        ssh(f"cp {TWORK}/server-{label}.log {TWORK}/server-{label}.log.keep 2>/dev/null; true")
        post = tam_sha(files)
        void = any(post[f] != pre[f] for f in files)
        if g.returncode != 0 or not os.path.exists(genout):
            log(f"  generation FAILED rc={g.returncode}")
            json.dump({"label": label, "status": "generation failed", "flags": flags, "pre": pre, "post": post},
                      open(summ, "w"), indent=1)
            continue
        vecs, osha = score(label, genout)
        pc = {k: sum(v.values()) for k, v in vecs.items()}
        n = len(vecs["cut"])
        res = {"label": label, "status": "VOID (pre/post sha256 mismatch)" if void else "ok", "flags": flags,
               "ncmoe": ncmoe, "files": files, "sha256_pre": pre, "sha256_post": post, "n": n,
               "passes": pc, "pass_at_1_pct": {k: round(100.0 * p / n, 2) if n else None for k, p in pc.items()},
               "out_sha16": osha, "vector": vecs}
        json.dump(res, open(summ, "w"), indent=1)
        log(f"  {label}: cut {pc['cut']}/{n} ({res['pass_at_1_pct']['cut']}%), raw {pc['raw']}/{n} "
            f"({res['pass_at_1_pct']['raw']}%), out_sha16 {osha}, {res['status']}")
    a, b = (os.path.join(HERE, f"gen-{x}.json") for x in ("A36", "A36-drift"))
    if os.path.exists(a) and os.path.exists(b):
        ta = {k: v["text"] for k, v in json.load(open(a))["results"].items()}
        tb = {k: v["text"] for k, v in json.load(open(b))["results"].items()}
        diff = sorted(k for k in ta if ta[k] != tb.get(k))
        json.dump({"byte_identical": not diff, "differing_tasks": diff}, open(os.path.join(HERE, "drift-check.json"), "w"), indent=1)
        log(f"drift check A36 vs A36-drift: {'byte-identical' if not diff else f'{len(diff)} tasks differ'}")
    paired()
    log("=== MBPP run ALL DONE")


if __name__ == "__main__":
    main()
