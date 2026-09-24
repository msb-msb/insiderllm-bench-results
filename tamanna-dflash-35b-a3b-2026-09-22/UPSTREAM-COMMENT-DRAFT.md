# Comment posted to ggml-org/llama.cpp issue #25618 on 2026-09-22

Posted at: https://github.com/ggml-org/llama.cpp/issues/25618#issuecomment-5780750697

Target thread: https://github.com/ggml-org/llama.cpp/issues/25618 ("Eval bug: Speculative decoding
(draft-mtp / draft-dspark): greedy output diverges from vanilla on quantized targets", open, 24 comments).
A new issue would duplicate it: the thread already holds the mechanism (batch-invariance violation, N=1 vs
N>1 kernel dispatch), CUDA sm_86 data (#27407, thc1006's mmvq.cu width table), a Qwen3.6-35B-A3B MoE
data point (dan-arnold, Q8_K_XL + draft-mtp) and a repro PR (#28488). What is not in the thread: a CUDA
release-build (v0.4.0) data point on an external DFlash drafter with a MoE + Gated DeltaNet hybrid target,
at width 16, with a no-drafter batched control on the same box. That is what this adds.

---

**CUDA sm_86, v0.4.0 release, Qwen3.6-35B-A3B UD-Q4_K_M + external DFlash drafter (width 16): same divergence, with a no-drafter control that isolates it to the target's batched logits**

Adding a data point on the release build and on an external block-diffusion drafter against a MoE + Gated
DeltaNet hybrid target, plus one control I did not see in the thread: reproducing the argmax flip with **no
drafter loaded at all**, by scoring the same prefix as a batch.

### Setup

- llama.cpp **v0.4.0** (`5266f24`), CUDA 12.4 toolkit, `CMAKE_CUDA_ARCHITECTURES=86`, `GGML_NATIVE=OFF`, gcc-13
- RTX 3090 24 GB, driver 580.178.04, Ubuntu 26.04, PCIe slot at gen 3
- Target: `unsloth/Qwen3.6-35B-A3B-GGUF` `Qwen3.6-35B-A3B-UD-Q4_K_M.gguf`, sha256 `ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61`, fully resident (`-ngl 99`), f16 KV, `-fa on -c 8192 -np 1`
- Draft: `z-lab/Qwen3.6-35B-A3B-DFlash` at HF revision `f181eece` (2026-06-19 weights), converted with v0.4.0's own `convert_hf_to_gguf.py --target-model-dir <Qwen/Qwen3.6-35B-A3B tree>` to F16 and quantized to Q8_0 with v0.4.0's `llama-quantize` (Q8_0 sha256 `17f7a3989c4b49392d79b9801f606cf8b627f0f97055a693d6044999d1a64634`); GGUF metadata `dflash.block_size=16`, `dflash.target_layers=[2,7,12,17,23,28,33,38]`, SWA 4096 on 5 of 6 layers
- Speculative arm adds `-md <draft> -ngld 99 --spec-type draft-dflash --spec-draft-n-max 15` (block 16 minus the anchor, so every verify batch is **16 tokens**, above `MMVQ_MAX_BATCH_SIZE`)
- Requests: raw `/completion`, no chat template, `temperature 0, seed 42, n_predict 192, cache_prompt false`; the nine prompts of am17an's gist (code, prose, QA, translation, math). Fresh server per arm; each arm run three times and byte-identical to itself every time (both arms are deterministic).

### Result

6 of 9 prompts diverge; the three that stay identical include the two with the highest acceptance
(code, 51% and 25%). Acceptance rule in this build is exact-match (`common_sampler_sample_and_accept_n`:
sample the target at each draft position, accept while `draft[i] == id`, stop at the first mismatch, emit
the target's own token there), so every emitted token is the target's greedy pick under whatever batch it
was scored in. The divergent token is the target's *own sampled token at the first mismatch* in 5 of 6
cases and an *accepted draft token* in 1 (the target's batched argmax agreed with the draft where the
single-token argmax did not).

Top candidates at the first divergent generated position, from `n_probs` on the **non-speculative**
server (the spec path leaves `probs` unset), single-token decode vs the same prefix scored as one batch
(`prompt = prompt_tokens + baseline_tokens[:i]`, `n_predict 1`; no drafter loaded):

| prompt | pos | single-token decode: top-1 / top-2 (logprob) | Δ | batched prefix scoring: top-1 / top-2 (logprob) | Δ | spec arm emitted |
|---|---:|---|---:|---|---:|---|
| explain_concept | 153 | ` (` −0.660 / `.` −0.797 | 0.138 | **`.` −0.705 / ` (` −0.751** (flipped) | 0.046 | `.` |
| creative_short | 66 | `,` −0.994 / ` against` −1.193 | 0.198 | **` against` −1.036 / `,` −1.146** (flipped) | 0.110 | ` against` |
| stepwise_math | 2 | `\n\n` −0.6912 / `\n` −0.6951 | **0.004** | `\n\n` −0.667 / `\n` −0.720 | 0.054 | `\n` |
| summarize | 22 | ` mechan` −0.623 / ` the` −0.788 | 0.165 | ` mechan` −0.558 / ` the` −0.873 | 0.315 | ` the` |
| qa_factual | 56 | `Relative` −1.2484 / `Character` −1.2485 / `Range` −1.445 | 0.0001 | `Relative` −0.889 / `Range` −1.461 | 0.572 | `Range` |
| long_code_review | 97 | `_history` −0.569 / ` history` −0.835 | 0.265 | `_history` −0.652 / ` history` −0.737 | 0.085 | ` history` |

Three things from that table:

1. In every case the token the speculative arm emitted is the target's **runner-up** (once third) under
   single-token decode, at gaps of 0.0001 to 0.27 nats. These are near-ties being resolved differently, not
   a different distribution.
2. The **no-drafter batched control flips the same argmax in 2 of 6 cases** and moves every logprob by
   0.05–0.4 nats. So the target's logits for a given position depend on the batch shape it was scored in,
   with no speculative code involved. The verify batch (16 tokens, plus the checkpoint-restore replay that
   a hybrid target needs after a partial accept) is a third shape again, which is why it does not always
   agree with the prefix-scoring batch (52–818 tokens here) either.
3. Draft quality is not a variable: the drafter proposes, the target decides, and both arms are
   deterministic run-to-run.

This matches the thread's standing explanation (N-dependent kernel dispatch and reduction order; on CUDA
the `mmvq.cu` width boundaries) and extends it to a release build, a MoE hybrid target where the expert
GEMM path also changes with N, and width 16. Throughput was fine (1.09x aggregate on this prompt set, 1.64x
on code), so as in #27407 this is a bit-exactness report, not a functional one.

Scripts and raw responses (per-token ids, `n_probs` dumps, and the per-step accept mapping from the
verbose server log) are in a public gist: https://gist.github.com/msb-msb/b253958ee294ff8d1ea4157ac7190284 (`divergence.py`,
`divergence2.py`, `probs3.py`, `divergence*.json`, README with the exact setup).

---

Gist created 2026-09-22 (public, msb-msb). Posted to #25618 the same day: https://github.com/ggml-org/llama.cpp/issues/25618#issuecomment-5780750697
