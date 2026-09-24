# Ornith-1.5-35B-A3B vs Qwen3.6-35B-A3B — A-B-B-A, Miu RTX 3090, 2026-08-28

RUN AND COMPLETE, 2026-08-28. Four slots of four, no failures. This README
described the intended protocol before the run and is kept as written below,
because a protocol recorded in advance is worth more than one written after the
numbers were seen. Only this header was added afterwards.

Protocol is the published 2026-08-14 paired sweep
(`comparison_set: qwen38-vs-qwen36-20260814`) with the models swapped.

## Outcome

Full figures in `results.json`; per-slot brackets and telemetry in `slots/`;
the orchestrator's own verdict lines at the end of `run.log`.

| | Ornith 1.5-35B-A3B | Qwen3.6-35B-A3B | verdict |
|---|---:|---:|---|
| tg128 d=0 | 172.44 | 158.18 | +9.01%, RESOLVABLE |
| tg128 d=4096 | 170.69 | 157.18 | +8.60%, RESOLVABLE |
| tg128 d=8192 | 166.59 | 153.47 | +8.55%, RESOLVABLE |
| pp512 d=0 | 3,602.94 | 3,694.22 | Qwen +2.53% |
| pp512 d=4096 | 3,387.42 | 3,493.14 | Qwen +3.12% |
| pp512 d=8192 | 3,263.34 | 3,362.46 | Qwen +3.04% |
| peak VRAM | 21,662 MiB | 21,676 MiB | 14 MiB apart |

Prompt processing **was** resolvable here, unlike the 08-14 run: the gaps clear
both the largest same-model repeat spread and the within-run stddev at all three
depths. The README's expectation above that it might again be unresolvable was
wrong, and is left standing rather than edited.

Repeat spreads came in at 0.365-0.725 tok/s against 0.00-0.02 on 08-14. The
gate still passed with room — the between-model gaps are 18-37x the largest
spread — but the "repeats land within 0.02" line does not generalise off that
run and should not be carried forward.

Cited by `/guides/ornith-1-5-35b-vs-qwen-3-6-35b-rtx-3090/`, and the 14 MiB
figure scopes the 254 MiB finding on `/guides/qwen-3-8-27b-vs-3-6-27b-rtx-3090/`.

## Design

| | |
|---|---|
| A | Ornith-1.5-35B-A3B Q4_K_M (bartowski), slots A1 / A2, positions 1 and 4 |
| B | Qwen3.6-35B-A3B UD-Q4_K_M (Unsloth), slots B1 / B2, positions 2 and 3 |
| Harness | `llama-bench -ngl 99 -fa 1 -p 512 -n 128 -d 0,4096,8192 -r 5` |
| Engine | llama.cpp b10088 `67b9b0e`, CUDA sm_86 — the dataset pin |
| Order | A-B-B-A, one session, page cache dropped between every slot |

A is the newcomer and B the incumbent, matching 08-14 where A was 3.8 and B
was 3.6. Each model is measured twice; those are repeats of one config, not
independent configs, so they average into one row per depth with the per-slot
figures kept — the rule v1.4.0 set and v1.5.0 applied.

The harness string is byte-identical to the published rows. `mmap` is left at
its default (on), as it was on 08-14. That is deliberate: it makes the bracket
stronger here, because llama-bench reads the very page-cache pages the script
hashed, and residency is re-checked after the run.

## Bracket

Per slot, per `docs/memory-fault-2026-08-15.md` section 5 (the bracket stays,
and is not conditional on the DIMM being replaced):

  evict -> mincore 0% residency -> buffered sha256 vs **upstream** digest ->
  launch immediately (step2->3 gap recorded) -> bench -> residency ->
  buffered sha256 again.

Any mismatch aborts the run and captures the byte diff, the XOR bit pattern and
the physical address. Root is required for that last part: `/proc/self/pagemap`
masks the PFN to 0 otherwise.

Both digests are upstream references, not local-vs-local:

| Model | sha256 | source |
|---|---|---|
| Ornith-1.5-35B-A3B Q4_K_M | `12d8d5c0…2614a` | bartowski LFS oid, in the model README |
| Qwen3.6-35B-A3B UD-Q4_K_M | `ac0e2c11…31a61` | Unsloth LFS oid, recovered from the `huggingface_hub` download metadata (repo commit `a483e9e6…`) |

The Qwen digest was **not** previously on record — the published 35B rows
predate `model.sha256`, which arrived in v1.4.0. It was recovered from
`bench-models/.cache/huggingface/download/*.metadata` (line 2 is the LFS etag)
and both files were verified against their digests on 2026-08-28 before this
harness was written.

## Repeatability is the gate

The 08-14 rows read a sub-one-percent between-model gap only because same-model
repeats landed within 0.02 tok/s. The script applies that test directly: a gap
is reported RESOLVABLE only if it exceeds the largest same-model repeat spread,
and UNRESOLVABLE otherwise. Prompt processing was unresolvable on 08-14 and may
well be again — publish it raw and draw no prefill comparison from it.

## Stated confounds

- **Quantizer mismatch.** Ornith is bartowski imatrix Q4_K_M; Qwen is Unsloth
  Dynamic UD-Q4_K_M. There is no Unsloth build of Ornith 1.5 (they stopped at
  1.0), so the recipe cannot be held constant in either direction. Both are
  `general.file_type` 15 and within 1.2% on size. State it; do not normalise it.
- **Storage asymmetry — REMOVED 2026-08-28, was not merely noted.** Ornith
  ships on Storage_Disk_1 (7200rpm HGST) and hashed there at ~129 MB/s, 2m50s
  for the file, against ~500 MB/s for the Qwen copy on the NVMe. That does not
  touch tok/s — llama-bench measures after load — but it made the Ornith slots
  idle far longer before benching, eroding the thermal cancellation A-B-B-A
  exists to provide. The file was staged to `/home/minotaur/bench-models/`
  alongside the Qwen copy and re-verified against the upstream bartowski LFS
  oid there: hash `12d8d5c0…2614a`, 37.5s, 35.6s of it user time. Both models
  now load from the same device and hash CPU-bound rather than I/O-bound, so
  the slots are symmetric. Start temps are recorded per slot regardless.
- **The 41st block** is the MTP head, not a transformer layer. llama-bench does
  not run speculation, so it is resident and unused for the whole sweep — the
  same footnote the 08-14 3.8 rows carry.
- **Kernel.** Miu is on 6.8.0-138; the published rows recorded 6.8.0-134.

## Contents

| path | what |
|---|---|
| `ornith_abba.py` | the harness, as run |
| `run.log` | orchestrator stdout: brackets, per-slot tables, verdicts |
| `slots/*.json` | per-slot record: bracket, telemetry, raw llama-bench JSON |
| `results.json` | merged, plus the repeatability and resolvability summary |
| `harness.pid` | the harness's own PID, written by the harness itself |
