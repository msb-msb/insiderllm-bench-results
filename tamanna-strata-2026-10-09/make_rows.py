"""Stage benchmarks.json rows for this record: python3 make_rows.py > benchmarks-rows-staged.json

Arms S1 (as shipped), S3 (engine speed), L1 (llama.cpp defaults), L2 (-b 4096 -ub 4096), at 4,096 / 16,384 / 32,512,
for both files (iq3xxs, coder). L3 is omitted: GGML_CUDA_REGISTER_HOST=1 pins nothing on v0.4.0, so it repeats L2
(../tamanna-register-host-2026-10-10/). S2 chunk-sweep rows are not staged (not asked for).
Templates: the rushuna-coder-iq1m-* rows in benchmarks.json v1.14.0 (same harness, same Coder file).
"""
import copy, json, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
BJ = os.path.join(HERE, "../../../insiderllm-hugo/static/benchmarks.json")
ROWS = {r["id"]: r for r in json.load(open(BJ))["benchmarks"]}
LENS = ["4096", "16384", "32512"]
ART = "https://insiderllm.com/guides/strata-vs-llama-cpp-rtx-3090/"
HARNESS = ("bench_strata.py (rushuna's bench_coder.py with 4 changes: llama.cpp path, -t 8, model picked by run directory, "
           "prep tokenizes rushuna's exact prompt files): streamed /v1/chat/completions, one user message (8-hex nonce + "
           "llama.cpp v0.4.0 source cut on the model's tokenizer + 'Summarise what this code does.'), enable_thinking false, "
           "temperature 0, max_tokens 256; engine-reported timings")
RUN_ORDER = ("Coder first, then IQ3_XXS; per file S1, S2-2048, S2-4096, S2-8192, (S0 refused), S3, L1, L2, L3, unattended by "
             "run_all.sh; one server resident at a time; a discarded priming request of the same length before each measured one")
METHOD = ("Pre-registered in docs/candidates/strata-2026-10-05.md section B6 (approved 2026-10-09) before any measured run. "
          "prompt_tok_s and generation_tok_s are means of 3 measured requests; spreads are max-min. Swap and NVMe figures are per "
          "measured request from /proc/vmstat and /proc/diskstats. Only MemAvailable < 2 GiB stopped a run (never tripped). "
          "Measured 2026-10-09 Pacific time (the IQ3_XXS sequence ran past midnight UTC). Strata engine binary compiled on rushuna "
          "from the same commit (sha256 aeb18940ab33e81129f5f04e6efbd2720293386d490d218c2f280d75178242ea, byte-identical to the "
          "rushuna run's): CUDA 13.0.2 cannot compile against Ubuntu 26.04's glibc 2.43. The v0.1.39 tag has since moved upstream; "
          "the commit is what ran. GGML_CUDA_REGISTER_HOST arm (L3) not included: it pins nothing on llama.cpp v0.4.0.")

HW = {
    "rig": "tamanna", "gpu": "NVIDIA GeForce RTX 3090 24GB", "gpu_count": 1, "vram_gb": 24, "driver": "580.178.04",
    "cpu": "AMD Ryzen 7 5700X (8c/16t, Zen 3)", "system_ram_gb": 64, "system_ram_type": "DDR4-3000",
    "system_ram_channels": 2, "system_ram_bandwidth_gbs": 48,
    "system_ram_detail": ("4 x 16 GB G.Skill F4-3200C16-16GVK, dual rank, all 4 slots (62 GiB visible), set manually to DDR4-3000 "
                          "at 1.35 V (BIOS P4.00; 3200 failed training at Auto, 1.35 and 1.38 V). memtest86+ one full pass, 0 errors. "
                          "Sustained read 42.30 GB/s (stream_read.c, docs/bench-results/tamanna-ram-speed-offload-2026-10-09); "
                          "system_ram_bandwidth_gbs is the dual-channel theoretical figure"),
    "motherboard": "ASRock B550 Phantom Gaming 4/ac (BIOS P4.00)",
    "pcie": "4.0 x16 (gen 4 x16 read from nvidia-smi during every measured prefill)",
    "os": "Ubuntu 26.04.1, kernel 7.0.0-38", "display_attached": False,
}

coder_model = copy.deepcopy(ROWS["rushuna-coder-iq1m-s1-p4096"]["model"])
iq3_model = copy.deepcopy(coder_model)
iq3_model.update({
    "name": "Qwen3.8-Flash-Next (ISTA GSQ-RCO)", "repo": "ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF",
    "repo_revision": "ed59f92082b1e93c0e96d60a8b11aab089b52f09", "experts_per_layer": 512, "quant": "IQ3_XXS",
    "gguf_file_type": 23, "file_size_value": 75.84, "file_size_unit": "GB", "file_size_bytes": 47039860096 + 28800138432,
    "sha256": "219ea929900dfa9ef091f3aa473fdba6874b65fcb36526d7d851ac9e95856d15",
    "sha256_shards": ["219ea929900dfa9ef091f3aa473fdba6874b65fcb36526d7d851ac9e95856d15",
                      "316b46f3a2dbd68c900f43136ab9449f9dcc3725dfd8c794847c204bc161e113"],
    "sha256_verified_at": "2026-10-09",
})

FILES = {
    "iq3xxs": dict(prefix="tamanna-iq3xxs", model=iq3_model, ncmoe=34, arena=20464, hit="98.7%",
                   shard1="Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf", pack="iq3_xxs"),
    "coder": dict(prefix="tamanna-coder-iq1m", model=coder_model, ncmoe=20, arena=11992, hit="99.7%",
                  shard1="Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-00001-of-00002.gguf", pack="coder-iq1_m"),
}
coder_model["sha256_verified_at"] = "2026-10-09"


def cells(sub, arm, n):
    return [c["measured"] for c in json.load(open(os.path.join(HERE, sub, f"results-{arm}.json")))["cells"][n]]


def stats(ms, key, nd):
    v = [m["timings"][key] for m in ms]
    return round(st.mean(v), nd), round(max(v) - min(v), nd)


def row(sub, arm, n):
    F = FILES[sub]; ms = cells(sub, arm, n)
    gen, gsp = stats(ms, "predicted_per_second", 2); pp, psp = stats(ms, "prompt_per_second", 1)
    peak = max(m["peak_card_mib"] for m in ms)
    strata = arm.startswith("S")
    mode = (f"strata normal (all routed experts pinned via cudaHostRegister: {F['arena']:,} x 2 MiB arena; setup picked "
            "normal mode on 64 GB)")
    sflags = ("strata (serve/server.py config) --expert-cache auto --prefill auto --spec 4 --spec-min-p 0.5 --mtp "
              "Strata-data/mtp/rt --max-context 34816 --kv int8")
    if arm == "S3":
        sflags = sflags.replace("--spec 4", "--spec 2") + " --mtp-max-t 1"
    lflags = (f"llama-server -m {F['shard1']} -ngl 99 -ncmoe {F['ncmoe']} -fa on -c 34816 -np 1 --lazy-mode on -t 8"
              + (" -b 4096 -ub 4096" if arm == "L2" else ""))
    cfg = {"flags": sflags if strata else lflags,
           "n_gpu_layers": None if strata else 99, "n_cpu_moe": None if strata else F["ncmoe"],
           "flash_attention": None if strata else True, "load_mode": mode if strata else "mmap",
           "threads": None if strata else 8,
           "batch_size": None if strata else (4096 if arm == "L2" else 2048),
           "ubatch_size": None if strata else (4096 if arm == "L2" else 512),
           "prompt_tokens": int(n), "context_depth_tokens": int(n), "batch": 1, "speculative_decoding": None}
    res = {"generation_tok_s": gen, "generation_repeat_spread_tok_s": gsp, "prompt_tok_s": pp,
           "prompt_repeat_spread_tok_s": psp, "status": "ok", "vram_peak_mib": peak,
           "vram_used_gb": round(peak * 1.048576 / 1000, 1), "system_ram_used_gb": None,
           "ttft_s": round(st.mean(m["ttft_s"] for m in ms), 2),
           "swap_out_kib_max_per_request": max(m["swapout_kib"] for m in ms),
           "swap_in_kib_max_per_request": max(m["swapin_kib"] for m in ms),
           "mem_available_min_mib": min(m["mem_after"]["avail_mib"] for m in ms)}
    if arm == "S1":
        dn = sum(m["timings"]["draft_n"] for m in ms); da = sum(m["timings"]["draft_n_accepted"] for m in ms)
        cfg["speculative_decoding"] = {
            "method": "Strata default: the model's own MTP draft layer plus prompt lookup (--spec 4: MTP windows of 4, lookup windows up to 6, per the engine's own widening)",
            "draft_model": "Strata-data/mtp (mtp-q2_0.gguf, 889 MB), fetched by Strata setup",
            "draft_vram_gib": None, "draft_budget": "--spec 4 --spec-min-p 0.5"}
        res.update({"acceptance_rate": round(da / dn, 4), "draft_tokens_generated": dn, "draft_tokens_accepted": da})
    if arm == "S3":
        assert all(m["timings"].get("draft_n", 0) == 0 for m in ms)
        res.update({"draft_tokens_generated": 0, "draft_tokens_accepted": 0})
    slots = []
    for i, m in enumerate(ms, 1):
        t = m["timings"]
        slots.append({"slot": f"rep {i}", "position": i, "prompt_n": t["prompt_n"], "prompt_tok_s": round(t["prompt_per_second"], 1),
                      "generation_tok_s": round(t["predicted_per_second"], 2), "ttft_s": round(m["ttft_s"], 2),
                      "draft_n": t.get("draft_n") if strata else None, "draft_n_accepted": t.get("draft_n_accepted") if strata else None,
                      "swap_in_kib": m["swapin_kib"], "swap_out_kib": m["swapout_kib"], "nvme_read_mib": m["nvme_read_mib"],
                      "pcie_rx_mb_s_prefill": round(m["prefill_rx_mb_s_mean"]) if m.get("prefill_rx_mb_s_mean") else None,
                      "mem_available_after_mib": m["mem_after"]["avail_mib"], "vram_peak_mib": m["peak_card_mib"]})
    armtxt = {"S1": "S1: as shipped (MTP + prompt lookup, --prefill auto = 8192)",
              "S3": "S3: no drafts (--spec 2 --mtp-max-t 1, draft layer loaded, draft_n 0 on every request)",
              "L1": "L1: defaults (-b 2048 -ub 512)", "L2": "L2: -b 4096 -ub 4096"}[arm]
    prov = {"engine": "Strata" if strata else "llama.cpp", "engine_build": "v0.1.39" if strata else "v0.4.0",
            "engine_commit": "6f32ec0" if strata else "5266f24",
            "compute": "CUDA sm_86 (engine compiled on rushuna by setup, nvcc 13.0.88, gcc 13.3; byte-identical binary)" if strata
            else "CUDA sm_86 (CUDA 12.4, gcc-13, built on tamanna)",
            "harness": HARNESS, "repetitions": 3, "run_order": RUN_ORDER, "comparison_set": "tamanna-strata-2026-10-09",
            "arm": armtxt, "run_slots": slots, "methodology_note": METHOD, "source_article": ART,
            "raw_log": f"docs/bench-results/tamanna-strata-2026-10-09/{sub}/results-{arm}.json"}
    what = "the full Qwen3.8-Flash-Next" if sub == "iq3xxs" else "the Coder cut (bridge to the rushuna-coder-iq1m-* rows)"
    notes = {"S1": f"Strata as shipped on {what}: prefill and the 'as shipped' decode figure (drafting on). Its baseline_ref is the S3 no-drafts row at the same length.",
             "S3": f"Strata engine-speed decode on {what}: draft layer loaded, zero drafts verified on every request (--spec 0 is refused on native IQ packs). Decode expert-cache hit rate {F['hit']} (engine log); {10553 if sub == 'iq3xxs' else 8843} experts resident on the card.",
             "L1": f"llama.cpp at default batch sizes on {what}; -ncmoe {F['ncmoe']} was the lowest that serves a 32,512-token prompt under L2, used for every llama.cpp arm.",
             "L2": f"llama.cpp with -b 4096 -ub 4096 on {what} (-ub is capped at -b, so both are needed)."}[arm]
    r = {"id": f"{F['prefix']}-{arm.lower()}-p{n}", "measurement_type": "measured", "date_measured": "2026-10-09",
         "date_measured_precision": "day"}
    if arm == "S1": r["baseline_ref"] = f"{F['prefix']}-s3-p{n}"
    r.update({"hardware": copy.deepcopy(HW), "model": copy.deepcopy(F["model"]), "config": cfg, "result": res,
              "provenance": prov, "notes": notes})
    return r


out = [row(sub, arm, n) for sub in ("iq3xxs", "coder") for arm in ("S1", "S3", "L1", "L2") for n in LENS]
json.dump({"_status": "STAGED 2026-10-10, not merged", "rows": out}, open(os.path.join(HERE, "benchmarks-rows-staged.json"), "w"), indent=1)
print(len(out), "rows")
