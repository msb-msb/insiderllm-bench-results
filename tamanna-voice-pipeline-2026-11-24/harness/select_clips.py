"""Clip selection and padding for the voice-pipeline run (pre-registration section 3.3 and 3.2).

FLEURS rule (locked, as amended by A2 on 2026-11-24): per language, the first 10 rows of data/<lang>/test.tsv, in row
order, whose file duration num_samples / 16000 is between 4 and 10 s (inclusive) AND that contain at least one 10 ms
frame with RMS above -40 dBFS. A2 fixes the expected rows; this script asserts them. Files: google/fleurs @ 70bb2e84 in
LLM_repo/datasets/fleurs-en_us-de_de-test/ (hashes checked against its SHA256SUMS before this runs).

Speech-end offset (section 3.2): for FLEURS, the end of the last 10 ms frame whose RMS is above -40 dBFS. For EN
real, the lock fixes it at clip duration - 0.500 s (the clips were trimmed to exactly 0.5 s of trailing silence).

Padding (section 3.2): every clip gets 12 s of digital silence appended (exact zero samples, same rate and format,
no resampling, no requantisation), because Chromium's fake capture loops the file. FLEURS padded copies are 16 kHz
mono 32-bit float WAV, the dataset's own format; EN real padded copies stay 48 kHz mono 16-bit PCM, their locked
format. Sample values before the padding are bit-identical to the source in both cases.

Usage: select_clips.py FLEURS_DIR REAL_DIR OUT_DIR
Writes OUT_DIR/fleurs/*.wav, OUT_DIR/real/*.wav (padded) and OUT_DIR/clips.tsv.
"""
import csv, hashlib, io, pathlib, sys, tarfile

import numpy as np
import soundfile as sf

FLEURS, REAL, OUT = (pathlib.Path(a) for a in sys.argv[1:4])
PAD_S = 12.0
csv.field_size_limit(10**7)


def speech_end(x, sr):
    n = sr // 100
    m = len(x) // n * n
    db = 20 * np.log10(np.sqrt((x[:m].reshape(-1, n).astype(np.float64) ** 2).mean(1)) + 1e-12)
    idx = np.nonzero(db > -40)[0]
    return (idx[-1] + 1) * n / sr


def max_frame_db(x, sr):
    n = sr // 100
    m = len(x) // n * n
    return float((20 * np.log10(np.sqrt((x[:m].reshape(-1, n).astype(np.float64) ** 2).mean(1)) + 1e-12)).max())


A2_ROWS = {"en_us": [7, 23, 28, 42, 58, 60, 66, 68, 74, 80], "de_de": [4, 8, 11, 14, 15, 16, 17, 26, 29, 30]}


def pad_write(x, sr, path, subtype):
    y = np.concatenate([x, np.zeros(int(round(PAD_S * sr)), dtype=x.dtype)])
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, y, sr, subtype=subtype)
    return hashlib.sha256(path.read_bytes()).hexdigest(), len(y) / sr


rows_out = []
for lang, tag, set_ in (("en_us", "en", "fleurs_en"), ("de_de", "de", "fleurs_de")):
    with open(FLEURS / "data" / lang / "test.tsv", newline="") as f:
        cand = [(rowno, r) for rowno, r in enumerate(csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE), 1)
                if 4.0 <= int(r[5]) / 16000 <= 10.0]
    names = {r[1] for _, r in cand}
    got = {}
    with tarfile.open(FLEURS / "data" / lang / "audio" / "test.tar.gz", "r:gz") as tf:
        for m in tf:
            name = m.name.rsplit("/", 1)[-1]
            if name in names and name not in got:
                got[name] = tf.extractfile(m).read()
    assert names <= set(got), (lang, len(names - set(got)))
    picked, ordered = [], []  # ordered: every qualifying row in order (the A2 fallback list)
    for rowno, r in cand:
        x, sr = sf.read(io.BytesIO(got[r[1]]), dtype="float32")
        if max_frame_db(x, sr) > -40:
            ordered.append(rowno)
            if len(picked) < 10:
                picked.append((rowno, r))
    assert [rn for rn, _ in picked] == A2_ROWS[lang], (lang, [rn for rn, _ in picked])
    print(f"{lang}: {len(cand)} rows of 4-10 s, {len(ordered)} cross -40 dBFS; next qualifying rows after the 10: {ordered[10:15]}")
    want = {r[1]: (i, rowno, r) for i, (rowno, r) in enumerate(picked, 1)}
    for name, (i, rowno, r) in want.items():
        data = got[name]
        assert sf.info(io.BytesIO(data)).subtype == "FLOAT", name
        x, sr = sf.read(io.BytesIO(data), dtype="float32")
        assert sr == 16000 and x.ndim == 1 and len(x) == int(r[5]), (name, sr, x.shape, r[5])
        cid = f"{tag}{i:02d}"
        h, padded_s = pad_write(x, sr, OUT / "fleurs" / f"{cid}.wav", "FLOAT")
        rows_out.append(dict(clip_id=cid, set=set_, language="english" if tag == "en" else "german",
                             source=f"data/{lang}/test.tsv row {rowno}: {name} (id {r[0]})",
                             source_sha256=hashlib.sha256(data).hexdigest(), sr=sr,
                             clip_s=round(len(x) / sr, 3), speech_end_s=round(speech_end(x, sr), 3),
                             padded_s=round(padded_s, 3), padded_sha256=h, gender=r[6], reference=r[2]))

refs = (REAL / "questions.txt").read_text().splitlines()
for k in range(1, 6):
    src = REAL / f"q{k}.wav"
    x, sr = sf.read(src, dtype="int16")
    assert sf.info(src).subtype == "PCM_16", src
    h, padded_s = pad_write(x, sr, OUT / "real" / f"q{k}.wav", "PCM_16")
    rows_out.append(dict(clip_id=f"q{k}", set="en_real", language="english", source=f"inputs q{k}.wav (private)",
                         source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(), sr=sr,
                         clip_s=round(len(x) / sr, 3), speech_end_s=round(len(x) / sr - 0.5, 3),
                         padded_s=round(padded_s, 3), padded_sha256=h, gender="", reference=refs[k - 1]))

with open(OUT / "clips.tsv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows_out[0]), delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(rows_out)
for r in rows_out:
    print(r["clip_id"], r["clip_s"], r["speech_end_s"], r["reference"][:70])
