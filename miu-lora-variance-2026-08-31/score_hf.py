#!/usr/bin/env python3
"""Score through PEFT + NF4 -- the exact configuration the adapters trained in.

Why this exists: llama.cpp's runtime adapter application perturbs output. Two
runs with every adapter scale pinned at 0.0 differed on 9/47 items while both
totalling 22/47, and scale 0.0 also differed from the no-adapter baseline on
8/47. So the llama.cpp path cannot answer whether adapter TRAINING is
reproducible -- it has instability of its own sitting on top.

This scorer changes the runtime and keeps the weights, which is the cleaner
control. It loads the base once and can evaluate several adapters in one
process, so the 18 GB NF4 load is paid a single time.

SCOPE: this measures whether adapter training is reproducible, as seen through
PEFT. It says nothing about what these adapters score through llama.cpp.
Those are two separate findings and must not be conflated.
"""
import json, os, sys, argparse, time
import torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deployed import (INTENT_SYSTEM_PROMPT, INTENT_DEFAULT, VALID_TOOLS,
                      VALID_MODES, VALID_SCOPES, detect_past_reference, SOLO_SHA256)
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

MODEL = "/media/minotaur/Storage_Disk_1/LLM_repo/qwen3.6-27b"
HERE = os.path.dirname(os.path.abspath(__file__))


def parse_and_sanitise(raw, query):
    """Identical to score_lora.py / run_arm.py: the deployed pipeline."""
    rec = {"raw_valid": False, "via": "model"}
    r = raw.strip().strip("`").strip()
    if r.startswith("json"):
        r = r[4:].strip()
    try:
        data = json.loads(r)
        if not isinstance(data, dict):
            raise ValueError("not an object")
    except (json.JSONDecodeError, ValueError):
        result = dict(INTENT_DEFAULT)
        low = r.lower()
        for cat in ("web_and_rag", "web_search", "rag", "answer"):
            if cat in low:
                result["tool"] = cat
                break
        rec.update(result); rec["via"] = "unparseable"
        return rec
    result = dict(INTENT_DEFAULT)
    ok = True
    for field, valid in (("tool", VALID_TOOLS), ("mode", VALID_MODES),
                         ("scope", VALID_SCOPES)):
        v = data.get(field, INTENT_DEFAULT[field])
        if v in valid:
            result[field] = v
        else:
            ok = False
    rec["raw_valid"] = ok
    if detect_past_reference(query):
        result["scope"] = "session"
    if result["scope"] == "docs" and result["tool"] == "web_and_rag":
        result["tool"] = "rag"
    rec.update(result)
    return rec


def score_one(pred, gold):
    exact = all(pred[f] == gold[f] for f in ("tool", "mode", "scope"))
    if gold["tool"] in ("rag", "web_and_rag"):
        eff = exact
    else:
        eff = pred["tool"] == gold["tool"] and pred["mode"] == gold["mode"]
    return exact, eff


def run_pass(model, tok, items, tag):
    recs, t0 = [], time.time()
    for x in items:
        msgs = [{"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": x["msg"]}]
        txt = tok.apply_chat_template(msgs, tokenize=False,
                                      add_generation_prompt=True,
                                      enable_thinking=False)
        ids = tok(txt, add_special_tokens=False, return_tensors="pt").to(0)
        with torch.no_grad():
            out = model.generate(**ids, max_new_tokens=100, do_sample=False,
                                 temperature=None, top_p=None, top_k=None,
                                 pad_token_id=tok.eos_token_id)
        gen = out[0][ids["input_ids"].shape[1]:]
        content = tok.decode(gen, skip_special_tokens=True)
        pred = parse_and_sanitise(content, x["msg"])
        ex, ef = score_one(pred, x["gold"])
        recs.append({"idx": x["idx"], "gold": x["gold"],
                     "pred": {k: pred[k] for k in ("tool", "mode", "scope")},
                     "raw": content, "raw_valid": pred["raw_valid"],
                     "via": pred["via"], "exact": ex, "effective": ef})
    n = len(recs)
    s = {"n": n, "exact": sum(r["exact"] for r in recs),
         "effective": sum(r["effective"] for r in recs),
         "raw_valid": sum(r["raw_valid"] for r in recs),
         "wall_s": round(time.time() - t0, 1)}
    s["exact_pct"] = round(100 * s["exact"] / n, 2)
    s["effective_pct"] = round(100 * s["effective"] / n, 2)
    print(f"  {tag:<26} exact {s['exact']}/{n} = {s['exact_pct']:>6.2f}%  "
          f"eff {s['effective_pct']:>6.2f}%  raw_valid {s['raw_valid']}/{n}  "
          f"{s['wall_s']}s", flush=True)
    return {"tag": tag, "summary": s, "records": recs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True,
                    help="comma list of tag:adapter_or_NONE:reps, e.g. "
                         "base:NONE:1,seed1:adapters/seed1:5")
    ap.add_argument("--split", default="test")
    ap.add_argument("--outdir", default="scored_hf")
    a = ap.parse_args()

    items = json.load(open(os.path.join(HERE, "splits", f"{a.split}.json")))
    items.sort(key=lambda x: x["idx"])
    tok = AutoTokenizer.from_pretrained(MODEL)

    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16,
                             bnb_4bit_use_double_quant=True)
    t0 = time.time()
    base = AutoModelForCausalLM.from_pretrained(
        MODEL, quantization_config=bnb, dtype=torch.bfloat16, device_map={"": 0})
    base.config.use_cache = True
    base.eval()
    print(f"base loaded {time.time()-t0:.0f}s | "
          f"vram {torch.cuda.memory_allocated()/2**30:.2f} GiB", flush=True)

    os.makedirs(os.path.join(HERE, a.outdir), exist_ok=True)
    for spec in a.plan.split(","):
        tag, adapter, reps = spec.split(":")
        reps = int(reps)
        if adapter.upper() == "NONE":
            model = base
        else:
            from peft import PeftModel
            model = PeftModel.from_pretrained(base, os.path.join(HERE, adapter))
            model.eval()
        for r in range(reps):
            rtag = f"{tag}_rep{r}" if reps > 1 else tag
            res = run_pass(model, tok, items, rtag)
            res.update({"adapter": adapter, "split": a.split,
                        "solo_sha256": SOLO_SHA256, "stack": "PEFT+NF4",
                        "model": "Qwen3.6-27B NF4"})
            json.dump(res, open(os.path.join(HERE, a.outdir, f"{rtag}.json"), "w"),
                      indent=1)
        if adapter.upper() != "NONE":
            model = model.unload()   # strip adapter, restore the base in place


if __name__ == "__main__":
    main()
