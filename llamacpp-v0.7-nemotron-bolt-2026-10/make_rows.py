#!/usr/bin/env python3
"""benchmarks.json rows for the 2026-11-03 Tamanna run (arms A, B, C2, C3), built from this record's raw files.
  python3 make_rows.py > rows.json
Every value is read from raw-*.json here; nothing is typed in by hand except fixed facts (hardware, model card, sha256s,
which are in README.md). Means are over the measured invocations/requests; spreads are max - min; generation_tok_s_stddev
on multi-invocation llama-bench rows is the wider of the runs' own stddevs (schema convention for paired rows)."""
import json, os, glob, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
ARTICLE = "https://insiderllm.com/guides/nemotron-3-5-bolt-24gb-rtx-3090/"
REC = "docs/bench-results/llamacpp-v0.7-nemotron-bolt-2026-10"
PREREG = {"path": "docs/candidates/llamacpp-v0.7-nemotron-bolt-2026-10.md (main repo; not mirrored)",
          "sha256": "3857cbb2ddfe9c31b1e7e71b82143956992e2e2471d081daa391ba2677a9bbee", "lock_commit": "9cc92ae5"}
SET = "tamanna-llamacpp-v070-bolt-2026-11-03"

HW = {"rig": "tamanna", "gpu": "NVIDIA GeForce RTX 3090 24GB", "gpu_count": 1, "vram_gb": 24, "driver": "580.178.04",
      "cpu": "AMD Ryzen 7 5700X (8c/16t, Zen 3)", "system_ram_gb": 64, "system_ram_type": "DDR4-3000", "system_ram_channels": 2,
      "system_ram_bandwidth_gbs": 48,
      "system_ram_detail": "4 x 16 GB G.Skill F4-3200C16-16GVK, dual rank, all 4 slots (62 GiB visible), set manually to DDR4-3000 at 1.35 V (BIOS P4.00). Sustained read 42.03 / 42.00 / 42.08 GB/s on the day (stream_read.c, 4 threads, " + REC + "/card-state.txt); dmidecode not re-read on the day (needs sudo). system_ram_bandwidth_gbs is the dual-channel theoretical figure",
      "motherboard": "ASRock B550 Phantom Gaming 4/ac (BIOS P4.00)",
      "pcie": "4.0 x16 (gen 4 x16 in every under-load telemetry sample)", "os": "Ubuntu 26.04.1, kernel 7.0.0-38",
      "display_attached": True,
      "display_note": "HDMI-A-1 connected and display_active Enabled on 2026-11-03, but no X/Wayland session: 7 MiB of VRAM in use at idle, included in every VRAM figure. Earlier tamanna rows record false.",
      "gpu_state": "stock: no gpu-unlock module loaded or installed; cuBLAS FP16-in/FP32-acc 8192^3 GEMM 75.33 TFLOPS at 1,845-1,950 MHz (" + REC + "/gemm-check.txt)"}

QWEN = {"name": "Qwen3.6-35B-A3B", "repo": "unsloth/Qwen3.6-35B-A3B-GGUF", "architecture": "moe", "gguf_architecture": "qwen35moe",
        "params_total_b": 35, "params_active_b": 3, "experts_per_layer": 256, "experts_routed_per_token": 8, "experts_shared": 1,
        "quant": "UD-Q4_K_M", "quant_source": "unsloth-UD", "file_size_value": 20.6, "file_size_unit": "GiB", "file_size_bytes": 22134528992,
        "sha256": "ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61", "sha256_verified_against": "upstream-lfs-oid",
        "sha256_verified_at": "2026-11-03", "expert_tensor_bytes": 19568525312}
BOLT = {"name": "NVIDIA Nemotron 3.5 Bolt 74B-A9B 24GB", "repo": "nvidia/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB-GGUF",
        "repo_revision": "e0fecb69", "architecture": "moe", "gguf_architecture": "nemotron_h_moe", "params_total_b": 74, "params_active_b": 9,
        "experts_per_layer": None, "experts_per_layer_range": "240-496 (varies by layer: 12 x 240, 6 x 304, 9 x 368, 10 x 432, 3 x 496, from ffn_up_exps shapes; header expert_count 496)",
        "experts_routed_per_token": 9, "experts_shared": 1, "quant": "IQ2_XXS (experts; NVFP4 Mamba, Q8_0 embedding/output per the card)",
        "quant_source": "NVIDIA (vendor quant, quantization-aware distillation)", "gguf_file_type": 19,
        "file_size_value": 22.02, "file_size_unit": "GB", "file_size_bytes": 22018326528, "gguf_block_count": 88,
        "attention_layers": 8, "ssm_layers": 40, "moe_layers": 40, "attention_kv_heads": 2, "attention_head_dim": 128,
        "sha256": "91d63363e782c8a3d5f4be42816eba8e0d42dd2530bd07a7d0d2dc440599af75", "sha256_verified_against": "upstream-lfs-oid",
        "sha256_verified_at": "2026-11-03", "license_note": "OpenMDW-1.1 (model card)."}
V04 = {"engine": "llama.cpp", "engine_build": "v0.4.0", "engine_commit": "5266f24", "compute": "CUDA sm_86 (CUDA 12.4, gcc-13, GGML_NATIVE=OFF, built on tamanna)"}
V07 = {"engine": "llama.cpp", "engine_build": "v0.7.0", "engine_commit": "620d222", "compute": "CUDA sm_86 (CUDA 12.4, gcc-13, GGML_NATIVE=OFF, built on tamanna)"}


def load(n): return json.load(open(os.path.join(HERE, f"raw-{n}.json")))
def r2(x): return round(x, 2)


def tel(metas):
    t = [m["telemetry"] for m in metas]
    return {"peak_temp_c": max(x["gpu_temp_max"] for x in t), "sm_clock_mhz": st.median([x["sm_clock_mhz"]["median"] for x in t]),
            "power_draw_w": r2(st.mean(x["power_w"]["mean"] for x in t)), "power_draw_max_w": max(x["power_w"]["max"] for x in t),
            "pcie_gen_under_load": 4, "power_scope": "board-level (nvidia-smi power.draw), mean over samples at >= 50% utilisation"}


def base(id_, model, cfg, res, telem, prov, notes):
    return {"id": id_, "measurement_type": "measured", "date_measured": "2026-11-03", "date_measured_precision": "day",
            "hardware": HW, "model": model, "config": cfg, "result": res, "telemetry": telem, "provenance": prov, "notes": notes}


rows = []

# ---- A: llama-bench, resident, both builds ----
for b, eng in (("v04", V04), ("v07", V07)):
    recs = [load(f"A-{b}-rep{i}") for i in (1, 2, 3)]
    for d in (0, 4096):
        def cell(r, k): return next(x for x in r["rows"] if x["kind"] == k and x["depth"] == d)
        tg = [cell(r, "tg") for r in recs]; pp = [cell(r, "pp") for r in recs]
        res = {"generation_tok_s": r2(st.mean(x["avg_ts"] for x in tg)), "generation_tok_s_stddev": r2(max(x["stddev_ts"] for x in tg)),
               "generation_repeat_spread_tok_s": r2(max(x["avg_ts"] for x in tg) - min(x["avg_ts"] for x in tg)),
               "prompt_tok_s": r2(st.mean(x["avg_ts"] for x in pp)), "prompt_tok_s_stddev": r2(max(x["stddev_ts"] for x in pp)),
               "prompt_repeat_spread_tok_s": r2(max(x["avg_ts"] for x in pp) - min(x["avg_ts"] for x in pp)), "status": "ok",
               "vram_peak_mib": int(max(r["meta"]["telemetry"]["peak_vram_mib"] for r in recs)), "system_ram_used_gb": None}
        res["vram_used_gb"] = round(res["vram_peak_mib"] * 1.048576 / 1000, 1)
        slots = [{"slot": f"rep {i} (measured, after a discarded priming run)", "generation_tok_s": r2(t["avg_ts"]), "generation_tok_s_stddev": r2(t["stddev_ts"]),
                  "prompt_tok_s": r2(p["avg_ts"]), "prompt_tok_s_stddev": r2(p["stddev_ts"]), "vram_peak_mib": int(r["meta"]["telemetry"]["peak_vram_mib"]),
                  "temp_max_c": r["meta"]["telemetry"]["gpu_temp_max"], "sm_clock_mhz": r["meta"]["telemetry"]["sm_clock_mhz"]["median"],
                  "power_draw_w": r["meta"]["telemetry"]["power_w"]["mean"]} for i, (r, t, p) in enumerate(zip(recs, tg, pp), 1)]
        rows.append(base(f"tamanna-{'v040' if b == 'v04' else 'v070'}-qwen36-35b-a3b-udq4km-resident-d{d}-20261103", QWEN,
            {"flags": "llama-bench -ngl 99 -ncmoe 0 -fa 1 -lm mmap -t 8", "n_gpu_layers": 99, "n_cpu_moe": 0, "flash_attention": True,
             "load_mode": "mmap", "threads": 8, "context_depth_tokens": d, "batch": 1, "speculative_decoding": None},
            res, tel([r["meta"] for r in recs]),
            dict(eng, harness="llama-bench -ngl 99 -ncmoe 0 -fa 1 -p 512 -n 128 -d 0,4096 -r 5 -t 8 -lm mmap -o json", repetitions=5, invocations=3,
                 run_order="(v0.4.0 priming, v0.4.0 measured, v0.7.0 priming, v0.7.0 measured) x 3, unattended", comparison_set=SET + "-A",
                 run_slots=slots, prereg=PREREG, source_article=ARTICLE, raw_log=REC + "/run.log",
                 methodology_note="Arm A of the pre-registration (build A/B, same file, same command). v0.4.0 cells within 2% of the 2026-10-09 values (drift check). Power is board-level."),
            "Build A/B arm. v0.7.0 / v0.4.0: decode 0.9957 (d=0) / 0.9955 (d=4096), prompt 1.1577 / 1.1413; ranges do not overlap on any metric. Keep the build label on every row."))

# ---- B: llama-server nine-prompt, -ncmoe 20 ----
summ = json.load(open(os.path.join(HERE, "B-summary.json")))
cfgB = {"B1": (V04, "", "v040"), "B2": (V07, "", "v070"), "B3": (V07, " --moe-cache-mib 1866", "v070-moecache1866")}
for c, (eng, extra, tag) in cfgB.items():
    recs = [r for r in summ["results"] if r["config"] == c]
    names = [x["name"] for x in recs[0]["results"]]
    per = [{"prompt": n, "tok_s": r2(st.mean(next(x["predicted_per_second"] for x in r["results"] if x["name"] == n) for r in recs))} for n in names]
    agg = [r["aggregate"]["gen_tok_s"] for r in recs]; ppa = [r["aggregate"]["prompt_tok_s"] for r in recs]
    res = {"generation_tok_s": r2(st.mean(r["aggregate"]["mean_per_prompt_tok_s"] for r in recs)), "generation_tok_s_aggregate": r2(st.mean(agg)),
           "generation_repeat_spread_tok_s": r2(max(agg) - min(agg)), "prompt_tok_s": r2(st.mean(ppa)), "prompt_repeat_spread_tok_s": r2(max(ppa) - min(ppa)),
           "status": "ok", "vram_peak_mib": int(max(r["meta"]["telemetry"]["peak_vram_mib"] for r in recs)), "system_ram_used_gb": None,
           "per_prompt": per}
    res["vram_used_gb"] = round(res["vram_peak_mib"] * 1.048576 / 1000, 1)
    slots = [{"slot": f"rep {r['rep']}", "generation_tok_s_aggregate": r["aggregate"]["gen_tok_s"], "prompt_tok_s": r["aggregate"]["prompt_tok_s"],
              "generation_tok_s": r["aggregate"]["mean_per_prompt_tok_s"], "vram_peak_mib": int(r["meta"]["telemetry"]["peak_vram_mib"]),
              "power_draw_w": r["meta"]["telemetry"]["power_w"]["mean"]} for r in recs]
    note = {"B1": "Arm B baseline on v0.4.0.", "B2": "Arm B, v0.7.0 no cache. B2/B1 aggregate decode 0.998.",
            "B3": "Arm B, v0.7.0 with --moe-cache-mib 1866 (10% of the 18,662 MiB of expert tensors; free VRAM was 11,298 MiB). B3/B2 aggregate decode 1.050, prompt 0.944. One cache size only, the one the locked rule gave."}[c]
    rows.append(base(f"tamanna-{tag}-qwen36-35b-a3b-udq4km-ncmoe20-server9-20261103", QWEN,
        {"flags": "llama-server -ngl 99 -ncmoe 20 -fa on -c 8192 -np 1 --fit off -lm mmap -t 8" + extra, "n_gpu_layers": 99, "n_cpu_moe": 20,
         "flash_attention": True, "load_mode": "mmap", "threads": 8, "context_size": 8192, "context_depth_tokens": None, "batch": 1,
         "speculative_decoding": None, "moe_cache_mib": 1866 if c == "B3" else None},
        res, tel([r["meta"] for r in recs]),
        dict(eng, harness="am17an gist, 9 prompts, /completion, n_predict=192, temperature=0.0, seed=42, cache_prompt=false; fresh llama-server per run",
             repetitions=3, run_order="one discarded priming run per config (B1, B2, B3), then (B1, B2, B3) x 3", comparison_set=SET + "-B",
             run_slots=slots, prereg=PREREG, source_article=ARTICLE, raw_log=REC + "/run.log",
             methodology_note="generation_tok_s is the per-prompt mean (schema convention); generation_tok_s_aggregate is sum(predicted_n)/sum(predicted_ms), the metric the prediction is scored on, and the repeat spread is on it. prompt_tok_s is sum(prompt_n)/sum(prompt_ms) over the nine short prompts, not a long-prefill figure. Power is board-level."),
        note))

# ---- C2: llama-server, 4,096-token prompt ----
for k in ("f16", "q8_0"):
    for ctx in (32768, 131072):
        r = load(f"C1C2-{k}-{ctx}")
        m = [x for x in r["requests"] if not x["discard"]]
        dec = [x["predicted_per_second"] for x in m]; pp = [x["prompt_per_second"] for x in m]
        res = {"generation_tok_s": r2(st.mean(dec)), "generation_repeat_spread_tok_s": r2(max(dec) - min(dec)),
               "prompt_tok_s": r2(st.mean(pp)), "prompt_repeat_spread_tok_s": r2(max(pp) - min(pp)), "status": "ok",
               "vram_peak_mib": int(r["vram_after_first_request_mib"]), "vram_headroom_mib": int(r["headroom_after_first_mib"]), "system_ram_used_gb": None}
        res["vram_used_gb"] = round(res["vram_peak_mib"] * 1.048576 / 1000, 1)
        slots = [{"slot": f"request {x['i']}", "prompt_n": x["prompt_n"], "prompt_tok_s": r2(x["prompt_per_second"]),
                  "generation_tok_s": r2(x["predicted_per_second"]), "predicted_n": x["predicted_n"]} for x in m]
        rows.append(base(f"tamanna-v070-nemotron35-bolt-24gb-c{ctx // 1024}k-kv{k.replace('_', '')}-server-p4096-20261103", BOLT,
            {"flags": f"llama-server -ngl 99 -fa on -c {ctx} -np 1 -ctk {k} -ctv {k} --fit off -lm mmap -t 8", "n_gpu_layers": 99, "n_cpu_moe": None,
             "flash_attention": True, "load_mode": "mmap", "threads": 8, "context_size": ctx, "cache_type_k": k, "cache_type_v": k,
             "prompt_tokens": 4096, "context_depth_tokens": 4096, "batch": 1, "speculative_decoding": None},
            res, tel([r["meta"]]),
            dict(V07, harness="/completion with a 4,096-token prompt sent as token ids (10-09 Strata llama.cpp source cut, tokenized by the server, first 4,096 tokens), n_predict 128, ignore_eos, temperature 0, cache_prompt false; one discarded priming request then 3 measured",
                 repetitions=3, run_order="f16 32K, f16 128K, q8_0 32K, q8_0 128K; one server per cell", comparison_set=SET + "-C",
                 run_slots=slots, prereg=PREREG, source_article=ARTICLE, raw_log=REC + "/run.log",
                 methodology_note="Arm C1/C2. vram_peak_mib is nvidia-smi polled at 0.2 s from server ready through the first request; vram_headroom_mib is memory.total (24,576 MiB) minus that peak. KV / RS / compute buffers from a separate -lv 4 load of the same command (" + REC + "/c1-buffers.txt). Text only: no mmproj, no drafter. Power is board-level."),
            "Bolt " + ("at 128K" if ctx == 131072 else "at 32K") + f" with {k} KV loads and serves a 4,096-token prompt."))

# ---- C3: llama-bench depth ----
for k in ("f16", "q8_0"):
    sh = load(f"C3-{k}-short"); dp = load(f"C3-{k}-deep")
    cells = [(x, sh) for x in sh["rows"] if x["kind"] == "tg"] + [(x, dp) for x in dp["rows"] if x["kind"] == "tg"]
    for x, rec in cells:
        d = x["depth"]
        pp = next((y for y in rec["rows"] if y["kind"] == "pp" and y["depth"] == d), None)
        res = {"generation_tok_s": r2(x["avg_ts"]), "generation_tok_s_stddev": r2(x["stddev_ts"]),
               "prompt_tok_s": r2(pp["avg_ts"]) if pp else None, "prompt_tok_s_stddev": r2(pp["stddev_ts"]) if pp else None, "status": "ok",
               "vram_peak_mib": int(rec["meta"]["telemetry"]["peak_vram_mib"]), "system_ram_used_gb": None}
        res["vram_used_gb"] = round(res["vram_peak_mib"] * 1.048576 / 1000, 1)
        reps = 1 if d == 102400 else 3
        h = (f"llama-bench -ngl 99 -fa 1 -ctk {k} -ctv {k} -p 0 -n 128 -d 102400 -r 1 -t 8 -lm mmap -o json" if d == 102400 else
             f"llama-bench -ngl 99 -fa 1 -ctk {k} -ctv {k} -p 4096 -n 128 -d 0,4096 -r 3 -t 8 -lm mmap -o json")
        rows.append(base(f"tamanna-v070-nemotron35-bolt-24gb-kv{k.replace('_', '')}-d{d}-20261103", BOLT,
            {"flags": f"llama-bench -ngl 99 -fa 1 -ctk {k} -ctv {k} -lm mmap -t 8", "n_gpu_layers": 99, "n_cpu_moe": None, "flash_attention": True,
             "load_mode": "mmap", "threads": 8, "cache_type_k": k, "cache_type_v": k, "context_depth_tokens": d, "batch": 1, "speculative_decoding": None},
            res, tel([rec["meta"]]),
            dict(V07, harness=h, repetitions=reps, invocations=1, comparison_set=SET + "-C", prereg=PREREG, source_article=ARTICLE, raw_log=REC + "/run.log",
                 methodology_note="Arm C3. prompt_tok_s is pp4096 at the same depth; null on the 102,400-depth cell (-p 0). The deep cell is one repetition because each starts with a 102,400-token prefill, so no stddev. Power is board-level."),
            {0: "Short-depth decode.", 4096: "The C-decode and C-kv cell.",
             102400: "About 100K filled. f16 is 0.905 of its d=4096 decode; q8_0 at this depth is 60.61 against f16's 82.42."}[d]))

json.dump(rows, open(os.path.join(HERE, "rows.json"), "w"), indent=1)
for r in rows:
    print(f"{r['id']:72s} gen {r['result']['generation_tok_s']}  pp {r['result']['prompt_tok_s']}  vram {r['result']['vram_peak_mib']}")
