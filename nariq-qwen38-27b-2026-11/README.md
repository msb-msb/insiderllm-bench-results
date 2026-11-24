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

## Results (run 2026-11-24, 23:20-23:32 UTC, Rushuna RTX 3060 12 GB)

Run folder: `run/` (`summary.txt` and `summary.json` from `harness/summarize.py`; per-request logs in `out-*.txt`, raw
JSON in `results-*.json`, server logs, memwatch, card 1 s samples). No cell is void: prompt_n 510-513 and 4,095-4,097
across all arms, cache_n 0, swap-out 0, PCIe 3.0 x16 in every prefill, decode NVMe reads ≤ 3 MiB. `build_info` read
`b12431-a946eb541` (mainline) and `b12442-9d5c990a2` (fork) on every arm. Daemon CPU ≤ 0.28 s per arm (no flag).
Memory floor never approached (min MemAvailable 26.9 GiB).

Cell = median of 3 (min..max), 256-token decode, thinking off:

| Arm | Prompt | Decode tok/s | Prompt tok/s | Card peak |
|---|---:|---|---|---:|
| M-IQ3 (mainline, UD-IQ3_XXS) | 512 | 20.55 (20.55..20.57) | 526.0 (370.4..530.1) | 10,857 MiB |
| M-IQ3 | 4,096 | 20.26 (20.26..20.26) | 581.0 (581.0..581.1) | 10,857 MiB |
| F-IQ3 (fork, UD-IQ3_XXS) | 512 | 20.53 (20.50..20.54) | 530.3 (529.6..530.9) | 10,857 MiB |
| F-IQ3 | 4,096 | 20.23 (20.23..20.24) | 580.2 (580.1..580.6) | 10,857 MiB |
| F-N3 (fork, NariQ 3.0 bpw) | 512 | 22.00 (21.98..22.02) | 369.4 (366.2..369.4) | 10,373 MiB |
| F-N3 | 4,096 | 21.65 (21.65..21.67) | 388.6 (388.2..388.8) | 10,373 MiB |
| F-N25 (fork, NariQ 2.5 bpw) | 512 | 23.05 (23.04..23.06) | 367.9 (367.8..368.3) | 8,771 MiB |
| F-N25 | 4,096 | 22.69 (22.68..22.69) | 389.0 (388.3..389.0) | 8,771 MiB |

Client TTFT at 4,096: M-IQ3 7.1-7.2 s, F-N3 and F-N25 10.6-10.7 s.

### Claims (N8)

- **F1 (F-N3 decodes slower than M-IQ3): FAILS at both lengths.** F-N3 is *faster*: 1.071x at 512 and 1.069x at
  4,096, ranges apart. On this card, NariQ 3.0 bpw decodes about 7% faster than the same-size stock file on mainline.
- **F2 (the fork leaves stock files alone): HOLDS at both lengths and both metrics.** F-IQ3/M-IQ3 decode 0.999 at
  both lengths (ranges apart, but inside the 0.97-1.03 band); prompt 1.008 (no difference shown) at 512 and 0.999
  (ranges apart, inside the band) at 4,096.
- **Format alone (F-N3/F-IQ3, same build):** decode 1.072x / 1.070x faster; prompt processing 0.697x / 0.670x
  slower (512 / 4,096).
- **F-N25/F-N3:** decode 1.048x faster at both lengths; prompt processing no difference shown.

### Predictions (N7)

| Prediction | Result | Score |
|---|---|---|
| F-N3/M-IQ3 decode 0.50-0.85x | 1.071 / 1.069 | **MISS** both (wrong direction) |
| F-N25/F-N3 decode 1.05-1.20x | 1.0475 / 1.0479 | **MISS** both (just under the band) |
| F-N3/M-IQ3 prompt 0.30-0.80x | 0.702 / 0.669 | HIT both |
| F-IQ3 vs M-IQ3: no difference shown | prompt @512 no difference; decode @512 and @4,096 and prompt @4,096 differ by ≤ 0.1% with ranges apart | HIT 1 of 4, MISS 3 of 4 (F2 still holds: its band allows these) |
| F-N3 loads and answers at 16K, not at 32K | answers at 16K; at 32K loads, then crashes on the first request | HIT (scored on "answers") |
| F-N25 loads at 32K | loads and answers, peak 10,309 MiB | HIT |
| M-IQ3 behaves like F-N3 | answers at 16K; at 32K does not load | HIT on "answers"; the failure differs (see below) |

### Fit probe (N5, reported only)

| File | -c 16384 | -c 32768 |
|---|---|---|
| F-N3 | loads, answers, 21.99 tok/s, peak 10,871 MiB | loads (peak 11,867 MiB), then **aborts** after the first token: `trellis.cu:344 tq_gemv_group launch: out of memory` (`server-P-F-N3-32768.log`) |
| F-N25 | loads, answers, 23.15 tok/s, peak 9,269 MiB | loads, answers, 23.07 tok/s, peak 10,309 MiB |
| M-IQ3 | loads, answers, 20.63 tok/s, peak 11,377 MiB | does not load: `cudaMalloc failed: out of memory` allocating the 150 MiB recurrent-state cache |

Scoring note (ours, written after the probe): the lock's outcomes are "loads/answers or does-not-fit". F-N3 at 32K is
neither: the server started, the 512-token request returned one token, and the server process aborted on a fork
kernel's OOM. We count that as not answering, which is how the fit predictions above are scored. `summarize.py`
first counted any non-empty answer head as an answer; it was changed to require a full 256-token answer before the
predictions were written here.

### Answers (N6 addition)

The third request of each cell is kept in full (`answer_full` in `results-*.json`). All 24 measured answers summarise
`common/arg.cpp` coherently. The NariQ answers are worded differently from the IQ3 ones (e.g. at 512 they open with
the includes list instead of a "Primary Purpose" heading) and are of the same standard. F-IQ3's third answer is
identical to M-IQ3's at 512; at 4,096 the two match for the first 1,126 characters, then diverge in wording near the
end (one token's choice, "multimodal projectors" vs "related assets"), as can happen with different kernel builds at
temperature 0.

### Observation (not scored)

Server RssAnon grows by about 350 MB per request in every arm (e.g. M-IQ3 600 MB after the cold request, 3.66 GB
after the sixth measured one), with `cache_prompt false` and cache_n 0. This looks like the server's host-side prompt
cache keeping each request's state; it doesn't touch the card, and it's the same on both builds.

**Checked 2026-11-24 (Mark's follow-up; observation, not a result).** `harness/ramcheck.py`, output in `ramcheck/`: the
M-IQ3 command, 5 requests of the 512 prompt in the same request shape, RSS read 1 s after each, run twice on the
mainline build, once as is and once with `--cache-ram 0` added.

| After | RssAnon, default (`--cache-ram` 8192) | RssAnon, `--cache-ram 0` |
|---|---:|---:|
| load | 266 MiB | 266 MiB |
| request 1 | 586 | 586 |
| request 2 | 933 | 586 |
| request 3 | 1,281 | 586 |
| request 4 | 1,628 | 586 |
| request 5 | 1,975 | 586 |

With the cache disabled, RssAnon rises once on the first request (working buffers) and then stays flat at 586 MiB. With
the default it grows by about 347 MiB per request. So the growth is llama.cpp's host prompt cache storing each
finished request's state even though the requests send `cache_prompt false` (and cache_n stays 0, so nothing is
reused). **It is not a leak.** The default caps the cache at 8,192 MiB, which we didn't run long enough to reach. None
of the measured arms came near the memory floor (min MemAvailable 26.9 GiB), and the cache lives in host RAM, not
on the card, so no cell is affected.

### What this does and doesn't say

- Speed only, one card (RTX 3060, Ampere, PCIe 3.0). The fork's README says Ampere decode is slower than stock GGUFs
  and that no GeForce card was tested; on this GeForce Ampere card, at these lengths, NariQ decoded faster and
  prefilled slower (about 0.67-0.70x).
- Quality is not measured here. Whether 3.0 bpw NariQ is as good as, better or worse than UD-IQ3_XXS waits for
  section T (KLD/PPL on Tamanna, BOS pinned and token counts matched per the N5 gate decision).
