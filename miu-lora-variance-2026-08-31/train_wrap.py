#!/usr/bin/env python3
"""Run train_adapter.main() unmodified and append torch's peak-memory counters
to run_meta.json. Instrumentation only: no training config is touched."""
import sys, json, os, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import train_adapter
seed = int(sys.argv[sys.argv.index("--seed") + 1])
train_adapter.main()
pa = torch.cuda.max_memory_allocated() / 2**20
pr = torch.cuda.max_memory_reserved() / 2**20
print(f"peak torch alloc {pa:.0f} MiB | peak torch reserved {pr:.0f} MiB", flush=True)
p = f"adapters/seed{seed}/run_meta.json"
m = json.load(open(p)); m["peak_alloc_mib"] = round(pa); m["peak_reserved_mib"] = round(pr)
json.dump(m, open(p, "w"), indent=1)
