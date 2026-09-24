#!/usr/bin/env python3
"""Ornith-1.5-35B-A3B vs Qwen3.6-35B-A3B — A-B-B-A llama-bench, one session.

Same protocol as the published 2026-08-14 Qwen3.8-vs-3.6 rows
(comparison_set qwen38-vs-qwen36-20260814):

  four slots, A1 B1 B2 A2, one session, page cache dropped between every slot,
  each slot bracketed against the page-cache fault -
     evict -> mincore 0% -> buffered sha256 vs UPSTREAM -> launch immediately
     (step2->3 gap recorded) -> bench -> residency -> buffered sha256 again.
  Abort + physaddr capture on any mismatch. MUST run as root: /proc/self/pagemap
  masks the PFN to 0 otherwise, so a mismatch would yield no physical address.

A is the new model (Ornith), B the incumbent (Qwen 3.6), matching 08-14 where
A was the newcomer 3.8 and B the incumbent 3.6.

The harness string is byte-identical to the published rows so the new rows are
comparable:  -ngl 99 -fa 1 -p 512 -n 128 -d 0,4096,8192 -r 5
mmap is left at its default (on), as it was on 08-14. That is deliberate and it
makes the bracket STRONGER here, not weaker: the model reads the very page-cache
pages this script hashed, and residency is re-checked after the run.

Writes only inside its own directory. No repo changes, no deploys, no network.
"""
import ctypes, ctypes.util, hashlib, json, mmap, os, statistics, struct
import subprocess, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
SLOTDIR = os.path.join(HERE, "slots")
LOGPATH = os.path.join(HERE, "run.log")
PIDPATH = os.path.join(HERE, "harness.pid")
RESULTS = os.path.join(HERE, "results.json")

BIN = "/home/minotaur/llama-bench-src/build/bin/llama-bench"

# (tag, path, upstream sha256, where that digest came from)
# Ornith ships on Storage_Disk_1, which is a 7200rpm HGST: a bracket hash reads
# at ~129 MB/s there (2m50s for the file) against ~500 MB/s on the NVMe where
# the Qwen bench copy lives. Set ORNITH_GGUF to a staged NVMe copy to cut ~8min
# of hashing AND to equalise load time between the two models, which is what
# A-B-B-A relies on to cancel thermal drift. The hash check is unchanged either
# way, so a bad copy cannot pass.
# Default is the NVMe bench copy, staged and re-verified against the upstream
# oid there on 2026-08-28. Set ORNITH_GGUF to override (e.g. back to the HDD
# original) — but note sudo strips the environment, so an override has to be
# passed as `sudo ORNITH_GGUF=... ./ornith_abba.py`, not as a shell prefix.
ORNITH_PATH = os.environ.get(
    "ORNITH_GGUF",
    "/home/minotaur/bench-models/Ornith-1.5-35B-A3B-Q4_K_M.gguf")

ORNITH = ("ornith-1.5-35b-a3b",
          ORNITH_PATH,
          "12d8d5c01bae7f23ea4822b2f96ba069d531f827d02a57c31002f2f95e72614a",
          "bartowski LFS oid, recorded in the model README at download (2026-08-26)")
QWEN36 = ("qwen3.6-35b-a3b",
          "/home/minotaur/bench-models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf",
          "ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61",
          "unsloth LFS oid, recovered from the huggingface_hub download metadata "
          "(repo commit a483e9e6cbd595906af30beda3187c2663a1118c) and verified "
          "against the file 2026-08-28")

# A-B-B-A. position is 1-indexed and goes into the row provenance.
SLOTS = [("A1", ORNITH, 1), ("B1", QWEN36, 2), ("B2", QWEN36, 3), ("A2", ORNITH, 4)]

BENCH_ARGS = ["-ngl", "99", "-fa", "1", "-p", "512", "-n", "128",
              "-d", "0,4096,8192", "-r", "5"]
HARNESS_STR = "llama-bench " + " ".join(BENCH_ARGS)

PS, CH = 4096, 1 << 22
LOG_CAP_BYTES = 64 << 20   # see note in log(): cap that does NOT kill the run

if os.geteuid() != 0:
    sys.exit("FATAL: not root. A hash mismatch would yield PFN=0 and no "
             "physaddr, which is the one thing the bracket exists to capture.")

libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int,
                      ctypes.c_int, ctypes.c_int, ctypes.c_long]
libc.mmap.restype = ctypes.c_void_p
libc.munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
libc.mincore.argtypes = [ctypes.c_void_p, ctypes.c_size_t,
                         ctypes.POINTER(ctypes.c_ubyte)]

_logf = open(LOGPATH, "a", buffering=1)
_capped = [False]


def log(s=""):
    # A ulimit -f cap (run-matrix.sh style) is wrong for a bench: SIGXFSZ would
    # kill the run mid-slot and lose the GPU time. Cap the FILE, keep benching,
    # and keep stdout so a tmux pane still shows everything.
    print(s, flush=True)
    if _capped[0]:
        return
    if _logf.tell() > LOG_CAP_BYTES:
        _logf.write(f"*** LOG CAP {LOG_CAP_BYTES} B REACHED — file logging stops, "
                    f"run continues; see stdout ***\n")
        _capped[0] = True
        return
    _logf.write(s + "\n")


# ----------------------------------------------------------- bracket primitives
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
    """Buffered read -> served through the page cache, and repopulates it."""
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
    """Byte diff + PFN/physaddr. Same procedure as the 08-16 and 08-17 brackets."""
    log("=" * 72)
    log("*** HASH MISMATCH — ABORTING, CAPTURING EVIDENCE ***")
    log("=" * 72)
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
            f"bit={','.join(map(str, bits))} dir={'1->0' if (d & x) else '0->1'}")
        log(f"    mod4096={o % 4096} mod512={o % 512}")
        if o % 4096 == 2309 and x == 0x40:
            log("    !! MATCHES PRIOR SIGNATURE (bit 6, offset mod4096 == 2309)")
        pgs = (o // PS) * PS
        v = addr + pgs
        _ = ctypes.cast(ctypes.c_void_p(v), ctypes.POINTER(ctypes.c_ubyte))[o % PS]
        with open("/proc/self/pagemap", "rb") as pm:
            pm.seek((v // PS) * 8)
            ent = struct.unpack("<Q", pm.read(8))[0]
        pfn = ent & ((1 << 55) - 1)
        log(f"    pagemap 0x{ent:016x} present={bool(ent >> 63 & 1)} PFN 0x{pfn:x}")
        log("    !! PFN==0, ROOT CAPTURE FAILED" if pfn == 0
            else f"    PHYSADDR 0x{(pfn << 12) + (o % PS):x}")
    libc.munmap(ctypes.c_void_p(addr), size); os.close(fd)
    log("=" * 72)


# ---------------------------------------------------------------- gpu telemetry
class Telemetry(threading.Thread):
    """Per-slot thermal/power/VRAM block, as published in provenance.run_slots."""
    Q = ("--query-gpu=temperature.gpu,clocks.sm,power.draw,memory.used"
         ",clocks_throttle_reasons.active")

    def __init__(self):
        super().__init__(daemon=True)
        self.stop = threading.Event()
        self.samples = []

    def sample(self):
        r = subprocess.run(["nvidia-smi", self.Q, "--format=csv,noheader,nounits"],
                           capture_output=True, text=True)
        if r.returncode != 0 or not r.stdout.strip():
            return None
        f = [x.strip() for x in r.stdout.strip().splitlines()[0].split(",")]
        try:
            return dict(temp=int(f[0]), sm=int(f[1]), pw=float(f[2]),
                        vram=int(f[3]), throttle=f[4] if len(f) > 4 else "")
        except (ValueError, IndexError):
            return None

    def run(self):
        while not self.stop.wait(1.0):
            s = self.sample()
            if s:
                self.samples.append(s)

    def block(self, start_temp):
        if not self.samples:
            return {"start_temp_c": start_temp}
        t = [s["temp"] for s in self.samples]
        thr = sorted({s["throttle"] for s in self.samples
                      if s["throttle"] and s["throttle"] != "Not Active"
                      and set(s["throttle"].replace("0x", "")) != {"0"}})
        return {
            "start_temp_c": start_temp,
            "temp_max_c": max(t),
            "temp_end_c": t[-1],
            "sm_clock_mhz": max(s["sm"] for s in self.samples),
            "power_draw_w": round(max(s["pw"] for s in self.samples), 2),
            "vram_peak_mib": max(s["vram"] for s in self.samples),
            "samples": len(self.samples),
            "throttle_reasons_seen": thr,
        }


def gpu_idle_mib():
    r = subprocess.run(["nvidia-smi", "--query-gpu=memory.used",
                        "--format=csv,noheader,nounits"],
                       capture_output=True, text=True)
    try:
        return int(r.stdout.strip().splitlines()[0])
    except (ValueError, IndexError):
        return -1


def gpu_temp():
    r = subprocess.run(["nvidia-smi", "--query-gpu=temperature.gpu",
                        "--format=csv,noheader,nounits"],
                       capture_output=True, text=True)
    try:
        return int(r.stdout.strip().splitlines()[0])
    except (ValueError, IndexError):
        return -1


def kill_strays():
    # -x, never -f: a -f pattern matches the full command line of every process
    # INCLUDING the shell doing the matching, so it kills the killer. That is
    # invariant (y), already hit twice in this tree.
    for name in ("llama-bench", "llama-server", "llama-cli"):
        subprocess.run(["pkill", "-x", name], capture_output=True)
    time.sleep(2)


# --------------------------------------------------------------------- one slot
def run_slot(slot, model, position):
    tag, path, expect, digest_src = model
    out = os.path.join(SLOTDIR, f"{slot}_{tag}.json")
    if os.path.exists(out):
        log(f"\n### slot {slot} ({tag}) already done — skipping, {out}")
        return json.load(open(out))

    log("\n" + "=" * 72)
    log(f"### slot {slot}   position {position}/4   {tag}")
    log(f"    {path}")
    log("=" * 72)
    kill_strays()

    idle = gpu_idle_mib()
    log(f"  [0] card idle at {idle} MiB before load")

    evict(path)
    res, npages = residency(path)
    log(f"  [1] evicted -> resident {res:,}/{npages:,} pages "
        f"({100.0 * res / npages:.2f}%)")
    if res:
        log(f"      WARNING {res:,} pages still resident; bracket is weaker")

    got, el = bsha(path)
    log(f"  [2] cached sha256 {got}")
    log(f"      upstream      {expect}")
    log(f"      read {el:.1f}s  ({os.path.getsize(path) / el / 1e6:.0f} MB/s)")
    if got != expect:
        capture(path, got)
        return None
    log("      MATCH")

    t2 = time.time()
    cmd = [BIN, "-m", path] + BENCH_ARGS + ["-o", "json", "-oe", "md"]
    start_temp = gpu_temp()
    tel = Telemetry(); tel.start()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         stdin=subprocess.DEVNULL, text=True,
                         start_new_session=True)
    gap = time.time() - t2
    log(f"  [3] launched pid {p.pid}, step2->3 gap {gap:.3f}s")
    stdout, stderr = p.communicate()
    tel.stop.set(); tel.join(timeout=5)
    elapsed = time.time() - t2

    if p.returncode != 0:
        log(f"      llama-bench exited {p.returncode} — slot FAILED")
        log("      last stderr:")
        for line in stderr.strip().splitlines()[-25:]:
            log(f"        {line}")
        return None

    try:
        rows = json.loads(stdout)
    except json.JSONDecodeError:
        log("      could not parse llama-bench JSON — slot FAILED")
        log(stdout[-2000:])
        return None

    log(f"      bench ok, {len(rows)} tests, {elapsed:.0f}s")
    for line in stderr.strip().splitlines():
        if line.startswith("|"):
            log(f"      {line}")

    res2, _ = residency(path)
    log(f"  [4] residency after run {res2:,}/{npages:,} "
        f"({100.0 * res2 / npages:.2f}%)")

    got2, el2 = bsha(path)
    ok2 = got2 == expect
    log(f"  [5] post-run sha256 {got2}  read {el2:.1f}s  "
        f"{'MATCH' if ok2 else '*** MISMATCH ***'}")
    if not ok2:
        capture(path, got2)

    block = tel.block(start_temp)
    log(f"      telemetry {block}")

    rec = {
        "slot": slot, "position": position, "model_tag": tag,
        "model_path": path, "model_bytes": os.path.getsize(path),
        "started": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(t2)),
        "elapsed_s": round(elapsed, 1),
        "bracket": {
            "expected_sha256": expect,
            "digest_source": digest_src,
            "pre_sha256": got, "pre_read_s": round(el, 1),
            "post_sha256": got2, "post_read_s": round(el2, 1),
            "match": ok2,
            "step2_to_3_gap_s": round(gap, 3),
            "pages": npages,
            "resident_after_evict": res,
            "resident_after_run": res2,
        },
        "gpu_idle_mib_before": idle,
        "telemetry": block,
        "llama_bench": rows,
    }
    json.dump(rec, open(out, "w"), indent=1)
    kill_strays()
    return rec if ok2 else None


# ------------------------------------------------------------------- reduction
def tps(rows, kind, depth):
    """kind: 'pp' (n_prompt>0) or 'tg' (n_gen>0), at a given -d depth."""
    for r in rows:
        if r["n_depth"] != depth:
            continue
        if kind == "pp" and r["n_prompt"] > 0:
            return r["avg_ts"], r["stddev_ts"]
        if kind == "tg" and r["n_gen"] > 0 and r["n_prompt"] == 0:
            return r["avg_ts"], r["stddev_ts"]
    return None, None


def reduce_and_report(recs):
    depths = [0, 4096, 8192]
    by_tag = {}
    for r in recs:
        by_tag.setdefault(r["model_tag"], []).append(r)

    log("\n" + "=" * 72)
    log("REPEATABILITY — the gate, not a formality")
    log("=" * 72)
    log("The 08-14 rows read a sub-one-percent between-model gap only because")
    log("same-model repeats landed within 0.02 tok/s. Same test here: a gap is")
    log("readable only if it is larger than the spread that produced it.")

    summary = {"depths": {}, "repeatability": {}}
    worst_tg_spread = 0.0
    for tag, rs in sorted(by_tag.items()):
        rs = sorted(rs, key=lambda x: x["position"])
        log(f"\n{tag}  slots {' '.join(r['slot'] for r in rs)}")
        for d in depths:
            g = [tps(r["llama_bench"], "tg", d)[0] for r in rs]
            pp = [tps(r["llama_bench"], "pp", d)[0] for r in rs]
            if any(v is None for v in g):
                continue
            gs, ps_ = max(g) - min(g), max(pp) - min(pp)
            worst_tg_spread = max(worst_tg_spread, gs)
            summary["repeatability"].setdefault(tag, {})[str(d)] = {
                "tg_slots": [round(v, 2) for v in g],
                "tg_repeat_spread": round(gs, 3),
                "pp_slots": [round(v, 2) for v in pp],
                "pp_repeat_spread": round(ps_, 3),
            }
            log(f"  d={d:<5} tg {'  '.join(f'{v:8.2f}' for v in g)}"
                f"   spread {gs:.3f} tok/s")
            log(f"  {'':<7} pp {'  '.join(f'{v:8.2f}' for v in pp)}"
                f"   spread {ps_:.3f} t/s")

    log("\n" + "=" * 72)
    log("BETWEEN-MODEL, averaged over each model's two slots")
    log("=" * 72)
    tags = sorted(by_tag)
    if len(tags) == 2:
        ta, tb = tags
        for d in depths:
            a = [tps(r["llama_bench"], "tg", d)[0] for r in by_tag[ta]]
            b = [tps(r["llama_bench"], "tg", d)[0] for r in by_tag[tb]]
            if any(v is None for v in a + b):
                continue
            ma, mb = statistics.fmean(a), statistics.fmean(b)
            gap = ma - mb
            spread = max(max(a) - min(a), max(b) - min(b))
            verdict = "RESOLVABLE" if abs(gap) > spread else "UNRESOLVABLE"
            pct = 100.0 * gap / mb if mb else 0.0
            summary["depths"][str(d)] = {
                ta: round(ma, 2), tb: round(mb, 2),
                "gap_tok_s": round(gap, 3), "gap_pct": round(pct, 3),
                "max_repeat_spread": round(spread, 3), "verdict": verdict,
            }
            log(f"  d={d:<5} {ta} {ma:7.2f}   {tb} {mb:7.2f}   "
                f"gap {gap:+.2f} tok/s ({pct:+.2f}%)   "
                f"max repeat spread {spread:.3f}   -> {verdict}")
        log("")
        log("UNRESOLVABLE means the two models differ by less than one model")
        log("differs from itself. Report it as unresolvable, not as a delta —")
        log("that is what the 08-14 run did for prompt processing.")
    return summary


# ------------------------------------------------------------------------ main
def main():
    os.makedirs(SLOTDIR, exist_ok=True)
    with open(PIDPATH, "w") as f:
        f.write(f"{os.getpid()}\n")
    log("\n" + "#" * 72)
    log(f"# Ornith-1.5-35B-A3B vs Qwen3.6-35B-A3B — A-B-B-A")
    log(f"# started {time.strftime('%Y-%m-%dT%H:%M:%S%z')}")
    log(f"# pid {os.getpid()}  (written to {PIDPATH})")
    log(f"# harness {HARNESS_STR}")
    log(f"# order   {' '.join(s for s, _, _ in SLOTS)}")
    log("#" * 72)

    recs, failed = [], None
    for slot, model, position in SLOTS:
        r = run_slot(slot, model, position)
        if r is None:
            failed = slot
            log(f"\n!!! slot {slot} FAILED — stopping. "
                f"Completed slots are kept in {SLOTDIR}.")
            break
        recs.append(r)

    summary = reduce_and_report(recs) if len(recs) >= 2 else {}
    json.dump({
        "run": "miu-ornith-abba-2026-08-28",
        "comparison_set": "ornith15-vs-qwen36-35b-a3b-20260828",
        "run_order": "A-B-B-A",
        "harness": HARNESS_STR,
        "repetitions": 5,
        "engine": "llama.cpp", "engine_build": "b10088",
        "engine_commit": "67b9b0e", "compute": "CUDA sm_86",
        "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "failed_slot": failed,
        "slots": recs,
        "summary": summary,
    }, open(RESULTS, "w"), indent=1)

    # Root-owned artifacts in a git tree are a nuisance to clean up; hand them
    # back to whoever invoked sudo.
    uid, gid = os.environ.get("SUDO_UID"), os.environ.get("SUDO_GID")
    if uid and gid:
        for root, dirs, files in os.walk(HERE):
            for name in dirs + files:
                try:
                    os.chown(os.path.join(root, name), int(uid), int(gid))
                except OSError:
                    pass
        try:
            os.chown(HERE, int(uid), int(gid))
        except OSError:
            pass
        log(f"  artifacts chowned back to uid {uid}:{gid}")

    log(f"\nDONE  slots_ok={len(recs)}/4  failed={failed}")
    log(f"  per-slot : {SLOTDIR}/")
    log(f"  merged   : {RESULTS}")
    log(f"  log      : {LOGPATH}")
    if failed:
        log("\nA failed slot means NO row is publishable from this session.")
    return 0 if failed is None else 1


if __name__ == "__main__":
    sys.exit(main())
