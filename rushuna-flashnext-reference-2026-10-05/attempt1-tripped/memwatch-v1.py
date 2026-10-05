#!/usr/bin/env python3
"""Stop rule (Mark, 2026-10-05): if the box starts swapping or the OS has under 2 GB free, stop and report.
Samples /proc/meminfo and /proc/vmstat every 2 s. Trips when MemAvailable < 2 GiB, or when swap-out activity
(pswpout) rises above its value at start. On trip: SIGTERM the named processes, write TRIPPED with the reason."""
import os, sys, time, signal, subprocess
out = sys.argv[1]; targets = sys.argv[2:]
def mi():
    d = {}
    for l in open('/proc/meminfo'):
        k, v = l.split(':'); d[k] = int(v.split()[0])
    return d
def pswpout():
    for l in open('/proc/vmstat'):
        if l.startswith('pswpout '): return int(l.split()[1])
base = pswpout(); minavail = 10**12
log = open(os.path.join(out, 'memwatch.log'), 'a')
log.write(f"{time.strftime('%H:%M:%S')} start pswpout={base} targets={targets}\n"); log.flush()
while True:
    m = mi(); s = pswpout(); a = m['MemAvailable']; minavail = min(minavail, a)
    swapused = m['SwapTotal'] - m['SwapFree']
    log.write(f"{time.strftime('%H:%M:%S')} avail_mib={a//1024} free_mib={m['MemFree']//1024} cached_mib={m['Cached']//1024} swapused_mib={swapused//1024} pswpout+={s-base}\n"); log.flush()
    reason = None
    if a < 2 * 1024 * 1024: reason = f"MemAvailable {a//1024} MiB < 2048"
    elif s > base: reason = f"swap-out began: pswpout +{s-base} pages"
    if reason:
        open(os.path.join(out, 'TRIPPED'), 'w').write(f"{time.strftime('%Y-%m-%d %H:%M:%S %Z')} {reason}\n")
        for t in targets: subprocess.run(['pkill', '-TERM', '-f', t])
        log.write(f"TRIPPED {reason}\n"); log.flush(); break
    time.sleep(2)
