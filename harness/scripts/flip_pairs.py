"""Swap chosen and rejected in a given share of a DPO file's pairs.

A label-noise control: the Radon pairs (scripts/static_ranking.py) prefer
the higher Maintainability Index every time, while the editing labels agree
with themselves between change sequences only 58% of the time. Training on
Radon pairs with a known share swapped shows how much label noise DPO
tolerates before the trained writer stops preferring higher-MI programs on
tasks it never saw (scripts/implicit_reward.py on held-out Radon pairs).
Exactly round(RATE x pairs) pairs are swapped, picked at random with SEED;
each swapped pair also swaps its ids and scores and gets a "flipped" field.

Usage (from harness/):
    .venv/bin/python scripts/flip_pairs.py runs/rtx5070_pc/dpo/radon_matched.jsonl \
        runs/rtx5070_pc/dpo/radon_f30.jsonl --rate 0.3
"""

import argparse
import json
import random
from pathlib import Path

SWAPS = (
    ("chosen", "rejected"),
    ("chosen_id", "rejected_id"),
    ("chosen_scores", "rejected_scores"),
    ("chosen_call_keys", "rejected_call_keys"),
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("source", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--rate", type=float, required=True, help="share of pairs to swap")
    parser.add_argument("--seed", type=int, default=20261116)
    args = parser.parse_args()
    if not 0 <= args.rate <= 1:
        parser.error("--rate must be between 0 and 1")
    pairs = [json.loads(line) for line in args.source.read_text().splitlines() if line]
    flipped = set(random.Random(args.seed).sample(range(len(pairs)), round(args.rate * len(pairs))))
    with args.out.open("w") as f:
        for i, pair in enumerate(pairs):
            if i in flipped:
                for a, b in SWAPS:
                    if a in pair or b in pair:
                        pair[a], pair[b] = pair.get(b), pair.get(a)
                if "margin" in pair and isinstance(pair["margin"], (int, float)):
                    pair["margin"] = -pair["margin"]
            pair["flipped"] = i in flipped
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
    print(f"{args.out}: {len(flipped)} of {len(pairs)} pairs swapped (seed {args.seed})")


if __name__ == "__main__":
    main()
