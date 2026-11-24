#!/usr/bin/env python3
"""10 Hz per-process VRAM sampler (pre-registration section 3.1 and 3.2). Writes CSV: wall_time,pid,used_mib.
One nvidia-smi process streams --query-compute-apps every 100 ms (-lms 100); each line is stamped with Tamanna's
wall clock as it arrives. A sample with no compute process writes nothing for that tick."""
import subprocess, sys, time

out = open(sys.argv[1], "a", buffering=1)
if out.tell() == 0:
    out.write("wall,pid,used_mib\n")
p = subprocess.Popen(["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits",
                      "-lms", "100"], stdout=subprocess.PIPE, text=True, bufsize=1)
for line in p.stdout:
    parts = [x.strip() for x in line.split(",")]
    if len(parts) == 2 and parts[0].isdigit():
        out.write(f"{time.time():.3f},{parts[0]},{parts[1]}\n")
