#!/usr/bin/env python3
"""N5 gate evidence (not a measurement): render the harness's own request shape with each file's chat template
and check the rendered prompts are byte-identical. Request = one user message, enable_thinking false,
add_generation_prompt true (bench_nariq.py). Run with a python that has jinja2.

  render_check.py TEMPLATE_A TEMPLATE_B [PROMPT_FILE]   exit 0 if identical
"""
import hashlib, sys
from jinja2.sandbox import ImmutableSandboxedEnvironment

def raise_exception(msg):
    raise Exception(msg)

def render(path, content):
    env = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True)
    env.globals["raise_exception"] = raise_exception
    t = env.from_string(open(path, encoding="utf-8").read())
    return t.render(messages=[{"role": "user", "content": content}], add_generation_prompt=True,
                    enable_thinking=False, bos_token="", eos_token="<|im_end|>")

a, b = sys.argv[1], sys.argv[2]
body = open(sys.argv[3], encoding="utf-8").read() if len(sys.argv) > 3 else "def f(x):\n    return x + 1\n"
content = f"request 0123abcd\n{body}\n\nSummarise what this code does."
ra, rb = render(a, content), render(b, content)
for p, r in ((a, ra), (b, rb)):
    print(f"{p.split('/')[-1]}: template sha256 {hashlib.sha256(open(p,'rb').read()).hexdigest()[:16]}"
          f"  rendered {len(r.encode())} bytes sha256 {hashlib.sha256(r.encode()).hexdigest()}")
print("wrapper (content replaced by <C>):", repr(ra.replace(content, "<C>")))
print("RESULT", "IDENTICAL" if ra == rb else "DIFFERENT")
sys.exit(0 if ra == rb else 1)
