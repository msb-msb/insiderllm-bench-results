#!/usr/bin/env python3
"""
Bit-6 page-cache fault soak for Miu. One cycle per invocation; systemd timer
drives the cadence. DIAGNOSTIC ONLY - reads and hashes, changes no config,
deploys nothing, and never evicts the target on the clean path.

Why periodic rather than continuous: the corruption is STABLE (event 4 of
2026-08-15 persisted across re-reads and cleared only under FADV_DONTNEED), so
a check every N minutes detects anything that landed during the idle gap.
Exposure accrues while the pages sit resident, not only while we read them.

Exposure crediting rules:
  - residency 100% at this cycle and hash matches -> credit the interval
  - residency < 100%                              -> BLIND SPOT, credit nothing
  - bench running                                 -> credit (residency is what
                                                     matters; only the hash
                                                     check was deferred)
  - manual pause                                  -> credit nothing
  - reboot detected                               -> discontinuity, credit
                                                     nothing across the gap

MUST run as root: /proc/self/pagemap masks the PFN to 0 otherwise, and the
physical address is the whole point of catching an event.
"""
import ctypes, ctypes.util, hashlib, json, mmap, os, re, struct, subprocess, sys, time
from datetime import datetime, timezone

MODEL = "/home/minotaur/Desktop/qwen3.8-27b-gguf/Qwen3.8-27B-UD-Q4_K_XL.gguf"
EXPECT = "bee238bbeb3dc0a34bde4d0dedbaee1f98c009e8bb4226f03070054c12fb1372"
PRIOR_OFF = 731252997

REPO = "/home/minotaur/Desktop/InsiderLLM"
SOAKDIR = os.path.join(REPO, "docs/bench-results/miu-memfault-soak-2026-08-16")
LOG = os.path.join(SOAKDIR, "soak.log")
EVIDENCE = os.path.join(SOAKDIR, "event")
MARKER = os.path.join(REPO, "MEMFAULT-FIRED.md")
DATED = os.path.join(REPO, "dated-markers.md")
PAUSE = "/home/minotaur/.soak-pause"
STATE = os.path.join(os.environ.get("STATE_DIRECTORY", "/var/lib/miu-memfault-soak"),
                     "state.json")

PERIOD_S = 20 * 60
CREDIT_CAP_S = int(PERIOD_S * 1.5)   # don't credit a suspend/stall as exposure
BENCH_PROCS = ("llama-server", "llama-bench", "llama-cli")
PS = 4096
CH = 1 << 22

libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int,
                      ctypes.c_int, ctypes.c_int, ctypes.c_long]
libc.mmap.restype = ctypes.c_void_p
libc.munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
libc.mincore.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_ubyte)]
PROT_READ, MAP_SHARED = 1, 1


def now():
    return datetime.now().astimezone()


def ts():
    return now().strftime("%Y-%m-%dT%H:%M:%S%z")


def logline(s):
    os.makedirs(SOAKDIR, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(s + "\n")
    print(s, flush=True)


def load_state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(st):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(st, f, indent=1)
    os.replace(tmp, STATE)


def boot_id():
    try:
        with open("/proc/sys/kernel/random/boot_id") as f:
            return f.read().strip()
    except Exception:
        return "?"


def residency():
    """Passive: mmap + mincore. Reads nothing, populates nothing."""
    fd = os.open(MODEL, os.O_RDONLY)
    size = os.fstat(fd).st_size
    npages = (size + PS - 1) // PS
    addr = libc.mmap(None, size, PROT_READ, MAP_SHARED, fd, 0)
    if addr in (None, 2 ** 64 - 1):
        os.close(fd)
        raise OSError("mmap failed")
    vec = (ctypes.c_ubyte * npages)()
    libc.mincore(ctypes.c_void_p(addr), ctypes.c_size_t(size), vec)
    res = sum(1 for i in range(npages) if vec[i] & 1)
    tp = PRIOR_OFF // PS
    tp_res = bool(vec[tp] & 1)
    del vec
    libc.munmap(ctypes.c_void_p(addr), size)
    os.close(fd)
    return res, npages, tp_res


def buffered_sha256():
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


def bench_running():
    for p in BENCH_PROCS:
        r = subprocess.run(["pgrep", "-x", p], capture_output=True)
        if r.returncode == 0:
            return p
    return None


def fmt_h(sec):
    return f"{sec/3600:.2f}h"


def mem_pressure():
    """MemFree / MemAvailable / Cached plus the top three RSS consumers.

    Residency is lost to ordinary memory pressure, so a blind window is only
    interpretable if we recorded what was competing for RAM at the time.
    Top-3 is summed RSS per command name, which OVERCOUNTS shared pages — it
    identifies the competitor, it is not a true footprint. ~0.02s per call.
    """
    try:
        want = {"MemFree", "MemAvailable", "Cached"}
        mi = {}
        for line in open("/proc/meminfo"):
            k, _, v = line.partition(":")
            if k in want:
                mi[k] = int(v.split()[0]) // 1024      # MiB
        out = subprocess.run(["ps", "-eo", "rss=,comm="],
                             capture_output=True, text=True, timeout=15).stdout
        agg = {}
        for line in out.splitlines():
            p = line.split(None, 1)
            if len(p) == 2 and p[0].isdigit():
                agg[p[1].strip()] = agg.get(p[1].strip(), 0) + int(p[0])
        top = sorted(agg.items(), key=lambda x: -x[1])[:3]
        tops = ",".join(f"{c}={r//1024}M" for c, r in top)
        return (f"mem free={mi.get('MemFree','?')}M avail={mi.get('MemAvailable','?')}M "
                f"cached={mi.get('Cached','?')}M | top3rss {tops}")
    except Exception as ex:
        return f"mem unavailable ({ex})"


TS_RE = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d{4}) \| ([A-Z*][A-Z* -]*?) \|")
# every kind that advances the cycle clock. Old names retained so the backfill
# still parses log lines written before the bench-skip fix.
CREDITED_KINDS = {"OK"}
BLIND_KINDS = {"BLINDSPOT", "SKIP-BENCH", "SKIP-BENCH-BLIND", "PAUSE", "PAUSE-BLIND"}
CYCLE_KINDS = CREDITED_KINDS | BLIND_KINDS | {"*** MISMATCH ***"}


def backfill(st):
    """One-time seed of counters added after this run had already started.

    Reads only our own log and runs only when the keys are absent, so it can
    never overwrite live state. Without it the first post-edit cycle would
    report a 0% credit ratio and misrepresent a run already 15h old.
    """
    if "blind_s" in st:
        return st
    run_start = prev = None
    ok = blind = 0
    blind_s = 0.0
    try:
        for line in open(LOG, errors="replace"):
            m = TS_RE.match(line)
            if not m:
                continue
            t = datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S%z").timestamp()
            kind = m.group(2).strip()
            if run_start is None:
                run_start = t
            if kind not in CYCLE_KINDS:
                continue
            iv = 0.0 if prev is None else min(max(0.0, t - prev), CREDIT_CAP_S)
            if kind in CREDITED_KINDS:
                ok += 1
            elif kind in BLIND_KINDS:
                blind += 1
                blind_s += iv
            prev = t
    except FileNotFoundError:
        pass
    st.setdefault("run_start_ts", run_start if run_start else time.time())
    st.setdefault("cycles_credited", ok)
    st.setdefault("cycles_blind", blind)
    st.setdefault("blind_s", blind_s)
    return st


def log_summary(st, t_now):
    """Running state, so health is readable without reconstructing timestamps.
    credit_ratio is the honest metric: a soak at 60% is much weaker than its
    calendar age suggests."""
    cred = float(st.get("credited_s", 0.0))
    blind = float(st.get("blind_s", 0.0))
    wall = max(0.0, t_now - float(st.get("run_start_ts", t_now)))
    ratio = (cred / wall * 100.0) if wall > 0 else 0.0
    logline(f"{ts()} | SUMMARY | cycles_total={st.get('cycles',0)} "
            f"cycles_credited={st.get('cycles_credited',0)} "
            f"cycles_blind={st.get('cycles_blind',0)} "
            f"credited={cred/3600:.2f}h blind={blind/3600:.2f}h "
            f"wall={wall/3600:.2f}h credit_ratio={ratio:.1f}%")


# ------------------------------------------------------------------ mismatch
def virt_to_phys(vaddr):
    with open("/proc/self/pagemap", "rb") as pm:
        pm.seek((vaddr // PS) * 8)
        entry = struct.unpack("<Q", pm.read(8))[0]
    return entry, bool(entry & (1 << 63)), entry & ((1 << 55) - 1)


def capture(cached_hash):
    """Full evidence capture. Order matters: no DONTNEED, no cache drop."""
    os.makedirs(EVIDENCE, exist_ok=True)
    out = []

    def e(s):
        out.append(s)
        print(s, flush=True)

    e("=" * 72)
    e(f"MEMFAULT EVENT — {ts()}")
    e("=" * 72)
    e(f"cached sha256 : {cached_hash}")
    e(f"expected      : {EXPECT}")

    # (b) disk still clean?
    d = direct_sha256()
    e(f"O_DIRECT sha256: {d}")
    e(f"disk verdict  : {'DISK CLEAN — this is RAM' if d == EXPECT else 'DISK ALSO WRONG — not a pure RAM fault'}")

    # (c) byte diff
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
    e(f"differing bytes: {len(diffs)}")

    # (d) physaddr  (e) stability
    fd = os.open(MODEL, os.O_RDONLY)
    addr = libc.mmap(None, size, PROT_READ, MAP_SHARED, fd, 0)
    sigs = []
    for (o, c, dd) in diffs:
        x = c ^ dd
        bits = [i for i in range(8) if x & (1 << i)]
        direction = "1->0" if (dd & x) else "0->1"
        e(f"offset {o} (0x{o:x}): cache=0x{c:02x} disk=0x{dd:02x} xor=0x{x:02x} "
          f"bit={','.join(map(str,bits))} dir={direction}")
        e(f"    mod512={o%512}  mod4096={o%4096}  mod2MiB={o%(2<<20)}")
        if o % 4096 == 2309 and x == 0x40:
            e("    !! MATCHES PRIOR SIGNATURE (mod4096==2309, xor==0x40)")
        page_start = (o // PS) * PS
        vaddr = addr + page_start
        ptr = ctypes.cast(ctypes.c_void_p(vaddr), ctypes.POINTER(ctypes.c_ubyte))
        _ = ptr[o % PS]
        entry, present, pfn = virt_to_phys(vaddr)
        e(f"    pagemap 0x{entry:016x} present={present}")
        if pfn == 0:
            e("    PFN=0 — ROOT CAPTURE FAILED, no physical address obtained")
            phys = None
        else:
            phys = (pfn << 12) + (o % PS)
            e(f"    PFN 0x{pfn:x}   PHYSADDR 0x{phys:x} ({phys})")
        # (e) stability: two re-reads, no eviction
        for k in (1, 2):
            with open(MODEL, "rb", buffering=0) as f:
                f.seek(page_start)
                b = f.read(PS)[o % PS]
            e(f"    re-read #{k}: cached=0x{b:02x} "
              f"{'STILL CORRUPT' if b != dd else 'now clean (TRANSIENT)'}")
        sigs.append((o, c, dd, x, bits, direction, pfn, phys))
    libc.munmap(ctypes.c_void_p(addr), size)
    os.close(fd)
    e("=" * 72)

    txt = "\n".join(out)
    with open(os.path.join(EVIDENCE, f"event-{now():%Y%m%dT%H%M%S}.txt"), "w") as f:
        f.write(txt + "\n")
    return sigs, txt


def write_marker(sigs, txt):
    stamp = now().isoformat()
    L = [f"# MEMORY FAULT SOAK FIRED — {stamp}", ""]
    L.append("The bit-6 page-cache fault recurred on Miu. The soak has stopped and")
    L.append("the corrupted page cache has been left intact for inspection.")
    L.append("")
    L.append("## Signature")
    L.append("")
    if not sigs:
        L.append("Hash mismatched but no differing byte was located on re-scan.")
    for (o, c, d, x, bits, direction, pfn, phys) in sigs:
        L.append(f"- offset **{o}** (0x{o:x}): cache=`0x{c:02x}` disk=`0x{d:02x}` "
                 f"xor=`0x{x:02x}` bit={','.join(map(str,bits))} dir={direction}")
        L.append(f"  - `offset % 4096 = {o%4096}`, `% 512 = {o%512}`")
        if phys is not None:
            L.append(f"  - **PFN `0x{pfn:x}` — PHYSADDR `0x{phys:x}` ({phys})**")
            L.append(f"  - A targeted memtest86+ range is now possible around this address.")
        else:
            L.append("  - **PFN came back 0 — the root capture FAILED, no physical "
                     "address was obtained.**")
    L += ["", "## Do not disturb yet", "",
          "- The corrupt pages are still cached. Do **not** run `POSIX_FADV_DONTNEED`,",
          "  drop caches, or reboot until the address above has been used.",
          "- Evicting destroys the evidence; that is what happened on 2026-08-15.",
          "", "## Context", "",
          "- Full record: `docs/memory-fault-2026-08-15.md`",
          f"- Soak log: `docs/bench-results/miu-memfault-soak-2026-08-16/soak.log`",
          f"- Raw capture: `docs/bench-results/miu-memfault-soak-2026-08-16/event/`",
          "",
          "**This file will not clear itself. Delete it once actioned.**", "",
          "<details><summary>Full capture</summary>", "", "```", txt, "```", "",
          "</details>", ""]
    with open(MARKER, "w") as f:
        f.write("\n".join(L))

    # morning-brief.py hardcodes QWEN38-27B-FIRED.md and does not glob for
    # *-FIRED.md, so this marker alone would never surface. dated-markers.md is
    # the generic channel the brief actually reads.
    try:
        line = (f"{now():%Y-%m-%d} | MEMFAULT-FIRED.md present — bit-6 page-cache "
                f"fault recurred on Miu | physaddr captured; do not evict or reboot; "
                f"see docs/memory-fault-2026-08-15.md\n")
        with open(DATED, "a") as f:
            f.write(line)
    except Exception as ex:
        print(f"(could not append dated marker: {ex})", flush=True)


def stop_timer():
    for cmd in (["systemctl", "stop", "miu-memfault-soak.timer"],
                ["systemctl", "disable", "miu-memfault-soak.timer"]):
        try:
            subprocess.run(cmd, capture_output=True, timeout=30)
        except Exception:
            pass


# ---------------------------------------------------------------------- main
def main():
    if os.geteuid() != 0:
        logline(f"{ts()} | ERROR | not root — PFN would mask to 0; refusing to run")
        sys.exit(1)

    st = load_state()
    if st.get("stopped"):
        print("soak already stopped after an event; exiting", flush=True)
        return
    st = backfill(st)          # seed counters added mid-run; never overwrites

    t_now = time.time()
    bid = boot_id()
    last = st.get("last_ts")
    credited = float(st.get("credited_s", 0.0))
    cycles = int(st.get("cycles", 0)) + 1
    disc = int(st.get("discontinuities", 0))

    # reboot / first run -> exposure discontinuity, credit nothing across the gap
    rebooted = (st.get("boot_id") != bid)
    interval = 0.0 if (rebooted or last is None) else max(0.0, t_now - last)
    capped = False
    if interval > CREDIT_CAP_S:
        interval = CREDIT_CAP_S
        capped = True

    if rebooted:
        disc += 1
        logline(f"{ts()} | DISCONTINUITY | reboot or first start (boot_id={bid[:8]}) "
                f"| cache is cold, re-verifying before crediting | credited={fmt_h(credited)}")

    st.update(boot_id=bid, cycles=cycles, discontinuities=disc)

    # residency is passive (no I/O), so it is safe even mid-bench and is read
    # BEFORE the pause/bench skips — the measurement is cheap and tells us how
    # much a bench or a pause window actually evicted.
    try:
        res, npages, tp_res = residency()
    except Exception as ex:
        logline(f"{ts()} | ERROR | residency check failed: {ex}")
        st.update(last_ts=t_now, credited_s=credited)
        save_state(st)
        return
    pct = 100.0 * res / npages
    rstr = (f"resident={res}/{npages} ({pct:.2f}%) "
            f"p{PRIOR_OFF // PS}={'Y' if tp_res else 'N'}")

    # manual pause: skip AND blind. A paused soak accrues no evidence, so the
    # interval must not be credited and must show up in blind_hours.
    if os.path.exists(PAUSE):
        blind_s = float(st.get("blind_s", 0.0)) + interval
        logline(f"{ts()} | PAUSE-BLIND | {rstr} | {PAUSE} present | interval NOT "
                f"credited, counted as blind | blind_total={fmt_h(blind_s)} | "
                f"credited={fmt_h(credited)} | cycles={cycles} | {mem_pressure()}")
        st.update(last_ts=t_now, credited_s=credited, blind_s=blind_s,
                  cycles_blind=int(st.get("cycles_blind", 0)) + 1)
        save_state(st)
        log_summary(st, t_now)
        return

    # bench guard: skip the 33s hash burst AND treat the interval as blind.
    #
    # This originally credited the interval, reasoning that only the check was
    # deferred while residency held. That is wrong for our actual protocol: a
    # --no-mmap bench copies the full 17.9 GB model into heap, which is exactly
    # the pressure that evicts page-cache pages. So a bench window is blind by
    # construction, and crediting it inflated the exposure figure — the same
    # failure class as the broken_for bug, a path unable to report its own bad
    # condition. Residency is still recorded above so the eviction is visible.
    b = bench_running()
    if b:
        blind_s = float(st.get("blind_s", 0.0)) + interval
        logline(f"{ts()} | SKIP-BENCH-BLIND | {rstr} | {b} running, hash deferred | "
                f"interval NOT credited, counted as blind | "
                f"blind_total={fmt_h(blind_s)} | credited={fmt_h(credited)} | "
                f"cycles={cycles} | {mem_pressure()}")
        st.update(last_ts=t_now, credited_s=credited, blind_s=blind_s,
                  cycles_blind=int(st.get("cycles_blind", 0)) + 1)
        save_state(st)
        log_summary(st, t_now)
        return

    # blind spot: a corrupted page evicted under pressure reloads clean
    if res < npages:
        # resid_broken_since is set on the FIRST broken cycle and cleared ONLY
        # when a later cycle observes 100% residency at its START (see below).
        # It is deliberately NOT cleared on a matching repopulation hash: a
        # clean re-read proves the data is clean, it does not prove the blind
        # window ended. Clearing it here was the bug that pinned broken_for
        # at 0.00h for every blind cycle of the 2026-08-16 run.
        broke = st.get("resid_broken_since") or t_now
        blind_s = float(st.get("blind_s", 0.0)) + interval
        logline(f"{ts()} | BLINDSPOT | {rstr} | residency BROKEN — interval NOT "
                f"credited; an evicted corrupt page would reload clean and the "
                f"event is unrecoverable | broken_for={fmt_h(t_now-broke)} | "
                f"blind_total={fmt_h(blind_s)} | "
                f"credited={fmt_h(credited)} | cycles={cycles} | {mem_pressure()}")
        got, el = buffered_sha256()          # repopulate
        ok = (got == EXPECT)
        logline(f"{ts()} | BLINDSPOT-REPOP | hash={'MATCH' if ok else 'MISMATCH'} "
                f"| read={el:.1f}s | cache repopulated, exposure clock resumes next cycle")
        st.update(last_ts=t_now, credited_s=credited, blind_s=blind_s,
                  cycles_blind=int(st.get("cycles_blind", 0)) + 1,
                  resid_broken_since=broke)
        save_state(st)
        log_summary(st, t_now)
        if not ok:
            sigs, txt = capture(got)
            write_marker(sigs, txt)
            st.update(stopped=True, stopped_at=ts())
            save_state(st)
            stop_timer()
        return

    # 100% resident observed at the START of this cycle -> the blind window,
    # if any, is genuinely over. This is the only place the marker is cleared.
    st["resid_broken_since"] = None

    got, el = buffered_sha256()
    if got == EXPECT:
        credited += interval
        logline(f"{ts()} | OK | {rstr} | hash=MATCH | read={el:.1f}s | "
                f"credited={fmt_h(credited)}{' (capped)' if capped else ''} | "
                f"cycles={cycles} | {mem_pressure()}")
        st.update(last_ts=t_now, credited_s=credited,
                  cycles_credited=int(st.get("cycles_credited", 0)) + 1)
        save_state(st)
        log_summary(st, t_now)
        return

    # ---- event
    credited += interval
    logline(f"{ts()} | *** MISMATCH *** | {rstr} | hash={got[:16]}… | read={el:.1f}s | "
            f"credited={fmt_h(credited)} | cycles={cycles} | CAPTURING, SOAK STOPPING "
            f"| {mem_pressure()}")
    st.update(last_ts=t_now, credited_s=credited)
    save_state(st)
    log_summary(st, t_now)
    sigs, txt = capture(got)
    write_marker(sigs, txt)
    st.update(stopped=True, stopped_at=ts())
    save_state(st)
    stop_timer()
    logline(f"{ts()} | STOPPED | evidence captured; cache left intact — do not "
            f"evict or reboot | marker={MARKER}")


main()
