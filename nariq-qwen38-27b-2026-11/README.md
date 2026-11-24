# NariQ Qwen3.8-27B on Rushuna's RTX 3060: record

Pre-registration: `docs/candidates/nariq-qwen38-27b-2026-11.md`, lock commit `03361fb7`, sha256
`58d8a3d946fb9a39a2e118a50098b5175faadcc9895049d93bc9b3fd74332e40` (public copy under `candidates/` in the mirror,
hash checked 2026-11-24). This record covers the Rushuna part only. Section T (Tamanna) is not locked yet.

Results are added below after the run. Everything above "Results" was written before the first arm.

## N5 gate decision (pre-results)

**What tripped.** Lock N5 compares the NariQ GGUFs' tokenizer and chat template with the IQ3 file's before any arm,
and says "If they differ, the run stops and Mark is told." `harness/compare_meta.py` (run 2026-11-24 with the fork's
gguf-py) returned MISMATCH, full output in `rec/compare-meta.txt`:

| Key | UD-IQ3_XXS | NariQ 3.0 / 2.5 bpw |
|---|---|---|
| tokenizer.ggml.model / pre | gpt2 / qwen35 | same |
| tokens | n=248,320, hash b038c530… | same |
| merges | n=247,587, hash 1ecf49b3… | same |
| token_type | n=248,320, hash 276e9a86… | same |
| bos_token_id / eos_token_id | 248044 / 248046 | same |
| **padding_token_id** | **248055** | **248044** |
| **add_bos_token** | **absent** | **False** |
| **chat_template** | **9,993 chars, sha256 12827f24…** | **8,952 chars, sha256 c3cf9e34…** |

The IQ3 template is Unsloth's: it adds handling for system/developer messages, tool-call checks and a high→xhigh
reasoning-effort mapping. Both templates are kept in `rec/chat_template-iq3.jinja` and `rec/chat_template-nariq.jinja`.

**Why the differences don't reach a measured prompt.**
- Render check (`harness/render_check.py`, output `rec/render-check.txt`): the harness's own request shape (one user
  message, `enable_thinking` false, generation prompt on), with the whole HotRod corpus as the body, renders to the
  same 600,194 bytes under both templates, sha256 `7fc11978…ad892`. The wrapper is
  `<|im_start|>user\n…<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n` in both.
- BOS: absent and False both mean no BOS is added for this gpt2-type vocab. Mainline `llama-tokenize` on the IQ3 file
  turns "hello\n" into `[14556, 198]`, with no BOS. A one-token difference would in any case trip the N6 prompt_n rule
  (more than 3 tokens apart between arms voids the cell), and the per-request prompt_n is recorded.
- The pad ID is not used by single-sequence chat completions.

**Decision (Mark, 2026-11-24 15:00): go.** The run proceeds on this basis: identical tokenizer (vocab, merges,
BOS/EOS), and the harness request renders byte-identical under both templates, so the template differences don't
reach any measured prompt.

**Added by the same decision, for any PPL/KLD run (on Rushuna, or later in section T):** BOS handling is pinned
explicitly and the same for every file, and token counts are checked to match across files before any comparison. A
mismatch voids that comparison, and it is reported.

**Recorded with the decision (deviation notes, not changes to any arm):**
- `/props` has no `build_commit` field at these commits; N3's check reads `build_info` instead, whose suffix is the
  commit (as in the MoE cache record: `"b12359-b1b770d90"`). Expected: mainline `b12431-a946eb541`, fork
  `b12442-9d5c990a2` (the fork's build number counts its own 11 commits; `--version` says build 12442).
- N3 default flags: the fork's 11 commits touch no file under `common/` or `tools/server/` (`git diff --stat
  a946eb5 9d5c990`: 156 files, of which 67 are deleted `.github/workflows` files; the rest are `ggml/src` (39),
  `ggml/include` (2), `src/` and tests). So no default differs between the two builds.

## Pre-arm state (not measurements)

- Builds: mainline `a946eb541`, `llama-server` sha256 `7b55b988…89d7`; fork `9d5c990a2`, `llama-server` sha256
  `b4f5c896…c492`. Both compiled under `unshare -Un`, log in `rec/build.log`.
- Models: the three working copies re-hashed OK on the run day (`run/machine-state.txt`); store copies in LLM_repo
  (`qwen3.8-27b-nariq-gguf/`, `qwen3.8-27b-gguf/`) re-hashed OK 2026-11-24.
- Machine: driver 580.173.02, PCIe 3.0 x16 at idle, swap 4 GiB with 0 used, `ollama ps` empty, mycoswarm and ollama
  active (A1 not in force, lock N5).
- Prompts: cut by `harness/cut_prompts.py` on the IQ3 file with mainline `llama-tokenize` (median of 16 nonces):
  `prompt-512.txt` 1,648 chars, sha256 `fe9c7420…99ea` (nonce counts 509-513); `prompt-4096.txt` 15,361 chars,
  sha256 `7ad80637…9a82` (4,093-4,097).
- Token-count check across files (`harness/token_counts.sh`, `rec/token-counts.txt`), one fixed nonce: the rendered
  512 request is 510 tokens and the 4096 request 4,094 tokens on all four file/build pairs (IQ3 on mainline and fork,
  both NariQ files on the fork), with **identical token-ID sequences** (ids sha256 `ac3df708…` and `cfeea90d…`).
