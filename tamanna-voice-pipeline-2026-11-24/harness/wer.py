"""WER for the voice-pipeline run (secondary measure). Pre-registration: docs/candidates/voice-pipeline-3090-2026-11.md.

Normalisers come from openai-whisper==20250625 (pinned), applied to reference AND hypothesis:
  English (FLEURS en_us, EN real): whisper.normalizers.EnglishTextNormalizer
  German  (FLEURS de_de):          whisper.normalizers.BasicTextNormalizer (Whisper's own non-English choice)
WER = jiwer 4.0.0 `wer` over the normalised strings, per clip, and corpus-level (all words pooled) per arm x set.
Pre-declared exclusion: EN real q3 ("their, there, and they're": homophones not resolvable from audio) is left out
of every WER figure. It stays in all timing, and its transcript is reported verbatim.
References: FLEURS `raw transcription` column of test.tsv; EN real = questions.txt line N for qN.

Only `whisper.normalizers` is loaded. The package __init__ (torch, numba, tiktoken) never runs, so the client venv
installs openai-whisper with --no-deps plus regex and more-itertools.

Usage: wer.py refs.tsv hyps.tsv out_prefix
  refs.tsv: clip_id <TAB> set (fleurs_en|fleurs_de|en_real) <TAB> reference
  hyps.tsv: clip_id <TAB> arm <TAB> hypothesis   (one measured pass: the first)
"""
import csv, importlib.util, json, pathlib, sys, types

import jiwer

_root = pathlib.Path(importlib.util.find_spec("whisper").submodule_search_locations[0])
_pkg = types.ModuleType("whisper")
_pkg.__path__ = [str(_root)]
sys.modules["whisper"] = _pkg
from whisper.normalizers import BasicTextNormalizer, EnglishTextNormalizer  # noqa: E402

NORM = {"fleurs_en": EnglishTextNormalizer(), "en_real": EnglishTextNormalizer(), "fleurs_de": BasicTextNormalizer()}
EXCLUDED = {"q3"}


def main(refs_path, hyps_path, out_prefix):
    refs = {r[0]: (r[1], r[2]) for r in csv.reader(open(refs_path), delimiter="\t")}
    per_clip, pooled = [], {}
    for clip, arm, hyp in csv.reader(open(hyps_path), delimiter="\t"):
        st, ref = refs[clip]
        row = {"clip": clip, "arm": arm, "set": st, "ref": ref, "hyp": hyp}
        if clip in EXCLUDED:
            row["wer"] = None
            row["note"] = "excluded by pre-declaration (homophones)"
        else:
            n = NORM[st]
            r, h = n(ref), n(hyp)
            row.update(ref_norm=r, hyp_norm=h, wer=jiwer.wer(r, h) if r else None)
            pooled.setdefault((arm, st), ([], []))
            pooled[(arm, st)][0].append(r)
            pooled[(arm, st)][1].append(h)
        per_clip.append(row)
    with open(out_prefix + "_per_clip.jsonl", "w") as f:
        for row in per_clip:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = {f"{a}|{s}": {"clips": len(r), "wer": round(jiwer.wer(r, h), 4)} for (a, s), (r, h) in sorted(pooled.items())}
    json.dump(summary, open(out_prefix + "_summary.json", "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
