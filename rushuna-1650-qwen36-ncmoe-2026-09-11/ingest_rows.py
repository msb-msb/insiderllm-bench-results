#!/usr/bin/env python3
"""Add the 2026-09-11 Rushuna rows to static/benchmarks.json (v1.7.0).

Qwen3.6-35B-A3B UD-Q4_K_M, llama.cpp v0.4.0 (5266f24, sm_75+sm_86 bundle), 4 threads, mmap:
  GTX 1650 4 GB  -ncmoe 40 and 38   (stock and best fit)
  RTX 3060 12 GB -ncmoe 40 and 24   (same day, same slot; sits BESIDE the July b10088 rows)
d=0 and d=4096 each: eight rows. Same row shape as the v1.6.0 Flash-Next rows.
"""
import json, statistics as st

ROOT = "/home/minotaur/Desktop/InsiderLLM"
DS = f"{ROOT}/insiderllm-hugo/static/benchmarks.json"
ART = "https://insiderllm.com/guides/qwen3-6-35b-a3b-gtx-1650-4gb-vs-rtx-3060/"
SHA = "ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61"

HW_BASE = {"rig": "rushuna", "gpu_count": 1, "driver": "580.173.02", "cpu": "Intel Core i7-7700 (4c/8t)",
           "system_ram_gb": 32, "system_ram_type": "DDR4-2133", "system_ram_channels": 2, "system_ram_bandwidth_gbs": 34,
           "pcie": "3.0 x16", "os": "Ubuntu 24.04.4, kernel 6.8.0-136", "display_attached": False}
HW = {
    "gtx1650": dict(HW_BASE, gpu="NVIDIA GeForce GTX 1650 4GB", vram_gb=4),
    "rtx3060": dict(HW_BASE, gpu="NVIDIA GeForce RTX 3060 12GB", vram_gb=12),
}
MODEL = {
    "name": "Qwen3.6-35B-A3B", "repo": "unsloth/Qwen3.6-35B-A3B-GGUF", "architecture": "moe",
    "params_total_b": 35, "params_active_b": 3, "experts_per_layer": 256, "experts_routed_per_token": 8, "experts_shared": 1,
    "quant": "UD-Q4_K_M", "quant_source": "unsloth-UD",
    "file_size_value": 20.6, "file_size_unit": "GiB", "file_size_bytes": 22134528992,
    "gguf_block_count": 40, "transformer_layers": 40,
    "sha256": SHA, "sha256_verified_against": "upstream-lfs-oid", "sha256_verified_at": "2026-09-11",
}
RUNS = [
    # key, results dir, ncmoe, reps used, note
    ("gtx1650", "rushuna-1650-qwen36-ncmoe-2026-09-11", 40, [1, 2, 3],
     "Stock on a GTX 1650 4 GB (TU117, 3,714 MiB usable): every routed expert on the host, dense layers, shared expert, head and KV on the card. The 22.1 GB file sits in the 32 GB page cache; /proc/diskstats moved 0 MiB during every decode and iostat averaged 0.9 kB/s read. llama.cpp prints at every load on this card: suboptimal performance due to a lack of tensor cores, consider CMAKE_CUDA_ARCHITECTURES=61-virtual;80-virtual and DGGML_CUDA_FORCE_MMQ. Not done; the sm_75 path as built is what these rows measure."),
    ("gtx1650", "rushuna-1650-qwen36-ncmoe-2026-09-11", 38, [1, 2, 3],
     "Best fit on 4 GB: two expert layers on the card. -ncmoe 37 loads its weights and fails compute-buffer allocation (283 MiB cudaMalloc out of memory in graph_reserve), so the load cliff and the usable cliff coincide at 38. Same tensor-core caveat as the stock row. A --load-mode none pair at this setting (three invocations, 20.70 / 20.22 at d=0 / d=4096; server prefill 70.5 vs 66.0) is in the raw record and the article, not in this file."),
    ("rtx3060", "rushuna-3060-qwen36-ncmoe-2026-09-11", 40, [1, 2, 3],
     "RTX 3060 back in the same slot the same day, same build, same file, file pre-read into page cache before the run. Sits beside the July b10088 row rushuna-qwen36-35b-a3b-udq4km-ncmoe40-d0 (28.1 at d=0), which it reproduces within 0.1 percent; that row is not replaced."),
    ("rtx3060", "rushuna-3060-qwen36-ncmoe-2026-09-11", 24, [1, 2, 3],
     "The published best fit on 12 GB, re-run on v0.4.0. Sits beside the July b10088 rows rushuna-qwen36-35b-a3b-udq4km-ncmoe24-d0 / -d4096 (38.9 / 38.5), which it reproduces within 1 percent; those rows are not replaced. Harness differs from July only in -p 0 and -t 4."),
]

def load_stats(dirname, n, reps):
    R = json.load(open(f"{ROOT}/docs/bench-results/{dirname}/results.json"))
    recs = [r for r in R["sweep"] if r["ncmoe"] == n and r.get("rows") and int(r["tag"][-1]) in reps]
    out = {}
    for d in (0, 4096):
        v = [(int(r["tag"][-1]), x["avg_ts"], x["stddev_ts"]) for r in recs for x in r["rows"] if x["depth"] == d]
        out[d] = {"mean": round(st.mean(a for _, a, _ in v), 2), "sd": round(st.mean(s for _, _, s in v), 2),
                  "spread": round(max(a for _, a, _ in v) - min(a for _, a, _ in v), 2),
                  "slots": [{"slot": f"invocation {i}", "position": i, "generation_tok_s": round(a, 2), "generation_tok_s_stddev": round(s, 2)} for i, a, s in v]}
    out["vram"] = max(r["peak_vram_mib"] for r in recs)
    return out

def row(key, dirname, n, d, s, reps, note):
    tag = "gtx1650" if key == "gtx1650" else "v040"
    return {
        "id": f"rushuna-{tag}-qwen36-35b-a3b-udq4km-ncmoe{n}-d{d}",
        "measurement_type": "measured", "date_measured": "2026-09-11", "date_measured_precision": "day",
        "hardware": HW[key], "model": MODEL,
        "config": {"flags": f"-ngl 99 -ncmoe {n} -fa 1 -t 4 -lm mmap", "n_gpu_layers": 99, "n_cpu_moe": n, "flash_attention": True,
                   "load_mode": "mmap", "threads": 4, "context_depth_tokens": d, "batch": 1, "speculative_decoding": None},
        "result": {"generation_tok_s": s[d]["mean"], "generation_tok_s_stddev": s[d]["sd"], "generation_repeat_spread_tok_s": s[d]["spread"],
                   "prompt_tok_s": None, "prompt_tok_s_stddev": None, "status": "ok",
                   "vram_peak_mib": s["vram"], "vram_used_gb": round(s["vram"] * 1.048576 / 1000, 1), "system_ram_used_gb": None},
        "provenance": {"engine": "llama.cpp", "engine_build": "v0.4.0", "engine_commit": "5266f24",
                       "compute": "CUDA sm_75" if key == "gtx1650" else "CUDA sm_86",
                       "harness": f"llama-bench -ngl 99 -ncmoe {n} -fa 1 -p 0 -n 128 -d 0,4096 -r 3 -t 4 -lm mmap",
                       "repetitions": 3, "invocations": len(reps), "run_slots": s[d]["slots"],
                       "methodology_note": note + " Build: v0.4.0 5266f24 compiled with CMAKE_CUDA_ARCHITECTURES=75;86 so one bundle serves both cards; otherwise the pinned build. Peak VRAM is the nvidia-smi maximum sampled every 0.5 s across the invocation. generation_tok_s_stddev is the mean of llama-bench's per-invocation stddev; generation_repeat_spread_tok_s is max minus min of the invocation means. The sha256 was checked on this box against the file behind the 2026-09-07 pin gate, itself verified against the upstream LFS object id.",
                       "source_article": ART, "raw_log": f"docs/bench-results/{dirname}/run.log"},
        "notes": ("Stock" if n == 40 else "Best fit") + f" on this card, -ncmoe {n}, {40 - n} of 40 expert layers on the GPU.",
    }

d = json.load(open(DS))
existing = {r["id"] for r in d["benchmarks"]}
new = []
for key, dirname, n, reps, note in RUNS:
    s = load_stats(dirname, n, reps)
    for depth in (0, 4096):
        r = row(key, dirname, n, depth, s, reps, note)
        assert r["id"] not in existing, r["id"]
        new.append(r)
d["benchmarks"].extend(new)
m = d["_meta"]
m["version"] = "1.7.0"; m["last_updated"] = "2026-09-11"; m["row_count"] = len(d["benchmarks"])
m["changelog"].insert(0, {"version": "1.7.0", "date": "2026-09-11", "changes": [
    "Added 8 rows for Qwen3.6-35B-A3B UD-Q4_K_M on rushuna, measured 2026-09-11 on llama.cpp v0.4.0 (5266f24), 4 threads, mmap: GTX 1650 4 GB at -ncmoe 40 and 38 (the first sub-8 GB rows in this file, and the first on a card without tensor cores), and RTX 3060 12 GB at -ncmoe 40 and 24, each at depth 0 and 4096.",
    "The 3060 rows sit beside the July b10088 rows for the same card and config; they do not replace them. v0.4.0 reproduces b10088 within 0.1 percent at -ncmoe 40 and within 1 percent at -ncmoe 24, the second machine to confirm the pin gate recorded in _meta.methodology.engine_pin.",
    "The 1650 rows carry llama.cpp's own no-tensor-cores warning for TU117 in their methodology_note; the suggested Pascal-code build was not tried and is an open variable, so these rows describe the sm_75 path as shipped.",
    "prompt_tok_s is null on all eight rows (-p 0). Server-path prefill on a 2,343-token prompt (1650: 65 to 66 tok/s; 3060: 242 stock, 365 at -ncmoe 24) is in the article, not in a row.",
]})
json.dump(d, open(DS, "w"), indent=1, ensure_ascii=False)
print("rows", len(d["benchmarks"]), "added", [r["id"] for r in new])
