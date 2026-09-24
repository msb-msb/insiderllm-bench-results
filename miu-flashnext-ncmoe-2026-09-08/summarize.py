#!/usr/bin/env python3
"""Table per rig from results.json: -ncmoe, layers on GPU, peak VRAM, decode mean [min..max], per-layer gain.
usage: summarize.py <results.json> [<results.json> ...]
"""
import json, sys, statistics as st

for path in sys.argv[1:]:
    R = json.load(open(path))
    print(f"\n## {R['host']}  threads {R['cfg']['threads']}  load-mode {R['cfg']['load_mode']}  build {R['build']}")
    NL = R["cfg"].get("n_layers", 48)
    by = {}
    for rec in R["sweep"]:
        by.setdefault(rec["ncmoe"], []).append(rec)
    base = {}
    rows = []
    for n in sorted(by, reverse=True):
        recs = by[n]
        ok = [r for r in recs if r.get("rows")]
        vram = max(r["peak_vram_mib"] for r in recs)
        if not ok:
            rows.append((n, NL - n, vram, None, None, "OOM" if any(r.get("oom") for r in recs) else f"rc={recs[0]['rc']}"))
            continue
        cells = {}
        for d in (0, 4096):
            v = [x["avg_ts"] for r in ok for x in r["rows"] if x["depth"] == d]
            cells[d] = (st.mean(v), min(v), max(v), len(v))
        if n == max(by):
            base = cells
        rows.append((n, NL - n, vram, cells[0], cells[4096], "ok"))
    print("| -ncmoe | expert layers on GPU | peak VRAM MiB | tg128 d=0 mean [min..max] | tg128 d=4096 mean [min..max] | gain vs stock d=0 | per layer d=0 | status |")
    print("|---:|---:|---:|---|---|---:|---:|---|")
    for n, L, vram, c0, c4, status in rows:
        if c0 is None:
            print(f"| {n} | {L} | {vram} | | | | | {status} |"); continue
        g = c0[0] - base[0][0]
        per = (g / L) if L else 0.0
        print(f"| {n} | {L} | {vram} | {c0[0]:.2f} [{c0[1]:.2f}..{c0[2]:.2f}] n={c0[3]} | {c4[0]:.2f} [{c4[1]:.2f}..{c4[2]:.2f}] n={c4[3]} | {g:+.2f} tok/s ({g/base[0][0]*100:+.1f}%) | {per:+.3f} tok/s/layer | {status} |")
    if R.get("first_fail") is not None:
        print(f"first failing -ncmoe: {R['first_fail']}; last that fit: {R.get('last_fit')}")
    c = R.get("control")
    if c and c.get("rows"):
        print(f"control -ncmoe 48 load-mode mmap: peak {c['peak_vram_mib']} MiB; " + "; ".join(f"tg128@d{x['depth']} {x['avg_ts']:.2f}±{x['stddev_ts']:.2f}" for x in c["rows"]))
    nn = R.get("none") or {}
    if nn.get("bench"):
        ok = [r for r in nn["bench"] if r.get("rows")]
        for d in (0, 4096):
            v = [x["avg_ts"] for r in ok for x in r["rows"] if x["depth"] == d]
            if v: print(f"load-mode none at best fit, tg128 d={d}: {st.mean(v):.2f} [{min(v):.2f}..{max(v):.2f}] n={len(v)}; peak VRAM {max(r['peak_vram_mib'] for r in ok)} MiB")
        if nn.get("server"): R["server"]["best-none"] = nn["server"]
    for tag, s in R.get("server", {}).items():
        ld = s.get("load", {})
        print(f"server[{tag}]: load {ld.get('load_s')} s, RSS {ld.get('rss_mib')} MiB, card {ld.get('vram_mib')} MiB, -ncmoe {ld['cmd'][6] if ld.get('cmd') else '?'}")
        for r in s.get("reps", []):
            print(f"  rep{r['rep']}: prefill {r['prompt_n']} tok {r['prefill_tps']:.1f} tok/s; decode {r['decode_tps']:.2f} tok/s; disk read prefill {r['disk_read_prefill_mib']:.0f} MiB, decode {r['disk_read_decode_mib']:.0f} MiB ({r['disk_read_decode_mib_per_s']} MiB/s, {r['disk_read_decode_mib_per_token']} MiB/token); RSS {r['rss_after_mib']} MiB; cached {r['mem_after']['cached_mib']} MiB")
