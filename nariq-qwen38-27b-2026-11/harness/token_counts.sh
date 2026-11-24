#!/bin/bash
# Pre-arm check (not a measurement): the rendered 512/4096 requests tokenize to the same count on every file.
# Each file is tokenized by the build its arms use (IQ3: mainline and fork; NariQ: fork). Run from the harness folder.
set -u
W=$HOME/nariq-2026-11; export LD_LIBRARY_PATH=$HOME/cuda-12.8/lib64; PY=$HOME/strata/.venv/bin/python
for n in 512 4096; do
  f=$(mktemp); $PY -I - "$W/rec/chat_template-iq3.jinja" "prompt-$n.txt" > "$f" <<'P'
import sys, jinja2
env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True)
t = env.from_string(open(sys.argv[1]).read()); body = open(sys.argv[2], encoding="utf-8").read()
sys.stdout.write(t.render(messages=[{"role": "user", "content": f"request 0123abcd\n{body}\n\nSummarise what this code does."}],
                          add_generation_prompt=True, enable_thinking=False, bos_token="", eos_token="<|im_end|>"))
P
  for pair in mainline:Qwen3.8-27B-UD-IQ3_XXS.gguf fork:Qwen3.8-27B-UD-IQ3_XXS.gguf fork:Qwen3.8-27B-NariQ-3.0bpw.gguf fork:Qwen3.8-27B-NariQ-2.5bpw.gguf; do
    b=${pair%%:*}; m=${pair#*:}
    ids=$("$W/$b/build/bin/llama-tokenize" -m "$W/model/$m" -f "$f" --ids --log-disable --no-escape 2>/dev/null | tail -1)
    echo "prompt-$n $b $m tokens=$(echo "$ids" | tr -d '[] ' | tr ',' '\n' | grep -c .) ids_sha256=$(echo -n "$ids" | sha256sum | cut -c1-16)"
  done; rm -f "$f"
done
