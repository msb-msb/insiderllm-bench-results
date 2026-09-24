#!/usr/bin/env python3
"""HumanEval CHAT-path arm: Qwen 3.6-27B and 3.8-27B, two seeds each.

NEW ARM. The published raw-completion result (3.6 82.32%, 3.8 80.49%) stands
and is not touched by this.

Four independent runs, each fully bracketed against the unresolved bit-6
page-cache fault:
   evict -> mincore 0% -> buffered sha256 vs upstream -> launch (gap recorded)
   -> generate -> buffered sha256 again.
Abort + physaddr capture on any mismatch. MUST run as root.

Resumable: a run whose generation JSON already exists is skipped.
"""
import ctypes, ctypes.util, hashlib, json, mmap, os, struct, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "chatrun")
PORT = 8099
BIN = "/home/minotaur/llama-bench-src/build/bin/llama-server"
GENPY = "/home/minotaur/Desktop/lucebox-hub/dflash/.venv/bin/python"
GEN = os.path.join(HERE, "chat_gen.py")

MODELS = {
    "3.8": ("/home/minotaur/Desktop/qwen3.8-27b-gguf/Qwen3.8-27B-UD-Q4_K_XL.gguf",
            "bee238bbeb3dc0a34bde4d0dedbaee1f98c009e8bb4226f03070054c12fb1372"),
    "3.6": ("/home/minotaur/Desktop/lucebox-hub/dflash/models/unsloth/Qwen3.6-27B-UD-Q4_K_XL.gguf",
            "ff6941ded525b34eb159496762c29dd0ec6e71dc31b74d57e75d871a03eec259"),
}
SEEDS = [42, 43]
# Pilot overrides. CHAT_LIMIT is passed through to the generator, which takes
# the FIRST N problems in canonical order. Defaults reproduce the full run.
TAGS = [t for t in os.environ.get("CHAT_MODELS", "3.8,3.6").split(",") if t]
SEEDS = [int(s) for s in os.environ.get("CHAT_SEEDS", "42,43").split(",") if s]
LIMIT = os.environ.get("CHAT_LIMIT", "")
SUFFIX = f"_pilot{LIMIT}" if LIMIT else ""
PS, CH = 4096, 1 << 22
PRIOR_OFF = 731252997

if os.geteuid() != 0:
    sys.exit("FATAL: not root. A mismatch would yield PFN=0 and no physaddr.")

libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int,
                      ctypes.c_int, ctypes.c_int, ctypes.c_long]
libc.mmap.restype = ctypes.c_void_p
libc.munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
libc.mincore.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_ubyte)]


def log(s=""):
    print(s, flush=True)


def residency(path):
    fd = os.open(path, os.O_RDONLY)
    size = os.fstat(fd).st_size
    n = (size + PS - 1) // PS
    addr = libc.mmap(None, size, 1, 1, fd, 0)
    vec = (ctypes.c_ubyte * n)()
    libc.mincore(ctypes.c_void_p(addr), ctypes.c_size_t(size), vec)
    res = sum(1 for i in range(n) if vec[i] & 1)
    del vec
    libc.munmap(ctypes.c_void_p(addr), size)
    os.close(fd)
    return res, n


def evict(path):
    fd = os.open(path, os.O_RDONLY)
    os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
    os.close(fd)


def bsha(path):
    h = hashlib.sha256()
    t0 = time.time()
    with open(path, "rb", buffering=0) as f:
        while True:
            b = f.read(CH)
            if not b:
                break
            h.update(b)
    return h.hexdigest(), time.time() - t0


def dsha(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECT)
    size = os.fstat(fd).st_size
    buf = mmap.mmap(-1, CH)
    h = hashlib.sha256()
    off = 0
    try:
        while off < size:
            k = os.preadv(fd, [buf], off)
            if k <= 0:
                break
            h.update(memoryview(buf)[:k])
            off += k
    finally:
        buf.close(); os.close(fd)
    return h.hexdigest()


def capture(path, cached):
    """Byte diff + PFN/physaddr. Same procedure as the 08-16 bracket."""
    log("=" * 72); log("*** HASH MISMATCH — ABORTING, CAPTURING EVIDENCE ***"); log("=" * 72)
    log(f"cached  {cached}")
    log(f"direct  {dsha(path)}")
    fd_d = os.open(path, os.O_RDONLY | os.O_DIRECT)
    f_c = open(path, "rb", buffering=0)
    buf = mmap.mmap(-1, CH)
    size = os.fstat(fd_d).st_size
    off, diffs = 0, []
    try:
        while off < size:
            n = os.preadv(fd_d, [buf], off)
            if n <= 0:
                break
            disk = bytes(memoryview(buf)[:n]); f_c.seek(off); cache = f_c.read(n)
            if cache != disk:
                for j in range(n):
                    if cache[j] != disk[j]:
                        diffs.append((off + j, cache[j], disk[j]))
            off += n
    finally:
        buf.close(); f_c.close(); os.close(fd_d)
    log(f"differing bytes: {len(diffs)}")
    fd = os.open(path, os.O_RDONLY)
    addr = libc.mmap(None, size, 1, 1, fd, 0)
    for (o, c, d) in diffs:
        x = c ^ d
        bits = [i for i in range(8) if x & (1 << i)]
        log(f"offset {o} (0x{o:x}): cache=0x{c:02x} disk=0x{d:02x} xor=0x{x:02x} "
            f"bit={','.join(map(str,bits))} dir={'1->0' if (d & x) else '0->1'}")
        log(f"    mod4096={o%4096} mod512={o%512}")
        if o % 4096 == 2309 and x == 0x40:
            log("    !! MATCHES PRIOR SIGNATURE")
        pgs = (o // PS) * PS
        v = addr + pgs
        _ = ctypes.cast(ctypes.c_void_p(v), ctypes.POINTER(ctypes.c_ubyte))[o % PS]
        with open("/proc/self/pagemap", "rb") as pm:
            pm.seek((v // PS) * 8)
            ent = struct.unpack("<Q", pm.read(8))[0]
        pfn = ent & ((1 << 55) - 1)
        log(f"    pagemap 0x{ent:016x} present={bool(ent>>63&1)} PFN 0x{pfn:x}")
        log("    !! PFN==0, ROOT CAPTURE FAILED" if pfn == 0
            else f"    PHYSADDR 0x{(pfn<<12)+(o%PS):x}")
    libc.munmap(ctypes.c_void_p(addr), size); os.close(fd)
    log("=" * 72)


def kill_servers():
    subprocess.run(["pkill", "-x", "llama-server"], capture_output=True)
    time.sleep(4)


def wait_ready(timeout=900):
    import urllib.request
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2) as r:
                if r.status == 200:
                    return True, time.time() - t0
        except Exception:
            pass
        time.sleep(1)
    return False, time.time() - t0


def run(tag, seed):
    path, expect = MODELS[tag]
    genout = os.path.join(OUT, f"chat_{tag}_s{seed}{SUFFIX}.json")
    if os.path.exists(genout):
        log(f"\n### {tag} seed {seed}: already done, skipping ({genout})")
        return True
    log("\n" + "=" * 72)
    log(f"### {tag}  seed {seed}   {os.path.basename(path)}")
    log("=" * 72)
    kill_servers()

    evict(path)
    res, n = residency(path)
    log(f"  [1] evicted -> resident {res}/{n} ({100.0*res/n:.2f}%)")
    if res:
        log(f"      WARNING {res} pages still resident; bracket is weaker")

    got, el = bsha(path)
    log(f"  [2] cached sha256 {got}")
    log(f"      expected      {expect}   read {el:.1f}s")
    if got != expect:
        capture(path, got)
        return False
    log("      MATCH")
    t2 = time.time()

    srvlog = os.path.join(OUT, f"server_{tag}_s{seed}{SUFFIX}.log")
    cmd = [BIN, "-m", path, "-ngl", "99", "-fa", "on", "-c", "32768",
           "--jinja", "--no-mmap", "--reasoning-format", "deepseek-legacy",
           "--port", str(PORT), "--host", "127.0.0.1"]
    lf = open(srvlog, "wb")
    p = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT,
                         stdin=subprocess.DEVNULL, start_new_session=True)
    gap = time.time() - t2
    log(f"  [3] launched pid {p.pid}, step2->3 gap {gap:.3f}s")
    ok, load = wait_ready()
    if not ok:
        log(f"      server not ready after {load:.0f}s — aborting")
        log(subprocess.run(["tail", "-20", srvlog], capture_output=True, text=True).stdout)
        p.terminate(); return False
    log(f"      ready in {load:.0f}s")

    env = dict(os.environ)
    if LIMIT:
        env["CHAT_LIMIT"] = LIMIT
    env.update(HF_HOME="/home/minotaur/.cache/huggingface",
               HF_DATASETS_CACHE="/home/minotaur/.cache/huggingface/datasets",
               HF_HUB_OFFLINE="1")
    g = subprocess.run([GENPY, GEN, f"qwen{tag}-chat-s{seed}", genout, str(seed)],
                       env=env)
    if g.returncode != 0:
        log("  generation FAILED"); p.terminate(); kill_servers(); return False

    got2, el2 = bsha(path)
    log(f"  [4] post-run sha256 {got2}  read {el2:.1f}s  "
        f"{'MATCH' if got2 == expect else '*** MISMATCH ***'}")
    if got2 != expect:
        capture(path, got2)
    d = json.load(open(genout)); d["bracket"] = {
        "pre": got, "post": got2, "gap_s": gap, "load_s": load,
        "resident_after_evict": res, "pages": n}
    json.dump(d, open(genout, "w"), indent=1)
    kill_servers()
    return got2 == expect


os.makedirs(OUT, exist_ok=True)
log(f"CHAT-path HumanEval arm — started {time.strftime('%Y-%m-%d %H:%M:%S')}")
log(f"euid {os.geteuid()} (root)")
allok = True
for tag in TAGS:
    for seed in SEEDS:
        if not run(tag, seed):
            allok = False
            log(f"\n!!! {tag} seed {seed} FAILED — stopping")
            break
    if not allok:
        break
log(f"\nDONE allok={allok}. Generation JSONs in {OUT}")
log("Next: extraction samples, then scoring. Neither has run yet.")
