#!/usr/bin/env python3
"""Phase-1 analysis over raw/{write,choose}_rep{0,1,2}.json -> analysis.json + stdout."""
import json, statistics, os
HERE = os.path.dirname(os.path.abspath(__file__))
def load(tag): return json.load(open(f"{HERE}/raw/{tag}.json"))
W = [load(f"write_rep{k}") for k in range(3)]; C = [load(f"choose_rep{k}") for k in range(3)]
def preds(d): return {r["idx"]: r["pred"] for r in d["records"]}
out = {"pre_registered": {"accuracy": "choose within +/-2 items of write", "latency": "choose at least 5x lower"}}
# determinism
out["determinism"] = {"write_reps_identical_preds": all(preds(W[0]) == preds(w) for w in W),
                      "choose_reps_identical_preds": all(preds(C[0]) == preds(c) for c in C),
                      "choose_reps_identical_probs": all(
                          all(abs(a["fields"][f]["probability"] - b["fields"][f]["probability"]) < 1e-9
                              for a, b in zip(C[0]["records"], c["records"]) for f in ("tool", "mode", "scope")) for c in C)}
w, c = W[0], C[0]
out["accuracy"] = {"write_exact": [x["summary"]["exact"] for x in W], "choose_exact": [x["summary"]["exact"] for x in C],
                   "n": 47, "delta_items": c["summary"]["exact"] - w["summary"]["exact"],
                   "write_per_field": w["summary"]["per_field"], "choose_per_field": c["summary"]["per_field"],
                   "write_raw_valid": w["summary"]["raw_valid"], "choose_raw_valid": c["summary"]["raw_valid"]}
out["accuracy"]["within_2"] = abs(out["accuracy"]["delta_items"]) <= 2
# item-level agreement
wp, cp = preds(w), preds(c); gold = {r["idx"]: r["gold"] for r in w["records"]}
both = [i for i in wp if wp[i] == gold[i] and cp[i] == gold[i]]
only_w = [i for i in wp if wp[i] == gold[i] and cp[i] != gold[i]]
only_c = [i for i in wp if wp[i] != gold[i] and cp[i] == gold[i]]
neither = [i for i in wp if wp[i] != gold[i] and cp[i] != gold[i]]
same_pred = sum(1 for i in wp if wp[i] == cp[i])
out["agreement"] = {"both_right": len(both), "write_only_right": only_w, "choose_only_right": only_c,
                    "neither": len(neither), "same_prediction_all_fields": same_pred,
                    "field_disagreements": {f: [i for i in wp if wp[i][f] != cp[i][f]] for f in ("tool", "mode", "scope")}}
# latency: wall (client) and server-reported, all three reps pooled
def pool(runs, key): return sorted(key(r) for d in runs for r in d["records"])
def stats(xs): return {"mean_s": round(statistics.mean(xs), 4), "median_s": round(statistics.median(xs), 4),
                       "p95_s": round(xs[int(round(0.95 * (len(xs) - 1)))], 4), "min_s": round(xs[0], 4), "max_s": round(xs[-1], 4), "n": len(xs)}
ww = pool(W, lambda r: r["wall_s"]); cw = pool(C, lambda r: r["wall_s"])
out["latency"] = {"write_wall": stats(ww), "choose_wall": stats(cw),
                  "ratio_mean": round(statistics.mean(ww) / statistics.mean(cw), 2),
                  "ratio_p95": round(ww[int(round(0.95 * (len(ww) - 1)))] / cw[int(round(0.95 * (len(cw) - 1)))], 2),
                  "write_server_ms": {"prompt_ms_mean": round(statistics.mean(r["timings"]["prompt_ms"] for d in W for r in d["records"]), 1),
                                      "predicted_ms_mean": round(statistics.mean(r["timings"]["predicted_ms"] for d in W for r in d["records"]), 1),
                                      "completion_tokens_mean": round(statistics.mean(r["completion_tokens"] for d in W for r in d["records"]), 2),
                                      "cache_n_mean": round(statistics.mean(r["timings"]["cache_n"] for d in W for r in d["records"]), 1),
                                      "prompt_n_mean": round(statistics.mean(r["timings"]["prompt_n"] for d in W for r in d["records"]), 1)},
                  "choose_server_ms": {"prefill_ms_mean": round(statistics.mean(r["timings"]["prefill_ms"] for d in C for r in d["records"]), 1),
                                       "scoring_ms_mean": round(statistics.mean(r["timings"]["scoring_ms"] for d in C for r in d["records"]), 1),
                                       "total_ms_mean": round(statistics.mean(r["timings"]["total_ms"] for d in C for r in d["records"]), 1),
                                       "rounds_max": max(r["timings"]["rounds"] for d in C for r in d["records"]),
                                       "scored_rows_mean": round(statistics.mean(r["usage"]["scored_rows"] for d in C for r in d["records"]), 1),
                                       "cached_tokens_mean": round(statistics.mean(r["usage"]["cached_tokens"] for d in C for r in d["records"]), 1),
                                       "context_tokens_mean": round(statistics.mean(r["usage"]["context_tokens"] for d in C for r in d["records"]), 1)}}
out["latency"]["at_least_5x"] = out["latency"]["ratio_mean"] >= 5
# confidence on right vs wrong (choose rep0; probabilities identical across reps)
right = [r for r in c["records"] if r["exact"]]; wrong = [r for r in c["records"] if not r["exact"]]
def conf(rs, key): xs = [r[key] for r in rs]; return {"mean": round(statistics.mean(xs), 3), "median": round(statistics.median(xs), 3), "min": round(min(xs), 3), "max": round(max(xs), 3)}
out["confidence"] = {"right_n": len(right), "wrong_n": len(wrong),
                     "min_field_prob": {"right": conf(right, "min_prob"), "wrong": conf(wrong, "min_prob")},
                     "product_prob": {"right": conf(right, "prod_prob"), "wrong": conf(wrong, "prod_prob")}}
# per-field: probability of the chosen value when that field is right vs wrong
pf = {}
for f in ("tool", "mode", "scope"):
    r_ = [r["fields"][f]["probability"] for r in c["records"] if r["pred"][f] == r["gold"][f]]
    w_ = [r["fields"][f]["probability"] for r in c["records"] if r["pred"][f] != r["gold"][f]]
    pf[f] = {"right_n": len(r_), "right_mean_prob": round(statistics.mean(r_), 3), "wrong_n": len(w_), "wrong_mean_prob": round(statistics.mean(w_), 3) if w_ else None}
out["confidence"]["per_field"] = pf
# threshold sweep: if you refused below min_prob t, how many wrong would you catch and how many right would you lose
sweep = []
for t in (0.5, 0.6, 0.7, 0.8, 0.9, 0.95):
    sweep.append({"t": t, "wrong_below": sum(1 for r in wrong if r["min_prob"] < t), "right_below": sum(1 for r in right if r["min_prob"] < t)})
out["confidence"]["min_prob_threshold_sweep"] = sweep
# ranked wrong items
out["confidence"]["wrong_items"] = sorted([{"idx": r["idx"], "min_prob": round(r["min_prob"], 3), "gold": r["gold"], "pred": r["pred"],
                                            "probs": {f: round(r["fields"][f]["probability"], 3) for f in ("tool", "mode", "scope")},
                                            "write_pred": wp[r["idx"]], "write_right": wp[r["idx"]] == r["gold"]} for r in wrong], key=lambda x: x["min_prob"])
out["confidence"]["right_items_lowest_conf"] = sorted([{"idx": r["idx"], "min_prob": round(r["min_prob"], 3)} for r in right], key=lambda x: x["min_prob"])[:5]
json.dump(out, open(f"{HERE}/analysis.json", "w"), indent=1)
print(json.dumps({k: out[k] for k in ("determinism", "accuracy", "agreement", "latency")}, indent=1))
print("confidence:", json.dumps({k: out["confidence"][k] for k in ("right_n", "wrong_n", "min_field_prob", "product_prob", "per_field", "min_prob_threshold_sweep", "right_items_lowest_conf")}, indent=1))
print("wrong items:"); [print(" ", x) for x in out["confidence"]["wrong_items"]]
