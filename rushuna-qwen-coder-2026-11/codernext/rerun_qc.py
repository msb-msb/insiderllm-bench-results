#!/usr/bin/env python3
"""P4 single re-run of void cells (lock 918e33f8). Uses bench_qc.py unchanged (imported, not edited): same build,
llama_cmd flags, prompts, REPS and per-request recording. Writes rerun-<ARM>.json and server-rerun-<ARM>.log.
usage: rerun_qc.py ARM N LENGTH [LENGTH ...]"""
import os, sys
sys.argv = [sys.argv[0]] + sys.argv[1:]
import bench_qc as B
arm, n, lengths = sys.argv[1], int(sys.argv[2]), [int(x) for x in sys.argv[3:]]
B.log(f"P4 RE-RUN {arm} -ncmoe {n} lengths {lengths}")
cmd, env = B.llama_cmd(n, arm)
p, ok = B.start(cmd, env, f"server-rerun-{arm}.log", 900)
assert ok, f"rerun {arm} did not start"
B.run_cells(arm + "-rerun", p.pid, lengths, os.path.join(B.HERE, f"rerun-{arm}.json"))
B.stop_server(p)
