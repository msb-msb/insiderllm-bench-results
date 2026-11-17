#!/usr/bin/env python3
"""P4 single re-run of the cells amendment A1 (2026-11-17) made void (lock 918e33f8). Identical to
codernext/rerun_qc.py except the output names carry "a1", so the 11-10 re-run files are not overwritten.
Uses bench_qc.py unchanged (imported, not edited): same build, llama_cmd flags, prompts, REPS and per-request
recording. Writes rerun-a1-<ARM>.json and server-rerun-a1-<ARM>.log.
usage: rerun_a1_qc.py ARM N LENGTH [LENGTH ...]"""
import os, sys
import bench_qc as B
arm, n, lengths = sys.argv[1], int(sys.argv[2]), [int(x) for x in sys.argv[3:]]
B.log(f"P4 RE-RUN (A1) {arm} -ncmoe {n} lengths {lengths}")
cmd, env = B.llama_cmd(n, arm)
p, ok = B.start(cmd, env, f"server-rerun-a1-{arm}.log", 900)
assert ok, f"rerun {arm} did not start"
B.run_cells(arm + "-rerun-a1", p.pid, lengths, os.path.join(B.HERE, f"rerun-a1-{arm}.json"))
B.stop_server(p)
