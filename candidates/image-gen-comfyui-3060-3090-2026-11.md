# Image generation in ComfyUI on an RTX 3060 12 GB and an RTX 3090 24 GB: seconds per image and peak VRAM (pre-registration)

**LOCKED 2026-11-26.** Written 2026-11-25 and locked 2026-11-26, both at the desk. At lock nothing had been
downloaded, installed or run for this pre-reg. Every field that was marked "at lock" is filled from the HF repos at
the commits in the G4 file table, the model cards and the ComfyUI v0.46.0 source and bundled templates.
- Its sha256 is in the lock commit message and in `image-gen-comfyui-3060-3090-2026-11.md.sha256`.
- It's in the LOCKS allowlist of `sync-bench-results-mirror.sh`, so the public copy is byte-exact.
- Changes after this point are amendments (G11), appended below G11.

Machines are named, never addressed.

**Decisions recorded 2026-11-26 (Mark), before lock:**
- A4a and A5b stay in. Mark accepted the BFL licence on both repos on 2026-11-26; the token on Miu now gets 200 on
  every file (it got 403 earlier that day). Files, from the HF LFS metadata, re-hashed after download:
  - black-forest-labs/FLUX.1-dev @ 45d95c497444bbaebe766e1528792fc9158c0c3a: `flux1-dev.safetensors` 23,802,932,552 B,
    sha256 4610115bb0c89560703c892c59ac2742fa821e60ef5871b33493ba544683abd7; `ae.safetensors` 335,304,388 B,
    sha256 afc8e28272cd15db3919bacdb6918ce9c1ed22e96cb12c4d5ed0fba823529e38.
  - black-forest-labs/FLUX.2-klein-9B @ 1498bcb8aaebb230bae82c34b02ecc4087beebac: `flux-2-klein-9b.safetensors`
    18,157,185,168 B, sha256 0975d6b77b5f510b99547d6724a208e36527df654e8f6134f59ece3f9f30da58.
- C1-C3 are scored by fit: does the run complete with all transformer weights in VRAM? Two extra FLUX BF16 runs on the
  3090 at `--reserve-vram 4` and `6` (A4a-R4, A4a-R6). Peak MiB is still reported, but it isn't scored.
- A12 added: FLUX.2 dev, city96 Q4_K_S GGUF, 3090 only.
- A11 (upscale) stays in. A10 (video) moves to a later session.
- GGUF files come from city96 where city96 publishes the model. The record gives the publisher and sha256 of every file.
- Rig copies are deleted after the run, after a same-day sha256 match against LLM_repo (invariant (ae)).
- P2 no longer uses "school uniform"; the subject is an adult woman.
- ComfyUI stays pinned to v0.46.0. Any move is a labelled amendment.

**Decisions recorded 2026-11-26, second set (Mark), before lock and before any result:**
- A9 on the 3060 uses unsloth's Qwen-Image-2.1 GGUF (Q4_K_M), since city96 publishes none. The publisher and sha256
  are in the file table.
- A fourth FLUX BF16 budget is added: A4a-R2 (`--reserve-vram 2`, ≈22 GiB usable). With R4 and R6 that tests
  22 / 20 / 18 GiB, and C2 is scored directly by R2 (G8).
- The FLUX prediction "C3 understates narrowly" (low confidence) stands as written.
- **Transfer method (Tamanna has 31 GB free, so nothing lands on its disk):** each file is streamed through Tamanna
  into LLM_repo and hashed on both ends (G4). Transfers start only after T-2133 is done and its DDR4-3000 restore is
  logged, and none run while T-2133 is on.
- **G11 is amended before lock (pre-results):** the files and the harness must be in place before any arm runs, not
  before the lock. Measured runs start only on Mark's go, after T-2133.
- Text fixes made at lock: the G6 step 6 swap rule now reads as one rule; "staged in passes (G9)" now points to G7;
  every "at lock" field is filled.

**Why.** The image-gen refresh plan (`docs/drafts/image-gen-refresh-PLAN.md`, `9840d1d9`) found that we have **no image-
or video-generation records**. Every seconds-per-image and VRAM figure on 11 guides and the four tier pages is borrowed
or unsourced, and several contradict each other. This run replaces them with measured figures from both of our cards.
Group 1 of the plan (`fd1ee8ce`) already reworded the first-person claims, so this measurement isn't propping up any
claim that is still live.

## G1. Claims under test (the site's own, as published on 2026-11-25)

| # | Claim | Where |
|---|---|---|
| C1 | FLUX.1 dev at full precision needs **18-20 GB** | what-can-you-run-24gb-vram (image section) |
| C2 | ... needs **22 GB** | vram-requirements-local-llms L257 (frozen page, so this only goes on the held list) |
| C3 | ... needs **~24 GB** | what-can-you-run-16gb-vram L163 |
| C4 | 3090, FLUX.1 dev: FP16 **~15 s**, FP8 **~26 s** per image | what-can-you-run-24gb-vram L171-177 |
| C5 | 3090, FLUX.1 dev FP16 **12-15 s** (also "12-30") | flux-locally-complete-guide L104, L108 |
| C6 | 3090, FLUX.1 dev FP16 **~40 s**; 3060 FP8 **~400 s** | sdxl-vs-sd-1-5-vs-flux L70-74 |
| C7 | 12 GB card, FLUX.1 dev quantized: **60-80 s** per image | flux-locally-complete-guide L102, L498 |
| C8 | 3060: SD 1.5 **~4 s**, SDXL **~20 s**, Flux NF4 **~80 s** | what-can-you-run-12gb-vram L160-183 |
| C9 | SDXL in ComfyUI: **~8.2 s, ~9.2 GB peak** (no GPU named) | comfyui-vs-automatic1111-vs-fooocus L40-41, L239-254 |
| C10 | ControlNet: SDXL base **8-10 GB**, Flux total **20-22 GB** | controlnet-guide-beginners L69-74 |
| C11 | BFL: FLUX 3 Image Klein INT8 **runs on 8 GB** | bfl.ai/blog/flux-3-image-klein |
| C12 | Video, 3060: Wan 14B Q5 480p **10-15 min** per clip; 3090 = 4090 **+40-50%** | local-ai-video-generation L306, L310 |
| C13 | Upscaling, 3060: **3-6 s** per image | local-ai-upscaling-guide L113 |

**C1-C3 are three different answers to one question.** G8 says which one holds.

## G2. Questions

1. **Seconds per image:** how many seconds each model takes on each card at fixed settings.
2. **Peak VRAM:** the peak each model uses, and whether ComfyUI loads it **completely** or **partially** (offloading weights to system RAM).
3. **FLUX.1 dev at full precision:**
   - Does it fit on a 24 GB card?
   - Which of 18-20 / 22 / ~24 GB describes it? Scored by fit: whether the run completes with all transformer weights in
     VRAM at a 24 / 22 / 20 / 18 GiB budget (G8).
   - What is the speed cost of the FP8 and GGUF quants?
4. **The 8 GB claims:** do the "runs on 8 GB" models (FLUX 3 Klein INT8 per BFL, FLUX.2 klein 4B, and Z-Image GGUF per the community) complete with 8 GB usable? Tested on the 3060 with 4 GB reserved; see G5.
5. **FLUX.2 dev (32B) on a 24 GB card:** does city96's Q4_K_S GGUF (19.3 GB) run on the 3090, how fast, and does it
   load completely?
6. **3060 vs 3090 ratio:** the ratio between the cards for each model. It isn't a prediction target, only reported.

## G3. Machines

- **Rushuna (3060):**
  - RTX 3060 12 GB, i7-7700, 32 GB DDR4-2133, PCIe 3.0 x16.
  - Default power limit **170 W**, as last recorded (Strata hotrod record, 2026-11-20). It's re-read at the G6
    machine-state check, and a different value is an amendment before the first Rushuna arm.
  - Reserved for CC#3 until released.
- **Tamanna (3090):**
  - RTX 3090 24 GB, Ryzen 7 5700X, 64 GB DDR4-3000, PCIe 4.0 x16.
  - Power limit **420 W**, the default restored in record `4804b3d6`; persistence on.

**Cross-rig limits.**
- **CPU, RAM and PCIe differ.** Wherever ComfyUI offloads weights, the 3060/3090 ratio mixes the card with the platform.
  The record says so in every row where offload occurs (DDR4 confound, as noted for earlier records).
- **Rushuna's 32 GB of RAM** can't hold every model at once. Arms are staged in passes (G7), and an OOM in system RAM is
  recorded as such, not as a VRAM result.

## G4. Software (pinned at lock)

- **ComfyUI v0.46.0** (release 2026-11-18), commit `a277b5bf213e8a44fa34817b7770b54f86ef4cea`.
- **Python, PyTorch and CUDA runtime,** the same on both rigs:
  - CPython **3.13.18**, uv-managed (python-build-standalone 20261110). ComfyUI's README calls 3.13 "very well
    supported", and neither rig's system Python is used, so both run the same interpreter.
  - **torch 2.14.1+cu130** and **torchvision 0.29.1+cu130**, from `download.pytorch.org/whl/cu130`.
  - Why not torch 2.15.0: it ships only cu132 wheels. Both rigs run driver 580 (CUDA 13.0), and cu130 is the build
    that matches it. ComfyUI's README requires cu130 or later for 20-series and newer cards.
  - Everything else comes from v0.46.0's `requirements.txt` as pinned there. `pip freeze` from each rig goes in the
    record.
- **Install:** a fresh venv per rig under `~/comfy-2026-11/`.
- **Custom nodes:**
  - ComfyUI-GGUF (city96) at commit `6ea2651e7df66d7585f6ffee804b20e92fb38b8a` (2026-01-12, the latest at lock),
    for the GGUF arms (A4c, A4d, A9 on the 3060, A12).
  - Every other arm uses only native nodes.
  - The node list and commits go in the record.
- **Launch:** `python main.py --port 8188 --disable-auto-launch --preview-method none` (localhost only, the default).
  - Default VRAM mode (`--normalvram` implied).
  - No `--highvram`, `--lowvram`, `--cache-none` or attention overrides, except where G5 names them.
  - The attention backend ComfyUI selects is read from its startup log and recorded.
- **Workflows:** one API-format JSON per arm, committed with the harness before the run. Only the seed and the filename
  prefix vary between repeats.

**Model files.**
- **Transfer (decision 2026-11-26):** every file is streamed through Tamanna (faster HF pulls) into **LLM_repo**.
  Nothing is written to Tamanna's disk.
  - `curl` on Tamanna fetches `resolve/<commit>/<path>` at the commit in the file table below. It pipes the file
    through `tee` into `sha256sum` on Tamanna and over ssh to Miu.
  - Miu writes it under `LLM_repo/image-gen-2026-11/<publisher>/<repo>/<path>` and hashes it again from disk.
  - Both hashes must equal the file table's sha256, or the file is fetched again.
  - All of this happens before any arm runs (invariant (ae)).
- **Working copies:** rigs get them per pass (G7), and each copy is re-hashed on the rig before its arm.
- **Settings source:** model-card settings come from the card at the commit in the table. Where the card gives none
  for ComfyUI, or is gated and unread at lock, the setting comes from the template that ComfyUI v0.46.0 bundles
  (`comfyui-workflow-templates-json` 0.1.137). Each G5 row names the template it uses.
- **After the run, rig copies are deleted.** First, the same day, each copy's sha256 must match its LLM_repo entry
  (invariant (ae)), and the match is logged in the record. A copy that doesn't match is kept for Mark and reported, not deleted.
- **GGUF publisher:** city96 wherever city96 publishes the model. For any other publisher, the publisher's name and the
  file's sha256 go in the file table. Every GGUF row gives the publisher and the sha256.
- **ComfyUI is pinned to v0.46.0.** Moving to a later release, for any reason, is a labelled amendment made before the
  affected arm runs.
- **Total:** 37 files, 266,124,315,928 B (266.1 GB) including A12 and without video. LLM_repo had 2.3 TB free on
  2026-11-26. That's more than the 190-250 GB estimated in the draft.

**File table (fixed at lock).** The commit fixes the bytes: a repo commit pins each file's LFS pointer, and so its
sha256. The sizes and sha256 come from those pointers, read 2026-11-26.
- **Gated repos:** BFL's FLUX.1-dev, FLUX.2-klein-9B and flux-3-image-klein-comfy. Mark accepted the first two
  licences on 2026-11-26. For the third (rows 18-22), the commit already fixes the bytes, but the sha256 can't be read
  until the licence is accepted. It's then read from the pointer at the pinned commit and appended below G11 as
  fill-in F1, before the transfer. The table isn't edited after lock.
- **Juggernaut XL Ragnarok:** RunDiffusion doesn't publish it on HF. Row 3 is the KandooAI mirror (Kandoo on HF). Its
  sha256 matches the SHA256 that Civitai lists for RunDiffusion's own release (model 133005, version 1759168,
  `JuggernautXL_Ragnarok_ByRunDiffusion.safetensors`).

| # | Arms | Publisher / repo @ commit | Path | Bytes | sha256 |
|---|---|---|---|---:|---|
| 1 | A1 | SG161222/Realistic_Vision_V6.0_B1_noVAE @ `9a857a696b9aabbf509073e0aa55ec8200b6ef7d` | `Realistic_Vision_V6.0_NV_B1_fp16.safetensors` | 2,132,625,894 | `c48bfd159cd7a6507b128685e963c398fa72399cefafaf603781df50ce836cc7` |
| 2 | A1 | stabilityai/sd-vae-ft-mse-original @ `629b3ad3030ce36e15e70c5db7d91df0d60c627f` | `vae-ft-mse-840000-ema-pruned.safetensors` | 334,641,190 | `735e4c3a447a3255760d7f86845f09f937809baa529c17370d83e4c3758f3c75` |
| 3 | A2,A3 | Kandoo/Juggernaut-XL-Ragnarok @ `aa701fd414bf7810d7403342d645c404cd307459` | `juggernautXL_ragnarok.safetensors` | 7,105,350,162 | `dd08fa32f98d05a2443ca1419e46df1575a0811f6e3b246d9dd47ff20f5eb66a` |
| 4 | A3 | xinsir/controlnet-union-sdxl-1.0 @ `801a4a3fa3d4c936f4feea95b98607bc6726f80c` | `diffusion_pytorch_model_promax.safetensors` | 2,513,342,408 | `9fae2e50cb431bfcbe05822b59ec2228df545ef27f711dea8949e9f4ed9f7cdc` |
| 5 | A4a | black-forest-labs/FLUX.1-dev @ `45d95c497444bbaebe766e1528792fc9158c0c3a` | `flux1-dev.safetensors` | 23,802,932,552 | `4610115bb0c89560703c892c59ac2742fa821e60ef5871b33493ba544683abd7` |
| 6 | A4*,A7 | black-forest-labs/FLUX.1-dev @ `45d95c497444bbaebe766e1528792fc9158c0c3a` | `ae.safetensors` | 335,304,388 | `afc8e28272cd15db3919bacdb6918ce9c1ed22e96cb12c4d5ed0fba823529e38` |
| 7 | A4* | comfyanonymous/flux_text_encoders @ `6af2a98e3f615bdfa612fbd85da93d1ed5f69ef5` | `clip_l.safetensors` | 246,144,152 | `660c6f5b1abae9dc498ac2d21e1347d2abdb0cf6c0c0c8576cd796491d9a6cdd` |
| 8 | A4a | comfyanonymous/flux_text_encoders @ `6af2a98e3f615bdfa612fbd85da93d1ed5f69ef5` | `t5xxl_fp16.safetensors` | 9,787,841,024 | `6e480b09fae049a72d2a8c5fbccb8d3e92febeb233bbe9dfe7256958a9167635` |
| 9 | A4b-d | comfyanonymous/flux_text_encoders @ `6af2a98e3f615bdfa612fbd85da93d1ed5f69ef5` | `t5xxl_fp8_e4m3fn.safetensors` | 4,893,934,904 | `7d330da4816157540d6bb7838bf63a0f02f573fc48ca4d8de34bb0cbfd514f09` |
| 10 | A4b | Kijai/flux-fp8 @ `2ef6f85f9f4b94634f995ba0bfa84fd3ab865c1d` | `flux1-dev-fp8-e4m3fn.safetensors` | 11,901,525,888 | `47d8dbdc6da6e996ff31567476c0a549afd1a99554b20af2be57f0ccfa93aa36` |
| 11 | A4c | city96/FLUX.1-dev-gguf @ `3c60ac659f4b1f2ab3ca8bd4488272069b36a148` | `flux1-dev-Q5_K_S.gguf` | 8,285,267,232 | `aa76146ca0f1b09c67e0c3fcef18be3a375837ecd5aaa021d3e9ebc558bd68f9` |
| 12 | A4d | city96/FLUX.1-dev-gguf @ `3c60ac659f4b1f2ab3ca8bd4488272069b36a148` | `flux1-dev-Q4_K_S.gguf` | 6,805,988,640 | `75bb19459b5240c9f373b5af527584af15b675867fa142efadf7478d6abbf62b` |
| 13 | A5 | black-forest-labs/FLUX.2-klein-4B @ `e7b7dc27f91deacad38e78976d1f2b499d76a294` | `flux-2-klein-4b.safetensors` | 7,751,105,712 | `ec3d4e733a771f61c052fb4856c48b336c55eaf2c65487c2a1faeb9bbda7a343` |
| 14 | A5,A7 | Comfy-Org/Flux-2-Klein-4B @ `5b3abca5c0dc1ecd4eaf3340868d09063fc1c965` | `split_files/text_encoders/qwen_3_4b.safetensors` | 8,044,982,048 | `6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a` |
| 15 | A5,A5b | Comfy-Org/Flux-2-Klein-4B @ `5b3abca5c0dc1ecd4eaf3340868d09063fc1c965` | `split_files/vae/flux2-vae.safetensors` | 336,211,292 | `868fe7b343cc8f3a19dbcfcafbc3d5f888802be3f89bd81b65b3621a066ce8f3` |
| 16 | A5b | black-forest-labs/FLUX.2-klein-9B @ `1498bcb8aaebb230bae82c34b02ecc4087beebac` | `flux-2-klein-9b.safetensors` | 18,157,185,168 | `0975d6b77b5f510b99547d6724a208e36527df654e8f6134f59ece3f9f30da58` |
| 17 | A5b | Comfy-Org/Flux-2-Klein-9B @ `1138ce884c8e977cdacacbe779784fec4426bb3f` | `split_files/text_encoders/qwen_3_8b.safetensors` | 16,381,517,176 | `f0ff9239d56269ca1d05e5f86da6a79fac111af464955681f11c7ab0ec5ef6c1` |
| 18 | A6 | black-forest-labs/flux-3-image-klein-comfy @ `09192d1abae1e57e1a2fcbc5b701cd1d9e2abd51` | `diffusion_models/flux3-image-klein-int8-convrot.safetensors` | 5,827,874,779 | gated: read from this commit's LFS pointer once the licence is accepted |
| 19 | A6 | black-forest-labs/flux-3-image-klein-comfy @ `09192d1abae1e57e1a2fcbc5b701cd1d9e2abd51` | `diffusion_models/flux3-image-klein-bf16.safetensors` | 11,097,404,512 | gated: read from this commit's LFS pointer once the licence is accepted |
| 20 | A6 | black-forest-labs/flux-3-image-klein-comfy @ `09192d1abae1e57e1a2fcbc5b701cd1d9e2abd51` | `text_encoders/qwen3vl_4b_int8_convrot.safetensors` | 4,858,559,240 | gated: read from this commit's LFS pointer once the licence is accepted |
| 21 | A6 | black-forest-labs/flux-3-image-klein-comfy @ `09192d1abae1e57e1a2fcbc5b701cd1d9e2abd51` | `text_encoders/qwen3vl_4b_bf16.safetensors` | 8,875,719,408 | gated: read from this commit's LFS pointer once the licence is accepted |
| 22 | A6 | black-forest-labs/flux-3-image-klein-comfy @ `09192d1abae1e57e1a2fcbc5b701cd1d9e2abd51` | `vae/flux2-vae.safetensors` | 336,211,292 | gated: read from this commit's LFS pointer once the licence is accepted |
| 23 | A7 | Comfy-Org/Z-Image-Turbo @ `6fc90a3b1b653e935a0d175e260736de25b84df5` | `split_files/diffusion_models/z_image_turbo_bf16.safetensors` | 12,309,866,400 | `2407613050b809ffdff18a4ac99af83ea6b95443ecebdf80e064a79c825574a6` |
| 24 | A7b | alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union-2.1 @ `5155fc56d17821007d6f62ac192c09e0f0e72016` | `Z-Image-Turbo-Fun-Controlnet-Union-2.1-2602-8steps.safetensors` | 6,712,485,600 | `d1251cc7bc3486bc61d25c3be498ef394c31c85ddf4ee9137d2e933411f4a689` |
| 25 | A8 | circlestone-labs/Anima @ `6e0b2da2112573380abfb6a1435a60a994b254f2` | `split_files/diffusion_models/anima-aesthetic-v1.1.safetensors` | 4,182,230,656 | `3c1868387a3a1ff504bbb87c33678321965ead381fcf87afbd0264daa600c082` |
| 26 | A8 | circlestone-labs/Anima @ `6e0b2da2112573380abfb6a1435a60a994b254f2` | `split_files/text_encoders/qwen_3_06b_base.safetensors` | 1,192,135,096 | `cd2a512003e2f9f3cd3c32a9c3573f820bb28c940f73c57b1ddaa983d9223eba` |
| 27 | A8 | circlestone-labs/Anima @ `6e0b2da2112573380abfb6a1435a60a994b254f2` | `split_files/vae/qwen_image_vae.safetensors` | 253,806,246 | `a70580f0213e67967ee9c95f05bb400e8fb08307e017a924bf3441223e023d1f` |
| 28 | A9 | Comfy-Org/Qwen-Image-2.1 @ `aacf31a6d48e707f352ecba714cee0680da3479b` | `diffusion_models/qwen_image_2.1_bf16.safetensors` | 14,230,280,616 | `89f4158d066cc33906a199fca85634f766892dd78f49b6698dabf187ac86c4bc` |
| 29 | A9 | unsloth/Qwen-Image-2.1-GGUF @ `2c31ccd392b367a6637841a143813320a02dff55` | `qwen-image-2.1-Q4_K_M.gguf` | 4,199,565,024 | `631d532e7ca71e8d90a87c71d3699761a812039d22e3370e87498d87754660fe` |
| 30 | A9 | Comfy-Org/Qwen-Image-2.1 @ `aacf31a6d48e707f352ecba714cee0680da3479b` | `text_encoders/qwen3vl_8b_bf16.safetensors` | 17,534,334,616 | `68bdc82bc1b66851162ae656225e7e2068166b603db19bd5d5a3b90eb12669a9` |
| 31 | A9 | Comfy-Org/Qwen-Image-2.1 @ `aacf31a6d48e707f352ecba714cee0680da3479b` | `vae/qwen_image_2.1_vae_bf16.safetensors` | 675,509,688 | `bb21f7473051e1ac368515dd3f2e15cd44d7a11748ee8823e1ddca3e4876b7c9` |
| 32 | A11 | Comfy-Org/Real-ESRGAN @ `5fd49b7b278836f48af63ecd314d0f98ab336105` | `RealESRGAN_x4plus.safetensors` | 66,857,836 | `37f9a931c215f040aa6d50f711f2cb115f713c46df1d0d6469a8bd7bfe9a60bb` |
| 33 | A11 | Comfy-Org/SeedVR2 @ `df48879708206a403d2a61acd55578c2e80fd233` | `diffusion_models/seedvr2_3b_fp16.safetensors` | 6,784,268,336 | `98669fd2c06df5eca88baf68cd5c478775c8e61fc110e598c52b350145ea2660` |
| 34 | A11 | Comfy-Org/SeedVR2 @ `df48879708206a403d2a61acd55578c2e80fd233` | `vae/seedvr2_ema_vae_fp16.safetensors` | 501,324,814 | `20678548f420d98d26f11442d3528f8b8c94e57ee046ef93dbb7633da8612ca1` |
| 35 | A12 | city96/FLUX.2-dev-gguf @ `ade5d688ddab0d9cf4a5b01bf4321e01c115020d` | `flux2-dev-Q4_K_S.gguf` | 19,299,128,288 | `b9c1c8295ed044f54c3a9894a800e003b4ecc94bfb0f63192b68bafc232c2b27` |
| 36 | A12 | Comfy-Org/Flux-2-Dev @ `9630c1b4b6e690497ae0c19bb6b1b35d4ebedcb7` | `split_files/text_encoders/mistral_3_small_flux2_fp8.safetensors` | 18,034,640,095 | `e3467b7d912a234fb929cdf215dc08efdb011810b44bc21081c4234cc75b370e` |
| 37 | A12 | Comfy-Org/Flux-2-Dev @ `9630c1b4b6e690497ae0c19bb6b1b35d4ebedcb7` | `split_files/vae/flux2-vae.safetensors` | 336,213,556 | `d64f3a68e1cc4f9f4e29b6e0da38a0204fe9a49f2d4053f0ec1fa1ca02f9c4b5` |


## G5. Arms

Every arm uses a fixed seed, **20251125**, a fixed prompt from the set in G6, batch 1, and one image per run. Steps,
sampler, scheduler, CFG or guidance, and resolution are fixed per model as below.
- A1-A4 use the settings written in this table since the draft.
- The other arms use the card or template settings named in their row (G4, "Settings source").
- The card revision is the repo commit in the G4 file table. File numbers (#) refer to that table.

| Arm | Model and files | Settings | 3060 | 3090 | Closes |
|---|---|---|---|---|---|
| **A1 SD15** | Realistic Vision V6.0 B1 fp16 (#1) + sd-vae-ft-mse 840000 (#2; the noVAE build's card recommends this VAE) | 512×512, 25 steps, dpmpp_2m karras, CFG 7 | ✓ | ✓ | C8, photoreal L164, art-styles L530 |
| **A2 SDXL** | Juggernaut XL Ragnarok fp16 (#3) | 1024×1024, 30 steps, dpmpp_2m karras, CFG 5 | ✓ | ✓ | C8, C9, checkpoint pages, tier pages |
| **A3 SDXL+CN** | A2 + xinsir controlnet-union-sdxl-1.0 ProMax (#4), canny from the fixed control image `cn-canny-1024.png` | as A2, strength 0.7 | ✓ | ✓ | C10 (SDXL row) |
| **A4a FLUX-BF16** | FLUX.1 dev BF16 transformer (`flux1-dev.safetensors`, 23,802,932,552 B, #5) + t5xxl_fp16 (#8) + clip_l (#7) + ae (#6) | 1024×1024, 20 steps, euler simple, guidance 3.5 | — | ✓ | C1-C6 |
| **A4a-R2 / R4 / R6 FLUX-BF16, reduced budget** | as A4a | as A4a; ComfyUI started with `--reserve-vram 2` (≈22 GiB usable), `4` (≈20 GiB) or `6` (≈18 GiB) | — | ✓ | C1, C2 |
| **A4b FLUX-FP8** | Kijai flux1-dev-fp8-e4m3fn (#10, 11,901,525,888 B) + t5xxl_fp8_e4m3fn (#9) + clip_l (#7) + ae (#6) | as A4a | ✓ | ✓ | C4, C6, C7 |
| **A4c FLUX-Q5** | city96 flux1-dev-Q5_K_S.gguf (#11, 8,285,267,232 B), t5 fp8 (#9) + clip_l + ae | as A4a | ✓ | ✓ | C7 |
| **A4d FLUX-Q4** | city96 flux1-dev-Q4_K_S.gguf (#12, 6,805,988,640 B), t5 fp8 (#9) + clip_l + ae | as A4a | ✓ | ✓ | C7, C8 (NF4 stand-in; NF4 itself is Forge-only, so the record says so) |
| **A5 FLUX.2 klein 4B** (+ **A5b 9B** on the 3090 only) | A5: BFL `flux-2-klein-4b` BF16 (#13) + Comfy-Org `qwen_3_4b` (#14) + `flux2-vae` (#15). A5b: BFL `flux-2-klein-9b` BF16 (#16) + Comfy-Org `qwen_3_8b` BF16 (#17) + #15 | 1024×1024, 4 steps, CFG 1, euler, Flux2Scheduler (card: 4 steps, guidance 1.0; template `image_flux2_klein_text_to_image`) | ✓ (4B) | ✓ | 8 GB page, flux guide |
| **A6 FLUX 3 Image Klein** (distilled) | INT8: `flux3-image-klein-int8-convrot` (#18) + `qwen3vl_4b_int8_convrot` (#20), both rigs. BF16, 3090 only: `flux3-image-klein-bf16` (#19) + `qwen3vl_4b_bf16` (#21). Both use `flux2-vae` (#22). The template's Qwen3.5 9B prompt upsampler isn't used | 1024×1024, 15 steps, CFG 1, er_sde, simple (template `image_flux3_klein_distilled_t2i`; the card is gated and unread at lock) | ✓ (INT8) | ✓ (INT8, BF16) | C11; flux, photoreal, anime |
| **A7 Z-Image-Turbo** | Comfy-Org `z_image_turbo_bf16` (#23) + `qwen_3_4b` (#14) + ae (#6; Comfy-Org's `ae.safetensors` has the same sha256) | 1024×1024, 8 steps, CFG 1, res_multistep, simple, ModelSamplingAuraFlow shift 3 (template `image_z_image_turbo`; the card's diffusers example uses 9 steps = 8 DiT forwards, guidance 0) | ✓ | ✓ | photoreal, art-styles |
| **A7b Z-Image + Fun Union 2.1** | A7 + alibaba-pai `Z-Image-Turbo-Fun-Controlnet-Union-2.1-2602-8steps` (#24, the newest Union build), through native ModelPatchLoader + QwenImageDiffsynthControlnet, canny `cn-canny-1024.png` | as A7 (card: 8 steps for the 8-step builds), control strength 0.75 (card: optimal range 0.65-1.00) | ✓ | ✓ | controlnet |
| **A8 Anima** | circlestone `anima-aesthetic-v1.1` (#25) + `qwen_3_06b_base` (#26) + `qwen_image_vae` (#27) | 1024×1024, 30 steps, CFG 4, er_sde, simple (card: 512²-1536², 30-50 steps, CFG 4-5, er_sde "a reasonable default") | ✓ | ✓ | anime page |
| **A9 Qwen-Image-2.1** | 3090: Comfy-Org `qwen_image_2.1_bf16` (#28). 3060: unsloth `qwen-image-2.1-Q4_K_M.gguf` (#29, publisher unsloth; city96 publishes none), through ComfyUI-GGUF. Both: Comfy-Org `qwen3vl_8b_bf16` text encoder (#30) + `qwen_image_2.1_vae_bf16` (#31). The prompt-enhancer encoder isn't used | 1024×1024, 40 steps (card), CFG 1, euler, simple (template `image_qwen_image_2_1_t2i`; the card gives no CFG) | ✓ (GGUF) | ✓ (BF16) | photoreal, model chooser |
| **A11 upscale** | Comfy-Org `RealESRGAN_x4plus.safetensors` (#32); Comfy-Org `seedvr2_3b_fp16` (#33) + `seedvr2_ema_vae_fp16` (#34), native SeedVR2 nodes | fixed 1024×1024 input `up-in-1024.png` → 4x (ESRGAN), 2x (SeedVR2: 1 step, euler, simple, CFG 1, template `utility_seedvr2_3b_int8_upscale_image`) | ✓ | ✓ | C13, upscaling page |
| **A12 FLUX.2 dev Q4** | city96 `flux2-dev-Q4_K_S.gguf` (#35, 19,299,128,288 B) + Comfy-Org `mistral_3_small_flux2_fp8` (#36) + Comfy-Org flux2-dev `flux2-vae` (#37; different bytes from #15) | 1024×1024, 50 steps, FluxGuidance 4, euler, Flux2Scheduler (diffusers Flux2Pipeline defaults; the BFL card is gated and unread). No Turbo LoRA | — | ✓ | flux guide (FLUX.2 dev "doesn't fit"), G2 question 5 |

**8 GB variants (3060 only), for G2 question 4.** A5, A6 INT8, A7 and A4d are re-run with `--reserve-vram 4`, so ComfyUI
treats about 8 GB as usable.
- **Pass:** the image completes. Seconds per image are reported, and the arm notes whether weights were offloaded
  (ComfyUI log).
- **Limit:** this emulates an 8 GB card's memory budget, not its bandwidth or compute. The record says so.

**Not run.**
- **FLUX.2 dev BF16/FP8:** neither fits either card (the FP8 mixed file alone is 35.5 GB), so they aren't run. A12
  tests the Q4 GGUF on the 3090 instead.
- **A10 video (Wan 2.2, LTX-2.5):** moved to a later session with its own lock. C12 stays open.
- **A1111, Forge and Fooocus:** out of scope. C9 is checked only for ComfyUI.

## G6. Measurement protocol

**Machine state** (every rig, before the first arm and between passes):
- **GPU:** nvidia-smi shows 1 MiB used and no compute processes.
- **Persistence and power:** persistence mode on; power limit as in G3.
- **PCIe:** the link reaches its rated gen and width under load.
  - Rushuna: 3.0 x16. Tamanna: 4.0 x16.
  - Read during the warm-up, because idle cards drop to gen 1. Same gate as the llama.cpp locks.
- **No other GPU users,** no Ollama, and no other ComfyUI instance.
- **Free system RAM and swap** recorded.

**Per arm:**
1. Start ComfyUI fresh for each arm, so every arm cold-loads its models and no other arm's models are cached.
2. **Warm-up:** one run at the arm's settings, seed 20251125 + 99.
   - Its wall time is reported separately as *cold time*, which includes the model load.
   - Not scored.
3. **Scored runs:** three runs at seeds 20251125, +1 and +2.
4. **Seconds per image:** wall time from the `/prompt` POST to the websocket's `execution_success` for that prompt id.
   - Median of the three.
   - Also reported: the sampler's it/s (or s/it) from ComfyUI's progress output, and the VAE decode time if the log shows it.
5. **Peak VRAM:**
   - `nvidia-smi --query-gpu=memory.used --format=csv -lms 200` runs across the warm-up and scored runs.
   - Peak during the scored runs, in MiB.
   - Also reported: the ComfyUI log lines "loaded completely" or "loaded partially" per model, with the MB figures they print.
6. **Swap and system RAM:** swap-in and swap-out deltas per arm (vmstat) are reported. A timing cell is void only if
   swap-in exceeds 64 MiB during the scored runs (the A2 rule from the NariQ record). Smaller swap activity is
   reported and doesn't void.
7. **Outputs:**
   - PNGs saved and hashed.
   - Smoke check: the image isn't blank or black (mean pixel value outside 5-250) and matches the prompt subject by eye.
   - A failed smoke check voids the arm's quality, not its timing, and is reported.

**Prompts** (fixed, committed with the harness):
- **P1 photoreal:** "a portrait photo of an elderly fisherman mending a net on a wooden dock at golden hour, 85mm, shallow depth of field".
- **P2 anime:** "anime style, an adult woman in her thirties with silver hair, wearing a tailored charcoal jacket, standing on a rainy neon city street at night, looking at viewer, masterpiece, best quality".
  - Used for A8 Anima and A2 as a second prompt only if time allows; reported, not scored.
- **P3 control:** P1's subject on the canny edges of `cn-canny-1024.png`, which comes from a CC0 photo committed with its source URL.
- **Negative prompt** (SD 1.5/SDXL only): "blurry, lowres, watermark, text".

**Void rules.** An arm is void if:
- the process crashes, or an OOM occurs in VRAM or system RAM;
- a scored run differs from the median by more than 25%;
- or the PCIe gate fails.

A void arm is re-run once after a clean restart. If it fails again, it is reported as failed and the failure itself is
the result. An out-of-memory error is a result for the fit questions (G2 questions 3 and 4).

## G7. Order

- **Tamanna first** (it holds every arm): A1 → A2 → A3 → A4a → A4a-R2 → A4a-R4 → A4a-R6 → A4b → A4c → A4d → A5 → A5b → A6 → A7 → A7b → A8 → A9 → A11 → A12.
- **Then Rushuna,** in the same order without A4a, A4a-R2/R4/R6, A5b, A6 BF16 and A12, then the `--reserve-vram 4`
  variants.
- **Files are staged in passes** that fit the rig's free disk. Each pass's files are re-hashed on arrival.
  - Rushuna had 65 GB free as last recorded (Inkling 2 Mini machine state, 2026-11-25). Free space is re-read before
    each pass.
  - Tamanna had 31 GB free on 2026-11-26, so it's staged in passes too. A pass's rig copies are cleared only under
    the G4 deletion rule, after that pass's arms.

## G8. Predictions (written 2026-11-25, before any download or run)

Prediction bands are wide on purpose: we have no measured image-gen figure of our own. A prediction **hits** if the
measured median falls inside its band.

**FLUX.1 dev at full precision on the 3090 (A4a), which answers C1-C3:**
- **The weights alone are about 23.8 GB, which is 22.2 GiB.** That makes "22 GB" plausibly the weights counted in GiB,
  not the peak.
- **Scoring is by fit, not peak** (decision 2026-11-26). A run *fits* a budget if it completes and ComfyUI's log says
  the FLUX transformer "loaded completely" in every scored run. Budgets: full card (A4a, 24 GiB), `--reserve-vram 2`
  (A4a-R2, ≈22 GiB), `--reserve-vram 4` (A4a-R4, ≈20 GiB) and `--reserve-vram 6` (A4a-R6, ≈18 GiB). ComfyUI counts the reserve in GiB, so the budgets are
  GiB. The usable figure ComfyUI logs at startup is recorded for each run.
  - **C1 "18-20 GB" holds** if A4a-R6 fits (18 GiB is enough), and holds at its top end only if A4a-R4 fits but R6
    doesn't. It fails if neither fits.
  - **C2 "22 GB" holds** if A4a-R2 fits (22 GiB is enough). If R2 loads partially, C2 **understates** (the need is
    over 22 GiB). R2 decides C2 directly, so the draft's "unresolved" case no longer arises.
  - **C3 "~24 GB" holds** if A4a fits on the full card. If it loads partially there, C3 **understates** (the need is
    over 24 GiB).
  - Peak MiB, seconds per image and the "loaded partially" MB figures are reported for all four runs.
- **The weights alone are 22.2 GiB** (≈23.8 GB), more than either reduced budget.
- **P-F1 (high confidence):** A4a-R2, A4a-R4 and A4a-R6 all load partially, since the weights alone (22.2 GiB)
  exceed even the 22 GiB budget. So C1 fails and C2 understates.
- **P-F2 (low confidence):** A4a loads partially on the full card at least once, because 22.2 GiB of weights plus
  activations and the CUDA context come within about 1 GiB of 24 GiB. If it fits, C3 holds.
- **P-F3:** A4a-R2, R4 and R6 each run at least 1.3x slower than A4a, because of offload over PCIe 4.0.
- **Predicted outcome:** C1 fails, C2 understates (P-F1), C3 understates narrowly (low confidence, P-F2).

**Seconds per image (median of 3, warm):**

| Arm | 3060 band | 3090 band | Basis |
|---|---|---|---|
| A1 SD15 512², 25 steps | 2.5-5.5 s | 1.0-3.0 s | C8's ~4 s on the 3060 |
| A2 SDXL 1024², 30 steps | 17-32 s | 6-13 s | C8's ~20 s; C9's 8.2 s, if it was a 3090/4080-class card |
| A3 SDXL + Union | 1.1-1.5x A2 | 1.1-1.5x A2 | one extra ControlNet pass per step |
| A4a FLUX BF16 | — | 25-55 s | C6's ~40 s; offload would push it to the top of the band. **C4's ~15 s and C5's 12-15 s are predicted to fail** |
| A4b FLUX FP8 | 60-150 s | 18-35 s | C4's ~26 s; the 3060's 11.9 GB transformer won't fit in 12 GB alongside activations, so offload |
| A4c FLUX Q5_K_S | 50-110 s | 20-40 s | GGUF dequant overhead on the 3090; fits the 3060 without offload |
| A4d FLUX Q4_K_S | 45-100 s | 20-40 s | **C7's 60-80 s predicted to hold**; **C6's ~400 s predicted to fail** |
| A5 klein 4B (4 steps) | 4-15 s | 1.5-6 s | distilled, 4 steps |
| A6 FLUX 3 Klein INT8 | 5-25 s | 2-10 s | 15 steps, CFG 1 (one pass per step); band as drafted. A6 BF16 on the 3090 is reported, not predicted |
| A7 Z-Image-Turbo | 15-60 s | 4-15 s | 6B, ~9 steps; BF16 offloads on the 3060 |
| A8 Anima | 8-30 s | 3-12 s | 2B, 30 steps at CFG 4 (two passes per step); low confidence |
| A9 Qwen-Image-2.1 | 60-240 s (GGUF Q4_K_M) | 20-80 s (BF16) | 7B, 40 steps at CFG 1, plus an 8B VL text encoder |
| A11 ESRGAN 4x | 1-6 s | 0.5-3 s | **C13's 3-6 s predicted to hold**, at the band's top end |
| A12 FLUX.2 dev Q4_K_S | — | 60-240 s | 32B with GGUF dequant, 50 steps. Predicted to **load completely** (19.3 GB = 18.0 GiB), the text encoder unloaded after encoding |

**Peak VRAM, as ComfyUI chooses to hold weights:**
- **A2 SDXL:** 3090 7,500-11,500 MiB; 3060 7,000-11,000 MiB. **C9's ~9.2 GB predicted to hold** on the 3090.
- **A3 SDXL + Union:** +1,500-3,500 MiB over A2. **C10's SDXL 8-10 GB predicted to hold on the 3060.**
- **A4b FP8 on the 3060:** ComfyUI loads it partially (offload). That's the reason for its slow band.

**8 GB variants (3060 with 4 GB reserved):**
- **C11 (BFL: FLUX 3 Klein INT8 runs on 8 GB): predicted to hold.** It completes, with weights offloaded at most partially.
- **A5 klein 4B and A4d Q4:** predicted to complete.
- **A7 Z-Image BF16:** predicted to complete, with offload.

**Ratio (reported only):** 3090/3060 speed between 2.0x and 3.5x for arms that fit both cards without offload. Wider
where the 3060 offloads.

## G9. Scoring and what changes on the site

- **Each prediction:** hit or miss, reported in the record, no rescoring.
- **Each C claim:** holds or fails, against its measured cell.
- **Measured figures go into `benchmarks.json`** as firsthand rows (rig, ComfyUI version, settings, median and peak),
  then into the pages in the plan's order.
- **A claim that fails is corrected,** with an Updated line naming the original figure.
- **Pages quote and link the record;** they don't restate settings that differ from it.
- **The frozen page's C2 goes on the post-freeze list** with the result. It isn't edited before 2026-12-16.

## G10. Limits stated in advance

- **One build of one tool:** ComfyUI v0.46.0, default VRAM mode. Forge Neo, SwarmUI or a different attention backend can
  give different speed and different peak VRAM.
- **Peak VRAM is what ComfyUI chooses to keep resident, not the minimum a model needs.** ComfyUI caches whatever fits,
  so a 24 GB card shows a higher peak than a 12 GB card for the same model. The 8 GB variants answer the minimum
  question only by emulation (`--reserve-vram`), which doesn't reproduce an 8 GB card's bandwidth.
- **One seed set, one resolution and one prompt per model.** This isn't a quality comparison. The smoke check only
  rules out broken output.
- **Cross-rig ratios mix card and platform** (CPU, DDR4 speed, PCIe gen), most of all where weights offload.
- **Model-card settings change between revisions,** so the revision used is in the record.

## G11. Go conditions

*Amended before lock, 2026-11-26, pre-results (Mark).* The draft required the files and the harness before the lock.
They now come before any arm, because Tamanna's disk and the T-2133 run push the transfer to after the lock. The
file table fixes the bytes at lock either way.

1. **Lock:** every field marked "at lock" is filled and this file is locked (sha256 in the commit message and
   `.sha256`, plus the mirror LOCKS entry).
2. **Before any arm:**
   - every file in the G4 table is in LLM_repo, with its Tamanna stream hash and its Miu disk hash both equal to the
     table's sha256;
   - fill-in F1 (the gated flux-3-image-klein-comfy hashes, rows 18-22) is appended and committed;
   - the workflows, harness, prompts and the two input images are committed.
3. **No transfer or run while T-2133 is on.** Transfers start after Mark logs T-2133 done and the DDR4-3000 restore.
   Measured runs start only on Mark's go.
4. Mark schedules both rigs. CC#3 has released Rushuna, and no other session holds the GPUs.
5. Any deviation found after locking is handled as an amendment (A1, A2, …) before the affected arm runs. Results are
   never used to justify one.
