#!/usr/bin/env python3
"""Section T token-count match check (A1, T4; Mark's N5 gate decision). Not a measurement.
  tokcheck.py REF.kld EVALSET PAIR...     PAIR = build:file (tokenized with that build's llama-tokenize --no-bos)
Every pair's ids must equal each other and the base file's stored token array (first n_chunk*n_ctx tokens).
Exit 0 = all match; else the mismatching pairs are printed (each voids every comparison involving that file)."""
import hashlib, os, struct, subprocess, sys
W = os.path.expanduser("~/nariq-t")
kld, evalset, pairs = sys.argv[1], sys.argv[2], sys.argv[3:]
with open(kld, "rb") as f:
    assert f.read(8) == b"_logits_"
    n_ctx, n_vocab, n_chunk = struct.unpack("<Iii", f.read(12))
    base = list(struct.unpack(f"<{n_ctx*n_chunk}i", f.read(4 * n_ctx * n_chunk)))
N = n_ctx * n_chunk
h = lambda ids: hashlib.sha256(",".join(map(str, ids)).encode()).hexdigest()[:16]
print(f"base: n_ctx {n_ctx} n_vocab {n_vocab} n_chunk {n_chunk} tokens {N} ids {h(base)}")
env = {**os.environ, "LD_LIBRARY_PATH": f"{W}/cuda-libs"}
bad = []
for p in pairs:
    b, fn = p.split(":")
    out = subprocess.run([os.path.expanduser(f"~/nariq-2026-11/{b}/build/bin/llama-tokenize"), "-m", f"{W}/model/{fn}", "-f", evalset, "--ids",
                          "--log-disable", "--no-bos", "--no-escape"], capture_output=True, text=True, env=env).stdout.strip().splitlines()[-1]
    ids = [int(x) for x in out.strip("[]").split(",") if x.strip()]
    ok = ids[:N] == base
    print(f"{b} {fn}: tokens {len(ids)} first-{N} ids {h(ids[:N])} {'MATCH' if ok else 'MISMATCH'}")
    if not ok:
        bad.append(p)
print("RESULT", "MATCH" if not bad else "MISMATCH " + " ".join(bad))
sys.exit(1 if bad else 0)
