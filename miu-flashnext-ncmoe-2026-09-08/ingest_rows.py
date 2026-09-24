#!/usr/bin/env python3
"""Add the Qwen3.8-Flash-Next rows to static/benchmarks.json (v1.6.0).

Four configs, two depths each, eight rows: miu -ncmoe 48 and 29, rushuna -ncmoe 48 and 41,
tg128 at d=0 and d=4096 from the 2026-09-08 sweeps. One row per config per depth, as every
llama-bench row in the file. Per-invocation figures go to provenance.run_slots; the row carries
the mean, the mean of llama-bench's per-run stddev, and the max-min spread across invocations.
"""
import json, statistics as st, os

ROOT = "/home/minotaur/Desktop/InsiderLLM"
DS = f"{ROOT}/insiderllm-hugo/static/benchmarks.json"
ART = "https://insiderllm.com/guides/qwen3-8-flash-next-rtx-3090-3060-32gb/"
SHA = ["268f81fdedf3149a538f252308927a4d5d1f6e062c178568a51e3b519744f8a8",
       "cfe600b236b88c7fad1613a5ca5e83b9f2beb63cbd44c32b2be50a44747c695f",
       "f1912ba34c79427d2295a58dcb2b732b5931af5bef7a373c60557a57d9ee7250"]

HW = {
    "miu": {"rig": "miu", "gpu": "NVIDIA GeForce RTX 3090 24GB", "gpu_count": 1, "vram_gb": 24, "driver": "580.178.04",
            "cpu": "Intel Core i7-8086K (6c/12t, Coffee Lake)", "system_ram_gb": 64, "system_ram_type": "DDR4-2667",
            "system_ram_channels": 2, "system_ram_bandwidth_gbs": 43,
            "system_ram_detail": "4 x 16GB Samsung M378A2K43DB1-CTD, dual-rank, all four slots populated across two channels",
            "motherboard": "ASRock B365M Pro4", "pcie": "3.0 x16", "os": "Ubuntu 24.04.4, kernel 6.8.0-138", "display_attached": False},
    "rushuna": {"rig": "rushuna", "gpu": "NVIDIA GeForce RTX 3060 12GB", "gpu_count": 1, "vram_gb": 12, "driver": "580.173.02",
                "cpu": "Intel Core i7-7700 (4c/8t)", "system_ram_gb": 32, "system_ram_type": "DDR4-2133", "system_ram_channels": 2,
                "system_ram_bandwidth_gbs": 34, "pcie": "3.0 x16", "os": "Ubuntu 24.04.4, kernel 6.8.0-136", "display_attached": False},
}
MODEL = {
    "name": "Qwen3.8-Flash-Next", "repo": "unsloth/Qwen3.8-Flash-Next-GGUF", "architecture": "moe", "gguf_architecture": "qwen4exp",
    "params_total_b": 125, "params_active_b": 6, "params_reported_b": 176.94,
    "experts_per_layer": 512, "experts_routed_per_token": 10, "experts_shared": 1, "ngram_embedding_params_b": 51,
    "quant": "UD-IQ3_XXS", "quant_source": "unsloth-UD", "quant_generation": "Unsloth Dynamic 2.0",
    "quant_reported_by_engine": "IQ3_XXS - 3.0625 bpw", "gguf_file_type": None,
    "file_size_value": 81.96, "file_size_unit": "GB", "file_size_bytes": 81961823936,
    "gguf_block_count": 48, "transformer_layers": 48, "trailing_mtp_block": None,
    "sha256": SHA[0], "sha256_shards": SHA, "sha256_verified_against": "upstream-lfs-oid", "sha256_verified_at": "2026-09-07",
}
THREADS = {"miu": 6, "rushuna": 4}
NOTES = {
    ("miu", 48): "Stock: every routed expert on the host. Mean of invocations 2 and 3 of 3. Invocation 1 (13.65 tok/s at d=0, 15.46 at d=4096) ran on a page cache emptied by the aborted --load-mode none attempt minutes earlier and re-read the 45 GiB expert set from NVMe during the run; it is excluded from the row as a cache-state artefact, in the same spirit as the v1.4.0 exclusion of -ncmoe 1/2 rows that measured nothing, and it is kept verbatim in the raw record and named in the article. The sweep ran -p 0, so prompt_tok_s is null here; pp512 at these flags on this rig was measured 2026-09-07 in docs/bench-results/miu-flashnext-stock-2026-09-07/ at 218.2 tok/s (d=0, warm) and 206.4 (d=4096), and those figures are in the article's method section.",
    ("miu", 29): "Best fit on 24 GB: the lowest -ncmoe that loads. -ncmoe 26 fails with cudaMalloc out of memory on a 24,991 MiB allocation (verbose load in the record). Peak VRAM 23,652 of 24,123 usable MiB.",
    ("rushuna", 48): "Stock on a 32 GB box whose page cache cannot hold the 45.3 GiB expert set. Read the d=4096 row as the decode figure: at d=0 the three repeats inside each invocation climb (7.18 / 9.04 / 9.91 in invocation 1) because each starts on whatever the previous one left cached, which is what the per-run stddev of 1.2 to 1.4 tok/s records. The server run in the same record measured 25 to 28 MiB read from the NVMe per decoded token at 220 to 250 MiB/s.",
    ("rushuna", 41): "Best fit on 12 GB: -ncmoe 38 fails with cudaMalloc out of memory on a 13,441 MiB allocation against 11,909 usable. Peak VRAM 11,665 MiB. Same d=0 cache-climb caveat as the stock row; d=4096 repeats agree to 0.06 tok/s.",
}

def load_stats(host, n, reps):
    R = json.load(open(f"{ROOT}/docs/bench-results/{host}-flashnext-ncmoe-2026-09-08/results.json"))
    recs = [r for r in R["sweep"] if r["ncmoe"] == n and r.get("rows") and int(r["tag"][-1]) in reps]
    out = {}
    for d in (0, 4096):
        v = [(int(r["tag"][-1]), x["avg_ts"], x["stddev_ts"]) for r in recs for x in r["rows"] if x["depth"] == d]
        out[d] = {"mean": round(st.mean(a for _, a, _ in v), 2), "sd": round(st.mean(s for _, _, s in v), 2),
                  "spread": round(max(a for _, a, _ in v) - min(a for _, a, _ in v), 2),
                  "slots": [{"slot": f"invocation {i}", "position": i, "generation_tok_s": round(a, 2), "generation_tok_s_stddev": round(s, 2)} for i, a, s in v]}
    out["vram"] = max(r["peak_vram_mib"] for r in recs)
    return out

def row(host, n, d, s, reps):
    t = THREADS[host]
    return {
        "id": f"{host}-qwen38-flashnext-udiq3xxs-ncmoe{n}-d{d}",
        "measurement_type": "measured", "date_measured": "2026-09-08", "date_measured_precision": "day",
        "hardware": HW[host], "model": MODEL,
        "config": {"flags": f"-ngl 99 -ncmoe {n} -fa 1 -t {t} -lm mmap", "n_gpu_layers": 99, "n_cpu_moe": n, "flash_attention": True,
                   "load_mode": "mmap", "threads": t, "context_depth_tokens": d, "batch": 1, "speculative_decoding": None},
        "result": {"generation_tok_s": s[d]["mean"], "generation_tok_s_stddev": s[d]["sd"], "generation_repeat_spread_tok_s": s[d]["spread"],
                   "prompt_tok_s": None, "prompt_tok_s_stddev": None, "status": "ok",
                   "vram_peak_mib": s["vram"], "vram_used_gb": round(s["vram"] * 1.048576 / 1000, 1), "system_ram_used_gb": None},
        "provenance": {"engine": "llama.cpp", "engine_build": "v0.4.0", "engine_commit": "5266f24", "compute": "CUDA sm_86",
                       "harness": f"llama-bench -ngl 99 -ncmoe {n} -fa 1 -p 0 -n 128 -d 0,4096 -r 3 -t {t} -lm mmap",
                       "repetitions": 3, "invocations": len(reps), "run_slots": s[d]["slots"],
                       "methodology_note": NOTES[(host, n)] + " Peak VRAM is the nvidia-smi maximum sampled every 0.5 s across the whole invocation. generation_tok_s_stddev is the mean of llama-bench's own per-invocation stddev; generation_repeat_spread_tok_s is max minus min of the invocation means.",
                       "source_article": ART, "raw_log": f"docs/bench-results/{host}-flashnext-ncmoe-2026-09-08/run.log"},
        "notes": ("Stock" if n == 48 else "Best fit") + f" on this rig, -ncmoe {n}, {48 - n} of 48 expert layers on the GPU.",
    }

d = json.load(open(DS))
existing = {r["id"] for r in d["benchmarks"]}
new = []
for host, n, reps in [("miu", 48, [2, 3]), ("miu", 29, [1, 2, 3]), ("rushuna", 48, [1, 2, 3]), ("rushuna", 41, [1, 2, 3])]:
    s = load_stats(host, n, reps)
    for depth in (0, 4096):
        r = row(host, n, depth, s, reps)
        assert r["id"] not in existing, r["id"]
        new.append(r)
d["benchmarks"].extend(new)
m = d["_meta"]
m["version"] = "1.6.0"; m["last_updated"] = "2026-09-08"; m["row_count"] = len(d["benchmarks"])
m["methodology"]["engine_pin"] = ("Rows measured from 2026-09-08 carry engine_build v0.4.0 / engine_commit 5266f24. The move from b10088 was gated on a back-to-back re-bench of the two canonical 3090 rows (Ornith-1.5-35B-A3B Q4_K_M and Qwen3.6-35B-A3B UD-Q4_K_M) on both builds in one session, 2026-09-07, harness byte-identical to the published rows: pooled over six reps per build no cell moved more than 2.4 percent, and the single-block prefill crossings of the 3 percent line (one against v0.4.0 in block 1, three for it in block 2) each trace to one low run and cancel when pooled. Rows measured on b10088 keep their b10088 tag; nothing was re-labelled. Record: docs/bench-results/miu-build-ab-2026-09-07/.")
m["schema"]["config.load_mode"] = "llama.cpp --load-mode as run (auto | none | mmap | mlock | mmap+mlock | dio). Present from v1.6.0. The 2026-09-08 Flash-Next rows ran mmap after --load-mode none was found to swap on the 62 GB rig with a 45 GiB host-resident expert set; the two none reps are in the raw record and the article, not in this file."
m["schema"]["config.threads"] = "llama-bench -t as run. Present from v1.6.0; earlier rows ran the harness default (physical cores)."
m["schema"]["model.sha256_shards"] = "For multi-shard GGUFs, the SHA-256 of every shard in order. model.sha256 carries shard 1 so the field stays a single string. Present from v1.6.0."
m["schema"]["model.experts_per_layer"] = "Routed experts per MoE layer, with experts_routed_per_token and experts_shared beside it, from the model card and confirmed by the loader. Present from v1.6.0."
m["schema"]["model.ngram_embedding_params_b"] = "Parameters in a non-transformer lookup table the file carries alongside the experts (Qwen3.8-Flash-Next: 51B n-gram embedding, 27,466 MiB at this quant, mmapped lazily). Counted in params_reported_b, not in params_total_b."
m["schema"]["provenance.invocations"] = "Number of separate llama-bench processes averaged into the row, each with its own -r repetitions. run_slots carries one entry per invocation. Present from v1.6.0."
m["changelog"].insert(0, {"version": "1.6.0", "date": "2026-09-08", "changes": [
    "Added 8 rows for Qwen3.8-Flash-Next UD-IQ3_XXS (Unsloth), the first rows on a model larger than either rig's RAM: miu (RTX 3090, 64 GB) at -ncmoe 48 and 29, rushuna (RTX 3060, 32 GB) at -ncmoe 48 and 41, each at depth 0 and 4096, measured 2026-09-08 on llama.cpp v0.4.0 (5266f24), headless, load-mode mmap.",
    "First rows on the v0.4.0 pin. The gate and its pooled result are in _meta.methodology.engine_pin; every earlier row keeps its b10088 tag.",
    "New fields: config.load_mode, config.threads, model.sha256_shards, model.experts_per_layer and companions, model.ngram_embedding_params_b, provenance.invocations. Each is described in _meta.schema.",
    "The miu stock row averages invocations 2 and 3 of 3; invocation 1 ran on a page cache emptied minutes earlier and is excluded as a cache-state artefact, with the figures kept in the raw record and in the row's methodology_note. The rushuna rows record 25 to 28 MiB of NVMe read per decoded token at stock, which is why their d=0 stddev is an order of magnitude above every other row's.",
    "prompt_tok_s is null on all eight rows because the sweep ran -p 0. pp512 at the miu stock flags was measured the day before (218.2 tok/s warm, d=0) and is published in the article's method section, not borrowed into a row measured on a different day.",
]})
json.dump(d, open(DS, "w"), indent=1, ensure_ascii=False)
print("rows", len(d["benchmarks"]), "added", [r["id"] for r in new])
