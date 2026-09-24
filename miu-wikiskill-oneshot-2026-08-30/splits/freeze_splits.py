#!/usr/bin/env python3
"""Freeze the WikiSkill one-shot splits. Deterministic, seeded, run once.

Corpus: LLM_repo/intent_gold.json (89 items, gold hand-corrected 2026-08-07).
We drop the 2 items that today's deployed classify_fast() short-circuits before
the model runs -- they are deterministic regex hits, both correct, and no
compiled skill can move them. Experimental corpus is therefore n=87.

Allocation 24 compile / 15 val / 48 test, stratified on the full gold triple,
largest-remainder within each stratum so global proportions hold and the rare
strata land somewhere rather than being dropped.
"""
import json, hashlib, random, sys
from collections import Counter, defaultdict

sys.path.insert(0, "/home/minotaur/Desktop/mycoSwarm/src")
from mycoswarm.intent_rules import classify_fast

GOLD = "/media/minotaur/Storage_Disk_1/LLM_repo/intent_gold.json"
SEED = 20260830
TARGET = {"compile": 24, "val": 15, "test": 48}

raw = json.load(open(GOLD))
short = [x for x in raw if classify_fast(x["msg"]) is not None]
exp = [x for x in raw if classify_fast(x["msg"]) is None]
assert len(exp) == 87, len(exp)
assert sum(TARGET.values()) == len(exp)

def triple(x):
    g = x["gold"]
    return f'{g["tool"]}/{g["mode"]}/{g["scope"]}'

strata = defaultdict(list)
for x in exp:
    strata[triple(x)].append(x)

rng = random.Random(SEED)
frac = {k: v / len(exp) for k, v in TARGET.items()}
out = {k: [] for k in TARGET}
# deterministic stratum order, then largest-remainder allocation per stratum
for name in sorted(strata, key=lambda s: (-len(strata[s]), s)):
    items = sorted(strata[name], key=lambda x: x["idx"])
    rng.shuffle(items)
    n = len(items)
    exact = {k: n * frac[k] for k in TARGET}
    base = {k: int(exact[k]) for k in TARGET}
    rem = n - sum(base.values())
    # break ties by which split is furthest below its global quota, then name
    order = sorted(TARGET, key=lambda k: (-(exact[k] - base[k]),
                                          -(TARGET[k] - len(out[k])), k))
    for k in order[:rem]:
        base[k] += 1
    i = 0
    for k in ("compile", "val", "test"):
        for _ in range(base[k]):
            out[k].append(items[i]); i += 1
    assert i == n

# repair any drift from per-stratum rounding against the global target
def rebalance():
    for _ in range(200):
        over = [k for k in TARGET if len(out[k]) > TARGET[k]]
        under = [k for k in TARGET if len(out[k]) < TARGET[k]]
        if not over:
            return True
        src, dst = over[0], under[0]
        cnt = Counter(triple(x) for x in out[dst])
        # move the item from the most-represented stratum in src
        srccnt = Counter(triple(x) for x in out[src])
        pick = max(out[src], key=lambda x: (srccnt[triple(x)], -cnt[triple(x)], x["idx"]))
        out[src].remove(pick); out[dst].append(pick)
    return False
assert rebalance()

for k in out:
    out[k] = sorted(out[k], key=lambda x: x["idx"])
    assert len(out[k]) == TARGET[k], (k, len(out[k]))

seen = [x["idx"] for k in out for x in out[k]]
assert len(seen) == len(set(seen)) == 87

manifest = {
    "created": "2026-08-30",
    "source": GOLD,
    "source_sha256": hashlib.sha256(open(GOLD, "rb").read()).hexdigest(),
    "seed": SEED,
    "n_gold": len(raw),
    "n_excluded_fast_rule": len(short),
    "excluded_idx": sorted(x["idx"] for x in short),
    "n_experimental": len(exp),
    "targets": TARGET,
    "splits": {k: sorted(x["idx"] for x in v) for k, v in out.items()},
    "stratum_counts": {k: dict(Counter(triple(x) for x in v)) for k, v in out.items()},
}
json.dump(manifest, open("splits/manifest.json", "w"), indent=1)
for k, v in out.items():
    json.dump(v, open(f"splits/{k}.json", "w"), indent=1)

print(f"gold {len(raw)} | excluded(fast-rule) {len(short)} -> idx {manifest['excluded_idx']}")
print(f"experimental n={len(exp)}")
for k in ("compile", "val", "test"):
    c = Counter(triple(x) for x in out[k])
    print(f"  {k:8s} n={len(out[k]):3d}  {dict(c.most_common())}")
print("manifest sha256(source) =", manifest["source_sha256"][:16])
