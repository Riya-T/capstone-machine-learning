"""Take as many pairs per task from one DPO file as another file has.

A baseline trained on a different preference signal (such as the Radon
ranking of scripts/static_ranking.py) should see the same tasks and the same
number of pairs per task as our training file, so the two differ only in
which program each pair prefers. For each task of REFERENCE this keeps that
many pairs of SOURCE in SOURCE's order (static_ranking.py writes the largest
score gaps first), skipping pairs that harness.train_dpo would refuse as
longer than --max-length.

Usage (from harness/):
    .venv/bin/python scripts/match_pairs.py runs/rtx5070_pc/dpo/radon_cap8_all.jsonl \
        runs/rtx5070_pc/dpo/pairs_cap8_f23_nocosm.jsonl \
        runs/rtx5070_pc/dpo/radon_matched.jsonl --model Qwen/Qwen2.5-Coder-7B-Instruct
"""

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("source", type=Path, help="pairs to take from")
    parser.add_argument("reference", type=Path, help="pairs whose per-task counts to match")
    parser.add_argument("out", type=Path)
    parser.add_argument("--model", required=True, help="tokenizer of the model to train")
    parser.add_argument("--max-length", type=int, default=3200, help="as passed to train_dpo")
    args = parser.parse_args()

    from transformers import AutoTokenizer

    from harness.train_dpo import chat_format

    tokenizer = AutoTokenizer.from_pretrained(args.model)

    def length(row: dict) -> int:
        prompt = chat_format([row], tokenizer)[0]["prompt"]
        n_prompt = len(tokenizer(prompt, add_special_tokens=False)["input_ids"])
        n_reply = max(
            len(tokenizer(row[key], add_special_tokens=False)["input_ids"])
            for key in ("chosen", "rejected")
        )
        return n_prompt + n_reply + 1  # train_dpo appends the end-of-turn token

    def read(path: Path) -> list[dict]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    wanted = Counter(row["task_id"] for row in read(args.reference))
    kept, too_long = [], Counter()
    for row in read(args.source):
        task = row["task_id"]
        if sum(r["task_id"] == task for r in kept) >= wanted[task]:
            continue
        if length(row) > args.max_length:
            too_long[task] += 1
            continue
        kept.append(row)
    got = Counter(row["task_id"] for row in kept)
    short = {task: (got[task], n) for task, n in wanted.items() if got[task] < n}
    args.out.write_text("".join(json.dumps(r) + "\n" for r in kept), encoding="utf-8")
    print(f"kept {len(kept)} of {sum(wanted.values())} pairs from {len(got)} tasks -> {args.out}")
    print(f"skipped as too long: {dict(too_long)}; tasks short of pairs: {short}")


if __name__ == "__main__":
    main()
