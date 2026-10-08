#!/usr/bin/env python3
"""Per-item tables and agreement counts for the primary (thinking off, pass 1) and the thinking-on pass. Writes quality/per-item.md and quality/agreement.json."""
import json, os
H = os.path.dirname(os.path.abspath(__file__)); Q = os.path.join(H, "quality")
B, D = "qwen3.6-35b-a3b-q4km", "qwen3.8-distill-q4km"
F = ("tool", "mode", "scope")
def fmt(p, g): return "/".join(f"**{p[f]}**" if p[f] != g[f] else p[f] for f in F)
def table(b, d, title, extra=None):
    bi, di = {r["idx"]: r for r in b}, {r["idx"]: r for r in d}
    cnt = {"both": 0, "base_only": 0, "distill_only": 0, "neither": 0}; rows = []
    for i in sorted(bi):
        x, y = bi[i], di[i]; g = x["gold"]
        k = "both" if x["exact"] and y["exact"] else "base_only" if x["exact"] else "distill_only" if y["exact"] else "neither"
        cnt[k] += 1
        diff = ", ".join(f for f in F if x["pred"][f] != y["pred"][f]) or "—"
        note = []
        if x["via"] == "unparseable": note.append("base unparseable")
        if y["via"] == "unparseable": note.append("distill unparseable")
        if extra: note += extra(x, y)
        rows.append(f"| {i} | {'/'.join(g[f] for f in F)} | {fmt(x['pred'], g)} | {fmt(y['pred'], g)} | {k.replace('_', ' ')} | {diff} | {'; '.join(note)} |")
    head = [f"### {title}", "", "| item | gold tool/mode/scope | Qwen3.6-35B-A3B Q4_K_M | Distill Q4_K_M | correct | fields that differ | note |", "|---:|---|---|---|---|---|---|"]
    return "\n".join(head + rows), cnt
p1 = lambda t: json.load(open(os.path.join(Q, f"raw-{t}.json")))["passes"][0]["records"]
th = lambda t: json.load(open(os.path.join(Q, f"thinking-{t}.json")))["records"]
t1, c1 = table(p1(B), p1(D), "Primary: thinking off, max_tokens 100 (pass 1 of 2; pass 2 identical for both models)")
t2, c2 = table(th(B), th(D), "Secondary: thinking on, max_tokens 8,192 (one pass)",
               extra=lambda x, y: [f"reasoning tokens {x['reasoning_tokens']} vs {y['reasoning_tokens']}"] + (["base hit cap"] if x["finish_reason"] == "length" else []) + (["distill hit cap"] if y["finish_reason"] == "length" else []))
open(os.path.join(Q, "per-item.md"), "w").write("# Per-item results\n\nWrong field values in **bold**.\n\n" + t1 + "\n\n" + t2 + "\n")
json.dump({"primary_pass1": c1, "thinking_on": c2}, open(os.path.join(Q, "agreement.json"), "w"), indent=1)
print("primary", c1); print("thinking", c2)
