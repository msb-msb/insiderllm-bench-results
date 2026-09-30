---
license: mit
library_name: transformers
pipeline_tag: text-generation
tags:
- dflash
- speculative-decoding
- diffusion
- efficiency
- flash-decoding
- qwen
- diffusion-language-model
---

# Qwen3.5-27B-DFlash
[**Paper**](https://arxiv.org/abs/2602.06036) | [**GitHub**](https://github.com/z-lab/dflash) | [**Blog**](https://z-lab.ai/projects/dflash/)

**DFlash** is a novel speculative decoding method that utilizes a lightweight **block diffusion** model for drafting. It enables efficient, high-quality parallel drafting that pushes the limits of inference speed.

This model is the **drafter** component. It must be used in conjunction with the target model `Qwen/Qwen3.5-27B`. It was trained with a context length of 4096 tokens.

<div align="center">
  <img src="assets/dflash_system.png" alt="DFlash Architecture" width="100%">
</div>

## Quick Start

### Installation

vLLM:
```bash
uv pip install vllm
uv pip install -U vllm --torch-backend=auto --extra-index-url https://wheels.vllm.ai/nightly
```

SGLang:
```bash
uv pip install "git+https://github.com/sgl-project/sglang.git@refs/pull/20547/head#subdirectory=python"
```

### Launch Server

vLLM:
```bash
vllm serve Qwen/Qwen3.5-27B \
  --speculative-config '{"method": "dflash", "model": "z-lab/Qwen3.5-27B-DFlash", "num_speculative_tokens": 15}' \
  --attention-backend flash_attn \
  --max-num-batched-tokens 32768
```

SGLang:
```bash
# Optional: enable schedule overlapping (experimental, may not be stable)
# export SGLANG_ENABLE_SPEC_V2=1
# export SGLANG_ENABLE_DFLASH_SPEC_V2=1
# export SGLANG_ENABLE_OVERLAP_PLAN_STREAM=1

python -m sglang.launch_server \
    --model-path Qwen/Qwen3.5-27B \
    --speculative-algorithm DFLASH \
    --speculative-draft-model-path z-lab/Qwen3.5-27B-DFlash \
    --speculative-num-draft-tokens 16 \
    --tp-size 1 \
    --attention-backend fa3 \
    --mem-fraction-static 0.75 \
    --mamba-scheduler-strategy extra_buffer \
    --trust-remote-code
```
> **Tip:** For long-context or agentic workloads, add `--speculative-dflash-draft-window-size WINDOW_SIZE` to enable sliding-window attention for the drafter.

### Usage

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:30000/v1", api_key="EMPTY")

response = client.chat.completions.create(
    model="Qwen/Qwen3.5-27B",
    messages=[{"role": "user", "content": "Write a quicksort in Python."}],
    max_tokens=4096,
    temperature=0.0
)
print(response.choices[0].message.content)
```

## Benchmark Results

**Setup:** Single NVIDIA B200, SGLang, thinking enabled, max output length 4096. We report end-to-end throughput, including prefill time. See our [GitHub repository](https://github.com/z-lab/dflash) for reproduction scripts.

### Throughput and Speedup

_Tokens/sec (speedup vs. autoregressive baseline)_

**Block Size = 16**

| Task | Concurrency | AR | MTP | **DFlash** |
|---|---:|---:|---:|---:|
| Math500 | 1 | 84 | 243 (2.9x) | **397 (4.7x)** |
| | 8 | 625 | 1457 (2.3x) | **2270 (3.6x)** |
| | 16 | 1121 | 2224 (2.0x) | **3135 (2.8x)** |
| | 32 | 1949 | 2504 (1.3x) | **3712 (1.9x)** |
| GSM8K | 1 | 83 | 215 (2.6x) | **330 (4.0x)** |
| | 8 | 625 | 1303 (2.1x) | **1868 (3.0x)** |
| | 16 | 1109 | 1773 (1.6x) | **2589 (2.3x)** |
| | 32 | 1914 | 2170 (1.1x) | **3152 (1.6x)** |
| HumanEval | 1 | 83 | 236 (2.9x) | **427 (5.2x)** |
| | 8 | 602 | 1345 (2.2x) | **2079 (3.5x)** |
| | 16 | 1031 | 1921 (1.9x) | **2748 (2.7x)** |
| | 32 | 1720 | 2234 (1.3x) | **3198 (1.9x)** |
| MBPP | 1 | 84 | 200 (2.4x) | **347 (4.2x)** |
| | 8 | 627 | 1049 (1.7x) | **1826 (2.9x)** |
| | 16 | 1075 | 1729 (1.6x) | **2479 (2.3x)** |
| | 32 | 1832 | 1933 (1.1x) | **2808 (1.5x)** |
| MT-Bench | 1 | 84 | 169 (2.0x) | **255 (3.0x)** |
| | 8 | 622 | 1035 (1.7x) | **1444 (2.3x)** |
| | 16 | 1113 | 1550 (1.4x) | **1984 (1.8x)** |
| | 32 | 1900 | 1772 (0.9x) | **2391 (1.3x)** |

**Block Size = 8**

| Task | Concurrency | AR | MTP | **DFlash** |
|---|---:|---:|---:|---:|
| Math500 | 1 | 84 | 273 (3.2x) | **335 (4.0x)** |
| | 8 | 625 | 1673 (2.7x) | **2020 (3.2x)** |
| | 16 | 1121 | 2731 (2.4x) | **3646 (3.3x)** |
| | 32 | 1949 | 3739 (1.9x) | **4288 (2.2x)** |
| GSM8K | 1 | 83 | 243 (2.9x) | **301 (3.6x)** |
| | 8 | 625 | 1539 (2.5x) | **1814 (2.9x)** |
| | 16 | 1109 | 2472 (2.2x) | **2896 (2.6x)** |
| | 32 | 1914 | 3431 (1.8x) | **3822 (2.0x)** |
| HumanEval | 1 | 83 | 258 (3.1x) | **350 (4.2x)** |
| | 8 | 602 | 1486 (2.5x) | **1856 (3.1x)** |
| | 16 | 1031 | 2302 (2.2x) | **2749 (2.7x)** |
| | 32 | 1720 | 2477 (1.4x) | **3412 (2.0x)** |
| MBPP | 1 | 84 | 234 (2.8x) | **311 (3.7x)** |
| | 8 | 627 | 1375 (2.2x) | **1757 (2.8x)** |
| | 16 | 1075 | 2159 (2.0x) | **2661 (2.5x)** |
| | 32 | 1832 | 2885 (1.6x) | **3309 (1.8x)** |
| MT-Bench | 1 | 84 | 210 (2.5x) | **250 (3.0x)** |
| | 8 | 622 | 1300 (2.1x) | **1495 (2.4x)** |
| | 16 | 1113 | 2105 (1.9x) | **2403 (2.2x)** |
| | 32 | 1900 | 2873 (1.5x) | **3256 (1.7x)** |

### Acceptance Length
_Format: MTP / DFlash (averaged across concurrency levels)_

| Task | B8 | B16 |
|---|---:|---:|
| Math500 | 5.73 / **5.90** | 7.14 / **7.93** |
| GSM8K | 5.54 / **5.57** | 6.84 / **7.22** |
| HumanEval | 5.81 / **6.34** | 7.38 / **9.18** |
| MBPP | 5.10 / **5.60** | 5.94 / **7.27** |
| MT-Bench | **4.60** / 4.54 | 5.30 / **5.47** |

## Acknowledgements

Special thanks to [David Wang](https://davidwa.ng/) for his outstanding engineering support on this project. We are also grateful to [Modal](https://modal.com/), [InnoMatrix](https://innomatrix.ai), and [Yotta Labs](https://www.yottalabs.ai/) for providing the compute resources used to train this draft model.

## Citation

If you find DFlash useful, please cite our work. To share feedback on DFlash or request new model support, please fill out this form: [DFlash Feedback](https://forms.gle/4YNwfqb4nJdqn6hq9).

```bibtex
@article{chen2026dflash,
  title   = {{DFlash: Block Diffusion for Flash Speculative Decoding}},
  author  = {Chen, Jian and Liang, Yesheng and Liu, Zhijian},
  journal = {arXiv preprint arXiv:2602.06036},
  year    = {2026}
}
```