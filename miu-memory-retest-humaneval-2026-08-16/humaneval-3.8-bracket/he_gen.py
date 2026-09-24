#!/usr/bin/env python3
"""HumanEval generation against llama-server /v1/completions, raw prompts.

Byte-for-byte the prior run's protocol (session b6d2cbb1 he_run.py) so the
result is comparable. All sampling confounds pinned explicitly and echoed into
the output file. Generation only - scoring is a separate step.

Usage: he_gen.py <label> <outfile>
"""
import json
import sys
import time
import urllib.request

LABEL, OUT = sys.argv[1], sys.argv[2]
URL = "http://127.0.0.1:8099/v1/completions"

# lm-evaluation-harness humaneval stop sequences
STOP = ["\nclass", "\ndef", "\n#", "\nif", "\nprint"]

PINNED = {
    "temperature": 0,
    "top_p": 1,
    "top_k": 0,
    "min_p": 0.0,
    "typical_p": 1.0,
    "repeat_penalty": 1.0,
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0,
    "seed": 42,
    "max_tokens": 512,
    "stop": STOP,
    "n_probs": 0,
    "stream": False,
}

sys.path.insert(0, "/home/minotaur/Desktop/lucebox-hub/dflash/.venv/lib/python3.12/site-packages")
from datasets import load_dataset  # noqa: E402

ds = load_dataset("openai_humaneval", split="test")
res, t0 = {}, time.time()
for i, s in enumerate(ds):
    body = dict(PINNED)
    body["prompt"] = s["prompt"]
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=600))
    ch = d["choices"][0]
    res[s["task_id"]] = {
        "text": ch["text"],
        "finish_reason": ch.get("finish_reason"),
        "completion_tokens": (d.get("usage") or {}).get("completion_tokens"),
    }
    if (i + 1) % 40 == 0:
        print("  %3d/164  %.0fs" % (i + 1, time.time() - t0), flush=True)

el = time.time() - t0
gen = sum(v["completion_tokens"] or 0 for v in res.values())
json.dump({"label": LABEL, "pinned": PINNED, "elapsed_s": el,
           "gen_tokens": gen, "results": res}, open(OUT, "w"), indent=1)
print("%s: 164 prompts in %.0fs, %d generated tokens (%.1f tok/s), -> %s"
      % (LABEL, el, gen, gen / el, OUT))
