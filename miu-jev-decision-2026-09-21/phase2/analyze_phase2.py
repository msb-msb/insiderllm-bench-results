#!/usr/bin/env python3
import json, statistics, os, glob
HERE = os.path.dirname(os.path.abspath(__file__))
def load(tag): return json.load(open(f"{HERE}/raw/{tag}.json"))
def preds(d): return {r["idx"]: r["pred"] for r in d["records"]}
def stats(xs): xs = sorted(xs); return {"mean_s": round(statistics.mean(xs), 4), "median_s": round(statistics.median(xs), 4), "p95_s": round(xs[int(round(0.95 * (len(xs) - 1)))], 4), "n": len(xs)}
out = {}
ref = load("choose_ref"); TP = [load(f"twopass_rep{k}") for k in range(3)]; TI = load("twopass_instr_rep0")
ref_w = stats([r["wall_s"] for r in ref["records"]])
# ---- A2
tp = TP[0]
out["A2"] = {"pre_registered": {"scope": "recovers to 30/30 (i.e. write's 30)", "overall": "23/47 +/- 1", "latency": "rises by ~one batched decode, under 2x single-pass choose"},
             "choose_ref_this_session": {"exact": ref["summary"]["exact"], "per_field": ref["summary"]["per_field"], "wall": ref_w},
             "twopass": {"exact_reps": [d["summary"]["exact"] for d in TP], "per_field": tp["summary"]["per_field"],
                         "deterministic": all(preds(TP[0]) == preds(d) for d in TP),
                         "wall_total": stats([r["wall_s"] for d in TP for r in d["records"]]),
                         "wall_pass1": stats([r["pass1"]["wall_s"] for d in TP for r in d["records"]]),
                         "wall_pass2": stats([r["pass2"]["wall_s"] for d in TP for r in d["records"]]),
                         "pass2_cached_tokens_mean": round(statistics.mean(r["pass2"]["usage"]["cached_tokens"] for d in TP for r in d["records"]), 1),
                         "pass2_prefill_ms_mean": round(statistics.mean(r["pass2"]["timings"]["prefill_ms"] for d in TP for r in d["records"]), 1),
                         "pass2_scoring_ms_mean": round(statistics.mean(r["pass2"]["timings"]["scoring_ms"] for d in TP for r in d["records"]), 1),
                         "pass1_scoring_ms_mean": round(statistics.mean(r["pass1"]["timings"]["scoring_ms"] for d in TP for r in d["records"]), 1)},
             "twopass_instr": {"exact": TI["summary"]["exact"], "per_field": TI["summary"]["per_field"], "wall_total": stats([r["wall_s"] for r in TI["records"]]),
                               "pass2_cached_tokens_mean": round(statistics.mean(r["pass2"]["usage"]["cached_tokens"] for r in TI["records"]), 1),
                               "pass2_prefill_ms_mean": round(statistics.mean(r["pass2"]["timings"]["prefill_ms"] for r in TI["records"]), 1)}}
out["A2"]["twopass"]["ratio_vs_single_pass"] = round(out["A2"]["twopass"]["wall_total"]["mean_s"] / ref_w["mean_s"], 2)
# scope changes single-pass -> two-pass
rp, tpp = preds(ref), preds(tp); gold = {r["idx"]: r["gold"] for r in ref["records"]}
ch = [i for i in rp if rp[i]["scope"] != tpp[i]["scope"]]
out["A2"]["scope_changed_items"] = [{"idx": i, "gold": gold[i]["scope"], "single": rp[i]["scope"], "two": tpp[i]["scope"], "fixed": tpp[i]["scope"] == gold[i]["scope"], "broken": rp[i]["scope"] == gold[i]["scope"] and tpp[i]["scope"] != gold[i]["scope"], "line": next(r["pass2"]["line"] for r in tp["records"] if r["idx"] == i)} for i in ch]
out["A2"]["tool_mode_changed_vs_single"] = [i for i in rp if (rp[i]["tool"], rp[i]["mode"]) != (tpp[i]["tool"], tpp[i]["mode"])]
SQ = [load(f"twopass_seq_rep{k}") for k in range(3)]
out["A2"]["twopass_seq"] = {"exact_reps": [d["summary"]["exact"] for d in SQ], "per_field": SQ[0]["summary"]["per_field"],
                            "deterministic": all(preds(SQ[0]) == preds(d) for d in SQ),
                            "wall_total": stats([r["wall_s"] for d in SQ for r in d["records"]]),
                            "wall_pass1": stats([r["pass1"]["wall_s"] for d in SQ for r in d["records"]]),
                            "wall_pass2": stats([r["pass2"]["wall_s"] for d in SQ for r in d["records"]]),
                            "pass1_cached_tokens_mean": round(statistics.mean(r["pass1"]["usage"]["cached_tokens"] for d in SQ for r in d["records"]), 1),
                            "pass2_cached_tokens_mean": round(statistics.mean(r["pass2"]["usage"]["cached_tokens"] for d in SQ for r in d["records"]), 1),
                            "pass1_scoring_ms_mean": round(statistics.mean(r["pass1"]["timings"]["scoring_ms"] for d in SQ for r in d["records"]), 1),
                            "pass2_scoring_ms_mean": round(statistics.mean(r["pass2"]["timings"]["scoring_ms"] for d in SQ for r in d["records"]), 1),
                            "pass2_prefill_ms_mean": round(statistics.mean(r["pass2"]["timings"]["prefill_ms"] for d in SQ for r in d["records"]), 1)}
out["A2"]["twopass_seq"]["ratio_vs_single_pass"] = round(out["A2"]["twopass_seq"]["wall_total"]["mean_s"] / ref_w["mean_s"], 2)
sq = preds(SQ[0])
out["A2"]["twopass_seq_scope_changed_vs_single"] = [{"idx": i, "gold": gold[i]["scope"], "single": rp[i]["scope"], "two": sq[i]["scope"], "fixed": sq[i]["scope"] == gold[i]["scope"]} for i in rp if rp[i]["scope"] != sq[i]["scope"]]
out["A2"]["twopass_alt_vs_seq_pass1_differs"] = [i for i in rp if (preds(TP[0])[i]["tool"], preds(TP[0])[i]["mode"]) != (sq[i]["tool"], sq[i]["mode"])]
# ---- B3
out["B3"] = {"pre_registered": "choose-vs-write ratio rises roughly in proportion to tokens generated", "choose_ref_wall_mean_s": ref_w["mean_s"], "formats": {}}
for m in ("write_short", "write_json", "write_pretty", "write_reason"):
    R = [load(f"{m}_rep{k}") for k in range(3)]
    recs = [r for d in R for r in d["records"]]
    w = stats([r["wall_s"] for r in recs])
    out["B3"]["formats"][m] = {"exact_reps": [d["summary"]["exact"] for d in R], "per_field": R[0]["summary"]["per_field"], "raw_valid": R[0]["summary"]["raw_valid"], "unparseable": R[0]["summary"]["unparseable"],
                               "deterministic": all(preds(R[0]) == preds(d) for d in R),
                               "tokens_mean": round(statistics.mean(r["completion_tokens"] for r in recs), 2), "tokens_p95": sorted(r["completion_tokens"] for r in recs)[int(round(0.95 * (len(recs) - 1)))],
                               "wall": w, "ratio_vs_choose": round(w["mean_s"] / ref_w["mean_s"], 2), "ratio_p95": round(w["p95_s"] / ref_w["p95_s"], 2),
                               "server_prompt_ms_mean": round(statistics.mean(r["timings"]["prompt_ms"] for r in recs), 1),
                               "server_predicted_ms_mean": round(statistics.mean(r["timings"]["predicted_ms"] for r in recs), 1),
                               "ms_per_generated_token": round(statistics.mean(r["timings"]["predicted_ms"] / max(1, r["completion_tokens"]) for r in recs), 2),
                               "prompt_n_mean": round(statistics.mean(r["timings"]["prompt_n"] for r in recs), 1), "cache_n_mean": round(statistics.mean(r["timings"]["cache_n"] for r in recs), 1),
                               "client_overhead_ms_mean": round(statistics.mean(1000 * r["wall_s"] - r["timings"]["prompt_ms"] - r["timings"]["predicted_ms"] for r in recs), 1),
                               "sample_raw": R[0]["records"][0]["raw"][:200]}
# proportionality: fit ratio vs tokens through the four formats
xs = [v["tokens_mean"] for v in out["B3"]["formats"].values()]; ys = [v["wall"]["mean_s"] for v in out["B3"]["formats"].values()]
mx, my = statistics.mean(xs), statistics.mean(ys); slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs); icpt = my - slope * mx
out["B3"]["fit"] = {"wall_s = a + b*tokens": {"a_s": round(icpt, 4), "b_s_per_token": round(slope, 5)}, "fixed_cost_share_at_json": round(icpt / out["B3"]["formats"]["write_json"]["wall"]["mean_s"], 3)}
json.dump(out, open(f"{HERE}/analysis_phase2.json", "w"), indent=1)
print(json.dumps(out, indent=1))
