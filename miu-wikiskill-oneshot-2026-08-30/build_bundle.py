#!/usr/bin/env python3
"""Assemble the compilation bundle sent to claude-opus-5.

Order is fixed: task definition + label schema, the deployed prompt verbatim,
the compile traces, then the instruction. Everything up to and including the
traces is the cached prefix; the instruction is the only thing after the
cache_control breakpoint, mirroring a real loop where the wiki+traces are the
stable bulk and the proposer's instruction is what varies.

Traces are stratified failure-first. The compile split's natural split under the
baseline is 15 fail / 9 pass = exactly the paper's 5:3 ratio, so the 16- and
8-trace variants subsample to 10/6 and 5/3 and preserve it.
"""
import json, os, sys, hashlib, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from deployed import INTENT_SYSTEM_PROMPT, SOLO_SHA256

SEED = 20260830

def triple(g): return f'{g["tool"]}/{g["mode"]}/{g["scope"]}'

def load():
    man = json.load(open(f"{HERE}/splits/manifest.json"))
    comp = json.load(open(f"{HERE}/splits/compile.json"))
    base = json.load(open(f"{HERE}/baseline/baseline_nothink.json"))
    # pass/fail from the baseline arm; assert compile-split preds are rep-stable
    per = {}
    for run in base["runs"]:
        for r in run["records"]:
            per.setdefault(r["idx"], []).append((triple(r["pred"]), r["exact"]))
    ci = {x["idx"] for x in comp}
    unstable = [i for i in ci if len({p for p, _ in per[i]}) > 1]
    assert not unstable, f"compile-split predictions not rep-stable: {unstable}"
    pred = {i: per[i][0] for i in ci}
    return man, comp, pred

TASK = """\
# Task

You are improving a production intent classifier that runs on a local 27B model
(Qwen3.6-27B, greedy decoding, 100-token output cap). It reads one user message
and must emit exactly one JSON object with three enum fields.

## Label schema

tool  ∈ {answer, web_search, rag, web_and_rag}
mode  ∈ {recall, explore, execute, chat}
scope ∈ {session, docs, facts, all}

Any value outside these sets is rewritten to the field default
(answer / chat / all) by a sanitiser before the result is used, so an invalid
enum silently becomes the majority answer rather than an error.

Two deterministic overrides are applied after the model, and you cannot change
them: a regex that detects references to past conversation forces scope=session,
and scope=docs with tool=web_and_rag is rewritten to tool=rag.

Scoring is exact match on all three fields.

## The prompt currently in production, verbatim

<<<DEPLOYED_PROMPT
@@PROMPT@@
DEPLOYED_PROMPT

## Execution traces from production logs

@@N@@ real messages, drawn from the classifier's own logs, with the hand-corrected
gold label and what the deployed 27B actually predicted. FAIL means the
prediction did not exactly match gold. Failures are listed first.

@@TRACES@@"""

INSTRUCTION = """\
Write a skill: a block of procedural instructions that will be appended verbatim
to the deployed prompt above, for the same 27B model, to make it classify more
accurately.

Constraints:
- Output ONLY the skill text. No preamble, no explanation, no code fences.
- It is appended after the deployed prompt, so it can add rules, sharpen
  existing ones, or correct them — but do not restate rules that are already
  there and already working.
- Target 120 lines or fewer.
- It must be procedural and decidable: rules the model can apply to a message it
  has not seen. Do not encode answers to these specific messages.
- The three enum vocabularies above are fixed. Never instruct the model to emit
  a value outside them."""

def build(n_traces, comp, pred):
    fails = sorted([x for x in comp if not pred[x["idx"]][1]], key=lambda x: x["idx"])
    passes = sorted([x for x in comp if pred[x["idx"]][1]], key=lambda x: x["idx"])
    assert len(fails) == 15 and len(passes) == 9, (len(fails), len(passes))
    nf = round(n_traces * 5 / 8); np_ = n_traces - nf
    rng = random.Random(SEED + n_traces)
    f = sorted(rng.sample(fails, nf), key=lambda x: x["idx"])
    p = sorted(rng.sample(passes, np_), key=lambda x: x["idx"])
    lines = []
    for x in f + p:
        pt, ok = pred[x["idx"]]
        lines.append(
            f"--- trace {x['idx']:02d} [{'PASS' if ok else 'FAIL'}] ---\n"
            f"message: {x['msg']}\n"
            f"gold:    {triple(x['gold'])}\n"
            f"model:   {pt}")
    prefix = (TASK.replace("@@PROMPT@@", INTENT_SYSTEM_PROMPT)
                  .replace("@@N@@", str(n_traces))
                  .replace("@@TRACES@@", "\n\n".join(lines)))
    return prefix, [x["idx"] for x in f + p], nf, np_

if __name__ == "__main__":
    man, comp, pred = load()
    test_idx = set(man["splits"]["test"]); val_idx = set(man["splits"]["val"])
    excluded = set(man["excluded_idx"])
    out = {}
    for n in (24, 16, 8):
        prefix, used, nf, np_ = build(n, comp, pred)
        # --- contamination checks: grep the assembled bytes, don't trust splits
        for x in json.load(open(f"{HERE}/splits/test.json")):
            assert x["msg"] not in prefix, f"TEST ITEM {x['idx']} IN BUNDLE"
        for x in json.load(open(f"{HERE}/splits/val.json")):
            assert x["msg"] not in prefix, f"VAL ITEM {x['idx']} IN BUNDLE"
        gold = json.load(open("/media/minotaur/Storage_Disk_1/LLM_repo/intent_gold.json"))
        for x in gold:
            if x["idx"] in excluded:
                assert x["msg"] not in prefix, f"FAST-RULE ITEM {x['idx']} IN BUNDLE"
        assert set(used) & (test_idx | val_idx | excluded) == set()
        assert INTENT_SYSTEM_PROMPT in prefix, "deployed prompt not embedded verbatim"
        json.dump({"n_traces": n, "n_fail": nf, "n_pass": np_, "used_idx": used,
                   "prefix": prefix, "instruction": INSTRUCTION,
                   "prefix_sha256": hashlib.sha256(prefix.encode()).hexdigest(),
                   "solo_sha256": SOLO_SHA256},
                  open(f"{HERE}/bundles/bundle_{n}.json", "w"), indent=1)
        out[n] = (prefix, used, nf, np_)
        print(f"bundle_{n}: {nf} FAIL + {np_} PASS = {n} traces | "
              f"prefix {len(prefix)} chars | idx {used}")
    print("\nALL CONTAMINATION CHECKS PASSED "
          "(no test item, no val item, no fast-rule item in any bundle)")
