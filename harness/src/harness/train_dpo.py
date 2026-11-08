"""Train the writer on collected preference pairs with QLoRA and DPO.

The base model is loaded in 4-bit (NF4) and trained through PEFT LoRA
adapters on every linear layer. The DPO loop is our own, not TRL's
DPOTrainer: TRL computes the logits of the whole 152k-word vocabulary at
every position, prompt included, which overflows a 12 GB GPU at these
lengths. Here the language-model head runs only on the completion's
positions, in chunks, and the vocabulary-sized layers stay in bf16. The
loss is standard DPO (sigmoid), with sequence log-probabilities summed over
the completion, and the reference log-probabilities (the same model with
the adapters disabled) computed once before training.

Usage:
    python -m harness.train_dpo runs/<run-id>/preferences.jsonl \
        --model Qwen/Qwen2.5-Coder-7B-Instruct --output-dir ../models/writer-dpo
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path
from typing import Any


def load_preferences(path: Path) -> list[dict[str, str]]:
    """Load and validate the scorer's JSONL as prompt/chosen/rejected rows."""
    rows = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number}: expected a JSON object")
            row = {key: record.get(key) for key in ("prompt", "chosen", "rejected")}
            if any(not isinstance(value, str) or not value.strip() for value in row.values()):
                raise ValueError(
                    f"{path}:{line_number}: prompt, chosen, and rejected must be non-empty strings"
                )
            if row["chosen"] == row["rejected"]:
                raise ValueError(f"{path}:{line_number}: chosen and rejected are identical")
            rows.append(row)
    if not rows:
        raise ValueError(f"{path}: no preference pairs found")
    return rows


def chat_format(rows: list[dict[str, str]], tokenizer: Any) -> list[dict[str, str]]:
    """Put the writer prompt in the model's user turn, leaving code as completion."""
    if not tokenizer.chat_template:
        raise ValueError("the tokenizer has no chat template; use an instruct model/tokenizer")
    formatted = []
    for row in rows:
        prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": row["prompt"]}],
            tokenize=False,
            add_generation_prompt=True,
        )
        formatted.append({**row, "prompt": prompt})
    return formatted


def tokenize(rows: list[dict[str, str]], tokenizer: Any, max_length: int) -> list[dict]:
    """Token ids per pair: the chat-formatted prompt, and each completion with
    the end-of-turn token appended (as the model ends its reply). Refuses to
    train if any prompt plus completion is longer than max_length, since
    cutting it would train on a different example."""
    eos = tokenizer.eos_token_id
    pairs, too_long = [], []
    for index, row in enumerate(rows):
        prompt = tokenizer(row["prompt"], add_special_tokens=False)["input_ids"]
        pair = {"prompt": prompt}
        for key in ("chosen", "rejected"):
            pair[key] = tokenizer(row[key], add_special_tokens=False)["input_ids"] + [eos]
            if len(prompt) + len(pair[key]) > max_length:
                too_long.append(f"pair {index} {key}: {len(prompt) + len(pair[key])} tokens")
        pairs.append(pair)
    if too_long:
        shown = "; ".join(too_long[:5])
        raise ValueError(f"{len(too_long)} examples exceed --max-length {max_length}: {shown}")
    return pairs


def dpo_loss(policy_chosen, policy_rejected, ref_chosen, ref_rejected, beta: float):
    """Sigmoid DPO loss and the implicit reward margin, from summed sequence
    log-probabilities (tensors of the same shape)."""
    import torch.nn.functional as F  # noqa: N812

    margin = beta * ((policy_chosen - ref_chosen) - (policy_rejected - ref_rejected))
    return -F.logsigmoid(margin), margin


def completion_logp(model: Any, prompt: list[int], completion: list[int], chunk: int = 256):
    """Summed log-probability of `completion` after `prompt`. Runs the
    transformer on the whole sequence but the vocabulary head only on the
    positions that predict completion tokens, `chunk` positions at a time."""
    import torch

    base = model.get_base_model() if hasattr(model, "get_base_model") else model
    device = next(model.parameters()).device
    ids = torch.tensor([prompt + completion], device=device)
    hidden = base.model(input_ids=ids).last_hidden_state[0]
    start = len(prompt) - 1  # the position before each completion token predicts it
    hidden = hidden[start : start + len(completion)]
    targets = ids[0, len(prompt) :]
    total = hidden.new_zeros((), dtype=torch.float32)
    for i in range(0, len(completion), chunk):
        logits = base.lm_head(hidden[i : i + chunk]).float()
        logp = torch.log_softmax(logits, dim=-1)
        total = total + logp.gather(1, targets[i : i + chunk, None]).sum()
    return total


def train(args: argparse.Namespace) -> None:
    try:
        import bitsandbytes as bnb
        import torch
        from peft import LoraConfig, get_peft_model
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            get_linear_schedule_with_warmup,
        )
    except ImportError as exc:
        raise RuntimeError(
            "DPO training dependencies are missing; install with `uv sync --extra training`"
        ) from exc

    if not torch.cuda.is_available():
        raise RuntimeError("QLoRA training requires a CUDA GPU with bitsandbytes support")

    rows = load_preferences(args.preferences)
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=False)
    pairs = tokenize(chat_format(rows, tokenizer), tokenizer, args.max_length)

    compute_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=compute_dtype,
    )
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        quantization_config=quantization,
        torch_dtype=compute_dtype,
        device_map={"": torch.cuda.current_device()},
        trust_remote_code=False,
    )
    model.config.use_cache = False
    # Not prepare_model_for_kbit_training: it casts the embedding and the
    # vocabulary head to fp32 (4.4 GB for this model), which doesn't fit.
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    lora = LoraConfig(
        r=args.lora_rank,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules="all-linear",
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    log_path = args.output_dir / "train_log.jsonl"
    log = log_path.open("w", encoding="utf-8")

    # Reference log-probabilities: the same model with the adapters off.
    model.eval()
    reference = []
    started = time.monotonic()
    with torch.no_grad(), model.disable_adapter():
        for pair in pairs:
            reference.append(
                (
                    completion_logp(model, pair["prompt"], pair["chosen"]).item(),
                    completion_logp(model, pair["prompt"], pair["rejected"]).item(),
                )
            )
    print(f"reference log-probabilities: {len(pairs)} pairs in {time.monotonic() - started:.0f}s")

    rng = random.Random(args.seed)
    torch.manual_seed(args.seed)
    whole, part = int(args.epochs), args.epochs - int(args.epochs)
    order = []
    for _ in range(whole):
        order += rng.sample(range(len(pairs)), len(pairs))
    if part:
        order += rng.sample(range(len(pairs)), round(part * len(pairs)))
    steps = math.ceil(len(order) / args.gradient_accumulation_steps)
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = bnb.optim.PagedAdamW8bit(params, lr=args.learning_rate, weight_decay=0.0)
    schedule = get_linear_schedule_with_warmup(optimizer, round(args.warmup_ratio * steps), steps)

    model.train()
    window = []
    started = time.monotonic()
    for i, index in enumerate(order, start=1):
        pair = pairs[index]
        policy_chosen = completion_logp(model, pair["prompt"], pair["chosen"])
        policy_rejected = completion_logp(model, pair["prompt"], pair["rejected"])
        ref_chosen, ref_rejected = reference[index]
        loss, margin = dpo_loss(policy_chosen, policy_rejected, ref_chosen, ref_rejected, args.beta)
        (loss / args.gradient_accumulation_steps).backward()
        window.append((loss.item(), margin.item()))
        if i % args.gradient_accumulation_steps == 0 or i == len(order):
            grad_norm = torch.nn.utils.clip_grad_norm_(params, args.max_grad_norm).item()
            optimizer.step()
            schedule.step()
            optimizer.zero_grad(set_to_none=True)
            entry = {
                "step": math.ceil(i / args.gradient_accumulation_steps),
                "steps": steps,
                "epoch": round(i / len(pairs), 3),
                "loss": sum(x for x, _ in window) / len(window),
                "reward_margin": sum(m for _, m in window) / len(window),
                "reward_accuracy": sum(m > 0 for _, m in window) / len(window),
                "grad_norm": grad_norm,
                "learning_rate": schedule.get_last_lr()[0],
                "elapsed_s": round(time.monotonic() - started),
                "max_memory_gb": round(torch.cuda.max_memory_allocated() / 2**30, 2),
            }
            print(json.dumps(entry), flush=True)
            log.write(json.dumps(entry) + "\n")
            log.flush()
            window = []
    log.close()
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    (args.output_dir / "train_args.json").write_text(
        json.dumps({k: str(v) for k, v in vars(args).items()}, indent=2), encoding="utf-8"
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("preferences", type=Path, help="scorer-generated preferences.jsonl")
    result.add_argument("--model", default="Qwen/Qwen2.5-Coder-7B-Instruct")
    result.add_argument("--output-dir", type=Path, required=True)
    result.add_argument("--epochs", type=float, default=2)
    result.add_argument("--gradient-accumulation-steps", type=int, default=8)
    result.add_argument(
        "--learning-rate", type=float, default=5e-5, help="5e-6 barely moves a LoRA adapter here"
    )
    result.add_argument("--warmup-ratio", type=float, default=0.0)
    result.add_argument("--max-grad-norm", type=float, default=1.0)
    result.add_argument("--beta", type=float, default=0.1)
    result.add_argument(
        "--max-length", type=int, default=4096, help="prompt plus completion, in tokens"
    )
    result.add_argument("--lora-rank", type=int, default=16)
    result.add_argument("--lora-alpha", type=int, default=32)
    result.add_argument("--lora-dropout", type=float, default=0.05)
    result.add_argument("--seed", type=int, default=42)
    return result


def main() -> None:
    train(parser().parse_args())


if __name__ == "__main__":
    main()
