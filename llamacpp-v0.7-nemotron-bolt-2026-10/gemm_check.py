#!/usr/bin/env python3
"""Stock-card record for llamacpp-v0.7-nemotron-bolt-2026-10 (2026-11-03): no gpu-unlock on Tamanna.
cuBLAS GEMM via torch (voice-01 train env, not an esp32-llm env), 8192^3, FP16 in / FP32 accumulate
(allow_fp16_reduced_precision_reduction off), BF16, and TF32. 5 warm-ups then 20 timed. GA102 white paper Table 9:
RTX 3090 dense FP16 tensor 71 TFLOPS with FP32 accumulate (142 with FP16 accumulate). A stock card lands below 71;
gpu-unlock would put the FP16/FP32-acc figure near the FP16-acc rate (issue #196: +63% on a 3090)."""
import json, sys, time, torch
torch.backends.cuda.matmul.allow_fp16_reduced_precision_reduction = False
torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False
N = 8192
out = {"torch": torch.__version__, "cuda": torch.version.cuda, "device": torch.cuda.get_device_name(0), "n": N, "results": {}}
for name, dt, tf32 in (("fp16_in_fp32_acc", torch.float16, False), ("bf16_in_fp32_acc", torch.bfloat16, False), ("tf32", torch.float32, True)):
    torch.backends.cuda.matmul.allow_tf32 = tf32
    a = torch.randn(N, N, device="cuda", dtype=dt); b = torch.randn(N, N, device="cuda", dtype=dt)
    for _ in range(5): a @ b
    torch.cuda.synchronize(); t = time.perf_counter()
    for _ in range(20): c = a @ b
    torch.cuda.synchronize(); el = time.perf_counter() - t
    tf = 2 * N**3 * 20 / el / 1e12
    out["results"][name] = round(tf, 2); print(f"{name}: {tf:.2f} TFLOPS", flush=True)
    del a, b, c; torch.cuda.empty_cache()
json.dump(out, open(sys.argv[1], "w"), indent=1)
