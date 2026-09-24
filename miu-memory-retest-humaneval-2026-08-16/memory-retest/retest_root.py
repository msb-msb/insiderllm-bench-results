#!/usr/bin/env python3
"""
Bit-6 page-cache memory fault re-test on Miu, post-DIMM-reseat.
DIAGNOSTIC ONLY. Reads and hashes. Does not modify the target file,
does not drop caches, changes no config.

Method per docs/memory-fault-2026-08-15.md steps 1-4.
MUST run as root: /proc/self/pagemap masks PFN to 0 otherwise.
"""
import ctypes, ctypes.util, hashlib, mmap, os, struct, sys, time

SMOKE = os.environ.get("RETEST_SMOKE") == "1"

# NOTE: absolute, not expanduser("~"). Under sudo, HOME=/root and the tilde
# resolves to /root/Desktop/... which does not exist.
P = os.environ.get("RETEST_FILE") or \
    "/home/minotaur/Desktop/qwen3.8-27b-gguf/Qwen3.8-27B-UD-Q4_K_XL.gguf"
EXPECT = "bee238bbeb3dc0a34bde4d0dedbaee1f98c009e8bb4226f03070054c12fb1372"
PRIOR_OFF = int(os.environ.get("RETEST_PRIOR_OFF", "731252997"))
CH = 1 << 22          # 4 MiB, page-aligned via mmap(-1)
ITERATIONS = int(os.environ.get("RETEST_ITERATIONS", "20"))
PS = 4096

if os.geteuid() != 0 and not SMOKE:
    sys.exit("FATAL: not root. PFN would mask to 0 and the capture would be worthless.")
if SMOKE:
    print("### SMOKE MODE — exercising code paths only. PFN will be 0. "
          "Not a real diagnostic run.\n", flush=True)

libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int,
                      ctypes.c_int, ctypes.c_int, ctypes.c_long]
libc.mmap.restype = ctypes.c_void_p
libc.munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
libc.mincore.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_ubyte)]
PROT_READ, MAP_SHARED = 1, 1


def log(s=""):
    print(s, flush=True)


def residency(tag):
    fd = os.open(P, os.O_RDONLY)
    size = os.fstat(fd).st_size
    npages = (size + PS - 1) // PS
    addr = libc.mmap(None, size, PROT_READ, MAP_SHARED, fd, 0)
    vec = (ctypes.c_ubyte * npages)()
    libc.mincore(ctypes.c_void_p(addr), ctypes.c_size_t(size), vec)
    res = sum(1 for i in range(npages) if vec[i] & 1)
    tp = PRIOR_OFF // PS
    log(f"[residency:{tag}] {res:,}/{npages:,} pages ({100.0*res/npages:.2f}%), "
        f"prior-offset page {tp:,} resident={'YES' if vec[tp] & 1 else 'NO'}")
    del vec
    libc.munmap(ctypes.c_void_p(addr), size)
    os.close(fd)
    return res, npages


def hash_cached():
    h = hashlib.sha256()
    with open(P, "rb", buffering=0) as f:
        while True:
            b = f.read(CH)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def hash_direct():
    fd = os.open(P, os.O_RDONLY | os.O_DIRECT)
    size = os.fstat(fd).st_size
    buf = mmap.mmap(-1, CH)          # page-aligned -> satisfies O_DIRECT
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
    return h.hexdigest(), off


def bit_indices(x):
    return [i for i in range(8) if x & (1 << i)]


def virt_to_phys(vaddr):
    """Read /proc/self/pagemap. Returns (entry, present, pfn)."""
    with open("/proc/self/pagemap", "rb") as pm:
        pm.seek((vaddr // PS) * 8)
        entry = struct.unpack("<Q", pm.read(8))[0]
    present = bool(entry & (1 << 63))
    pfn = entry & ((1 << 55) - 1)
    return entry, present, pfn


def capture_physaddr(off):
    """mmap the file, touch the page holding off, resolve PFN -> physaddr."""
    page_start = (off // PS) * PS
    fd = os.open(P, os.O_RDONLY)
    size = os.fstat(fd).st_size
    addr = libc.mmap(None, size, PROT_READ, MAP_SHARED, fd, 0)
    if addr in (None, 2**64 - 1):
        os.close(fd)
        return None
    # touch the page so it is present in this process's page tables
    vaddr = addr + page_start
    ptr = ctypes.cast(ctypes.c_void_p(vaddr), ctypes.POINTER(ctypes.c_ubyte))
    touched = ptr[off % PS]
    entry, present, pfn = virt_to_phys(vaddr)
    result = {
        "byte_via_mmap": touched,
        "vaddr": vaddr,
        "pagemap_entry": entry,
        "present": present,
        "pfn": pfn,
        "physaddr": (pfn << 12) + (off % PS) if pfn else 0,
    }
    libc.munmap(ctypes.c_void_p(addr), size)
    os.close(fd)
    return result


def read_page_cached(off):
    """Re-read the single page holding off, through the page cache."""
    page_start = (off // PS) * PS
    with open(P, "rb", buffering=0) as f:
        f.seek(page_start)
        return f.read(PS)


def read_page_direct(off):
    page_start = (off // PS) * PS
    fd = os.open(P, os.O_RDONLY | os.O_DIRECT)
    buf = mmap.mmap(-1, PS)
    try:
        n = os.preadv(fd, [buf], page_start)
        return bytes(memoryview(buf)[:n])
    finally:
        buf.close()
        os.close(fd)


def full_diff():
    """Byte-by-byte cached vs device over the whole file."""
    fd_d = os.open(P, os.O_RDONLY | os.O_DIRECT)
    f_c = open(P, "rb", buffering=0)
    buf = mmap.mmap(-1, CH)
    size = os.fstat(fd_d).st_size
    off = 0
    diffs = []
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
        buf.close()
        f_c.close()
        os.close(fd_d)
    return diffs


def on_mismatch(it):
    log()
    log("=" * 72)
    log(f"*** MISMATCH ON ITERATION {it} — FAULT PRESENT ***")
    log("=" * 72)

    log("\n--- byte-by-byte diff (cached vs O_DIRECT) ---")
    diffs = full_diff()
    log(f"differing bytes: {len(diffs)}")
    for (off, c, d) in diffs:
        x = c ^ d
        bits = bit_indices(x)
        direction = "1->0" if (d & x) else "0->1"
        log(f"offset {off} (0x{off:x}): cache=0x{c:02x} disk=0x{d:02x} "
            f"xor=0x{x:02x} bit={','.join(map(str,bits))} dir={direction}")
        log(f"    mod512={off % 512}  mod4096={off % 4096}  mod2MiB={off % (2<<20)}")
        if off % 4096 == 2309 and x == 0x40:
            log("    !! MATCHES PRIOR SIGNATURE (mod4096==2309, xor==0x40)")

    log("\n--- PHYSICAL ADDRESS CAPTURE ---")
    for (off, c, d) in diffs:
        cap = capture_physaddr(off)
        if not cap:
            log(f"offset {off}: mmap failed, no physaddr")
            continue
        log(f"offset {off}:")
        log(f"    vaddr          0x{cap['vaddr']:x}")
        log(f"    pagemap entry  0x{cap['pagemap_entry']:016x}  present={cap['present']}")
        log(f"    PFN            0x{cap['pfn']:x} ({cap['pfn']})")
        if cap["pfn"] == 0:
            log("    !! PFN==0 — NOT effectively root, capture FAILED")
        else:
            log(f"    PHYSADDR       0x{cap['physaddr']:x} ({cap['physaddr']})")
            log(f"    byte via mmap  0x{cap['byte_via_mmap']:02x}")

    log("\n--- stability: re-read same page twice, NO eviction ---")
    for (off, c, d) in diffs:
        disk_pg = read_page_direct(off)
        for k in (1, 2):
            pg = read_page_cached(off)
            b = pg[off % PS]
            log(f"offset {off} re-read #{k}: cached=0x{b:02x} "
                f"disk=0x{disk_pg[off % PS]:02x} "
                f"{'STILL CORRUPT' if b != disk_pg[off % PS] else 'now clean (TRANSIENT)'}")

    log("\n--- eviction test: POSIX_FADV_DONTNEED on the affected range ---")
    for (off, c, d) in diffs:
        page_start = (off // PS) * PS
        fd = os.open(P, os.O_RDONLY)
        os.posix_fadvise(fd, page_start, PS, os.POSIX_FADV_DONTNEED)
        os.close(fd)
        pg = read_page_cached(off)
        b = pg[off % PS]
        disk_pg = read_page_direct(off)
        log(f"offset {off} post-evict re-read: cached=0x{b:02x} "
            f"disk=0x{disk_pg[off % PS]:02x} "
            f"{'CLEARED' if b == disk_pg[off % PS] else 'STILL CORRUPT'}")
    log("=" * 72)


def main():
    log("=" * 72)
    log("bit-6 page-cache fault re-test — post-reseat")
    log(f"file      {P}")
    st = os.stat(P)
    log(f"size      {st.st_size:,}  inode {st.st_ino}  links {st.st_nlink}")
    log(f"mtime     {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.st_mtime))}")
    log(f"expect    {EXPECT}")
    log(f"euid      {os.geteuid()} (root)")
    log("=" * 72)

    log("\n### Step 0: residency BEFORE touching (no cache drop, no fadvise)")
    residency("pre")

    if SMOKE:
        log("\n### (smoke: skipping dmidecode / RAM / EDAC evidence)")
    else:
        log("\n### dmidecode memory (reseat verification)")
        os.system("dmidecode -t memory | grep -E "
                  "'Locator|Size|Speed|Configured|Manufacturer|Part Number|Rank|Error Correction|Type:' "
                  "| sed 's/^/    /'")
        log("\n### total RAM")
        os.system("grep MemTotal /proc/meminfo | sed 's/^/    /'")
        log("\n### EDAC / MCE since boot")
        os.system("journalctl -k -b | grep -iE "
                  "'edac|mce|machine check|memory error|hardware error' "
                  "| tail -20 | sed 's/^/    /'")
        os.system("echo '    --- edac mc ---'; "
                  "ls /sys/devices/system/edac/mc/ 2>&1 | sed 's/^/    /'")

    log(f"\n### Steps 1-4, x{ITERATIONS} iterations (file held resident, no eviction)")
    log(f"{'iter':>4} {'cached sha256':>16} {'direct sha256':>16} {'result':>8} {'secs':>8}")
    t_all = time.time()
    total_bytes = 0
    failures = 0
    for it in range(1, ITERATIONS + 1):
        t0 = time.time()
        c = hash_cached()
        d, dbytes = hash_direct()
        el = time.time() - t0
        total_bytes += st.st_size + dbytes
        ok = (c == d)
        if not ok:
            failures += 1
        log(f"{it:>4} {c[:16]} {d[:16]} {'PASS' if ok else 'FAIL':>8} {el:>8.1f}")
        if c != EXPECT:
            log(f"     note: cached hash != upstream expected digest")
        if d != EXPECT:
            log(f"     note: DIRECT hash != upstream expected digest (on-platter corruption?)")
        if not ok:
            on_mismatch(it)
            log("\nHalting loop to preserve evidence.")
            break
        if it == 1:
            residency("after-iter-1")

    wall = time.time() - t_all
    log("\n" + "=" * 72)
    log(f"iterations run     {it}")
    log(f"failures           {failures}")
    log(f"total bytes read   {total_bytes:,} ({total_bytes/(1<<30):.1f} GiB)")
    log(f"wall clock         {wall:.1f}s ({wall/60:.1f} min)")
    log("=" * 72)
    residency("final")


main()
