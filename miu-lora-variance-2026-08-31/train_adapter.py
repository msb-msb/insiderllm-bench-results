#!/usr/bin/env python3
"""Train one LoRA adapter on the frozen 24-example compile split.

Seed varies; data, hyperparameters and target modules are byte-identical across
runs. That is the analogue of the prompt experiment, which sent byte-identical
input and let the compiler's own sampling vary.

Architecture note: Qwen3.6-27B is hybrid -- 48 linear-attention (Mamba-style)
blocks and 16 full-attention blocks, MLP on all 64. The conventional QLoRA
target set below touches the MLP of all 64 layers and the attention of only the
16 full-attention ones; the linear_attn projections are deliberately left out
because convert_lora_to_gguf.py has no mapping for Mamba-style tensors.
"""
import json, os, sys, argparse, random, time
import numpy as np, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deployed import INTENT_SYSTEM_PROMPT
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

MODEL = "/media/minotaur/Storage_Disk_1/LLM_repo/qwen3.6-27b"
TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]


def build_examples(tok):
    comp = json.load(open("splits/compile.json"))
    out = []
    for x in sorted(comp, key=lambda r: r["idx"]):
        g = x["gold"]
        answer = json.dumps({"tool": g["tool"], "mode": g["mode"], "scope": g["scope"]})
        msgs = [{"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": x["msg"]}]
        prompt_txt = tok.apply_chat_template(
            msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        prompt_ids = tok(prompt_txt, add_special_tokens=False)["input_ids"]
        ans_ids = tok(answer, add_special_tokens=False)["input_ids"] + [tok.eos_token_id]
        ids = prompt_ids + ans_ids
        labels = [-100] * len(prompt_ids) + ans_ids   # loss on the answer only
        out.append({"input_ids": ids, "labels": labels, "idx": x["idx"]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--accum", type=int, default=4)
    ap.add_argument("--out", default=None)
    ap.add_argument("--inspect", action="store_true",
                    help="print one formatted example and exit")
    a = ap.parse_args()

    tok = AutoTokenizer.from_pretrained(MODEL)
    ex = build_examples(tok)
    if a.inspect:
        print("n examples:", len(ex))
        lens = [len(x["input_ids"]) for x in ex]
        print("token lens:", lens)
        print("max len:", max(lens))
        e = ex[0]
        print("\n--- example idx", e["idx"], "---")
        print(tok.decode(e["input_ids"]))
        sup = [i for i, l in enumerate(e["labels"]) if l != -100]
        print("\n--- supervised span ---")
        print(repr(tok.decode([e["input_ids"][i] for i in sup])))
        return

    random.seed(a.seed); np.random.seed(a.seed)
    torch.manual_seed(a.seed); torch.cuda.manual_seed_all(a.seed)

    # lm_head is left UNQUANTISED (bnb's default skip), and this is a memory
    # optimisation, not a concession. Quantising it saves 2.54 GB resident but
    # forces a 2.37 GiB dequantisation on every logit computation -- seed 1 fit
    # by luck and seed 2 OOMed on the same config with 4.44 GiB reserved-but-
    # unallocated. Resident cost is paid once; the transient is paid per forward.
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16,
                             bnb_4bit_use_double_quant=True)
    # AutoModelForCausalLM already unwraps the VLM to the text tower, so the
    # 0.46B vision encoder and 0.42B MTP head are never loaded -- runtime modules
    # are model.layers.*, not model.language_model.*. Everything on GPU.
    dmap = {"": 0}
    t0 = time.time()
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, quantization_config=bnb, dtype=torch.bfloat16, device_map=dmap)
    load_s = time.time() - t0
    model.config.use_cache = False
    # NOT prepare_model_for_kbit_training(): it upcasts every non-quantised
    # parameter to fp32, and with a 248,320-token vocab the embedding alone is
    # 1.27B params -> a 4.74 GiB allocation that OOMs a 24 GB card. The fp32
    # upcast is a stability nicety, not a requirement; gradient checkpointing
    # and input grads are the parts that matter.
    # use_reentrant=False is load-bearing, not cosmetic. The reentrant
    # checkpoint implementation does not reliably discard activations when the
    # block's inputs do not require grad, which is exactly the QLoRA case -- so
    # the dequantised weight bitsandbytes materialises in its unfused fallback
    # (B_dq, saved by F.linear for backward) is retained per layer instead of
    # being recomputed. That is what pushed peak memory past 24 GB.
    model.gradient_checkpointing_enable(
        gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    lcfg = LoraConfig(r=a.rank, lora_alpha=a.rank * 2, lora_dropout=0.05, bias="none",
                      task_type="CAUSAL_LM", target_modules=TARGETS)
    model = get_peft_model(model, lcfg)
    tr = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"load {load_s:.0f}s | trainable params {tr:,} | "
          f"gc={model.base_model.model.model.gradient_checkpointing} | "
          f"vram {torch.cuda.memory_allocated()/2**30:.2f} GiB", flush=True)

    # REQUIRED. Every checkpointing implementation guards on
    # `self.gradient_checkpointing and self.training`, so without this the flag
    # is set but never fires: a single 700-token forward retained 8.4 GiB of
    # activations and dequantised weights and OOMed a 24 GB card.
    model.train()
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=a.lr)
    order = list(range(len(ex)))
    rng = random.Random(a.seed)
    steps = 0
    t1 = time.time()
    losses = []
    for ep in range(a.epochs):
        rng.shuffle(order)
        for n, i in enumerate(order):
            e = ex[i]
            ids = torch.tensor([e["input_ids"]], device=0)
            lab = torch.tensor([e["labels"]], device=0)
            loss = model(input_ids=ids, labels=lab).loss / a.accum
            loss.backward()
            losses.append(loss.item() * a.accum)
            if (n + 1) % a.accum == 0:
                opt.step(); opt.zero_grad(set_to_none=True); steps += 1
        print(f"  epoch {ep+1}/{a.epochs} mean_loss {np.mean(losses[-len(ex):]):.4f} "
              f"({time.time()-t1:.0f}s)", flush=True)

    out = a.out or f"adapters/seed{a.seed}"
    model.save_pretrained(out)
    json.dump({"seed": a.seed, "epochs": a.epochs, "lr": a.lr, "rank": a.rank,
               "accum": a.accum, "targets": TARGETS, "opt_steps": steps,
               "train_s": round(time.time() - t1, 1), "load_s": round(load_s, 1),
               "final_epoch_loss": float(np.mean(losses[-len(ex):])),
               "n_examples": len(ex), "trainable_params": tr},
              open(f"{out}/run_meta.json", "w"), indent=1)
    print(f"saved {out} | train {time.time()-t1:.0f}s | steps {steps}")


if __name__ == "__main__":
    main()
