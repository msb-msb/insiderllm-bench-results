# Tamanna, GGML_CUDA_REGISTER_HOST × RAM speed, 2026-10-10: STOPPED at the gate, nothing measured

Results record for `docs/candidates/tamanna-register-host-ram-speed-2026-10.md` (approved by Mark 2026-10-10; Mark
available for the BIOS switches today, overriding the "not this weekend" note).

## Step 1 at DDR4-3000: checks done

- **Box:** up since 2026-10-09 15:44, the boot after Mark restored DDR4-3000 / 1.350 V (dmidecode 3000 MT/s × 4 on that
  boot, voltage confirmed in the BIOS). Idle: no Strata, llama.cpp or download running; card 7 MiB used.
- **Bandwidth, 10:54 PDT** (`stream_read.c` md5 `331785328ca94900143b5c062c101bcd`, 4 threads): **42.25 / 42.30 / 42.20
  GB/s** (`stream-read-before.txt`), matching 42.44 and 42.30 on 10-09. The only kernel log line matching MCE is
  "MCE: In-kernel MCE decoding enabled", the boot banner.
- **File:** Qwen3.6-35B-A3B UD-Q4_K_M sha256 `ac0e2c11…53e31a61` (`sha256.txt`), **match**.

## The gate: FAILED. llama.cpp v0.4.0 never registers host memory

The pre-registration's staging check: the first registration-on load must print "pinned … MiB of mapped model memory";
if v0.4.0 doesn't print it, the on-cells are void and the run stops.

`GGML_CUDA_REGISTER_HOST=1 llama-bench -m Qwen3.6-35B-A3B-UD-Q4_K_M.gguf -ngl 99 -ncmoe 40 -fa 1 -p 0 -n 8 -r 1 -t 8
-lm mmap` (`gate-check.txt`): ran (tg8 41.57 tok/s), **no "pinned" line**.

To tell apart "registration happened but llama-bench hides the log" from "registration didn't happen", I read the v0.4.0
source (`5266f24`, `v040-source-excerpt.txt`):

- `ggml-cuda.cu` still has `ggml_backend_cuda_register_host_buffer()`, which checks the env var and calls
  `cudaHostRegister`, and exposes it through the backend registry as `"ggml_backend_register_host_buffer"`.
- **Nothing in `src/`, `common/` or `tools/` looks it up or calls it** (`grep register_host` there: 0 hits; the
  registry lookups in `src/` are numa, features, extra bufts, split buffer, threads, abort callback, threadpool).
  The string "mapped model memory" is not in the tree.

So on v0.4.0, **`GGML_CUDA_REGISTER_HOST=1` is a no-op for model weights**: the env var is read only inside a function
that llama never calls. The 08-24 Rushuna run (`../rushuna-hostregister-2026-08-24/`) printed "pinned 12564.33 MiB of
mapped model memory" from **build `20f5994`**, which had that call. Both local trees are shallow clones, so when and
where the call was removed isn't traceable here.

**Per the abort rule the run stopped here.** No measured cell, no BIOS switch. Tamanna stays at DDR4-3000 / 1.35 V
(the 10:54 bandwidth above). The tg8 gate run is not a result.

## Pass/fail

Not applicable: the test can't be run with the pinned engine. **The candidate explanation for the +27–30% offloaded
pp512 gain (pageable staging memcpy) is still untested**, and still not ruled out. Testing it needs a build that
registers the mapping (e.g. `20f5994`, or v0.4.0 with the loader call put back), which is a new engine, so a new
pre-registration. Mark's call.

## What this changes in earlier records (report; nothing published edited)

- **Strata L3 arms are the same configuration as L2.** `tamanna-strata-2026-10-09` (Tamanna) and
  `rushuna-strata-coder-2026-10-05` (Rushuna) both ran L3 = L2 + `GGML_CUDA_REGISTER_HOST=1` on v0.4.0. Nothing was
  pinned. Their "L3 adds nothing" findings are two repeats of L2, not a finding about pinned memory.
- **Published:** `strata-vs-llama-cpp-rtx-3060` says the third arm "pins the host copy of the experts" and "The batch
  size is the lever — pinning isn't." The figures stand; the mechanism is wrong (nothing was pinned), so the page can't
  say pinning doesn't help. Needs a dated correction: Mark's decision.
- **Drafts:** `docs/drafts/strata-vs-llama-cpp-rtx-3090.md` carried the same wording, and
  `docs/drafts/b550-four-sticks-ddr4-3000.md` said the test was scheduled. Both updated (drafts only).
