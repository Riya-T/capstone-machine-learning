"""Does a trained writer prefer the editor's winners on pairs it never saw?

Scores DPO's implicit reward, log p_adapter(program) - log p_base(program),
for the chosen and the rejected program of each pair, for one or more
LoRA adapters on the same base model (the reference is the base model, as
in training). A pair is ranked correctly when the chosen program gets the
higher reward. Pairs come from training files (--pairs) or are built from
the store for a config (--config: the pairs its scorer makes, e.g. the base
writer's dev-task or eval-task pairs, which no adapter was trained on).
Forward passes only; the base model is loaded in 4-bit like in training.

Also shown, without any adapter: how often the base model itself gives the
chosen program the higher log-probability, and how often the chosen program
is the shorter one, since summed log-probabilities favour short programs.

Usage (from harness/, inside WSL, with the training extras):
    .venv/bin/python scripts/implicit_reward.py \
        --model /home/pc/models/hf/Qwen2.5-Coder-7B-Instruct \
        --adapter dpo3=/home/pc/models/dpo/dpo3 --adapter sft=/home/pc/models/dpo/sft \
        --pairs runs/rtx5070_pc/dpo/pairs_cap8_f23_nocosm.jsonl \
        --config configs/rtx5070_pc.yaml --config configs/rtx5070_eval.yaml \
        --out runs/rtx5070_pc/dpo/implicit_reward.jsonl
"""

import argparse
import json
import random
import time
from pathlib import Path

from diagnostics import load_records

from harness.collection.scorer import Scorer
from harness.config import load_config
from harness.train_dpo import chat_format, completion_logp, tokenize


def config_pairs(path):
    cfg = load_config(path)
    records, programs = load_records(cfg)
    return Scorer(cfg.scorer, cfg.editor.reps).build(records, programs.__getitem__).pairs


def file_pairs(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def accuracy_interval(rows, key, n, seed):
    """Share of pairs with key(row) true, and a 95% interval resampling tasks."""
    tasks = {}
    for row in rows:
        tasks.setdefault(row["task_id"], []).append(key(row))
    groups = list(tasks.values())
    rng = random.Random(seed)
    shares = []
    for _ in range(n):
        sample = [x for g in (rng.choice(groups) for _ in groups) for x in g]
        shares.append(sum(sample) / len(sample))
    shares.sort()
    flat = [x for g in groups for x in g]
    return sum(flat) / len(flat), shares[int(0.025 * n)], shares[int(0.975 * n) - 1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--model", required=True)
    parser.add_argument("--adapter", action="append", required=True, help="name=path")
    parser.add_argument("--pairs", type=Path, action="append", default=[])
    parser.add_argument("--config", type=Path, action="append", default=[])
    parser.add_argument("--out", type=Path, required=True, help="per-pair log-probabilities")
    parser.add_argument("--bootstrap", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20261105)
    args = parser.parse_args()

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    sets = [(p.name, file_pairs(p)) for p in args.pairs]
    sets += [(p.name, config_pairs(p)) for p in args.config]
    adapters = dict(a.split("=", 1) for a in args.adapter)

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    dtype = torch.bfloat16
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=dtype,
        ),
        torch_dtype=dtype,
        device_map={"": 0},
    )
    names = list(adapters)
    model = PeftModel.from_pretrained(model, adapters[names[0]], adapter_name=names[0])
    for name in names[1:]:
        model.load_adapter(adapters[name], adapter_name=name)
    model.eval()

    out = args.out.open("w", encoding="utf-8")
    results = {}
    started = time.monotonic()
    with torch.no_grad():
        for set_name, rows in sets:
            tokens = tokenize(chat_format(rows, tokenizer), tokenizer, max_length=16384)
            scored = []
            for row, pair in zip(rows, tokens, strict=True):
                entry = {"set": set_name, "task_id": row["task_id"],
                         "chosen_tokens": len(pair["chosen"]),
                         "rejected_tokens": len(pair["rejected"])}  # fmt: skip
                with model.disable_adapter():
                    for key in ("chosen", "rejected"):
                        entry[f"base_{key}"] = completion_logp(
                            model, pair["prompt"], pair[key]
                        ).item()
                for name in names:
                    model.set_adapter(name)
                    for key in ("chosen", "rejected"):
                        entry[f"{name}_{key}"] = completion_logp(
                            model, pair["prompt"], pair[key]
                        ).item()
                out.write(json.dumps(entry) + "\n")
                out.flush()
                scored.append(entry)
            results[set_name] = scored
            print(f"{set_name}: {len(scored)} pairs, {time.monotonic() - started:.0f}s", flush=True)
    out.close()

    lines = [
        "| Pairs | Pairs (tasks) | Ranker | Chosen ranked higher | 95% interval | "
        "Mean reward margin |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for set_name, rows in results.items():
        k = len({r["task_id"] for r in rows})
        rankers = [("chosen is shorter", lambda r: r["chosen_tokens"] < r["rejected_tokens"], None),
                   ("base model log-probability", lambda r: r["base_chosen"] > r["base_rejected"],
                    None)]  # fmt: skip
        for name in names:

            def margin(r, name=name):
                return (r[f"{name}_chosen"] - r["base_chosen"]) - (
                    r[f"{name}_rejected"] - r["base_rejected"]
                )

            rankers.append((f"{name} implicit reward", lambda r, m=margin: m(r) > 0, margin))
        for label, key, margin in rankers:
            share, lo, hi = accuracy_interval(rows, key, args.bootstrap, args.seed)
            mean = f"{0.1 * sum(margin(r) for r in rows) / len(rows):+.3f}" if margin else "–"
            lines.append(f"| {set_name} | {len(rows)} ({k}) | {label} | {share:.0%} | "
                         f"{lo:.0%} to {hi:.0%} | {mean} |")  # fmt: skip
    print("\n".join(lines))
    print("\nReward margin uses beta 0.1, as in training.")


if __name__ == "__main__":
    main()
