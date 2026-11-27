# Image-gen lock: file transfer into LLM_repo (2026-11-26)

Lock: `docs/candidates/image-gen-comfyui-3060-3090-2026-11.md` (lock `eaf6324d`, F1 appended `eb7d3427`).
This is the G4 transfer and the first half of G11 item 2.

- **Window:** 13:38:16 to 18:08:25 PST. That was before T-2133, which Mark had postponed (F1 note). No run happened
  during it.
- **Method:** `stream-2026-11-26.py`, 4 files at a time.
  - curl on Tamanna streams each file at the pinned commit over ssh into
    `LLM_repo/image-gen-2026-11/<publisher>/<repo>/<path>` on Miu.
  - Tamanna hashes the stream and Miu hashes the file on disk. Nothing was written to Tamanna's disk: it had 31 GB
    free before and after.
- **Result:** 37 of 37 files OK on the first try, with no retries. That's 266,124,315,928 B, 36 distinct files, since
  rows 15 and 22 are the same bytes. Every Tamanna stream hash and Miu disk hash equals the sha256 in the lock's file
  table (plus F1).
  - Re-checked after the run against `manifest-2026-11-26.json`, which holds the table's rows: size, marker and both
    hashes match for all 37 (0 bad).
- **Files:** `stream-2026-11-26.log` has one line per file. `verified-markers.txt` holds the per-file markers as
  written next to each file in LLM_repo.

**Still open before any arm (G11 item 2):** the workflows, harness, prompts and the two input images. Each rig's
working copies are re-hashed on arrival (G4, G7). Measured runs wait for Mark's go.
