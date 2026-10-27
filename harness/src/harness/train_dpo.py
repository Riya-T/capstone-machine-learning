"""Train the writer on collected preference pairs with QLoRA and TRL DPO.

Usage:
    python -m harness.train_dpo runs/<run-id>/preferences.jsonl \
        --output-dir ../models/writer-dpo
"""

from __future__ import annotations

import argparse
import json
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


def train(args: argparse.Namespace) -> None:
    try:
        import torch
        from datasets import Dataset
        from peft import LoraConfig, prepare_model_for_kbit_training
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
        )
        from trl import DPOConfig, DPOTrainer
    except ImportError as exc:
        raise RuntimeError(
            "DPO training dependencies are missing; install with `uv sync --extra training`"
        ) from exc

    if not torch.cuda.is_available():
        raise RuntimeError("QLoRA training requires a CUDA GPU with bitsandbytes support")

    rows = load_preferences(args.preferences)
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=False)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

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
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    dataset = Dataset.from_list(chat_format(rows, tokenizer))
    lora = LoraConfig(
        r=args.lora_rank,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules="all-linear",
        bias="none",
        task_type="CAUSAL_LM",
    )
    training_args = DPOConfig(
        output_dir=str(args.output_dir),
        beta=args.beta,
        learning_rate=args.learning_rate,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        max_length=args.max_length,
        max_prompt_length=args.max_prompt_length,
        logging_steps=1,
        save_strategy="epoch",
        report_to="none",
        gradient_checkpointing=True,
        bf16=compute_dtype == torch.bfloat16,
        fp16=compute_dtype == torch.float16,
        optim="paged_adamw_8bit",
        seed=args.seed,
    )
    trainer = DPOTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
        peft_config=lora,
    )
    trainer.train()
    trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(args.output_dir)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("preferences", type=Path, help="scorer-generated preferences.jsonl")
    result.add_argument("--model", default="Qwen/Qwen2.5-Coder-7B-Instruct")
    result.add_argument("--output-dir", type=Path, required=True)
    result.add_argument("--epochs", type=float, default=3)
    result.add_argument("--batch-size", type=int, default=1)
    result.add_argument("--gradient-accumulation-steps", type=int, default=8)
    result.add_argument("--learning-rate", type=float, default=5e-5)
    result.add_argument("--beta", type=float, default=0.1)
    result.add_argument("--max-length", type=int, default=4096)
    result.add_argument("--max-prompt-length", type=int, default=2048)
    result.add_argument("--lora-rank", type=int, default=16)
    result.add_argument("--lora-alpha", type=int, default=32)
    result.add_argument("--lora-dropout", type=float, default=0.05)
    result.add_argument("--seed", type=int, default=42)
    return result


def main() -> None:
    train(parser().parse_args())


if __name__ == "__main__":
    main()
