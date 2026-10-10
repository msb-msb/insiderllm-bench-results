#!/usr/bin/env python3
"""Tamanna RAM speed (DDR4-2133 vs 3000) on offloaded decode, 2026-10-09.

Pre-registered in docs/candidates/tamanna-ram-speed-offload-2026-10.md (approved by Mark 2026-10-09, including the
BIOS switch protocol). One arm per RAM speed, same files, same build, same flags; this script runs one speed:
  python3 ramspeed.py 3000     # or 2133
Arm A, primary: Qwen3.6-35B-A3B UD-Q4_K_M,
  llama-bench -ngl 99 -ncmoe N -fa 1 -p 512 -n 128 -d 0,4096 -r 5 -t 8 -lm mmap -o json, N = 40, 20, 0.
  3 reps; each rep runs N = 40, 20, 0 in that order, each as (discarded priming invocation, measured invocation).
Arm B, secondary: Qwen3.8-Flash-Next UD-IQ3_XXS (3 shards), the Miu 2026-09-08 sweep's flags:
  llama-bench -ngl 99 -ncmoe 29 -fa 1 -p 0 -n 128 -d 0,4096 -r 3 -t 6 -lm mmap -o json
  one priming invocation, then 3 measured.
Per invocation: nvidia-smi at 1 s (PCIe gen/width, VRAM, clocks, power, temp, clock-event reasons), CPU Tctl
(k10temp) at 1 s, NVMe read bytes from /proc/diskstats, MemAvailable before and after.
llama.cpp v0.4.0 5266f24 at ~/llama-v0.4.0 (CUDA 12.4 / gcc-13, sm_86).
"""
import json, os, subprocess, sys, time, threading, statistics as st, glob

SPEED = sys.argv[1]
assert SPEED in ("3000", "2133")
OUT = os.path.expanduser(f"~/tamanna-ram-speed-2026-10-09/{SPEED}")
BENCH = os.path.expanduser("~/llama-v0.4.0/build/bin/llama-bench")
LIBDIR = os.path.expanduser("~/llama-v0.4.0/build/bin")
A_FILE = os.path.expanduser("~/bench-models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf")
B_FILE = os.path.expanduser("~/bench-models/qwen3.8-flash-next/Qwen3.8-Flash-Next-UD-IQ3_XXS-00001-of-00003.gguf")
A_ARGS = ["-ngl", "99", "-fa", "1", "-p", "512", "-n", "128", "-d", "0,4096", "-r", "5", "-t", "8", "-lm", "mmap"]
B_ARGS = ["-ngl", "99", "-ncmoe", "29", "-fa", "1", "-p", "0", "-n", "128", "-d", "0,4096", "-r", "3", "-t", "6", "-lm", "mmap"]
A_N = [40, 20, 0]
SMI = ["timestamp", "pcie.link.gen.current", "pcie.link.width.current", "temperature.gpu", "clocks.sm", "clocks.mem",
       "power.draw", "utilization.gpu", "memory.used", "clocks_event_reasons.active"]
NVME = "nvme0n1"


def log(s):
    line = time.strftime("%H:%M:%S ") + s
    print(line, flush=True)
    with open(os.path.join(OUT, "run.log"), "a") as f: f.write(line + "\n")


def nvme_read_bytes():
    for l in open("/proc/diskstats"):
        p = l.split()
        if p[2] == NVME: return int(p[5]) * 512
    return 0


def mem_available_mib():
    for l in open("/proc/meminfo"):
        if l.startswith("MemAvailable:"): return int(l.split()[1]) // 1024


def tctl_path():
    for h in glob.glob("/sys/class/hwmon/hwmon*"):
        try:
            if open(h + "/name").read().strip() == "k10temp": return h + "/temp1_input"
        except OSError: pass


TCTL = tctl_path()


class Sampler:
    def __init__(self, path):
        self.f = open(path, "w"); self.cpu = []; self.stop = False
        self.p = subprocess.Popen(["nvidia-smi", "--query-gpu=" + ",".join(SMI), "--format=csv,noheader,nounits", "-lms", "1000"],
                                  stdout=self.f, stderr=subprocess.DEVNULL)
        self.t = threading.Thread(target=self._cpu); self.t.start()

    def _cpu(self):
        while not self.stop:
            if TCTL: self.cpu.append(int(open(TCTL).read()) / 1000)
            time.sleep(1)

    def close(self):
        self.stop = True; self.t.join(); self.p.terminate(); self.p.wait(); self.f.close()


def telemetry(path):
    rows = []
    for l in open(path):
        p = [x.strip() for x in l.split(",")]
        if len(p) != len(SMI): continue
        try: rows.append({"gen": p[1], "width": p[2], "temp": float(p[3]), "sm": float(p[4]), "mem_clock": float(p[5]),
                          "power": float(p[6]), "util": float(p[7]), "vram": float(p[8]), "reasons": p[9]})
        except ValueError: pass
    load = [r for r in rows if r["util"] > 0] or rows
    if not rows: return {}
    return {"samples": len(rows), "peak_vram_mib": max(r["vram"] for r in rows),
            "pcie_gen_under_load": sorted({r["gen"] for r in load}), "pcie_width_under_load": sorted({r["width"] for r in load}),
            "gpu_temp_max": max(r["temp"] for r in rows), "power_mean_load": round(st.mean(r["power"] for r in load), 1),
            "sm_clock_median_load": st.median(r["sm"] for r in load), "reasons_under_load": sorted({r["reasons"] for r in load})}


def run(arm, n, rep, tag):
    name = f"{tag}{arm}-ncmoe{n}-rep{rep}"
    if arm == "A":
        cmd = [BENCH, "-m", A_FILE] + A_ARGS[:2] + ["-ncmoe", str(n)] + A_ARGS[2:] + ["-o", "json"]
    else:
        cmd = [BENCH, "-m", B_FILE] + B_ARGS + ["-o", "json"]
    env = dict(os.environ); env["LD_LIBRARY_PATH"] = LIBDIR
    tpath = os.path.join(OUT, f"telemetry-{name}.csv")
    ma0, rd0 = mem_available_mib(), nvme_read_bytes()
    s = Sampler(tpath); time.sleep(1.2)
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    el = time.time() - t0
    time.sleep(1.2); s.close()
    rd = nvme_read_bytes() - rd0; ma1 = mem_available_mib()
    if p.returncode != 0:
        log(f"  FAILED {name} rc={p.returncode}: {p.stderr[-400:]}")
        with open(os.path.join(OUT, f"raw-{name}.json"), "w") as f: json.dump({"cmd": cmd, "rc": p.returncode, "stderr_tail": p.stderr[-4000:]}, f, indent=1)
        return None
    rows = json.loads(p.stdout)
    tel = telemetry(tpath)
    rec = {"arm": arm, "ncmoe": n, "rep": rep, "tag": tag.strip("-") or "measured", "started": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(t0)),
           "elapsed_s": round(el, 1), "nvme_read_mib": round(rd / 2**20, 1), "mem_available_mib": [ma0, ma1],
           "cpu_tctl_max": max(s.cpu) if s.cpu else None, "cpu_tctl_mean": round(st.mean(s.cpu), 1) if s.cpu else None, "telemetry": tel, "rows": []}
    for r in rows:
        rec["rows"].append({"kind": "pp" if r["n_prompt"] > 0 else "tg", "depth": r.get("n_depth", 0), "avg_ts": r["avg_ts"], "stddev_ts": r["stddev_ts"],
                            "samples": r.get("samples_ts", []), "build_commit": r.get("build_commit"), "n_threads": r.get("n_threads")})
    with open(os.path.join(OUT, f"raw-{name}.json"), "w") as f:
        json.dump({"cmd": cmd, "stdout": rows, "stderr_tail": p.stderr[-2000:]}, f, indent=1)
    tg = {x["depth"]: x["avg_ts"] for x in rec["rows"] if x["kind"] == "tg"}
    pp = {x["depth"]: x["avg_ts"] for x in rec["rows"] if x["kind"] == "pp"}
    log(f"  {name:26s} tg128 d0/4k {tg.get(0, 0):.2f}/{tg.get(4096, 0):.2f}  pp512 d0/4k {pp.get(0, 0):.0f}/{pp.get(4096, 0):.0f}  "
        f"nvme {rec['nvme_read_mib']} MiB  vram {tel.get('peak_vram_mib')}  pcie {tel.get('pcie_gen_under_load')}x{tel.get('pcie_width_under_load')}  "
        f"cpu {rec['cpu_tctl_max']} C  avail {ma0}->{ma1} MiB  ({el:.0f}s)")
    return rec


def main():
    os.makedirs(OUT, exist_ok=True)
    log(f"start speed={SPEED}  bench {BENCH}")
    log("  card: " + subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version,pcie.link.gen.max,memory.used,temperature.gpu", "--format=csv,noheader"], capture_output=True, text=True).stdout.strip())
    log("  free -g: " + subprocess.run(["free", "-g"], capture_output=True, text=True).stdout.strip().split("\n")[1])
    results, primes = [], []
    for rep in (1, 2, 3):
        for n in A_N:
            pr = run("A", n, rep, "prime-"); pr and primes.append(pr)
            r = run("A", n, rep, ""); r and results.append(r)
    pr = run("B", 29, 0, "prime-"); pr and primes.append(pr)
    for rep in (1, 2, 3):
        r = run("B", 29, rep, ""); r and results.append(r)
    json.dump({"speed": SPEED, "a_args": A_ARGS, "b_args": B_ARGS, "results": results, "primes": primes},
              open(os.path.join(OUT, "results.json"), "w"), indent=1)
    log("summary (mean of 3 measured invocations of llama-bench's own average; spread = min..max)")
    summ = {}
    for arm, ns in (("A", A_N), ("B", [29])):
        for n in ns:
            for kind in ("tg", "pp"):
                for d in (0, 4096):
                    v = [x["avg_ts"] for r in results if r["arm"] == arm and r["ncmoe"] == n for x in r["rows"] if x["kind"] == kind and x["depth"] == d]
                    if not v: continue
                    summ[f"{arm}|{n}|{kind}|{d}"] = {"mean": st.mean(v), "min": min(v), "max": max(v), "reps": v}
                    log(f"  {arm} ncmoe {n:<2d} {kind}{'128' if kind == 'tg' else '512'} d={d:<5d} {st.mean(v):8.2f} [{min(v):.2f}..{max(v):.2f}]")
    json.dump(summ, open(os.path.join(OUT, "summary.json"), "w"), indent=1)
    log("done")


if __name__ == "__main__":
    main()
