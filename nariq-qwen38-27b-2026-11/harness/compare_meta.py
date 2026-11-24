#!/usr/bin/env python3
"""Lock N5: compare the NariQ GGUFs' tokenizer and chat template with the IQ3 file's before any arm.
Not a measurement. Run with PYTHONPATH=<fork>/gguf-py (the fork's gguf-py knows the NariQ tensor types 44-49).

  compare_meta.py FILE...      exit 0 if every file matches the first on all compared keys, 1 otherwise
"""
import hashlib, sys
from gguf import GGUFReader

KEYS = ["general.architecture", "tokenizer.ggml.model", "tokenizer.ggml.pre", "tokenizer.ggml.tokens",
        "tokenizer.ggml.merges", "tokenizer.ggml.token_type", "tokenizer.ggml.bos_token_id",
        "tokenizer.ggml.eos_token_id", "tokenizer.ggml.padding_token_id", "tokenizer.ggml.add_bos_token",
        "tokenizer.chat_template"]


def val(f):
    if not f.types:
        return None
    if len(f.data) == 1 and f.types[0].name != "ARRAY":
        part = f.parts[f.data[0]]
        try:
            return bytes(part).decode("utf-8") if f.types[0].name == "STRING" else part.tolist()
        except Exception:
            return part.tolist()
    out = []
    for i in f.data:
        part = f.parts[i]
        out.append(bytes(part).decode("utf-8", "replace") if f.types[-1].name == "STRING" else part.tolist())
    return out


def summary(path):
    r = GGUFReader(path)
    s = {}
    for k in KEYS:
        f = r.fields.get(k)
        if f is None:
            s[k] = "MISSING"; continue
        v = val(f)
        if isinstance(v, list) and len(v) > 4:
            s[k] = f"n={len(v)} sha256={hashlib.sha256(repr(v).encode()).hexdigest()[:16]}"
        elif isinstance(v, str) and len(v) > 80:
            s[k] = f"len={len(v)} sha256={hashlib.sha256(v.encode()).hexdigest()[:16]}"
        else:
            s[k] = repr(v)
    return s


files = sys.argv[1:]
S = {p: summary(p) for p in files}
ref = files[0]
ok = True
for k in KEYS:
    vals = {p: S[p][k] for p in files}
    same = len(set(vals.values())) == 1
    ok &= same
    print(f"{'SAME' if same else 'DIFF'}  {k}")
    for p in files:
        print(f"      {p.split('/')[-1]}: {vals[p]}")
print("RESULT", "MATCH" if ok else "MISMATCH")
sys.exit(0 if ok else 1)
