#!/usr/bin/env python3
"""power-01 scoring, exactly as PREREG.md (locked 2026-10-14, sha256 b75eb427…) specifies.

  esp32-ai/.venv/bin/python evals/power-01/score.py   -> writes score_output.md and scores.json

Inputs: runs.jsonl (generate and idle records) and each scored run's logs/<tag>.power/
(raw.bin + summary.json) for the operating points (mean current and VBUS).

Locked rules applied here:
- Scored generate reps: the first three passing reps per board in run order (rerun rule);
  passing = the PREREG's per-rep acceptance checks. Every attempt is listed.
- Idle power per board: the mean of its three fresh-reset idle reps (<build>_idle_{1,2,3}r).
- Total J/token = logger energy over the generate window / tokens.
  Marginal J/token = (window energy - idle power x window duration) / tokens.
  Window (gross) J/token = energy inside the sync windows / tokens (headline; scores nothing).
- Reference-instrument term (Aneng SZ20 spec at the operating point):
  eps_I = 0.5% + 0.03 mA / I, eps_V = 0.2% + 10 mV / V, eps_E = eps_I + eps_V.
  Generate operating point = each board's own scored generate reps (mean I, mean VBUS);
  idle operating point = its idle reps.
- Idle term: +-3.7% of the board's idle power, for the subtracted idle in marginal J/token only.
- Error bars: per board, lowest to highest over its 3 reps, each rep computed at both ends
  of every term that applies; all terms worst case (linear). Comparisons: worst case over
  the two boards' intervals. No credit for the common calibration term.
- Verdict: HELD if the whole interval satisfies the prediction, FAILED if the whole
  interval violates it, UNRESOLVED if it straddles the threshold.
"""
import itertools, json, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "tools", "power-logger", "host"))
from powerlog import protocol as P  # noqa: E402

APPS = {"B": "06abb9ada33896db6f2f07adcbeed03ff45e50473009aab470f35f2af581f8f8",
        "D": "cf2ff730cd0392b673fc2d25fa357092586f95e02df9269be24566cfafbf1a9d",
        "P4": "38299f178b6e3ff02806a5ba6793fcb02ef4c25ea6074a0d1cb34d25c3bf2b7a"}
NAME = {"B": "S3-B", "D": "S3-D", "P4": "P4"}
IDLE_TERM = 0.037
NEED, MAXATT = 3, 6


def gen_checks(rec):
    """The PREREG's per-rep acceptance checks for a generate rep."""
    L = rec.get("logger", {})
    return {
        "app": rec.get("app_sha256") == APPS[rec["build"]],
        "fresh_reset": rec.get("reset", {}).get("boot_seen") is True,
        "status_ok": not rec.get("status", "").startswith("FAILED"),
        "gate_3pct": rec.get("gate_3pct") == "PASS",
        "host_vs_fw<=0.5%": abs(L.get("host_vs_firmware_pct", 99)) <= 0.5,
        "drops==0": L.get("dropped_frames") == 0,
        "late==0": L.get("late_conversions") == 0,
        "bus_errors==0": L.get("bus_errors") == 0,
        "gaps==0": L.get("gaps") == 0,
        "all_generations_identical": rec.get("all_generations_identical") is True,
        "sync_windows==generations": L.get("sync_windows") == rec.get("generations") and "j_per_token" in L,
    }


def operating_point(run_dir):
    """Mean calibrated current (A) and VBUS (V) over the run (reset SNAP to final SNAP)."""
    d = os.path.join(HERE, run_dir)
    s = json.load(open(os.path.join(d, "summary.json")))
    cal = s["calibration"]
    frames = P.decode_all(open(os.path.join(d, "raw.bin"), "rb").read())[0]
    S = [f for f in frames if isinstance(f, P.Sample) and s["seq_from"] <= f.seq <= s["seq_to"]]
    lsb = s["lsb"]
    i = statistics.mean(x.cur for x in S) * lsb["current_a"] * cal["gi"] + cal["oi"]
    v = statistics.mean(x.vbus for x in S) * lsb["vbus_v"] * cal["gv"] + cal["ov"]
    return i, v, len(S)


def eps_ref(i, v):
    ei = 0.005 + 0.03e-3 / i
    ev = 0.002 + 0.010 / v
    return ei, ev, ei + ev


def verdict(lo, hi, holds, fails):
    if holds(lo) and holds(hi):
        return "HELD"
    if fails(lo) and fails(hi):
        return "FAILED"
    return "UNRESOLVED"


def main():
    recs = [json.loads(l) for l in open(os.path.join(HERE, "runs.jsonl"))]
    out, md = {}, []
    w = md.append

    # ---- idle per board ----
    idle = {}
    for b in ("B", "D", "P4"):
        reps = [r for r in recs if r["tag"] in (f"{b}_idle_1r", f"{b}_idle_2r", f"{b}_idle_3r")]
        assert len(reps) == 3, (b, [r["tag"] for r in reps])
        ops = [operating_point(r["logger"]["run_dir"]) for r in reps]
        i = statistics.mean(o[0] for o in ops); v = statistics.mean(o[1] for o in ops)
        ei, ev, ee = eps_ref(i, v)
        p = [r["logger"]["mean_power_W"] for r in reps]
        idle[b] = {"tags": [r["tag"] for r in reps], "power_W": p, "mean_W": statistics.mean(p),
                   "I_mA": i * 1e3, "V": v, "eps_I": ei, "eps_V": ev, "eps_E": ee,
                   "rep_ends_W": [(x * (1 - ee), x * (1 + ee)) for x in p]}
        idle[b]["interval_W"] = (min(a for a, _ in idle[b]["rep_ends_W"]), max(c for _, c in idle[b]["rep_ends_W"]))
    out["idle"] = idle

    # ---- generate attempts and scored reps ----
    gen = {}
    for b in ("P4", "D", "B"):
        attempts = [r for r in recs if r.get("mode") == "gen" and r.get("build") == b]
        rows, scored = [], []
        for n, r in enumerate(attempts, 1):
            c = gen_checks(r)
            ok = all(c.values())
            rows.append({"attempt": n, "tag": r["tag"], "pass": ok, "failed_checks": [k for k, v in c.items() if not v],
                         "status": r.get("status"), "meter": r.get("meter_inline")})
            if ok and len(scored) < NEED:
                scored.append(r)
        assert len(attempts) <= MAXATT
        g = {"attempts": rows, "scored": [r["tag"] for r in scored], "resolved": len(scored) == NEED}
        if len(scored) == NEED:
            ops = [operating_point(r["logger"]["run_dir"]) for r in scored]
            i = statistics.mean(o[0] for o in ops); v = statistics.mean(o[1] for o in ops)
            ei, ev, ee = eps_ref(i, v)
            g.update(I_mA=i * 1e3, V=v, eps_I=ei, eps_V=ev, eps_E=ee)
            pidle = idle[b]["mean_W"]; eidle = idle[b]["eps_E"]
            reps = []
            for r in scored:
                L = r["logger"]; E = L["energy_J_firmware"]; T = L["duration_s"]; N = r["tokens"]
                Ew = L["j_per_token"]["J_per_token_sync"] * N
                total = E / N
                marg = (E - pidle * T) / N
                window = Ew / N
                tot_ends = (E * (1 - ee) / N, E * (1 + ee) / N)
                # marginal: E at both ends of eps_E(gen); subtracted idle at both ends of the idle term
                # and of the reference-instrument idle term (worst case = all combinations)
                combos = [((E * (1 + se * ee)) - pidle * (1 + si * IDLE_TERM) * (1 + sr * eidle) * T) / N
                          for se, si, sr in itertools.product((-1, 1), repeat=3)]
                reps.append({"tag": r["tag"], "tokens": N, "energy_J": E, "duration_s": T, "window_energy_J": Ew,
                             "generations": r["generations"], "median_ms": r["median_ms_per_tok"], "mean_W": L["mean_power_W"],
                             "total": total, "total_ends": tot_ends,
                             "marginal": marg, "marginal_ends": (min(combos), max(combos)),
                             "window": window, "window_ends": (window * (1 - ee), window * (1 + ee)),
                             "tok_per_J_total": 1 / total, "tok_per_J_marginal": 1 / marg, "tok_per_J_window": 1 / window,
                             "post_idle_W": r.get("post_idle", {}).get("mean_power_W")})
            g["reps"] = reps
            for m in ("total", "marginal", "window"):
                g[m + "_mean"] = statistics.mean(x[m] for x in reps)
                g[m + "_interval"] = (min(x[m + "_ends"][0] for x in reps), max(x[m + "_ends"][1] for x in reps))
        gen[b] = g
    out["gen"] = gen

    # ---- predictions ----
    def ok(b):
        return gen[b]["resolved"]

    pred = {}
    # P1: S3-B total within 10-25 mJ
    if ok("B"):
        lo, hi = gen["B"]["total_interval"]
        pred["P1"] = {"interval_mJ": (lo * 1e3, hi * 1e3), "threshold": "10 <= x <= 25 mJ",
                      "verdict": verdict(lo, hi, lambda x: 0.010 <= x <= 0.025, lambda x: x < 0.010 or x > 0.025)}
    else:
        pred["P1"] = {"verdict": "UNRESOLVED", "why": "S3-B lacks three passing reps"}
    # P2: P4 total < S3-B total ; P4 (prediction): S3-D total < S3-B total
    for key, a in (("P2", "P4"), ("P4", "D")):
        if ok(a) and ok("B"):
            alo, ahi = gen[a]["total_interval"]; blo, bhi = gen["B"]["total_interval"]
            lo, hi = alo - bhi, ahi - blo
            pred[key] = {"diff_interval_mJ": (lo * 1e3, hi * 1e3), "arith": f"[{NAME[a]} low - S3-B high, {NAME[a]} high - S3-B low]",
                         "threshold": "difference < 0", "verdict": verdict(lo, hi, lambda x: x < 0, lambda x: x >= 0)}
        else:
            pred[key] = {"verdict": "UNRESOLVED", "why": "a board lacks three passing reps"}
    # P3: P4 marginal <= 0.6 x S3-B marginal
    if ok("P4") and ok("B"):
        alo, ahi = gen["P4"]["marginal_interval"]; blo, bhi = gen["B"]["marginal_interval"]
        lo, hi = alo / bhi, ahi / blo
        pred["P3"] = {"ratio_interval": (lo, hi), "arith": "[P4 low / S3-B high, P4 high / S3-B low]",
                      "threshold": "ratio <= 0.6", "verdict": verdict(lo, hi, lambda x: x <= 0.6, lambda x: x > 0.6)}
    else:
        pred["P3"] = {"verdict": "UNRESOLVED", "why": "a board lacks three passing reps"}
    # P5: P4 idle - S3 idle >= 0.2 W, against S3-B and S3-D separately
    p5 = {}
    for s3 in ("B", "D"):
        alo, ahi = idle["P4"]["interval_W"]; blo, bhi = idle[s3]["interval_W"]
        lo, hi = alo - bhi, ahi - blo
        p5[NAME[s3]] = {"diff_interval_W": (lo, hi), "arith": f"[P4 low - {NAME[s3]} high, P4 high - {NAME[s3]} low]",
                        "threshold": "difference >= 0.2 W", "verdict": verdict(lo, hi, lambda x: x >= 0.2, lambda x: x < 0.2)}
    pred["P5"] = {"against": p5, "note": "outcome observed before lock"}
    out["predictions"] = pred
    json.dump(out, open(os.path.join(HERE, "scores.json"), "w"), indent=1)

    # ---- markdown of every intermediate number ----
    f = lambda x, n=4: f"{x:.{n}f}"
    w("## Idle power (fresh reset, 300 s; scores P5, subtracted in marginal J/token)\n")
    w("| Board | Reps | Power per rep (W) | Mean (W) | Operating point | ε_I | ε_V | ε_E (instrument, idle) | Rep ends at ±ε_E (W) | Interval (W) |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for b in ("B", "D", "P4"):
        d = idle[b]
        ends = "; ".join(f"{f(a,5)}–{f(c,5)}" for a, c in d["rep_ends_W"])
        w(f"| {NAME[b]} | {', '.join(d['tags'])} | {', '.join(f(x,5) for x in d['power_W'])} | {f(d['mean_W'],5)} | "
          f"{d['I_mA']:.2f} mA, {d['V']:.4f} V | ±{d['eps_I']*100:.3f}% | ±{d['eps_V']*100:.3f}% | ±{d['eps_E']*100:.3f}% | {ends} | "
          f"{f(d['interval_W'][0],5)}–{f(d['interval_W'][1],5)} |")
    w("")
    w("## Generate attempts (all, in run order) and scored reps\n")
    w("| Board | Attempt | Tag | Pass | Failed checks | Status | Meter rep |")
    w("|---|---|---|---|---|---|---|")
    for b in ("P4", "D", "B"):
        for a in gen[b]["attempts"]:
            w(f"| {NAME[b]} | {a['attempt']} | {a['tag']} | {'yes' if a['pass'] else 'NO'} | {', '.join(a['failed_checks']) or '–'} | "
              f"{a['status'] or '–'} | {'yes' if a['meter'] else ''} |")
    w("")
    for b in ("P4", "D", "B"):
        w(f"- **{NAME[b]} scored reps:** {', '.join(gen[b]['scored'])} (first three passing, in run order).")
    w("")
    w("## Reference-instrument term at the generate operating points\n")
    w("| Board | Mean current (scored reps) | Mean VBUS | ε_I = 0.5% + 0.03 mA / I | ε_V = 0.2% + 10 mV / V | **ε_E** |")
    w("|---|---|---|---|---|---|")
    for b in ("P4", "D", "B"):
        g = gen[b]
        w(f"| {NAME[b]} | {g['I_mA']:.2f} mA | {g['V']:.4f} V | ±{g['eps_I']*100:.3f}% | ±{g['eps_V']*100:.3f}% | **±{g['eps_E']*100:.3f}%** |")
    w("")
    w("## Per-rep figures and their ends\n")
    w("All J/token in mJ. Total ends: energy at ±ε_E(generate). Marginal ends: the min and max over energy at ±ε_E(generate) × subtracted idle at ±3.7% × subtracted idle at ±ε_E(idle) (8 combinations). Window ends: ±ε_E(generate).\n")
    w("| Board | Rep | Gens | Tokens | Energy (J) | Duration (s) | Mean W | ms/token | Total | Total ends | Marginal | Marginal ends | Window | Window ends | Post-run idle W (exploratory) |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for b in ("P4", "D", "B"):
        for r in gen[b]["reps"]:
            m = lambda x: f"{x*1e3:.4f}"
            w(f"| {NAME[b]} | {r['tag']} | {r['generations']} | {r['tokens']} | {r['energy_J']:.4f} | {r['duration_s']:.3f} | {r['mean_W']:.4f} | "
              f"{r['median_ms']:.3f} | {m(r['total'])} | {m(r['total_ends'][0])}–{m(r['total_ends'][1])} | {m(r['marginal'])} | "
              f"{m(r['marginal_ends'][0])}–{m(r['marginal_ends'][1])} | {m(r['window'])} | {m(r['window_ends'][0])}–{m(r['window_ends'][1])} | "
              f"{r['post_idle_W']:.4f} |")
    w("")
    w("## Board intervals (lowest to highest end over the three scored reps)\n")
    w("| Board | Total mean | Total interval | Marginal mean | Marginal interval | Window mean | Window interval | Idle subtracted (W) |")
    w("|---|---|---|---|---|---|---|---|")
    for b in ("P4", "D", "B"):
        g = gen[b]; m = lambda x: f"{x*1e3:.4f}"
        w(f"| {NAME[b]} | {m(g['total_mean'])} | {m(g['total_interval'][0])}–{m(g['total_interval'][1])} | {m(g['marginal_mean'])} | "
          f"{m(g['marginal_interval'][0])}–{m(g['marginal_interval'][1])} | {m(g['window_mean'])} | {m(g['window_interval'][0])}–{m(g['window_interval'][1])} | "
          f"{idle[b]['mean_W']:.5f} ± 3.7% ± {idle[b]['eps_E']*100:.3f}% |")
    w("")
    w("## Tokens per joule (means of the scored reps)\n")
    w("| Board | Total | Marginal | Window |")
    w("|---|---|---|---|")
    for b in ("P4", "D", "B"):
        R = gen[b]["reps"]
        w(f"| {NAME[b]} | {statistics.mean(x['tok_per_J_total'] for x in R):.2f} | {statistics.mean(x['tok_per_J_marginal'] for x in R):.2f} | "
          f"{statistics.mean(x['tok_per_J_window'] for x in R):.2f} |")
    w("")
    w("## Predictions: comparisons and verdicts\n")
    p = pred
    lo, hi = p["P1"]["interval_mJ"]
    w(f"- **P1** (S3-B total J/token in 10–25 mJ): interval {lo:.4f} to {hi:.4f} mJ. "
      f"Threshold: 10 ≤ x ≤ 25 mJ at both ends. → **{p['P1']['verdict']}**.")
    for key, a in (("P2", "P4"), ("P4", "S3-D")):
        q = p[key]; lo, hi = q["diff_interval_mJ"]
        w(f"- **{key}** ({a} total < S3-B total): difference interval {q['arith']} = {lo:.4f} to {hi:.4f} mJ. "
          f"Threshold: difference < 0. → **{q['verdict']}**.")
    q = p["P3"]; lo, hi = q["ratio_interval"]
    w(f"- **P3** (P4 marginal ≤ 0.6 × S3-B marginal): ratio interval {q['arith']} = {lo:.4f} to {hi:.4f}. "
      f"Threshold: ratio ≤ 0.6. → **{q['verdict']}**.")
    for s3, q in p["P5"]["against"].items():
        lo, hi = q["diff_interval_W"]
        w(f"- **P5 against {s3}** (P4 idle − S3 idle ≥ 0.2 W): difference interval {q['arith']} = {lo:.5f} to {hi:.5f} W. "
          f"Threshold: ≥ 0.2 W. → **{q['verdict']}** (outcome observed before lock).")
    w("")
    open(os.path.join(HERE, "score_output.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
