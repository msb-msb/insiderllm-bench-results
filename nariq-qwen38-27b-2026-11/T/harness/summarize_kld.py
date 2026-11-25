#!/usr/bin/env python3
"""Section T quality summary (A1, T4/T6/T7) from log-Q-*.txt (llama-perplexity KL mode) and bpb.json.
  summarize_kld.py RUNDIR BPB.json [REFLABEL]     REFLABEL = "BF16" or "Q8_0 reference (not BF16)"
Scoring (T7): A "lower" than B on mean KLD when the mean ± 2 SE intervals don't overlap, else "no difference shown".
Per-half values come from the tool's running per-chunk means (chunks 1-16 = code, 17-32 = prose; equal counts),
reported, scored only where T6 says so (on means)."""
import json, math, os, re, sys
D, BPB = sys.argv[1], json.load(open(sys.argv[2])); REF = sys.argv[3] if len(sys.argv) > 3 else "BF16"
ARMS = ["Q-M-IQ3", "Q-F-IQ3", "Q-F-N3", "Q-F-N25", "Q-R-Q4"]
num = r"([-0-9.]+)"


def parse(p):
    t = open(p, errors="replace").read(); r = {}
    for key, pat in (("ppl", rf"Mean PPL\(Q\)\s*:\s*{num} ± {num}"), ("ppl_base", rf"Mean PPL\(base\)\s*:\s*{num} ± {num}"),
                     ("ln_ratio", rf"Mean ln\(PPL\(Q\)/PPL\(base\)\)\s*:\s*{num} ± {num}"), ("kld", rf"Mean    KLD:\s*{num} ± {num}"),
                     ("same_top_p", rf"Same top p:\s*{num} ± {num}")):
        m = re.search(pat, t)
        r[key] = (float(m.group(1)), float(m.group(2))) if m else None
    for key, pat in (("kld_max", rf"Maximum KLD:\s*{num}"), ("kld_999", rf"99\.9%   KLD:\s*{num}"),
                     ("kld_99", rf"99\.0%   KLD:\s*{num}"), ("kld_median", rf"Median  KLD:\s*{num}")):
        m = re.search(pat, t); r[key] = float(m.group(1)) if m else None
    rows = {}
    for l in t.splitlines():
        m = re.match(r"^\s*(\d+)\s+" + r"\s+".join([rf"{num} ± {num}"] * 5), l)
        if m:
            v = [float(x) for x in m.groups()[1:]]
            rows[int(m.group(1))] = {"ppl": v[0], "ln_ratio": v[2], "kld": v[4]}
    r["override_logged"] = "Using metadata override" in t and "add_bos_token" in t
    if 16 in rows and 32 in rows:
        c, a = rows[16], rows[32]
        r["code"] = {"kld": c["kld"], "nll": math.log(c["ppl"])}
        r["prose"] = {"kld": 2 * a["kld"] - c["kld"], "nll": 2 * math.log(a["ppl"]) - math.log(c["ppl"])}
    return r


R = {a: parse(os.path.join(D, f"log-{a}.txt")) for a in ARMS if os.path.exists(os.path.join(D, f"log-{a}.txt"))}
S = {"reference": REF, "bpb_denominator": BPB, "arms": R, "scores": {}, "predictions": {}}
N, B = BPB["scored_tokens"], BPB["scored_bytes"]
bpb = lambda nll, n, b: nll * n / (math.log(2) * b)
print(f"Reference: {REF}. Scored tokens {N}, bytes {B}.")
print("| arm | mean KLD ± SE | median | 99% | 99.9% | same top p % | PPL(Q) | ln(PPL(Q)/PPL(base)) | bpb | code KLD | prose KLD |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for a, r in R.items():
    if not r.get("kld"):
        print(f"| {a} | (no result) |"); continue
    r["bpb"] = bpb(math.log(r["ppl"][0]), N, B)
    print(f"| {a} | {r['kld'][0]:.5f} ± {r['kld'][1]:.5f} | {r['kld_median']} | {r['kld_99']} | {r['kld_999']} | "
          f"{r['same_top_p'][0]:.3f} ± {r['same_top_p'][1]:.3f} | {r['ppl'][0]:.4f} | {r['ln_ratio'][0]:.5f} ± {r['ln_ratio'][1]:.5f} | "
          f"{r['bpb']:.4f} | {r.get('code', {}).get('kld', float('nan')):.5f} | {r.get('prose', {}).get('kld', float('nan')):.5f} |")
any_r = next((r for r in R.values() if r.get("ppl_base")), None)
if any_r:
    S["ref_bpb"] = bpb(math.log(any_r["ppl_base"][0]), N, B)
    print(f"reference PPL {any_r['ppl_base'][0]:.4f}, bpb {S['ref_bpb']:.4f}")
for a, r in R.items():
    if not r.get("override_logged"):
        print(f"VOID {a}: BOS override line not in its log")


def k(a):
    r = R.get(a); return r["kld"] if r and r.get("kld") and r.get("override_logged") else None


def cmp(a, b):
    x, y = k(a), k(b)
    if not x or not y:
        return None
    apart = x[0] + 2 * x[1] < y[0] - 2 * y[1] or y[0] + 2 * y[1] < x[0] - 2 * x[1]
    v = "no difference shown" if not apart else ("lower" if x[0] < y[0] else "higher")
    return {"ratio": round(x[0] / y[0], 3), "verdict": v}


print()
for a, b in (("Q-F-N3", "Q-M-IQ3"), ("Q-F-N3", "Q-R-Q4"), ("Q-F-N25", "Q-F-N3"), ("Q-F-N25", "Q-M-IQ3"),
             ("Q-F-IQ3", "Q-M-IQ3"), ("Q-F-N3", "Q-F-IQ3"), ("Q-R-Q4", "Q-M-IQ3")):
    c = cmp(a, b)
    if c:
        S["scores"][f"{a} vs {b}"] = c; print(f"KLD {a} vs {b}: {c['ratio']}x, {c['verdict']}")


def pred(name, hit):
    S["predictions"][name] = hit; print(f"{name} -> {'HIT' if hit else 'MISS'}")


print()
if k("Q-R-Q4"): pred("R-Q4 mean KLD 0.010-0.040", 0.010 <= k("Q-R-Q4")[0] <= 0.040)
if k("Q-M-IQ3"): pred("M-IQ3 mean KLD 0.060-0.150", 0.060 <= k("Q-M-IQ3")[0] <= 0.150)
c = cmp("Q-F-N3", "Q-M-IQ3")
if c: pred("F-N3 lower than M-IQ3, at 0.35-0.80x", c["verdict"] == "lower" and 0.35 <= c["ratio"] <= 0.80)
c = cmp("Q-F-N3", "Q-R-Q4")
if c: pred("F-N3 higher than R-Q4", c["verdict"] == "higher")
c1, c2 = cmp("Q-F-N25", "Q-F-N3"), cmp("Q-F-N25", "Q-M-IQ3")
if c1 and c2: pred("F-N25 higher than F-N3 and no worse than M-IQ3", c1["verdict"] == "higher" and c2["verdict"] != "higher")
order = ["Q-R-Q4", "Q-F-N3", "Q-F-N25", "Q-M-IQ3"]
if all(k(a) for a in order):
    stp = [R[a]["same_top_p"][0] for a in order]
    pred("same top p: R-Q4 > F-N3 > F-N25 >= M-IQ3", stp[0] > stp[1] > stp[2] >= stp[3])
    kl = sorted(R[a]["kld"][0] for a in order + ["Q-F-IQ3"])
    five = order + ["Q-F-IQ3"]
    by_kld = sorted(five, key=lambda a: R[a]["kld"][0]); by_ln = sorted(five, key=lambda a: R[a]["ln_ratio"][0])
    pred("ln(PPL ratio) ordering matches mean KLD ordering (5 arms)", by_kld == by_ln)
if k("Q-F-IQ3") and k("Q-M-IQ3"):
    pred("F-IQ3 vs M-IQ3: |dKLD| <= 0.002 and same top p within 0.2 pp",
         abs(k("Q-F-IQ3")[0] - k("Q-M-IQ3")[0]) <= 0.002 and abs(R["Q-F-IQ3"]["same_top_p"][0] - R["Q-M-IQ3"]["same_top_p"][0]) <= 0.2)
if all(R.get(a, {}).get("code") for a in ARMS):
    pred("code half lower mean KLD than prose half, every arm", all(R[a]["code"]["kld"] < R[a]["prose"]["kld"] for a in ARMS))
json.dump(S, open(os.path.join(D, "summary.json"), "w"), indent=1)
