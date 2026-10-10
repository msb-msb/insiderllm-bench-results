# Rushuna, GGML_CUDA_REGISTER_HOST A-B-B-A, 2026-08-24

The record is `raw.log` (RTX 3060 12 GB, PCIe 3.0, Qwen3.6-35B-A3B UD-Q4_K_M, llama-bench). This README was added
2026-10-10 only to carry the dated note below. `raw.log` and its numbers are unchanged.

**Dated note, 2026-10-10.** Every run in `raw.log` reports `build: 20f5994`. That is **`20f5994bfeb91d24da328077c4b6095998cc9888`,
"llama : pin mmap-backed CPU weights for faster H2D uploads" (2026-07-02). It is an unmerged branch commit, not a
llama.cpp release.** GitHub's compare shows it diverged from master, 1 ahead and 1,690 behind, and lists no pull
request for it. That commit's loader change is what printed "pinned 12564.33 MiB of mapped model memory" and produced the pp512
gain here: 409.46 / 413.48 → 528.44 / 528.90 tok/s, about **+28%**, at `-ncmoe 24`, with tg128 unchanged.

Mainline llama.cpp stopped calling the pin function at **b3868 (2024-10-02)**: commit `c83ad6d01`, "ggml-backend :
add device and backend reg interfaces" (#9707). The last release that calls it is b3867. On mainline releases since,
including v0.4.0 (`5266f24`, the site's pin), `GGML_CUDA_REGISTER_HOST=1` pins no model weights. So this +28% is a
figure for that branch build only. It doesn't carry over to any release we run. See
`../tamanna-register-host-2026-10-10/` (the gate that found it) and
`docs/candidates/pinned-host-offload-register-build-2026-10.md` (the upstream history and method).

No `benchmarks.json` row was built from this record (checked 2026-10-10: no row cites it, `20f5994`, or its figures).
