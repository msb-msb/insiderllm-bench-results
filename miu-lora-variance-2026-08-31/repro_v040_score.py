#!/usr/bin/env python3
"""v0.4.0 re-run of the section-7 runtime-LoRA-scale checks, for the upstream issue.

Same pipeline as score_lora.py (imports its parser and scorer), plus:
  --url            server to hit (default the section-7 port 8081)
  --cache-prompt   omit (server default), true, or false — sent as the request's
                   `cache_prompt` field, to separate a runtime-scale effect from
                   prompt-cache reuse across requests with different lora config
                   (ggml-org/llama.cpp#26207)
  --outdir         default scored_v040
The output also records /props (build id) and GET /lora-adapters as seen by the
server at run time, so each result file carries its own provenance.
"""
import json, sys, time, urllib.request, argparse, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from score_lora import parse_and_sanitise, score          # noqa: E402
from deployed import INTENT_SYSTEM_PROMPT, SOLO_SHA256      # noqa: E402


def get(url):
    return json.load(urllib.request.urlopen(url, timeout=60))


def call(url, msg, lora_id, cache_prompt, maxtok=100):
    body = {"model": "local",
            "messages": [{"role": "system", "content": INTENT_SYSTEM_PROMPT},
                         {"role": "user", "content": msg}],
            "temperature": 0.0, "max_tokens": maxtok, "stream": False,
            "chat_template_kwargs": {"enable_thinking": False}}
    if lora_id is not None and lora_id >= 0:
        body["lora"] = [{"id": lora_id, "scale": 1.0}]
    elif lora_id is not None:            # -1 => all adapters explicitly off
        body["lora"] = []
    if cache_prompt is not None:
        body["cache_prompt"] = cache_prompt
    t = time.time()
    req = urllib.request.Request(url + "/v1/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=900))
    m = r["choices"][0]["message"]
    return (m.get("content") or ""), r["usage"], time.time() - t, body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("--id", type=int, default=None,
                    help="adapter id for per-request selection; -1 = all off; omit = no lora field")
    ap.add_argument("--cache-prompt", choices=["true", "false"], default=None)
    ap.add_argument("--url", default="http://127.0.0.1:8081")
    ap.add_argument("--split", default="test")
    ap.add_argument("--outdir", default="scored_v040")
    ap.add_argument("--note", default="")
    a = ap.parse_args()
    cache_prompt = None if a.cache_prompt is None else (a.cache_prompt == "true")

    props = get(a.url + "/props")
    try:
        adapters = get(a.url + "/lora-adapters")
    except Exception as e:                       # no adapters loaded -> 500 on some builds
        adapters = f"unavailable: {e}"

    items = json.load(open(os.path.join(HERE, "splits", f"{a.split}.json")))
    items.sort(key=lambda x: x["idx"])
    recs, t0, body_template = [], time.time(), None
    for x in items:
        content, usage, el, body = call(a.url, x["msg"], a.id, cache_prompt)
        if body_template is None:
            body_template = {k: v for k, v in body.items() if k != "messages"}
        pred = parse_and_sanitise(content, x["msg"])
        ex, ef = score(pred, x["gold"])
        recs.append({"idx": x["idx"], "msg": x["msg"], "gold": x["gold"],
                     "pred": {k: pred[k] for k in ("tool", "mode", "scope")},
                     "raw": content, "raw_valid": pred["raw_valid"],
                     "via": pred["via"], "exact": ex, "effective": ef,
                     "prompt_tokens": usage["prompt_tokens"],
                     "completion_tokens": usage["completion_tokens"],
                     "elapsed_s": round(el, 3)})
    n = len(recs)
    summ = {"n": n, "lora_id": a.id, "cache_prompt": cache_prompt,
            "exact": sum(r["exact"] for r in recs),
            "effective": sum(r["effective"] for r in recs),
            "raw_valid": sum(r["raw_valid"] for r in recs),
            "unparseable": sum(r["via"] == "unparseable" for r in recs),
            "prompt_tokens": sum(r["prompt_tokens"] for r in recs),
            "completion_tokens": sum(r["completion_tokens"] for r in recs),
            "wall_s": round(time.time() - t0, 1)}
    summ["exact_pct"] = round(100 * summ["exact"] / n, 2)
    os.makedirs(os.path.join(HERE, a.outdir), exist_ok=True)
    path = os.path.join(HERE, a.outdir, f"{a.tag}.json")
    json.dump({"tag": a.tag, "lora_id": a.id, "cache_prompt": cache_prompt,
               "split": a.split, "solo_sha256": SOLO_SHA256,
               "model": "Qwen3.6-27B-Q4_K_M", "note": a.note,
               "build_info": props.get("build_info"),
               "lora_adapters_at_run": adapters,
               "request_body_template": body_template,
               "summary": summ, "records": recs}, open(path, "w"), indent=1)
    print(f"  {a.tag}: lora_id={a.id} cache_prompt={cache_prompt} "
          f"exact {summ['exact']}/{n}  raw_valid {summ['raw_valid']}/{n}  "
          f"tok(p/c) {summ['prompt_tokens']}/{summ['completion_tokens']}  {summ['wall_s']}s  "
          f"build={props.get('build_info')}  adapters={adapters}")


if __name__ == "__main__":
    main()
