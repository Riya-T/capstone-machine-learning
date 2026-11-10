"""Fine-tune the writer on its own passing programs (the correctness-only baseline).

The same QLoRA setup as harness.train_dpo (4-bit NF4 base, LoRA on every
linear layer, the vocabulary head run only on completion positions), with
the plain supervised loss: the mean negative log-probability of each
program's tokens after its writer prompt. The training file comes from
scripts/sft_programs.py. The defaults match the DPO writer's settings (2
epochs, 8 examples per optimizer step, learning rate 2e-5, seed 42), so the
two differ in the loss, not in how far training goes.

Usage:
    python -m harness.train_sft runs/rtx5070_pc/dpo/sft_programs.jsonl \
        --model Qwen/Qwen2.5-Coder-7B-Instruct --output-dir ../models/writer-sft
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path
from typing import Any

from harness.train_dpo import chat_format, completion_logp


def load_programs(path: Path) -> list[dict[str, str]]:
    """Read prompt and completion columns from a JSONL training file."""
    rows = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number}: expected a JSON object")
            row = {key: record.get(key) for key in ("prompt", "completion")}
            if any(not isinstance(value, str) or not value.strip() for value in row.values()):
                raise ValueError(f"{path}:{line_number}: prompt and completion must be non-empty")
            rows.append(row)
    if not rows:
        raise ValueError(f"{path}: no programs found")
    return rows


def tokenize(rows: list[dict[str, str]], tokenizer: Any, max_length: int) -> list[dict]:
    """Token ids per example: the chat-formatted prompt, and the completion
    with the end-of-turn token appended. Refuses examples longer than
    max_length, as train_dpo does."""
    eos = tokenizer.eos_token_id
    examples, too_long = [], []
    for index, row in enumerate(rows):
        prompt = tokenizer(row["prompt"], add_special_tokens=False)["input_ids"]
        completion = tokenizer(row["completion"], add_special_tokens=False)["input_ids"] + [eos]
        if len(prompt) + len(completion) > max_length:
            too_long.append(f"example {index}: {len(prompt) + len(completion)} tokens")
        examples.append({"prompt": prompt, "completion": completion})
    if too_long:
        shown = "; ".join(too_long[:5])
        raise ValueError(f"{len(too_long)} examples exceed --max-length {max_length}: {shown}")
    return examples


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
            "training dependencies are missing; install with `uv sync --extra training`"
        ) from exc

    if not torch.cuda.is_available():
        raise RuntimeError("QLoRA training requires a CUDA GPU with bitsandbytes support")

    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=False)
    rows = chat_format(load_programs(args.programs), tokenizer)
    examples = tokenize(rows, tokenizer, args.max_length)

    # The model setup of train_dpo.train.
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
    log = (args.output_dir / "train_log.jsonl").open("w", encoding="utf-8")

    rng = random.Random(args.seed)
    torch.manual_seed(args.seed)
    whole, part = int(args.epochs), args.epochs - int(args.epochs)
    order = []
    for _ in range(whole):
        order += rng.sample(range(len(examples)), len(examples))
    if part:
        order += rng.sample(range(len(examples)), round(part * len(examples)))
    steps = math.ceil(len(order) / args.gradient_accumulation_steps)
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = bnb.optim.PagedAdamW8bit(params, lr=args.learning_rate, weight_decay=0.0)
    schedule = get_linear_schedule_with_warmup(optimizer, round(args.warmup_ratio * steps), steps)

    model.train()
    window = []
    started = time.monotonic()
    for i, index in enumerate(order, start=1):
        example = examples[index]
        loss = -completion_logp(model, example["prompt"], example["completion"]) / len(
            example["completion"]
        )
        (loss / args.gradient_accumulation_steps).backward()
        window.append(loss.item())
        if i % args.gradient_accumulation_steps == 0 or i == len(order):
            grad_norm = torch.nn.utils.clip_grad_norm_(params, args.max_grad_norm).item()
            optimizer.step()
            schedule.step()
            optimizer.zero_grad(set_to_none=True)
            entry = {
                "step": math.ceil(i / args.gradient_accumulation_steps),
                "steps": steps,
                "epoch": round(i / len(examples), 3),
                "loss": sum(window) / len(window),
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
    result.add_argument("programs", type=Path, help="scripts/sft_programs.py output")
    result.add_argument("--model", default="Qwen/Qwen2.5-Coder-7B-Instruct")
    result.add_argument("--output-dir", type=Path, required=True)
    result.add_argument("--epochs", type=float, default=2)
    result.add_argument("--gradient-accumulation-steps", type=int, default=8)
    result.add_argument("--learning-rate", type=float, default=2e-5, help="the DPO writer's (dpo3)")
    result.add_argument("--warmup-ratio", type=float, default=0.0)
    result.add_argument("--max-grad-norm", type=float, default=1.0)
    result.add_argument(
        "--max-length", type=int, default=3200, help="prompt plus completion, in tokens"
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
