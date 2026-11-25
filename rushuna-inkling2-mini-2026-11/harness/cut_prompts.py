#!/usr/bin/env python3
"""Lock I5 prompts: cut prompt-<TAG>-<n>.txt from corpus.txt (concatenated with itself as needed) so that a request's
prompt_n (chat template + "request <nonce>" line + text + fixed instruction) is n on the model's tokenizer. Not a
measurement: it talks to a llama-server started CPU-only (CUDA_VISIBLE_DEVICES="") from the L build, and uses that
server's own /apply-template and /tokenize, so the count is the server's. Each candidate cut is counted with 4 fixed
nonces; the cut is the smallest whose median count reaches n. The spread is printed.

  cut_prompts.py TAG PORT CORPUS OUTDIR N [N ...]
"""
import json, os, random, statistics, sys, urllib.request

tag, port, corpus_path, outdir = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
targets = [int(x) for x in sys.argv[5:]]
base = open(corpus_path, encoding="utf-8").read()
rng = random.Random(20261124)
NONCES = ["%08x" % rng.getrandbits(32) for _ in range(4)]


def post(path, body):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


def count(text, nonce):
    msg = f"request {nonce}\n{text}\n\nSummarise what this code does."
    p = post("/apply-template", {"messages": [{"role": "user", "content": msg}]})["prompt"]
    return len(post("/tokenize", {"content": p, "add_special": True, "parse_special": True})["tokens"])


def counts(text):
    return [count(text, n) for n in NONCES]


for n in targets:
    corpus = base
    while len(post("/tokenize", {"content": corpus})["tokens"]) < n * 1.05:
        corpus += "\n" + base
    lo, hi = 1, len(corpus)
    while lo < hi:
        mid = (lo + hi) // 2
        if statistics.median(counts(corpus[:mid])) >= n:
            hi = mid
        else:
            lo = mid + 1
    c = counts(corpus[:lo])
    open(os.path.join(outdir, f"prompt-{tag}-{n}.txt"), "w", encoding="utf-8").write(corpus[:lo])
    print(f"{tag} target {n}: {lo} chars, corpus copies {corpus.count(base[:200])}, median {statistics.median(c)}, min {min(c)}, max {max(c)}, counts {c}", flush=True)
