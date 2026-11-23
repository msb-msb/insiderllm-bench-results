#!/usr/bin/env python3
"""Lock M5: cut prompt-512.txt and prompt-4096.txt from the HotRod corpus so that a request's prompt_n (chat template
+ "request <nonce>" line + text + the fixed instruction) is 512 and 4,096 on this file's tokenizer, counted with this
build's llama-tokenize. Run after the build, before arm (a24). Not a measurement: no server is started.

The template is the GGUF's own tokenizer.chat_template (extracted to chat_template.jinja), rendered with jinja2 for
one user message, add_generation_prompt, enable_thinking false: the same message bench_moecache.py sends. The nonce
is 8 random hex digits and tokenizes to a varying length, so each candidate cut is counted with 16 fixed sample
nonces and the cut is chosen so that the MEDIAN count equals the target. The spread across the 16 is reported.

  cut_prompts.py TEMPLATE CORPUS OUTDIR      (run with a python that has jinja2)
"""
import os, random, statistics, subprocess, sys, tempfile
import jinja2

W = os.path.expanduser("~/moecache-2026-11")
TOK = f"{W}/llama.cpp/build/bin/llama-tokenize"
MODEL = f"{W}/model/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf"
tmpl_path, corpus_path, outdir = sys.argv[1:4]
env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True)
env.globals["raise_exception"] = lambda m: (_ for _ in ()).throw(Exception(m))
T = env.from_string(open(tmpl_path).read())
corpus = open(corpus_path, encoding="utf-8").read()
rng = random.Random(20261122)
NONCES = ["%08x" % rng.getrandbits(32) for _ in range(16)]


def render(text, nonce):
    msg = f"request {nonce}\n{text}\n\nSummarise what this code does."
    return T.render(messages=[{"role": "user", "content": msg}], add_generation_prompt=True, enable_thinking=False,
                    bos_token="", eos_token="<|im_end|>")


def count(s):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(s); p = f.name
    r = subprocess.run([TOK, "-m", MODEL, "-f", p, "--ids", "--log-disable", "--no-escape"], capture_output=True, text=True)
    os.unlink(p)
    ids = r.stdout.strip().splitlines()[-1]
    return len([x for x in ids.strip("[]").split(",") if x.strip()])


def counts(n_chars):
    return [count(render(corpus[:n_chars], nc)) for nc in NONCES]


rendered_example = render("TEXT", NONCES[0])
print("rendered form:", repr(rendered_example))
for target in (512, 4096):
    lo, hi = 1, min(len(corpus), target * 8)
    while lo < hi:                       # smallest n_chars whose median count >= target
        mid = (lo + hi) // 2
        if statistics.median(counts(mid)) >= target:
            hi = mid
        else:
            lo = mid + 1
    c = counts(lo)
    text = corpus[:lo]
    open(os.path.join(outdir, f"prompt-{target}.txt"), "w", encoding="utf-8").write(text)
    print(f"target {target}: {lo} chars, median {statistics.median(c)}, min {min(c)}, max {max(c)}, counts {c}")
