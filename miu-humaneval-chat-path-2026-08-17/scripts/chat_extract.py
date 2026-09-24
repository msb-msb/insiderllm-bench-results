#!/usr/bin/env python3
"""Turn a chat response into the bare function-body continuation human-eval needs.

The official harness evaluates  prompt + completion , so what we emit must be a
CONTINUATION of the stub — an indented body, not a whole redefined function.

Order of operations:
  1. TRUNCATION CHECK first. See "Disposition rules" below. A generation we cut
     off is never scored, because the ceiling is our parameter and not the
     model's choice. Truncations are excluded from the pass@1 denominator and
     reported separately.

Disposition rules — every response lands in exactly one of these, and the
status decides whether it reaches the scorer at all:

  OK                 finish_reason == "stop", usable body extracted.
                     SCORED.

  NO_ANSWER          finish_reason == "stop", but no usable body. The model
                     had budget left and chose to end without answering. That
                     is a real failure to produce output, not an artifact of
                     our limits, so it IS scored, as a fail (empty completion).
                     SCORED.

  TRUNCATED_EMPTY    finish_reason == "length", nothing usable after stripping
                     thinking. It never reached an answer. EXCLUDED.

  TRUNCATED_PARTIAL  finish_reason == "length" with some usable body: the model
                     finished thinking and was mid-answer when we cut it. Still
                     EXCLUDED. We cannot distinguish "finished and the ceiling
                     landed on trailing prose" from "cut off halfway", and
                     scoring a generation we interrupted attributes our budget
                     to the model's capability. Kept as its own status rather
                     than folded into TRUNCATED_EMPTY so that if it ever fires
                     it is visible and this rule can be revisited on real data.

  EXTRACTOR_REVIEW   Content was present but extraction produced nothing. This
                     is ambiguous — it may be a model that emitted prose with
                     no code, or a bug in to_continuation(). Those must not be
                     conflated. EXCLUDED from the automated denominator AND
                     flagged: the run exits non-zero and pass@1 is provisional
                     until a human adjudicates each one.

pass@1 denominator = count(OK) + count(NO_ANSWER). It is written to the sidecar
manifest and printed, because a denominator that silently differs from the
dataset size is exactly how a budget artifact turns into a capability claim.
  2. Strip thinking: everything up to and including the LAST </think>.
     Marker spelling verified from both GGUF chat templates, not assumed.
  3. Pull the code out of markdown fences if present, else use the prose as-is.
  4. Reduce to a continuation of the stub:
       - if the code redefines the target function, keep only its body
       - if the code is already a bare indented body, keep it
       - drop imports/helpers that precede the def by re-emitting them ABOVE
         the body is not possible in a continuation, so they are kept only
         when they appear inside the function body
Usage: chat_extract.py <gen.json> <out.jsonl> [--samples N]
"""
import json, re, sys

THINK_CLOSE = "</think>"
THINK_OPEN = "<think>"
FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.S | re.I)


# Statuses whose completions go to the scorer. Everything else is excluded
# from the pass@1 denominator. Keep these two sets exhaustive and disjoint.
SCORED = ("OK", "NO_ANSWER")
EXCLUDED = ("TRUNCATED_EMPTY", "TRUNCATED_PARTIAL", "EXTRACTOR_REVIEW")


def hit_ceiling(rec):
    return rec.get("finish_reason") == "length"


def is_truncated(rec):
    """Any generation we cut off. The ceiling is ours, so we never score it.

    Note: on the chat endpoint llama.cpp splits thinking into reasoning_content,
    so `content` normally carries no <think> markers at all and the unterminated
    check below is a belt-and-braces path for harnesses that inline them.
    """
    raw = rec.get("content") or ""
    unterminated = (THINK_OPEN in raw and THINK_CLOSE not in raw)
    return hit_ceiling(rec) or unterminated


def strip_think(raw):
    if THINK_CLOSE in raw:
        return raw.rsplit(THINK_CLOSE, 1)[1]
    if THINK_OPEN in raw:          # unterminated -> nothing usable after it
        return ""
    return raw


def pick_code(text):
    blocks = FENCE.findall(text)
    if blocks:
        # prefer the block that mentions a def, else the longest
        withdef = [b for b in blocks if re.search(r"^\s*def\s", b, re.M)]
        return (withdef or sorted(blocks, key=len, reverse=True))[0]
    return text


def entry_name(prompt):
    m = None
    for m in re.finditer(r"^\s*def\s+([A-Za-z_]\w*)\s*\(", prompt, re.M):
        pass
    return m.group(1) if m else None


def to_continuation(code, prompt):
    """Return an indented body that can be appended to the stub."""
    fn = entry_name(prompt)
    lines = code.split("\n")
    if fn:
        # find the LAST def of the target fn and take everything after it
        idx = None
        for i, l in enumerate(lines):
            if re.match(rf"^\s*def\s+{re.escape(fn)}\s*\(", l):
                idx = i
        if idx is not None:
            body = lines[idx + 1:]
            # drop a re-stated docstring immediately after the signature
            j = 0
            while j < len(body) and not body[j].strip():
                j += 1
            if j < len(body) and re.match(r'^\s*(""" |"""|\'\'\')', body[j].strip()[:3] + " "):
                q = body[j].strip()[:3]
                k = j
                if body[j].strip().count(q) >= 2 and len(body[j].strip()) > 3:
                    k = j
                else:
                    k = j + 1
                    while k < len(body) and q not in body[k]:
                        k += 1
                body = body[:j] + body[k + 1:]
            body = [l for l in body if l.strip()] and body or body
            txt = "\n".join(body).rstrip()
            if txt.strip():
                return txt if txt.startswith((" ", "\t")) else "\n".join(
                    "    " + l if l.strip() else l for l in txt.split("\n"))
    # Already a bare body? Judge on the first NON-EMPTY line: after stripping
    # </think> the leading line is usually blank, and testing it directly made
    # an already-indented body get indented a second time.
    lines2 = code.rstrip().split("\n")
    while lines2 and not lines2[0].strip():
        lines2.pop(0)
    if lines2 and lines2[0].startswith((" ", "\t")):
        return "\n".join(lines2)
    # last resort: indent whatever we have
    return "\n".join("    " + l if l.strip() else l for l in lines2)


def extract(rec, prompt):
    body = strip_think(rec.get("content") or "")

    # 1. Anything we cut off is excluded, whether or not it left usable text.
    if is_truncated(rec):
        return None, "TRUNCATED_PARTIAL" if body.strip() else "TRUNCATED_EMPTY"

    # 2. Stopped of its own accord with nothing to show: a real failure, scored.
    if not body.strip():
        return "", "NO_ANSWER"

    # 3. Had content but we got nothing out of it. Ambiguous — never silently
    #    scored in either direction.
    cont = to_continuation(pick_code(body), prompt)
    if not cont.strip():
        return None, "EXTRACTOR_REVIEW"

    return cont, "OK"


def main():
    gen = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    nsamp = 0
    if "--samples" in sys.argv:
        nsamp = int(sys.argv[sys.argv.index("--samples") + 1])

    sys.path.insert(0, "/home/minotaur/Desktop/lucebox-hub/dflash/.venv/lib/python3.12/site-packages")
    from datasets import load_dataset
    prompts = {s["task_id"]: s["prompt"] for s in load_dataset("openai_humaneval", split="test")}

    stats = {k: 0 for k in SCORED + EXCLUDED}
    by_status, rows = {}, []
    for tid, rec in gen["results"].items():
        cont, status = extract(rec, prompts[tid])
        stats[status] += 1
        by_status.setdefault(status, []).append(tid)
        rows.append((tid, cont if cont is not None else "", status, rec))

    if nsamp:
        shown = 0
        print("=" * 78)
        print("EXTRACTOR SAMPLES — raw response -> emitted continuation")
        print("=" * 78)
        for tid, cont, status, rec in rows:
            if status != "OK" or shown >= nsamp:
                continue
            raw = rec.get("content") or ""
            print(f"\n### {tid}   finish={rec.get('finish_reason')} "
                  f"tokens={rec.get('completion_tokens')}")
            print("--- RAW (first 300 / last 300 chars) ---")
            print(raw[:300].replace("\n", "\\n"))
            print("   ...")
            print(raw[-300:].replace("\n", "\\n"))
            print("--- EMITTED CONTINUATION ---")
            print(cont[:500])
            print("--- prompt+completion compiles? ---")
            try:
                compile(prompts[tid] + cont, "<t>", "exec")
                print("    YES")
            except SyntaxError as e:
                print(f"    NO -> {e}")
            shown += 1

    # THE FILTER. Only scoreable statuses reach the scorer; excluded rows are
    # not written at all, so they cannot become fails by omission.
    written = 0
    with open(out, "w") as f:
        for tid, cont, status, rec in rows:
            if status not in SCORED:
                continue
            f.write(json.dumps({"task_id": tid, "completion": cont}) + "\n")
            written += 1

    denom = sum(stats[k] for k in SCORED)
    manifest = {
        "source": sys.argv[1],
        "n_dataset": len(rows),
        "pass_at_1_denominator": denom,
        "written_to_scorer": written,
        "stats": stats,
        "by_status": by_status,
        "provisional": bool(stats["EXTRACTOR_REVIEW"]),
    }
    mpath = out + ".manifest.json"
    json.dump(manifest, open(mpath, "w"), indent=1)

    print("\n" + "=" * 78)
    print(f"extraction stats: {stats}")
    for k in EXCLUDED:
        if stats[k]:
            print(f"  EXCLUDED {k} ({stats[k]}): {by_status[k]}")
    if stats["NO_ANSWER"]:
        print(f"  SCORED AS FAIL — NO_ANSWER ({stats['NO_ANSWER']}): {by_status['NO_ANSWER']}")
    assert written == denom, f"filter/denominator mismatch: {written} != {denom}"
    print(f"\npass@1 denominator: {denom} of {len(rows)} dataset problems")
    if denom != len(rows):
        print(f"  -> {len(rows) - denom} excluded. This denominator MUST be stated "
              f"wherever the resulting pass@1 is published.")
    print(f"wrote {out}  ({written} samples)")
    print(f"wrote {mpath}")

    if stats["EXTRACTOR_REVIEW"]:
        print("\n*** PROVISIONAL: EXTRACTOR_REVIEW is non-empty. Each of those is either a\n"
              "*** model that emitted no code or a bug in to_continuation(). Adjudicate by\n"
              "*** hand before quoting pass@1. Exiting non-zero so this cannot pass silently.")
        sys.exit(2)


main()
