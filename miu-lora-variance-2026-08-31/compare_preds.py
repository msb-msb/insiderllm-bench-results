#!/usr/bin/env python3
"""Count prediction and raw-string differences between scored runs.

    compare_preds.py BASELINE.json RUN.json [RUN.json ...]

Prints, per run: exact score, predictions differing from BASELINE on
(tool, mode, scope), raw strings differing, and the differing item indexes.
"""
import json, sys


def load(p):
    d = json.load(open(p))
    if "records" not in d and "runs" in d:      # noisefloor file: first rep
        d = dict(d, records=d["runs"][0]["records"], summary=d["runs"][0]["summary"])
    return d, {r["idx"]: r for r in d["records"]}


def main():
    base_path, *runs = sys.argv[1:]
    base, brec = load(base_path)
    print(f"baseline {base['tag']}: exact {base['summary']['exact']}/{base['summary']['n']}")
    for p in runs:
        d, rec = load(p)
        pd = [i for i in brec if rec[i]["pred"] != brec[i]["pred"]]
        rd = [i for i in brec if rec[i]["raw"] != brec[i]["raw"]]
        print(f"{d['tag']:<28} exact {d['summary']['exact']:>2}/{d['summary']['n']}  "
              f"preds differ {len(pd):>2}  raw differ {len(rd):>2}  "
              f"lora_id={d.get('lora_id')} cache_prompt={d.get('cache_prompt')}  "
              f"idx={pd}")


if __name__ == "__main__":
    main()
