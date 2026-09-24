# z-lab DFlash drafter vs the published negative spec-decode result on Qwen3.6-35B-A3B — Tamanna, 2026-09-22

RUN AND COMPLETE, 2026-09-22 09:06:07 to 09:08:27 PDT. Results record; facts as measured. Clears the
2026-09-22 marker in `dated-markers.md`. Runner is `dflash_bench.py` (its docstring is the pre-registration);
`harness.out` / `run.log` are the live log; `raw-*.json` hold per-prompt server timings and 1 s telemetry
summaries; `telemetry-*.csv` are the samples; `server-*.log` are the llama-server logs; `results.json` and
`summary.json` are the machine-readable record.

## Verdict, by the pre-registered rule

**OVERTURNED, narrowly.** With the purpose-built drafter the fully resident 35B-A3B generates **1.092x** faster
on the published nine-prompt set than without it: 172.03 vs 157.58 tok/s aggregate, a gap of +14.45 tok/s
against a larger same-config spread of 0.12. The published negative was 0.28x. Token acceptance is **23.4%**
(3.50 accepted per 15-token draft block). The speedup is real, resolvable and small, and it is carried by the
two coding prompts and the math prompt; two of nine prompts got slower.

| | baseline (no drafter) | DFlash drafter, Q8_0 | ratio |
|---|---:|---:|---:|
| aggregate generation tok/s, mean of 3 reps [min..max] | 157.58 [157.51..157.62] | **172.03** [171.98..172.10] | **1.092x** |
| per-prompt mean tok/s | 155.83 [155.76..155.87] | 165.65 [165.57..165.75] | 1.063x |
| wall time, nine prompts | 9.68 s | 9.37 s | 0.968 |
| tokens generated | 1,285 | 1,288 | |
| draft tokens proposed / accepted | — | 4,225 / 987 | 23.4% |
| mean accepted per 15-token block | — | 3.50 | |
| VRAM after load / peak (24,576 MiB card) | 21,234 / 21,258 MiB | 23,676 / 23,762 MiB | +2.4 GiB |
| PCIe under load, every sample | gen 3 x16 | gen 3 x16 | |
| SM clock median (min) | 1935 (1860) MHz | 1935 (1935) MHz | |
| power mean (max) | 296-304 (378) W | 277-281 (353) W | |
| temperature start -> max | 55-59 -> 62-65 °C | 56-59 -> 61-63 °C | |

Every rep of each config landed within 0.12 tok/s of the others; the three drafter reps proposed and accepted
exactly the same 4,225 / 987 tokens (greedy, seed 42, identical prompts).

### Per prompt (mean of 3 reps)

| prompt | baseline tok/s | drafter tok/s | speedup | token acceptance | accepted / block | tokens out (base/draft) | same text at T=0? |
|---|---:|---:|---:|---:|---:|---:|---|
| code_python | 156.40 | **255.95** | **1.64x** | 0.509 | 7.64 | 192/192 | yes |
| code_cpp | 155.35 | 188.91 | 1.22x | 0.250 | 3.75 | 58/58 | yes |
| explain_concept | 156.93 | 162.39 | 1.04x | 0.216 | 3.24 | 192/192 | diverges at token 153 |
| summarize | 155.35 | 142.95 | **0.92x** | 0.178 | 2.67 | 53/56 | diverges at token 22 |
| qa_factual | 157.00 | 164.30 | 1.05x | 0.213 | 3.20 | 192/192 | diverges at token 56 |
| translation | 151.73 | **62.59** | **0.41x** | 0.033 | 0.50 | 22/22 | yes |
| creative_short | 156.98 | 158.84 | 1.01x | 0.203 | 3.04 | 192/192 | diverges at token 66 |
| stepwise_math | 156.94 | 196.69 | 1.25x | 0.276 | 4.14 | 192/192 | diverges at token 2 |
| long_code_review | 155.77 | 158.27 | 1.02x | 0.211 | 3.16 | 192/192 | diverges at token 97 |

Acceptance tracks speedup exactly, as it did for MTP in May. Below roughly 3.2 accepted tokens per block the
drafter pays for itself and no more; below 1 it loses. The translation prompt is 22 tokens of output at 0.5
accepted per block, so the drafter's own forward passes cost more than they save and throughput drops to
0.41x — a short-answer workload is where this drafter hurts.

## Beside the published negative

| | published negative (benchmarks.json `rushuna-qwen36-35b-a3b-udq4km-specdec-qwen35-08b`) | this run |
|---|---|---|
| box | Rushuna: RTX 3060 12 GB, i7-7700, DDR4-2133, PCIe 3.0 | Tamanna: RTX 3090 24 GB, Ryzen 7 5700X, DDR4, **PCIe slot at gen 3** (BIOS-capped; card advertises 4) |
| target | Qwen3.6-35B-A3B UD-Q4_K_M, `ac0e2c11…31a61` | the same file, same digest |
| residency | `-ncmoe 24`: experts streamed over PCIe from system RAM | `-ngl 99`, fully resident, 814 MiB VRAM headroom left with the drafter at -c 8192 |
| drafter | Qwen 3.5 0.8B, conventional draft model | z-lab Qwen3.6-35B-A3B-DFlash (June 2026 Modal retrain), block diffusion, Q8_0, 6 layers / 0.4 GB |
| engine | llama.cpp, build unpublished | llama.cpp v0.4.0 5266f24, mainline DFlash support, no fork |
| harness | unpublished | am17an's nine-prompt gist, the site's published spec-decode harness (May MTP bench) |
| baseline | 38.9 tok/s | 157.58 tok/s |
| with drafter | 11 tok/s, **0.28x** | 172.03 tok/s, **1.092x** |
| acceptance | 65% (definition and draft length unrecorded) | 23.4% of 15-token blocks, 3.50 accepted per block |

**What this does and does not settle.** The marker asked whether a purpose-built drafter overturns the
negative or reproduces it. On the published file, the published harness, mainline llama.cpp and a fully
resident card, it overturns it: the drafter helps. So "speculative drafting cannot help the 35B-A3B" is not a
property of the model class. But the published row's *mechanism* — batched verification pulling up to 64
experts per layer through a card that is already streaming experts over PCIe — is an offload-regime claim,
and this run is not in that regime. The card holds every expert. Whether the DFlash drafter also wins at
`-ncmoe 24` on the 3060 is the direct retest of the row and is still unrun; that, not this, decides whether
the row's explanation survives. The 65% acceptance figure on the published row is not comparable to the
23.4% here: acceptance per token falls as the draft length rises, and the 0.8B run's draft length was never
recorded.

**The article is now wrong in two places** (`best-way-run-qwen-3-6-35b-moe-locally`, not touched in this
commit): "No DFlash support for MoE … The DFlash team hasn't said when or whether it will" — z-lab shipped
the drafter in April and retrained it in June, and llama.cpp v0.4.0 runs it on mainline with no fork; and
"What doesn't help: a separate speculative-decoding drafter", which is true of the 0.8B drafter on the 3060
and false as a general statement. The correction is owed with these numbers and a 3060 offload retest.

## Setup, as run

| | |
|---|---|
| build | `~/llama-v0.4.0`, v0.4.0 `5266f24`, CUDA 12.4 toolkit, gcc-13, sm_86, GGML_NATIVE=OFF — the 09-21 build, unchanged |
| target | `~/bench-models/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf`, 22,134,528,992 B, sha256 `ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61` (matches Miu 08-28, Rushuna, Tamanna 09-21) |
| drafter source | `z-lab/Qwen3.6-35B-A3B-DFlash`, HF revision `f181eece`, `model.safetensors` 771,819,674 B sha256 `1fb90ef50a32bfb8dd2abfe601dd3608d6d5b59dc342820a98830f76f8cd72b7` = the LFS record; downloaded to `LLM_repo/qwen3.6-35b-a3b-dflash/` first |
| why not the ready-made GGUF | `starskyzheng/Qwen3.6-35B-DFlash-GGUF` is dated 2026-05-08; z-lab's "Update weights and config from Modal retrain" commit is 2026-06-19 (`0ce151d0`), so that GGUF is a quant of the superseded weights, as the marker suspected |
| conversion | v0.4.0 `convert_hf_to_gguf.py --outtype f16 --target-model-dir LLM_repo/qwen3.6-35b-a3b` on Miu (tokenizer comes from the target's HF tree; the drafter repo ships none). GGUF metadata: arch `dflash`, 6 blocks, block_size 16, target_layers [2,7,12,17,23,28,33,38], SWA 4096 on 5 of 6 layers, mask token 248077. F16 sha256 `564740dc…e7fc`, 782,819,712 B |
| quant | v0.4.0 `llama-quantize … Q8_0` on Tamanna: 391 MiB, 8.50 BPW, sha256 `17f7a3989c4b49392d79b9801f606cf8b627f0f97055a693d6044999d1a64634`; both GGUFs archived in `LLM_repo/qwen3.6-35b-a3b-dflash-gguf/` with `SHA256SUMS` |
| server, baseline | `llama-server -m TARGET -ngl 99 -fa on -c 8192 -np 1` |
| server, drafter | same + `-md DRAFT -ngld 99 --spec-type draft-dflash --spec-draft-n-max 15` (15 = trained block 16 minus the anchor; llama.cpp clamps anything higher; the default n_max of 3 would have throttled the drafter to a fifth of its block) |
| requests | `/completion`, `n_predict 192, temperature 0, seed 42, cache_prompt false`, the nine prompts of `docs/bench-results/mtp-2026-05-06/am17an_bench.sh` lifted by AST, unmodified |
| design | one discarded priming run per config (cold NVMe load; kept as `raw-prime-*`), then A, B, A, B, A, B measured, fresh server each run, warm page cache throughout (22 GB + 0.4 GB in 31 GiB) |
| telemetry | 1 s `nvidia-smi` from before launch to after exit, the 09-21 sampler fields; PCIe gen 3 x16 in every under-load sample of all 8 runs, host view and GPU view |
| card before first load | 7 MiB, 44 °C; `pcie.link.gen.max / gpumax` = 3 / 4 |
| metric | aggregate tok/s = sum(predicted_n) / sum(predicted_ms) from the server's own timings; resolvability by the 08-28 rule (gap must exceed the larger same-config rep spread) |

## Things to know before quoting this

- **Disclosure on pre-registration order.** One smoke test (`smoke-server.log`, code_python only, 249.4 tok/s at
  0.509 acceptance) ran before the pre-registration text was written, to confirm the drafter loaded and to see
  the clamp rule for `--spec-draft-n-max`. The design, metric and verdict rule were fixed after that and before
  any measured run; nothing was changed after the measured runs.
- **Greedy outputs are not bit-identical.** At temperature 0, six of nine prompts produce different text with
  the drafter than without (`divergence.py` / `divergence.json`, a diagnostic run after the measured block,
  first divergent token position in the table above). The three that stay identical include the two fastest.
  The usual explanation is that the verification batch runs different CUDA kernel paths over the Q4 weights
  than single-token decode, so the target's own argmax can flip on near-ties; that mechanism was not verified
  here. It means "lossless" should not be claimed for this path without a quality check.
- **Baseline cross-check.** The same box, build and file did 161.75 tok/s on `llama-bench` tg128 at d=0 the
  night before (gen 3 half). The server path on this prompt mix reads 157.6 — the usual server-vs-bench gap,
  and coincidentally the number Miu's published resident row carries (157.66, different rig, different build).
- **Regime.** Fully resident on a 24 GB card. The drafter adds 2.4 GiB (draft weights, its KV cache, the
  verification batch); 814 MiB remained at -c 8192. An F16 draft (+360 MiB) should still fit and was not run.
  A 16 GB card cannot hold this pairing without offload, which puts it back in the untested regime.
- **Not run, by design:** `-ncmoe` offload, the F16 draft, other block sizes, the model's own MTP head
  (`unsloth/Qwen3.6-35B-A3B-MTP-GGUF`), chat-template / thinking-enabled prompts (the drafter card and the
  GGUF quant card both warn that `<think>` collapses acceptance; these prompts are raw `/completion`, no
  template). Each is a follow-up, not a caveat on this number.
- Gen 3, not gen 4: Mark set the slot to gen 3 for the 09-21 test and it was still there this morning. The
  09-21 halves put the gen 3 penalty at 0.5-0.9% on resident decode, under the size of any effect here.

## Addendum, 2026-09-22 afternoon: the greedy divergence, run down

Asked and answered in three diagnostics after the measured block (`divergence2.py`, `probs3.py`, outputs in
`divergence2.json`, `divergence3-probs.json`, verbose server log `server-divergence2-dflash.log.gz`).

**The acceptance rule is exact-match.** `common/sampling.cpp` `common_sampler_sample_and_accept_n`: for each
draft position, sample the target (greedy at temperature 0), accept while `draft[i] == id`, break at the first
mismatch and emit the target's own sampled token there. The server calls it at `tools/server/server-context.cpp:3900`.
No tolerance, no probability threshold on this path (`synth_probs` is empty unless synthetic rates are set).
So the drafter never puts a token in the output; every token is the target's argmax under the batch that
scored it.

**Where the six diverge, and what the drafter's log says at that token.** Positions are generated-token
indices; the step log comes from `SLT_DBG "add accepted tokens"` / `"accepted N/15 draft tokens"` with
`--verbose`, mapped by cumulative `ids.size`.

| prompt | first divergent token | baseline emits | drafter arm emits | in the drafter's step log, that token was |
|---|---:|---|---|---|
| explain_concept | 153 | ` (` | `.` | the target's own sampled token, step 33, after 1/15 accepted |
| summarize | 22 | ` mechan` | ` the` | the target's own sampled token, step 7, after 3/15 accepted |
| qa_factual | 56 | `Relative` | `Range` | the target's own sampled token, step 13, after 8/15 accepted |
| creative_short | 66 | `,` | ` against` | the target's own sampled token, step 14, after 1/15 accepted |
| stepwise_math | 2 | `\n\n` | `\n` | the target's own sampled token, step 1, 0/15 accepted |
| long_code_review | 97 | `_history` | ` history` | **an accepted draft token**, step 26, 3/15 accepted (the target's batched argmax agreed with the draft) |

**Why they diverge: the target's logits depend on batch shape.** `n_probs` on the non-speculative server at
each position, single-token decode versus the same prefix scored as one batch with no drafter loaded:

| prompt | single-token top-2 gap (nats) | drafter's token's rank under single-token decode | batched prefix scoring picks |
|---|---:|---|---|
| explain_concept | 0.138 | 2nd | **the drafter arm's token** (order flipped) |
| creative_short | 0.198 | 2nd | **the drafter arm's token** (order flipped) |
| stepwise_math | 0.004 | 2nd | baseline's |
| summarize | 0.165 | 2nd | baseline's |
| qa_factual | 0.0001 (`Relative` vs `Character`) | 3rd | baseline's |
| long_code_review | 0.265 | 2nd | baseline's |

Every divergent token is a near-tie resolved differently, and a batched scoring pass with no speculative
code involved flips two of them and moves every logprob by 0.05–0.4 nats. The verify batch is 16 tokens
(above `MMVQ_MAX_BATCH_SIZE`), and a hybrid target takes the checkpoint-restore-and-replay path after a
partial accept, so it is a third batch shape. This is the batch-invariance problem already documented
upstream in [#25618](https://github.com/ggml-org/llama.cpp/issues/25618) (24 comments, Vulkan / Metal /
ROCm / CUDA, repro PR #28488) and [#27407](https://github.com/ggml-org/llama.cpp/issues/27407) (CUDA sm_86).
Not a drafter bug, not a DFlash bug, not specific to this model. A new issue would be a duplicate; a comment
adding the release-build, MoE-hybrid, width-16, no-drafter-control data point was posted on 2026-09-22:
https://github.com/ggml-org/llama.cpp/issues/25618#issuecomment-5780750697 (text in `UPSTREAM-COMMENT-DRAFT.md`; scripts and JSON in the public gist
https://gist.github.com/msb-msb/b253958ee294ff8d1ea4157ac7190284).

**Consequence for the number.** None for throughput. For quality claims: "lossless" cannot be claimed for
greedy spec decode on a quantized target in this build, on any backend, until upstream lands batch-invariant
kernels. The text is still the target's own greedy choice at every position; it is the target being scored
in a batch that differs.

The article got its dated note the same afternoon (`best-way-run-qwen-3-6-35b-moe-locally`, under the 3060
section's drafter paragraph, plus a superseded pointer on the "No DFlash support for MoE" bullet), deployed
and verified live.

**2026-09-23, PCIe generation of this run.** Every run in this record was made with Tamanna's slot at **PCIe Gen 3**: the BIOS was set to Gen 3 on 2026-09-21 for the gen 3 half of the baseline (`../tamanna-gen3-baseline-2026-09-21/`) and restored to Gen 4 on 2026-09-23, verified that day by re-running the 09-21 gen 4 set (every cell within 1%, worst 0.58%). The 09-21 gen 3 / gen 4 comparison bounds the effect on a fully resident model at 0.5–0.9% on decode and ~0 on prefill, so no figure above is changed.
