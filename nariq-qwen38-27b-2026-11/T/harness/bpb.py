#!/usr/bin/env python3
"""Section T bits-per-byte denominator (A1, T4). Not a measurement.
  bpb.py TOKENS_SOURCE EVALSET GGUF OUT.json
TOKENS_SOURCE = the base .kld file (its stored token array) or a text file of ids ("[1, 2, ...]") for a dry run.
Decodes each token's piece through the GGUF vocab (gpt2 byte-level BPE: inverse of bytes_to_unicode), checks that the
concatenated pieces of all stored tokens equal the eval set's bytes (prefix), and counts the UTF-8 bytes of the
scored targets: per chunk, tokens[start+n_ctx/2+1 .. start+n_ctx-1] (n_ctx-1-n_ctx/2 per chunk, as llama-perplexity's
KL mode scores them). Run with PYTHONPATH=<llama.cpp>/gguf-py."""
import json, struct, sys
from gguf import GGUFReader
src, evalset, gg, out = sys.argv[1:5]
N_CTX = 4096
if src.endswith(".kld"):
    with open(src, "rb") as f:
        assert f.read(8) == b"_logits_"
        n_ctx, n_vocab, n_chunk = struct.unpack("<Iii", f.read(12))
        toks = list(struct.unpack(f"<{n_ctx*n_chunk}i", f.read(4 * n_ctx * n_chunk)))
else:
    toks = [int(x) for x in open(src).read().strip().strip("[]").split(",") if x.strip()]
    n_ctx = N_CTX; n_chunk = len(toks) // n_ctx; toks = toks[:n_ctx * n_chunk]


def bytes_to_unicode():
    bs = list(range(ord("!"), ord("~") + 1)) + list(range(ord("¡"), ord("¬") + 1)) + list(range(ord("®"), ord("ÿ") + 1))
    cs = bs[:]; n = 0
    for b in range(256):
        if b not in bs:
            bs.append(b); cs.append(256 + n); n += 1
    return {chr(c): b for b, c in zip(bs, cs)}


u2b = bytes_to_unicode()
r = GGUFReader(gg); f = r.fields["tokenizer.ggml.tokens"]
vocab = [bytes(f.parts[i]).decode("utf-8") for i in f.data]
piece = lambda t: bytes(u2b[c] for c in vocab[t])
allb = b"".join(piece(t) for t in toks)
text = open(evalset, "rb").read()
prefix_ok = text.startswith(allb)
first = n_ctx // 2
scored = [toks[c * n_ctx + j] for c in range(n_chunk) for j in range(first + 1, n_ctx)]
half = n_chunk // 2
code = [toks[c * n_ctx + j] for c in range(half) for j in range(first + 1, n_ctx)]
res = {"n_ctx": n_ctx, "n_chunk": n_chunk, "decode_matches_evalset_prefix": prefix_ok, "decoded_bytes": len(allb),
       "scored_tokens": len(scored), "scored_bytes": sum(len(piece(t)) for t in scored),
       "scored_tokens_code_half": len(code), "scored_bytes_code_half": sum(len(piece(t)) for t in code),
       "scored_bytes_prose_half": sum(len(piece(t)) for t in scored) - sum(len(piece(t)) for t in code)}
json.dump(res, open(out, "w"), indent=1); print(json.dumps(res))
sys.exit(0 if prefix_ok else 1)
