#!/usr/bin/env python3
"""Free pre-flight: exact token counts for each bundle, before any billed call."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_common import load_env, request_shape, MODEL
import anthropic

load_env()
client = anthropic.Anthropic()
MIN_CACHEABLE = 512  # Claude Opus 5, per platform docs 2026-08-30

print(f"model={MODEL}  min cacheable prefix={MIN_CACHEABLE} tokens\n")
print(f"{'bundle':>7} {'prefix tok':>11} {'instr tok':>10} {'total tok':>10} {'clears floor':>13}")
out = {}
for n in (24, 16, 8):
    b = json.load(open(f"bundles/bundle_{n}.json"))
    shape = request_shape(b)
    total = client.messages.count_tokens(model=MODEL, **shape).input_tokens
    # prefix alone: count with a 1-char user message, then subtract its overhead
    pre = client.messages.count_tokens(
        model=MODEL, system=shape["system"],
        messages=[{"role": "user", "content": "."}]).input_tokens
    instr = total - pre
    ok = "YES" if pre >= MIN_CACHEABLE else "NO -- WILL NOT CACHE"
    print(f"{n:>7} {pre:>11,} {instr:>10,} {total:>10,} {ok:>13}")
    out[n] = {"prefix_tokens_approx": pre, "instruction_tokens_delta": instr,
              "total_input_tokens": total, "clears_min_cacheable": pre >= MIN_CACHEABLE}
json.dump({"model": MODEL, "min_cacheable": MIN_CACHEABLE, "bundles": out},
          open("bundles/token_counts.json", "w"), indent=1)
print("\n-> bundles/token_counts.json")
