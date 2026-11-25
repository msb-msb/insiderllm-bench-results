"""Collects the per-arm figures for the README tables from each arm's per_clip.tsv, summary.json and WER output.
Pooled = all measured passes, ok clips; median/p90 numpy 'linear'. Usage: tables.py RECORD_DIR [ARM_PREFIX] -> JSON."""
import csv, json, pathlib, statistics, sys
import numpy as np
R = pathlib.Path(sys.argv[1]); PFX = sys.argv[2] if len(sys.argv) > 2 else ""
def f(x):
    try: return float(x)
    except (TypeError, ValueError): return None
def q(v, p):
    v = [x for x in v if x is not None]
    return round(float(np.percentile(v, p)), 1) if v else None
out = {}
for A in ("S1", "S2", "S3", "R0"):
    d = R / f"{PFX}{A}"
    if not (d / "per_clip.tsv").exists(): continue
    rows = list(csv.DictReader(open(d / "per_clip.tsv"), delimiter="\t"))
    ok = [r for r in rows if r["ok"] == "True"]
    sm = json.load(open(d / "summary.json"))
    o = {"ncmoe": sm["ncmoe"], "free_mib": sm["free_mib"], "vram_peak_mib": {k: v for k, v in sm["vram_peak_mib"].items() if k != "all_pids"},
         "n_clips": len(rows), "failed": sm["failed"], "sets": {}}
    groups = {"fleurs_en": [r for r in ok if r["set"] == "fleurs_en"], "fleurs_de": [r for r in ok if r["set"] == "fleurs_de"],
              "en_real": [r for r in ok if r["set"] == "en_real"], "fleurs_all": [r for r in ok if r["set"].startswith("fleurs")]}
    for g, rs in groups.items():
        e = {}
        for k in ("e2e_ms", "stt_ms", "stt_infer_ms", "llm_ttft_ms", "llm_first_sentence_ms", "tts_first_ms", "residual_ms",
                  "pre_reply_ms", "llm_decode_tok_s", "llm_prompt_eval_tokens", "llm_prompt_cached_tokens",
                  "llm_select_to_launch_ms", "reply_tokens", "first_sentence_tokens"):
            e[k] = {"median": q([f(r[k]) for r in rs], 50), "p90": q([f(r[k]) for r in rs], 90)}
        noresid = [f(r["e2e_ms"]) - f(r["residual_ms"]) for r in rs if f(r["e2e_ms"]) is not None and f(r["residual_ms"]) is not None]
        e["e2e_minus_residual_ms"] = {"median": q(noresid, 50), "p90": q(noresid, 90)}
        e["n"] = len(rs)
        e["per_pass"] = {p: {k: q([f(r[k]) for r in rs if r["pass"] == p], 50) for k in
                             ("llm_ttft_ms", "llm_prompt_eval_tokens", "llm_prompt_cached_tokens", "llm_select_to_launch_ms", "e2e_ms", "stt_ms")}
                         for p in ("1", "2", "3")}
        o["sets"][g] = e
    tc = [len((r.get("reply") or "")) for r in ok]
    for wf in ("wer_summary.json", "wer-unstripped_summary.json"):
        if (d / wf).exists():
            o[wf.replace("_summary.json", "")] = {k.split("|")[1]: v for k, v in json.load(open(d / wf)).items()}
    out[A] = o
# S2 faster than S1 and S3 on every clip (per clip: median STT over the 3 passes)
per = {}
for A in ("S1", "S2", "S3"):
    if A in out:
        rows = list(csv.DictReader(open(R / f"{PFX}{A}" / "per_clip.tsv"), delimiter="\t"))
        by = {}
        for r in rows:
            if f(r["stt_ms"]) is not None: by.setdefault(r["clip_id"], []).append(f(r["stt_ms"]))
        per[A] = {c: statistics.median(v) for c, v in by.items()}
if len(per) == 3:
    clips = sorted(set(per["S1"]) & set(per["S2"]) & set(per["S3"]))
    out["s2_faster_every_clip"] = {"clips": len(clips), "s2_fastest": sum(1 for c in clips if per["S2"][c] < per["S1"][c] and per["S2"][c] < per["S3"][c]),
                                   "exceptions": [c for c in clips if not (per["S2"][c] < per["S1"][c] and per["S2"][c] < per["S3"][c])]}
print(json.dumps(out, indent=1))
