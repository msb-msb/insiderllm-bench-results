"""Per-arm analysis for the voice-pipeline run (pre-registration sections 3.2, 3.3, 4; amendments A1, A2, A3).

Inputs per arm, under RUN/<ARM>/ (Miu copy of Tamanna's folder plus the client logs):
  client-{1,2,3}.jsonl     Playwright records (client-warmup.jsonl is discarded, never read here)
  clock.json               Miu-Tamanna clock offset, measured at arm start (tamanna_wall - miu_wall, seconds)
  llm.log, stt.log         llama-server logs: '# wall_start' header, then per-task print_timing lines
  stt_s2.jsonl, tts.jsonl  wrapper logs (one line per request)
  vram.csv, meta.json      10 Hz sampler; serve.py's record of warm-ups, fit trials, -ncmoe, A1 reading

Per clip (window = this clip's start .. next clip's start, on Tamanna's clock):
  STT ms      S1/S3: the window's first STT task, print_timing 'total time' (prompt eval incl. the audio encoder,
              plus decode): llama-server's own `timings`. S2: the window's first stt_s2.jsonl line, total_ms
              (read + ffmpeg decode + inference); infer_ms is reported beside it. llama-server's file decode runs
              before the task starts and is not in its figure; the record says so.
  LLM TTFT    the window's first LLM task after the STT request: 'prompt eval time'.
  LLM first   TTFT + first-sentence tokens x the task's mean decode ms/token (first sentence = text up to the first
  sentence    [.!?] followed by whitespace, Open WebUI's punctuation split; tokens counted with the server's
              /tokenize). Capped at the task's total time.
  TTS first   the window's first tts.jsonl line, total_ms (generation + mp3 encode).
  Residual    E2E - STT - LLM first sentence - TTS first (section 3.2).
Aggregates: median and p90 (numpy 'linear') per arm x set over the 3 measured passes. VRAM: per-process peak over
the arm (ready .. last clip), and the per-tick total. WER: harness/wer.py on pass 1, hypotheses exactly as Open WebUI
delivered them (the chat's user turn). A3: for S1, hyps.tsv holds the hypotheses with the Qwen3-ASR prefix stripped
by S1_PREFIX (primary S1 WER) and hyps-unstripped.tsv the hypotheses as delivered (locked scoring, reported beside
it); per_clip.tsv records whether the delivered transcript still carried the prefix.

Usage: analyze.py RUNDIR ARM  -> writes RUNDIR/<ARM>/per_clip.tsv, summary.json, refs.tsv, hyps.tsv
"""
import csv, json, pathlib, re, statistics, sys

import numpy as np

RUN, ARM = pathlib.Path(sys.argv[1]), sys.argv[2]
D = RUN / ARM
S1_PREFIX = re.compile(r"^\s*language [A-Za-z]+<asr_text>")  # A3 item 2, S1 only: S1_PREFIX.sub("", hyp, count=1)
TS = re.compile(r"^(\d+)\.(\d{2})\.(\d{3})\.(\d{3}) ")


def llama_tasks(path):
    """[{wall_launch, prompt_ms, prompt_tok, eval_ms, eval_tok, total_ms}] from a llama-server log."""
    if not path.exists():
        return []
    wall0, tasks, cur = None, [], {}
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith("# wall_start"):
            wall0 = float(line.split()[2])
            continue
        m = TS.match(line)
        if not m:
            continue
        rel = int(m[1]) * 60 + int(m[2]) + int(m[3]) / 1e3 + int(m[4]) / 1e6
        tid = re.search(r"task (\d+)", line)
        if "launch_slot_" in line and tid:
            cur[tid[1]] = {"task": int(tid[1]), "wall_launch": wall0 + rel}
        elif "print_timing" in line and tid and tid[1] in cur:
            t = cur[tid[1]]
            g = re.search(r"prompt eval time =\s+([\d.]+) ms /\s+(\d+) tokens", line)
            if g:
                t["prompt_ms"], t["prompt_tok"] = float(g[1]), int(g[2])
            g = re.search(r"\beval time =\s+([\d.]+) ms /\s+(\d+) tokens", line)
            if g and "prompt" not in line:
                t["eval_ms"], t["eval_tok"] = float(g[1]), int(g[2])
            g = re.search(r"total time =\s+([\d.]+) ms", line)
            if g:
                t["total_ms"] = float(g[1])
                tasks.append(t)
    return tasks


def jsonl(path):
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()] if path.exists() else []


def q(v, p):
    v = [x for x in v if x is not None]
    return round(float(np.percentile(v, p)), 1) if v else None


off = json.loads((D / "clock.json").read_text())["tamanna_minus_miu_s"]
meta = json.loads((D / "meta.json").read_text())
clips = []
for p in ("1", "2", "3"):
    clips += [r for r in jsonl(D / f"client-{p}.jsonl")]
clips.sort(key=lambda r: r["wall_clip_start"])
llm = llama_tasks(D / "llm.log")
stt = llama_tasks(D / "stt.log") if ARM in ("S1", "S3") else jsonl(D / "stt_s2.jsonl")
tts = jsonl(D / "tts.jsonl")

rows = []
for i, c in enumerate(clips):
    lo = c["wall_clip_start"] + off
    hi = clips[i + 1]["wall_clip_start"] + off if i + 1 < len(clips) else float("inf")
    r = {k: c.get(k) for k in ("pass", "clip_id", "set", "ok", "e2e_ms", "speech_end_s", "first_sentence_tokens",
                               "reply_tokens", "transcript", "reply", "error")}
    t_stt = None
    if ARM in ("S1", "S3"):
        s = [t for t in stt if lo <= t["wall_launch"] < hi]
        if s:
            r["stt_ms"], t_stt = s[0]["total_ms"], s[0]["wall_launch"]
            r["stt_prompt_tokens"] = s[0].get("prompt_tok")
    elif ARM == "S2":
        s = [t for t in stt if lo <= t["wall_recv"] < hi]
        if s:
            r["stt_ms"], r["stt_infer_ms"], t_stt = s[0]["total_ms"], s[0]["infer_ms"], s[0]["wall_recv"]
    L = [t for t in llm if (t_stt or lo) <= t["wall_launch"] < hi]
    if L:
        t = L[0]
        per_tok = t["eval_ms"] / t["eval_tok"] if t.get("eval_tok") else None
        r["llm_ttft_ms"] = t["prompt_ms"]
        r["llm_prompt_tokens"] = t["prompt_tok"]
        r["llm_decode_tok_s"] = round(1e3 / per_tok, 2) if per_tok else None
        if per_tok is not None and c.get("first_sentence_tokens") is not None:
            r["llm_first_sentence_ms"] = round(min(t["prompt_ms"] + c["first_sentence_tokens"] * per_tok, t["total_ms"]), 1)
        r["llm_tasks_in_window"] = len(L)
    T = [t for t in tts if lo <= t["wall_recv"] < hi]
    if T:
        r["tts_first_ms"], r["tts_first_chars"], r["tts_requests_in_window"] = T[0]["total_ms"], T[0]["chars"], len(T)
    if ARM != "R0" and all(r.get(k) is not None for k in ("e2e_ms", "stt_ms", "llm_first_sentence_ms", "tts_first_ms")):
        r["residual_ms"] = round(r["e2e_ms"] - r["stt_ms"] - r["llm_first_sentence_ms"] - r["tts_first_ms"], 1)
    if ARM == "S1":
        r["s1_prefix_delivered"] = bool(S1_PREFIX.match(c.get("transcript") or ""))
    rows.append(r)

cols = ["pass", "clip_id", "set", "ok", "e2e_ms", "stt_ms", "stt_infer_ms", "llm_ttft_ms", "llm_first_sentence_ms",
        "tts_first_ms", "residual_ms", "stt_prompt_tokens", "s1_prefix_delivered", "llm_prompt_tokens", "llm_decode_tok_s", "first_sentence_tokens", "reply_tokens",
        "llm_tasks_in_window", "tts_requests_in_window", "speech_end_s", "transcript", "reply", "error"]
with open(D / "per_clip.tsv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: (str(v).replace("\t", " ").replace("\n", " ") if v is not None else "") for k, v in r.items()})

summary = {"arm": ARM, "ncmoe": meta.get("ncmoe"), "free_mib": meta.get("free_mib"),
           "stt_peak_mib_warmup": meta.get("stt_peak_mib"), "tts_peak_mib_warmup": meta.get("tts_peak_mib"),
           "a1": meta.get("a1_reading"), "n_clips": len(rows), "n_failed": sum(1 for r in rows if not r.get("ok")),
           "sets": {}}
for s in ("fleurs_en", "fleurs_de", "en_real"):
    rs = [r for r in rows if r.get("set") == s and r.get("ok")]
    summary["sets"][s] = {"n": len(rs)} | {
        f"{k}_{lab}": q([r.get(k) for r in rs], p)
        for k in ("e2e_ms", "stt_ms", "stt_infer_ms", "llm_ttft_ms", "llm_first_sentence_ms", "tts_first_ms",
                  "residual_ms", "llm_decode_tok_s", "reply_tokens")
        for lab, p in (("median", 50), ("p90", 90))}

# VRAM over the arm: from READY to the last clip's close.
t0 = meta.get("wall_ready", 0)
t1 = max((c.get("wall_closed") or c["wall_clip_start"]) for c in clips) + off if clips else float("inf")
per_pid, ticks = {}, []
cur_t, cur = None, 0
for line in (D / "vram.csv").read_text().splitlines()[1:]:
    t, pid, mib = line.split(",")
    t, pid, mib = float(t), int(pid), int(mib)
    if not (t0 <= t <= t1):
        continue
    per_pid[pid] = max(per_pid.get(pid, 0), mib)
    if cur_t is None or t - cur_t > 0.05:
        if cur_t is not None:
            ticks.append(cur)
        cur_t, cur = t, 0
    cur += mib
if cur_t is not None:
    ticks.append(cur)
pids = {n: int((D / f"{n}.pid.final").read_text()) for n in ("llm", "stt", "tts") if (D / f"{n}.pid.final").exists()}
summary["vram_peak_mib"] = {n: per_pid.get(p) for n, p in pids.items()} | {"total": max(ticks) if ticks else None,
                                                                            "all_pids": per_pid}
(D / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))

# WER inputs: pass 1, hypotheses as delivered.
if ARM != "R0":
    refs = {r["clip_id"]: r for r in csv.DictReader(open(RUN / "clips" / "clips.tsv"), delimiter="\t")}
    g2 = open(D / "hyps-unstripped.tsv", "w") if ARM == "S1" else None
    with open(D / "refs.tsv", "w") as f, open(D / "hyps.tsv", "w") as g:
        for r in rows:
            if r.get("pass") == "1" and r.get("ok"):
                hyp = (r.get("transcript") or "").replace(chr(9), " ").replace(chr(10), " ")
                f.write(f"{r['clip_id']}\t{refs[r['clip_id']]['set']}\t{refs[r['clip_id']]['reference']}\n")
                g.write(f"{r['clip_id']}\t{ARM}\t{S1_PREFIX.sub('', hyp, count=1) if ARM == 'S1' else hyp}\n")
                if g2:
                    g2.write(f"{r['clip_id']}\t{ARM}\t{hyp}\n")
    if g2:
        g2.close()
    summary["s1_prefix_delivered"] = sum(1 for r in rows if r.get("s1_prefix_delivered")) if ARM == "S1" else None
    (D / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
print(json.dumps(summary["sets"], indent=1)[:3000])
