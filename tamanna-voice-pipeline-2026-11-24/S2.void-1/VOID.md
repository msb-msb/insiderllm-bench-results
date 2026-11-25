# S2.void-1: voided (A1 item 1)

First S2 attempt, 2026-11-24 16:18-16:20. During the section 3.1 `-ncmoe` fit, the downward search (6 and 5 fit)
tried 4, where the LLM llama-server ran out of CUDA memory while loading and aborted. `serve.py` treated the exited
server as fatal and the arm stopped before READY: no warm-up clip, no measured clip. Fix (harness defect, not a method
change): a fit trial whose server exits while loading is recorded as "does not fit". S2 was re-run from the start.
