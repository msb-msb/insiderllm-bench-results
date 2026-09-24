#!/usr/bin/env python3
"""
Qwen3.8-27B-UD-Q4_K_XL HumanEval pass@1, load bracketed by hash verification.

DIAGNOSTIC ONLY. Reads, hashes, serves, scores. Writes nothing outside its own
output dir. No deploys, no repo changes.

Sequence (no gaps between 2 and 3):
  1. POSIX_FADV_DONTNEED the GGUF; confirm 0% residency via mincore
  2. Buffered read -> sha256; must match EXPECT; abort + physaddr on mismatch
  3. IMMEDIATELY launch llama-server --no-mmap; record the 2->3 gap
  4. HumanEval 164, greedy, official OpenAI human-eval scorer in the sandbox
  5. Residency check, then buffered read -> sha256 again (post-run bracket)
  6. Engine identity

MUST run as root: /proc/self/pagemap masks PFN to 0 otherwise, so a mismatch
would yield no physical address.

Protocol is byte-for-byte the prior run (session b6d2cbb1) so the number is
comparable.
"""
import ctypes, ctypes.util, hashlib, json, mmap, os, shutil
import struct, subprocess, sys, time, urllib.request

# ---------------------------------------------------------------- constants
MODEL = "/home/minotaur/Desktop/qwen3.8-27b-gguf/Qwen3.8-27B-UD-Q4_K_XL.gguf"
EXPECT = "bee238bbeb3dc0a34bde4d0dedbaee1f98c009e8bb4226f03070054c12fb1372"
PRIOR_OFF = 731252997

BIN = "/home/minotaur/llama-bench-src/build/bin/llama-server"
GGML = "/home/minotaur/llama-bench-src/build/bin/libggml-cuda.so"
GENPY = "/home/minotaur/Desktop/lucebox-hub/dflash/.venv/bin/python"
HERE = os.path.dirname(os.path.abspath(__file__))
GEN_SCRIPT = os.path.join(HERE, "he_gen.py")
OUTDIR = os.path.join(HERE, "he38run")
EVALDIR = os.path.join(OUTDIR, "eval")
PORT = 8099
LABEL = "qwen3.8-bracketed"

# prior run baselines (session b6d2cbb1)
PRIOR_PASSES = 132
PRIOR_N = 164
PRIOR_PCT = 80.49
PRIOR_OUT_SHA16 = "987646660b2af81b"
# problems where 3.8 passed and 3.6 failed -> 3.8 MUST pass these
PRIOR_38_ONLY = ["HumanEval/1", "HumanEval/109", "HumanEval/110", "HumanEval/113",
                 "HumanEval/115", "HumanEval/127", "HumanEval/135", "HumanEval/140",
                 "HumanEval/141", "HumanEval/26", "HumanEval/39", "HumanEval/59"]
# problems where 3.6 passed and 3.8 failed -> 3.8 MUST fail these
PRIOR_36_ONLY = ["HumanEval/10", "HumanEval/119", "HumanEval/123", "HumanEval/125",
                 "HumanEval/131", "HumanEval/138", "HumanEval/139", "HumanEval/142",
                 "HumanEval/162", "HumanEval/38", "HumanEval/64", "HumanEval/67",
                 "HumanEval/69", "HumanEval/76", "HumanEval/92"]

PS = 4096
CH = 1 << 22

if os.geteuid() != 0:
    sys.exit("FATAL: not root. A mismatch would yield PFN=0 and no physaddr.")

libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int,
                      ctypes.c_int, ctypes.c_int, ctypes.c_long]
libc.mmap.restype = ctypes.c_void_p
libc.munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
libc.mincore.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_ubyte)]
PROT_READ, MAP_SHARED = 1, 1


def log(s=""):
    print(s, flush=True)


def sh(cmd, **kw):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)


# ---------------------------------------------------------------- primitives
def residency(tag):
    fd = os.open(MODEL, os.O_RDONLY)
    size = os.fstat(fd).st_size
    npages = (size + PS - 1) // PS
    addr = libc.mmap(None, size, PROT_READ, MAP_SHARED, fd, 0)
    vec = (ctypes.c_ubyte * npages)()
    libc.mincore(ctypes.c_void_p(addr), ctypes.c_size_t(size), vec)
    res = sum(1 for i in range(npages) if vec[i] & 1)
    tp = PRIOR_OFF // PS
    pct = 100.0 * res / npages
    log(f"[residency:{tag}] {res:,}/{npages:,} pages ({pct:.2f}%), "
        f"prior-offset page {tp:,} resident={'YES' if vec[tp] & 1 else 'NO'}")
    del vec
    libc.munmap(ctypes.c_void_p(addr), size)
    os.close(fd)
    return res, npages, pct


def evict():
    fd = os.open(MODEL, os.O_RDONLY)
    os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
    os.close(fd)


def buffered_sha256():
    """Normal buffered read -> served from page cache, repopulates it."""
    h = hashlib.sha256()
    t0 = time.time()
    with open(MODEL, "rb", buffering=0) as f:
        while True:
            b = f.read(CH)
            if not b:
                break
            h.update(b)
    return h.hexdigest(), time.time() - t0


def direct_sha256():
    fd = os.open(MODEL, os.O_RDONLY | os.O_DIRECT)
    size = os.fstat(fd).st_size
    buf = mmap.mmap(-1, CH)
    h = hashlib.sha256()
    off = 0
    try:
        while off < size:
            n = os.preadv(fd, [buf], off)
            if n <= 0:
                break
            h.update(memoryview(buf)[:n])
            off += n
    finally:
        buf.close()
        os.close(fd)
    return h.hexdigest()


def virt_to_phys(vaddr):
    with open("/proc/self/pagemap", "rb") as pm:
        pm.seek((vaddr // PS) * 8)
        entry = struct.unpack("<Q", pm.read(8))[0]
    return entry, bool(entry & (1 << 63)), entry & ((1 << 55) - 1)


def capture_mismatch():
    """Locate every differing byte cached-vs-disk and capture physaddr."""
    log("\n" + "=" * 72)
    log("*** HASH MISMATCH — ABORTING RUN, CAPTURING EVIDENCE ***")
    log("=" * 72)
    fd_d = os.open(MODEL, os.O_RDONLY | os.O_DIRECT)
    f_c = open(MODEL, "rb", buffering=0)
    buf = mmap.mmap(-1, CH)
    size = os.fstat(fd_d).st_size
    off, diffs = 0, []
    try:
        while off < size:
            n = os.preadv(fd_d, [buf], off)
            if n <= 0:
                break
            disk = bytes(memoryview(buf)[:n])
            f_c.seek(off)
            cache = f_c.read(n)
            if cache != disk:
                for j in range(n):
                    if cache[j] != disk[j]:
                        diffs.append((off + j, cache[j], disk[j]))
            off += n
    finally:
        buf.close(); f_c.close(); os.close(fd_d)

    log(f"differing bytes: {len(diffs)}")
    fd = os.open(MODEL, os.O_RDONLY)
    size = os.fstat(fd).st_size
    addr = libc.mmap(None, size, PROT_READ, MAP_SHARED, fd, 0)
    for (o, c, d) in diffs:
        x = c ^ d
        bits = [i for i in range(8) if x & (1 << i)]
        direction = "1->0" if (d & x) else "0->1"
        log(f"offset {o} (0x{o:x}): cache=0x{c:02x} disk=0x{d:02x} xor=0x{x:02x} "
            f"bit={','.join(map(str, bits))} dir={direction}")
        log(f"    mod512={o % 512}  mod4096={o % 4096}  mod2MiB={o % (2 << 20)}")
        if o % 4096 == 2309 and x == 0x40:
            log("    !! MATCHES PRIOR SIGNATURE (mod4096==2309, xor==0x40)")
        page_start = (o // PS) * PS
        vaddr = addr + page_start
        ptr = ctypes.cast(ctypes.c_void_p(vaddr), ctypes.POINTER(ctypes.c_ubyte))
        _ = ptr[o % PS]                     # touch so the PTE is populated
        entry, present, pfn = virt_to_phys(vaddr)
        log(f"    vaddr 0x{vaddr:x}  pagemap 0x{entry:016x} present={present}")
        log(f"    PFN 0x{pfn:x} ({pfn})")
        if pfn == 0:
            log("    !! PFN==0 — NOT effectively root, capture FAILED")
        else:
            log(f"    PHYSADDR 0x{(pfn << 12) + (o % PS):x} "
                f"({(pfn << 12) + (o % PS)})")
    libc.munmap(ctypes.c_void_p(addr), size)
    os.close(fd)
    log("=" * 72)


def kill_servers():
    sh("pkill -x llama-server")
    time.sleep(3)


def wait_ready(timeout=600):
    """Proper readiness: HTTP 200 from /health. curl -s exits 0 on 503, which
    broke the prior run's readiness loop."""
    t0 = time.time()
    url = f"http://127.0.0.1:{PORT}/health"
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status == 200:
                    return True, time.time() - t0
        except Exception:
            pass
        time.sleep(1)
    return False, time.time() - t0


# ---------------------------------------------------------------- main
def main():
    os.makedirs(EVALDIR, exist_ok=True)
    log("=" * 72)
    log("Qwen3.8-27B-UD-Q4_K_XL — HumanEval pass@1, hash-bracketed load")
    log(f"model   {MODEL}")
    st = os.stat(MODEL)
    log(f"size    {st.st_size:,}  inode {st.st_ino}")
    log(f"expect  {EXPECT}")
    log(f"euid    {os.geteuid()} (root)")
    log("=" * 72)

    # ---- step 6 evidence gathered up front (does not touch the GGUF cache)
    log("\n### Step 6: engine identity")
    ver = sh(f"{BIN} --version 2>&1 | head -3").stdout.strip()
    log(f"  llama-server --version: {ver.splitlines()[0] if ver else '?'}")
    log(f"  llama-server sha256   : {sh(f'sha256sum {BIN}').stdout.split()[0]}")
    log(f"  libggml-cuda sha256   : {sh(f'sha256sum {GGML}').stdout.split()[0]}")
    log(f"  git describe          : "
        f"{sh('cd /home/minotaur/llama-bench-src && git describe --tags').stdout.strip()}")
    drv = sh("nvidia-smi --query-gpu=driver_version,display_active,memory.used,memory.total "
             "--format=csv,noheader").stdout.strip()
    log(f"  driver,display,mem    : {drv}")
    disp = sh("pgrep -x Xorg >/dev/null && echo true || echo false").stdout.strip()
    log(f"  display_attached      : {disp}")

    kill_servers()

    # ---- step 1
    log("\n### Step 1: evict + confirm 0% residency")
    evict()
    res, npages, pct = residency("post-evict")
    if res != 0:
        log(f"  WARNING: {res} pages still resident after FADV_DONTNEED "
            f"({pct:.2f}%) — eviction incomplete, bracket is weaker.")

    # ---- step 2
    log("\n### Step 2: buffered read -> sha256 (repopulates AND verifies cache)")
    got, el = buffered_sha256()
    log(f"  cached sha256 : {got}")
    log(f"  expected      : {EXPECT}")
    log(f"  read time     : {el:.1f}s")
    if got != EXPECT:
        log("  *** MISMATCH ***")
        log(f"  O_DIRECT sha256: {direct_sha256()}")
        capture_mismatch()
        sys.exit(3)
    log("  MATCH — cache verified clean immediately before load")
    residency("post-verify")
    t2_end = time.time()

    # ---- step 3 (IMMEDIATE, no work in between)
    srvlog = os.path.join(OUTDIR, "server.log")
    cmd = [BIN, "-m", MODEL, "-ngl", "99", "-fa", "on", "-c", "4096",
           "--no-jinja", "--no-mmap", "--port", str(PORT), "--host", "127.0.0.1"]
    lf = open(srvlog, "wb")
    proc = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, start_new_session=True)
    t3_launch = time.time()
    gap = t3_launch - t2_end
    log(f"\n### Step 3: llama-server launched (pid {proc.pid})")
    log(f"  step 2 -> step 3 gap: {gap:.3f} s")
    log(f"  flags: -ngl 99 -fa on -c 4096 --no-jinja --no-mmap --port {PORT}")

    ok, load_s = wait_ready()
    if not ok:
        log(f"  server not ready after {load_s:.0f}s — aborting")
        log(sh(f"tail -20 {srvlog}").stdout)
        proc.terminate()
        sys.exit(4)
    log(f"  ready in {load_s:.0f}s")
    residency("after-model-load")

    # ---- step 4
    log("\n### Step 4: HumanEval 164, greedy, pinned sampling")
    genout = os.path.join(OUTDIR, "he_38_bracket.json")
    env = dict(os.environ)
    env["HF_HOME"] = "/home/minotaur/.cache/huggingface"          # root's HOME is /root
    env["HF_DATASETS_CACHE"] = "/home/minotaur/.cache/huggingface/datasets"
    env["HF_HUB_OFFLINE"] = "1"
    g = subprocess.run([GENPY, GEN_SCRIPT, LABEL, genout], env=env,
                       capture_output=True, text=True)
    log(g.stdout.strip())
    if g.returncode != 0:
        log("generation FAILED:")
        log(g.stderr[-3000:])
        proc.terminate()
        kill_servers()
        sys.exit(5)

    # ---- step 5 BEFORE killing the server, so we measure the state the run saw
    log("\n### Step 5: post-run bracket")
    res2, _, pct2 = residency("pre-postread")
    if pct2 < 99.0:
        log(f"  NOTE: only {pct2:.2f}% resident before the post-run read. Pages "
            f"evicted under memory pressure are re-read from disk, so this "
            f"bracket covers only the pages that survived.")
    got2, el2 = buffered_sha256()
    log(f"  cached sha256 : {got2}")
    log(f"  read time     : {el2:.1f}s")
    post_ok = (got2 == EXPECT)
    if not post_ok:
        log("  *** POST-RUN MISMATCH — the window was open during the run ***")
        log(f"  O_DIRECT sha256: {direct_sha256()}")
        capture_mismatch()
    else:
        log("  MATCH — cache still clean after the run")

    kill_servers()
    try:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=30)
    except Exception as e:
        log(f"  (server cleanup: {e})")

    # ---- scoring
    log("\n### Scoring: official OpenAI human-eval, sandboxed")
    d = json.load(open(genout))
    samples = os.path.join(EVALDIR, "he_38_bracket.jsonl")
    with open(samples, "w") as f:
        for tid, r in d["results"].items():
            f.write(json.dumps({"task_id": tid, "completion": r["text"]}) + "\n")
    log(f"  {len(d['results'])} samples -> {samples}")

    # outputs fingerprint, identical method to the prior run
    out_sha16 = hashlib.sha256(json.dumps(
        {k: v["text"] for k, v in sorted(d["results"].items())}
    ).encode()).hexdigest()[:16]

    os.chmod(OUTDIR, 0o777); os.chmod(EVALDIR, 0o777)
    os.chmod(samples, 0o666)
    sc = sh(f"docker run --rm --network none --cap-drop ALL "
            f"--security-opt no-new-privileges --memory 4g --pids-limit 256 "
            f"-v {EVALDIR}:/work he-scorer:b10088 /work/he_38_bracket.jsonl 2>&1")
    log(sc.stdout.strip()[-2000:])

    # ---- results
    rf = samples + "_results.jsonl"
    vec = {}
    if os.path.exists(rf):
        for line in open(rf):
            r = json.loads(line)
            vec[r["task_id"]] = bool(r["passed"])
    passes = sum(vec.values())
    n = len(vec)
    pct_pass = 100.0 * passes / n if n else 0.0

    log("\n" + "=" * 72)
    log("RESULT")
    log("=" * 72)
    log(f"  pass@1            {pct_pass:.2f}%  ({passes}/{n})")
    log(f"  prior run         {PRIOR_PCT:.2f}%  ({PRIOR_PASSES}/{PRIOR_N})")
    log(f"  reproduces 80.49% {'YES' if (passes == PRIOR_PASSES and n == PRIOR_N) else 'NO'}")
    log(f"  outputs sha256-16 {out_sha16}   prior {PRIOR_OUT_SHA16}   "
        f"{'IDENTICAL' if out_sha16 == PRIOR_OUT_SHA16 else 'DIFFERENT'}")
    log(f"  bracket pre       {EXPECT[:16]}…  MATCH")
    log(f"  bracket post      {got2[:16]}…  {'MATCH' if post_ok else 'MISMATCH'}")
    log(f"  step2->3 gap      {gap:.3f} s")
    log(f"  gen elapsed       {d['elapsed_s']:.0f}s, {d['gen_tokens']} tokens "
        f"({d['gen_tokens']/d['elapsed_s']:.1f} tok/s)")

    log("\n  --- pass/fail vector vs prior ---")
    if out_sha16 == PRIOR_OUT_SHA16:
        log("  Outputs are byte-identical to the prior run, so the pass/fail")
        log("  vector is necessarily identical problem-for-problem.")
    else:
        log("  Outputs DIFFER from the prior run. Checking the 27 problems whose")
        log("  prior 3.8 state is known from the paired 3.6/3.8 breakdown:")
        bad = []
        for t in PRIOR_38_ONLY:
            if vec.get(t) is not True:
                bad.append((t, "expected PASS", vec.get(t)))
        for t in PRIOR_36_ONLY:
            if vec.get(t) is not False:
                bad.append((t, "expected FAIL", vec.get(t)))
        if not bad:
            log("    all 27 known-state problems match the prior vector")
        else:
            for t, exp, act in bad:
                log(f"    {t}: {exp}, got {act}")
        log(f"    (the remaining {n-27} problems have no per-problem record in")
        log("     the prior session — only the 120 both-pass / 17 both-fail counts)")

    json.dump({"pass_at_1": pct_pass, "passes": passes, "n": n,
               "outputs_sha16": out_sha16, "bracket_pre": EXPECT,
               "bracket_post": got2, "gap_s": gap, "vector": vec},
              open(os.path.join(OUTDIR, "summary.json"), "w"), indent=1)
    log(f"\n  summary -> {os.path.join(OUTDIR, 'summary.json')}")
    log("=" * 72)


main()
