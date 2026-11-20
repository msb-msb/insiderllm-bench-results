#!/usr/bin/env python3
"""EXPLORATORY, UNSCORED (Mark, 2026-11-19): why H tripped the 2 GiB MemAvailable floor on Rushuna.

Samples every 1 s, for every process whose command line mentions the HotRod work folder (server.py, the engine,
the bench tool, any python): VmRSS, RssAnon, RssFile, RssShmem, VmLck, VmPin, VmSwap, plus MemAvailable/Cached/
free and the card's memory.used. Writes rss.jsonl and prints one line per sample.
Floor: MemAvailable < 2048 MiB -> SIGKILL the engine(s), SIGTERM the server(s) and the watched command, write TRIPPED.
Never lets it reach the OOM killer.
  explore_rss.py OUTDIR -- COMMAND...    (runs COMMAND, samples until it exits or the floor trips)
"""
import json, os, signal, subprocess, sys, time

OUT = sys.argv[1]; CMD = sys.argv[sys.argv.index("--") + 1:]
MARK = "hotrod-2026-11"
FLOOR = 2048
FIELDS = ("VmRSS", "RssAnon", "RssFile", "RssShmem", "VmLck", "VmPin", "VmSwap")


def meminfo():
    d = {}
    for l in open("/proc/meminfo"):
        k, v = l.split(":"); d[k] = int(v.split()[0]) // 1024
    return d


def procs():
    out = {}
    for p in os.listdir("/proc"):
        if not p.isdigit() or int(p) == os.getpid():
            continue
        try:
            cmd = open(f"/proc/{p}/cmdline", "rb").read().replace(b"\0", b" ").decode(errors="replace").strip()
            if MARK not in cmd:
                continue
            st = {}
            for l in open(f"/proc/{p}/status"):
                k = l.split(":")[0]
                if k in FIELDS or k == "Name":
                    st[k] = l.split(":", 1)[1].strip()
            row = {"name": st.get("Name"), "cmd": cmd[:120]}
            for f in FIELDS:
                row[f] = int(st.get(f, "0 kB").split()[0]) // 1024     # MiB
            out[int(p)] = row
        except (OSError, ValueError):
            pass
    return out


def gpu():
    try:
        return int(subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                                  capture_output=True, text=True, timeout=5).stdout.split()[0])
    except Exception:
        return -1


def label(r):
    c = r["cmd"]
    if "/engine/strata" in c: return "engine"
    if "server.py" in c: return "server"
    if "strata_bench" in c: return "bench"
    return r["name"] or "other"


def main():
    os.makedirs(OUT, exist_ok=True)
    child = subprocess.Popen(CMD, stdout=open(os.path.join(OUT, "workload.out"), "w"), stderr=subprocess.STDOUT)
    t0 = time.time(); f = open(os.path.join(OUT, "rss.jsonl"), "w"); peak = {}
    while child.poll() is None:
        m = meminfo(); ps = procs(); g = gpu()
        rec = {"t": round(time.time() - t0, 1), "avail": m["MemAvailable"], "free": m["MemFree"], "cached": m["Cached"],
               "gpu": g, "procs": {str(k): v for k, v in ps.items()}}
        f.write(json.dumps(rec) + "\n"); f.flush()
        summ = " ".join(f"{label(r)}:{r['VmRSS']}(anon {r['RssAnon']} file {r['RssFile']} lck {r['VmLck']} pin {r['VmPin']})"
                        for r in ps.values() if r["VmRSS"] > 200)
        print(f"{rec['t']:7.1f}s avail {m['MemAvailable']} cached {m['Cached']} gpu {g} | {summ}", flush=True)
        for r in ps.values():
            k = label(r); peak[k] = max(peak.get(k, 0), r["RssAnon"])
        if m["MemAvailable"] < FLOOR:
            print(f"TRIPPED MemAvailable {m['MemAvailable']} MiB < {FLOOR}", flush=True)
            open(os.path.join(OUT, "TRIPPED"), "w").write(json.dumps(rec))
            for pid, r in ps.items():
                if label(r) not in ("engine", "server", "bench"): continue
                try: os.kill(pid, signal.SIGKILL if label(r) == "engine" else signal.SIGTERM)
                except OSError: pass
            child.terminate()
            break
        time.sleep(1)
    try: child.wait(timeout=60)
    except subprocess.TimeoutExpired: child.kill()
    time.sleep(3)
    for pid, r in procs().items():                       # no engine/server/bench may survive (shells are left alone)
        if label(r) not in ("engine", "server", "bench"): continue
        try: os.kill(pid, signal.SIGKILL)
        except OSError: pass
    json.dump({"peak_anon_mib": peak, "rc": child.returncode, "tripped": os.path.exists(os.path.join(OUT, "TRIPPED"))},
              open(os.path.join(OUT, "summary.json"), "w"), indent=1)
    print("summary", peak)


if __name__ == "__main__":
    main()
