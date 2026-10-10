#!/usr/bin/env python3
"""Stop rule, as agreed with Mark 2026-10-05 (v2; v2.1 fixes the load detector, see below):

  - MemAvailable < 2 GiB at any time            -> trip   (MemAvailable, not MemFree: mmapped page cache fills
                                                            "free" memory by design)
  - swap-out outside model load > 64 MiB in total -> trip   (sustained swap-out over the run)
  - any swap-in outside model load               -> trip
  - swap activity during model load is logged, not ruled on

"Model load" = from the moment a new llama-server / llama-bench PID appears until the card holds more than
1,024 MiB and its memory.used has not grown by more than 64 MiB across the last 3 samples (6 s). (v2 lacked the
1,024 MiB condition and ended a load at the ~113 MiB CUDA-context plateau, attempt 2.) Everything after that, until the PID exits, is
"measured". Samples every 2 s: MemAvailable, MemFree, Cached, SwapUsed, pswpin/pswpout deltas, phase.

usage: memwatch.py OUTDIR HARNESS_PID
On trip: SIGTERM the harness PID and every process named exactly llama-server / llama-bench, write TRIPPED.
On harness exit: write memwatch-summary.json with the run's swap and page-cache counters by phase.
"""
import json, os, signal, subprocess, sys, time

OUT, HPID = sys.argv[1], int(sys.argv[2])
# v3 (Mark, 2026-10-05, option 1): "--count-swap" = swap is allowed, counted and published; only the MemAvailable floor stops a run
COUNT_ONLY = "--count-swap" in sys.argv[3:]
PAGE_KIB = os.sysconf("SC_PAGE_SIZE") // 1024
NAMES = ("llama-server", "llama-bench")


def meminfo():
    d = {}
    for l in open("/proc/meminfo"):
        k, v = l.split(":")
        d[k] = int(v.split()[0])
    return d


def vmstat():
    d = {}
    for l in open("/proc/vmstat"):
        k, v = l.split()
        if k in ("pswpin", "pswpout"):
            d[k] = int(v)
    return d


def llama_pids():
    r = subprocess.run(["pgrep", "-x", "-d", " ", "|".join(NAMES)], capture_output=True, text=True)
    return set(int(p) for p in r.stdout.split())


def gpu_mib():
    try:
        return int(subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                                  capture_output=True, text=True).stdout.split()[0])
    except Exception:
        return -1


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


log = open(os.path.join(OUT, "memwatch.log"), "a")
v0 = vmstat()
prev = dict(v0)
S = {"mode": "count-swap" if COUNT_ONLY else "trip-on-swap", "start": time.strftime("%Y-%m-%d %H:%M:%S %Z"), "harness_pid": HPID, "page_kib": PAGE_KIB,
     "load": {"swapout_kib": 0, "swapin_kib": 0}, "measured": {"swapout_kib": 0, "swapin_kib": 0},
     "idle": {"swapout_kib": 0, "swapin_kib": 0}, "min_avail_mib": 10**9, "max_swapused_mib": 0,
     "min_cached_mib": 10**9, "max_cached_mib": 0, "loads": 0, "tripped": None}
known, loading, gpu_hist = set(), False, []
log.write(f"{time.strftime('%H:%M:%S')} v2 start harness_pid={HPID} pswpin={v0['pswpin']} pswpout={v0['pswpout']}\n")
log.flush()


def trip(reason):
    S["tripped"] = f"{time.strftime('%Y-%m-%d %H:%M:%S %Z')} {reason}"
    open(os.path.join(OUT, "TRIPPED"), "w").write(S["tripped"] + "\n")
    try:
        os.kill(HPID, signal.SIGTERM)
    except OSError:
        pass
    for n in NAMES:
        subprocess.run(["pkill", "-TERM", "-x", n])
    # llama-server treats the first SIGTERM as "cancel the task" and keeps running (attempt 3): KILL after 10 s
    for _ in range(10):
        if not llama_pids():
            break
        time.sleep(1)
    for n in NAMES:
        subprocess.run(["pkill", "-KILL", "-x", n])
    log.write(f"TRIPPED {reason}\n")
    log.flush()


while True:
    m, v, pids, g = meminfo(), vmstat(), llama_pids(), gpu_mib()
    new = pids - known
    if new:
        loading, gpu_hist = True, []
        S["loads"] += 1
    known = pids
    if not pids:
        loading = False
    gpu_hist = (gpu_hist + [g])[-4:]
    # v2.1: the CUDA context alone (~113 MiB) plateaus while an mmap load is still reading the file, so a load only
    # ends once the card holds weights (> 1,024 MiB) AND has grown <= 64 MiB across the last 3 samples.
    if loading and len(gpu_hist) == 4 and gpu_hist[0] > 1024 and gpu_hist[-1] - gpu_hist[0] <= 64:
        loading = False
    phase = "load" if loading else ("measured" if pids else "idle")
    d_out = (v["pswpout"] - prev["pswpout"]) * PAGE_KIB
    d_in = (v["pswpin"] - prev["pswpin"]) * PAGE_KIB
    prev = v
    S[phase]["swapout_kib"] += d_out
    S[phase]["swapin_kib"] += d_in
    avail, cached = m["MemAvailable"] // 1024, m["Cached"] // 1024
    swapused = (m["SwapTotal"] - m["SwapFree"]) // 1024
    S["min_avail_mib"] = min(S["min_avail_mib"], avail)
    S["max_swapused_mib"] = max(S["max_swapused_mib"], swapused)
    S["min_cached_mib"] = min(S["min_cached_mib"], cached)
    S["max_cached_mib"] = max(S["max_cached_mib"], cached)
    log.write(f"{time.strftime('%H:%M:%S')} phase={phase} avail_mib={avail} free_mib={m['MemFree']//1024} "
              f"cached_mib={cached} swapused_mib={swapused} swapout_kib+={d_out} swapin_kib+={d_in} gpu_mib={g}\n")
    log.flush()
    if avail < 2048:
        trip(f"MemAvailable {avail} MiB < 2048")
    elif COUNT_ONLY:
        pass
    elif S["measured"]["swapout_kib"] + S["idle"]["swapout_kib"] > 64 * 1024:
        trip(f"swap-out outside model load {(S['measured']['swapout_kib'] + S['idle']['swapout_kib'])//1024} MiB > 64")
    elif phase != "load" and d_in > 0:
        trip(f"swap-in outside model load: {d_in} KiB in one sample (phase {phase})")
    if S["tripped"] or not alive(HPID):
        S["end"] = time.strftime("%Y-%m-%d %H:%M:%S %Z")
        json.dump(S, open(os.path.join(OUT, "memwatch-summary.json"), "w"), indent=1)
        break
    time.sleep(2)
