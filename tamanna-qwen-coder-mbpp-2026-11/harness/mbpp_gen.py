#!/usr/bin/env python3
r'''MBPP (sanitized, test split, 257 problems) generation against llama-server /v1/completions, raw prompts.
Pre-registration: docs/candidates/qwen-coder-mbpp-confirm-2026-11.md. Same sampling as the HumanEval lock's
he_gen.py (P5); only the dataset, prompt format and stop list differ, as the pre-registration states.

Prompt (bigcode-evaluation-harness MBPP format, sanitized field names):  '"""\n{prompt}\n{test_list[0]}\n"""\n'
Stops: bigcode's MBPP list minus "\n```" (kept out so raw and fence-cut scoring can differ, which is the test).
Generation only; scoring is mbpp_score.py.   usage: mbpp_gen.py <label> <outfile>
'''
import json, sys, time, urllib.request

URL = "http://192.168.x.x:8099/v1/completions"
REVISION = "4bb6404fdc6cacfda99d4ac4205087b89d32030c"
STOP = ["\nclass", "\nassert", '\n"""', "\nprint", "\nif", "\n<|/"]
PINNED = {"temperature": 0, "top_p": 1, "top_k": 0, "min_p": 0.0, "typical_p": 1.0, "repeat_penalty": 1.0,
          "presence_penalty": 0.0, "frequency_penalty": 0.0, "seed": 42, "max_tokens": 512, "stop": STOP,
          "n_probs": 0, "stream": False}


def prompt_of(doc):
    return f'"""\n{doc["prompt"]}\n{doc["test_list"][0]}\n"""\n'


if __name__ == "__main__":
    LABEL, OUT = sys.argv[1], sys.argv[2]
    sys.path.insert(0, "/home/minotaur/Desktop/lucebox-hub/dflash/.venv/lib/python3.12/site-packages")
    from datasets import load_dataset  # noqa: E402
    ds = load_dataset("mbpp", "sanitized", split="test", revision=REVISION)
    assert len(ds) == 257, len(ds)
    res, t0 = {}, time.time()
    for i, s in enumerate(ds):
        body = dict(PINNED); body["prompt"] = prompt_of(s)
        req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        d = json.load(urllib.request.urlopen(req, timeout=600))
        ch = d["choices"][0]
        res[str(s["task_id"])] = {"text": ch["text"], "finish_reason": ch.get("finish_reason"),
                                  "completion_tokens": (d.get("usage") or {}).get("completion_tokens"),
                                  "prompt": body["prompt"],
                                  "test": "\n".join(s["test_imports"]) + "\n" + "\n".join(s["test_list"]) + "\n"}
        if (i + 1) % 50 == 0:
            print("  %3d/257  %.0fs" % (i + 1, time.time() - t0), flush=True)
    el = time.time() - t0
    gen = sum(v["completion_tokens"] or 0 for v in res.values())
    json.dump({"label": LABEL, "pinned": PINNED, "revision": REVISION, "elapsed_s": el, "gen_tokens": gen,
               "results": res}, open(OUT, "w"), indent=1)
    print("%s: 257 prompts in %.0fs, %d generated tokens (%.1f tok/s), -> %s" % (LABEL, el, gen, gen / el, OUT))
