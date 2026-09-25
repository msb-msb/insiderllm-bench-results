#!/usr/bin/env python3
"""Multi-user serving bench for llama-server: N concurrent chat turns at -np N.

Dependency-free on purpose — Tamanna has Python 3.14 and no aiohttp/httpx, and a bench client
should not need a wheel. Concurrency is threads over urllib; each request streams, so time to
first token is measured in the worker thread at the moment the first content chunk lands, with
no event-loop scheduling between the socket and the clock.

Per request it records:
  ttft_s        wall from send to the first chunk carrying content
  decode_tok_s  (tokens - 1) / (t_last_chunk - t_first_chunk), i.e. the generation phase only,
                with prefill excluded. Tokens come from the server's own usage block when
                stream_options.include_usage is honoured, else from the chunk count.
  wall_s        send to final chunk

The client runs ON the server box, so LAN latency is not in ttft. One warm-up round is discarded
(it pays for prompt-cache and CUDA-graph warm state), then N rounds are measured. Every round
fires all N requests at once with a barrier, so the level is genuinely concurrent rather than
staggered.
"""
import argparse, json, statistics as st, threading, time, urllib.request, subprocess, sys

PROMPT = (
    "I'm working through a problem set for my introductory statistics course and I'm stuck on one "
    "question. The question gives me a sample of 40 students' exam scores with a sample mean of 73.2 "
    "and a sample standard deviation of 11.4, and asks me to construct a 95 percent confidence "
    "interval for the population mean. I know I need to use the t-distribution because the population "
    "standard deviation is unknown, and I found the critical value is about 2.023 for 39 degrees of "
    "freedom. Where I'm getting confused is the standard error. Do I divide the sample standard "
    "deviation by the square root of 40, or by 39? My textbook uses n in one example and n minus 1 in "
    "another and I can't work out which applies here. Could you explain which one is correct and why, "
    "and then walk through the full calculation step by step so I can check my arithmetic against yours?"
)

def one_request(host, port, model, max_tokens, temp, out, idx, barrier):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": max_tokens, "temperature": temp, "stream": True,
        "stream_options": {"include_usage": True},
        # Both models are hybrid thinking models. With --jinja and thinking left on, llama.cpp
        # streams the chain of thought as delta.reasoning_content and the whole 256-token budget
        # is spent before any answer appears — the first run of this bench measured nothing at all
        # for exactly that reason. A student turn that returns no answer is not the workload, so
        # thinking is off, matching the convention the intent-split work on this site already uses.
        "chat_template_kwargs": {"enable_thinking": False},
    }).encode()
    req = urllib.request.Request(f"http://{host}:{port}/v1/chat/completions", body,
                                 {"Content-Type": "application/json"})
    barrier.wait()                      # fire together
    t0 = time.perf_counter()
    t_first = t_last = None
    chunks = 0
    reasoning = 0
    usage = None
    try:
        with urllib.request.urlopen(req, timeout=1200) as r:
            for raw in r:
                if not raw.startswith(b"data: "):
                    continue
                payload = raw[6:].strip()
                if payload == b"[DONE]":
                    break
                try:
                    d = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                if d.get("usage"):
                    usage = d["usage"]
                ch = d.get("choices") or []
                delta = (ch[0].get("delta") or {}) if ch else {}
                # Count either field. reasoning_content should be empty with thinking off, but a
                # counter that only watches one field reports zero instead of reporting a problem.
                piece = delta.get("content") or delta.get("reasoning_content")
                if piece:
                    if delta.get("reasoning_content"):
                        reasoning += 1
                    now = time.perf_counter()
                    if t_first is None:
                        t_first = now
                    t_last = now
                    chunks += 1
    except Exception as e:
        out[idx] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        return
    t_end = time.perf_counter()
    if t_first is None:
        out[idx] = {"ok": False, "error": "no content chunks"}
        return
    toks = (usage or {}).get("completion_tokens") or chunks
    gen_s = max(t_last - t_first, 1e-9)
    out[idx] = {"ok": True, "ttft_s": round(t_first - t0, 4), "wall_s": round(t_end - t0, 4),
                "tokens": toks, "chunks": chunks, "reasoning_chunks": reasoning,
                "decode_tok_s": round((toks - 1) / gen_s, 3) if toks > 1 else 0.0,
                "gen_s": round(gen_s, 4), "usage": usage}

def run_round(host, port, model, n, max_tokens, temp):
    out = [None] * n
    barrier = threading.Barrier(n)
    ths = [threading.Thread(target=one_request,
                            args=(host, port, model, max_tokens, temp, out, i, barrier))
           for i in range(n)]
    t0 = time.perf_counter()
    for t in ths: t.start()
    for t in ths: t.join()
    return out, time.perf_counter() - t0

def gpu():
    q = "memory.used,power.draw,temperature.gpu,clocks.sm,utilization.gpu"
    r = subprocess.run(["nvidia-smi", f"--query-gpu={q}", "--format=csv,noheader,nounits"],
                       capture_output=True, text=True).stdout.strip().split(", ")
    return {"vram_mib": int(r[0]), "power_w": float(r[1]), "temp_c": int(r[2]),
            "sm_mhz": int(r[3]), "util": int(r[4])}

class Sampler(threading.Thread):
    """1 s GPU sampler; board power is the mean over samples taken while the round is in flight."""
    def __init__(self): super().__init__(daemon=True); self.rows=[]; self.stop=threading.Event()
    def run(self):
        while not self.stop.is_set():
            try: self.rows.append(gpu())
            except Exception: pass
            self.stop.wait(1.0)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1"); ap.add_argument("--port", type=int, default=8081)
    ap.add_argument("--n", type=int, required=True, help="concurrent requests; set equal to -np")
    ap.add_argument("--rounds", type=int, default=3); ap.add_argument("--warmup", type=int, default=1)
    ap.add_argument("--max-tokens", type=int, default=256); ap.add_argument("--temp", type=float, default=0.7)
    ap.add_argument("--model", default="local"); ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rec = {"tag": a.tag, "n": a.n, "rounds": a.rounds, "warmup": a.warmup,
           "max_tokens": a.max_tokens, "temperature": a.temp,
           "prompt_chars": len(PROMPT), "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "idle_before": gpu(), "warmup_rounds": [], "measured_rounds": []}
    for w in range(a.warmup):
        out, wall = run_round(a.host, a.port, a.model, a.n, a.max_tokens, a.temp)
        ok = [r for r in out if r and r.get("ok")]
        rec["warmup_rounds"].append({"wall_s": round(wall,3), "ok": len(ok), "n": a.n})
        print(f"  warm-up {w+1}: {len(ok)}/{a.n} ok in {wall:.1f}s", flush=True)
    for rnd in range(a.rounds):
        s = Sampler(); s.start()
        out, wall = run_round(a.host, a.port, a.model, a.n, a.max_tokens, a.temp)
        s.stop.set(); s.join(timeout=3)
        ok = [r for r in out if r and r.get("ok")]
        load = [g for g in s.rows if g["util"] >= 20] or s.rows
        row = {"round": rnd+1, "wall_s": round(wall,3), "ok": len(ok), "n": a.n,
               "requests": out, "gpu_samples": s.rows,
               "power_w_mean": round(st.mean([g["power_w"] for g in load]),1) if load else None,
               "power_w_max": max([g["power_w"] for g in load]) if load else None,
               "vram_peak_mib": max([g["vram_mib"] for g in s.rows]) if s.rows else None}
        if ok:
            dec = [r["decode_tok_s"] for r in ok]; ttft = [r["ttft_s"] for r in ok]
            row.update({"decode_mean": round(st.mean(dec),2), "decode_worst": round(min(dec),2),
                        "ttft_mean": round(st.mean(ttft),3),
                        "ttft_p95": round(sorted(ttft)[max(0,int(len(ttft)*0.95)-1)],3),
                        "tokens_total": sum(r["tokens"] for r in ok),
                        "aggregate_tok_s": round(sum(r["tokens"] for r in ok)/wall,2)})
            print(f"  round {rnd+1}: decode mean {row['decode_mean']} worst {row['decode_worst']} "
                  f"tok/s | ttft mean {row['ttft_mean']}s p95 {row['ttft_p95']}s | agg "
                  f"{row['aggregate_tok_s']} tok/s | {row['power_w_mean']}W | VRAM {row['vram_peak_mib']}MiB", flush=True)
        else:
            print(f"  round {rnd+1}: ALL FAILED — {out[0]}", flush=True)
        rec["measured_rounds"].append(row)
    m = [r for r in rec["measured_rounds"] if r.get("ok")]
    if m:
        allok = [q for r in m for q in r["requests"] if q and q.get("ok")]
        dec = [q["decode_tok_s"] for q in allok]; ttft = [q["ttft_s"] for q in allok]
        rec["summary"] = {
            "requests": len(allok),
            "decode_tok_s_mean": round(st.mean(dec),2), "decode_tok_s_worst": round(min(dec),2),
            "ttft_s_mean": round(st.mean(ttft),3),
            "ttft_s_p95": round(sorted(ttft)[max(0,int(len(ttft)*0.95)-1)],3),
            "aggregate_tok_s": round(st.mean([r["aggregate_tok_s"] for r in m]),2),
            "power_w_mean": round(st.mean([r["power_w_mean"] for r in m if r["power_w_mean"]]),1),
            "vram_peak_mib": max(r["vram_peak_mib"] for r in m if r["vram_peak_mib"]),
            "interactive": st.mean(dec) >= 10.0}
    json.dump(rec, open(a.out,"w"), indent=1)
    print(f"  -> {a.out}", flush=True)

if __name__ == "__main__":
    main()
