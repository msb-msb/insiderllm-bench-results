# Miu — memory-fault re-test + HumanEval bracket, 2026-08-16

Raw artifacts for the two runs of 2026-08-16. Manifest only; the analysis and
conclusions live in `docs/memory-fault-2026-08-15.md`, section
"2026-08-16 — post-reseat re-test and bracketed HumanEval".

These were the only copies. They lived in `$HOME` until this commit because
`/tmp` was cleaned across the 2026-08-15 reseat reboot, which destroyed the
prior session's per-problem HumanEval results file.

Both runs were executed as root and are diagnostic only. No config changes,
no deploys. The GGUF itself is not archived here.

## memory-retest/

Post-reseat re-test of the bit-6 page-cache fault. 20 iterations of cached
vs `O_DIRECT` comparison with the file held resident.

| file | what it is |
|---|---|
| `retest_root.py` | the runner: evict-free residency check, 20x cached-vs-O_DIRECT sha256, and on mismatch the byte diff + PFN/physaddr capture + stability re-reads + `FADV_DONTNEED` clear-confirm |
| `retest_out.txt` | full stdout of the run, including `dmidecode` DIMM population and per-iteration timings |

## humaneval-3.8-bracket/

HumanEval pass@1 for Qwen3.8-27B-UD-Q4_K_XL with the model load bracketed by
sha256 verification of the page-cache copy on both sides.

| file | what it is |
|---|---|
| `he38_bracket.py` | orchestrator: evict, mincore-confirm 0%, verify hash, launch `llama-server`, run the eval, re-verify hash, score |
| `he_gen.py` | generation harness against `llama-server /v1/completions`; sampling params pinned inline and echoed into the output |
| `he38_out.txt` | full stdout of the run |
| `he_38_bracket.json` | raw generations: per-problem completion text, finish_reason, completion_tokens, plus the pinned sampling block |
| `eval/he_38_bracket.jsonl` | the 164 samples as fed to the official scorer |
| `eval/he_38_bracket.jsonl_results.jsonl` | official OpenAI human-eval per-problem output (`passed`, `result`) |
| `summary.json` | pass@1, both bracket hashes, outputs fingerprint, step2->3 gap, and the full 164-entry pass/fail vector |
| `server.log` | `llama-server` stdout/stderr for the run |

`he_gen.py` is not in the original archive request but is included because
`he38_bracket.py` invokes it — without it the run is not reproducible.

## Provenance

- Engine: llama.cpp b10088, commit `67b9b0e`
- `llama-server` sha256 `ac2bb7684e022a4e0160946a28de38719097490f5c5d64ea7b4b9f3966fd03f1`
- `libggml-cuda.so` sha256 `e6016ef9f362db6de19785a08e414a8c443a98f4fe1e0f9f41419ae4304c36e3`
- Scorer: official OpenAI `human-eval` in `he-scorer:b10088`, `--network none
  --cap-drop ALL --security-opt no-new-privileges --memory 4g --pids-limit 256`
- GPU: RTX 3090, driver 580.178.04, display attached
