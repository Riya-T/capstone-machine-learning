"""How well could a writer that learned a signal rank held-out labels this noisy?

Takes the Radon-ranked held-out pairs and an adapter's implicit rewards on
them (scripts/implicit_reward.py, which writes the pairs' rows in order),
gives each program its reward (adapter minus base log-probability) and its
MI, and ranks every pair of a task's programs with unequal MI. Against MI
itself that is how well the adapter learned the signal. Against MI plus
per-program noise of reliability R (MI standardized within the task times
sqrt(R), plus Gaussian noise times sqrt(1 - R), as in
`scripts/static_ranking.py --score-noise`) it is what the same writer would
score on held-out labels as noisy as editing scores of that reliability.

Usage (from harness/):
    .venv/bin/python scripts/noise_ceiling.py runs/rtx5070_pc/dpo/radon_evaltasks.jsonl \
        runs/rtx5070_pc/dpo/implicit_reward_dpoall.jsonl --adapter radon_rel18_all \
        --reliability 0.18 --reliability 0.42
"""

import argparse
import json
import math
import random
import statistics
from collections import defaultdict
from itertools import combinations
from pathlib import Path


def load_programs(pairs_path: Path, rewards_path: Path, adapter: str) -> dict[str, dict]:
    """task -> candidate id -> (MI, reward)."""
    pairs = [json.loads(line) for line in pairs_path.open(encoding="utf-8")]
    rows = [json.loads(line) for line in rewards_path.open(encoding="utf-8")]
    rows = [row for row in rows if row["set"] == pairs_path.name]
    if len(rows) != len(pairs):
        raise SystemExit(
            f"{rewards_path}: {len(rows)} rows for {pairs_path.name}, not {len(pairs)}"
        )
    programs: dict[str, dict] = defaultdict(dict)
    for pair, row in zip(pairs, rows, strict=True):
        if pair["task_id"] != row["task_id"]:
            raise SystemExit(f"row order differs from {pairs_path} at task {pair['task_id']}")
        for side in ("chosen", "rejected"):
            reward = row[f"{adapter}_{side}"] - row[f"base_{side}"]
            programs[pair["task_id"]][pair[f"{side}_id"]] = (pair[f"{side}_scores"][0], reward)
    return programs


def accuracy(programs: dict[str, dict], labels: dict[str, dict]) -> tuple[float, int]:
    """Share of pairs with unequal MI and labels whose reward order matches the labels."""
    agree = total = 0
    for task_id, task_programs in programs.items():
        for a, b in combinations(sorted(task_programs), 2):
            (mi_a, reward_a), (mi_b, reward_b) = task_programs[a], task_programs[b]
            label_a, label_b = labels[task_id][a], labels[task_id][b]
            if mi_a == mi_b or label_a == label_b:
                continue
            agree += (reward_a > reward_b) == (label_a > label_b)
            total += 1
    return agree / total, total


def noisy_labels(programs: dict[str, dict], reliability: float, rng: random.Random) -> dict:
    labels = {}
    for task_id, task_programs in programs.items():
        mis = [mi for mi, _ in task_programs.values()]
        mean, sd = statistics.fmean(mis), statistics.pstdev(mis)
        labels[task_id] = {
            program_id: math.sqrt(reliability) * ((mi - mean) / sd if sd else 0.0)
            + math.sqrt(1 - reliability) * rng.gauss(0.0, 1.0)
            for program_id, (mi, _) in sorted(task_programs.items())
        }
    return labels


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("pairs", type=Path, help="Radon-ranked held-out pairs")
    parser.add_argument("rewards", type=Path, help="implicit_reward.py --out file covering them")
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--reliability", type=float, action="append", default=[])
    parser.add_argument("--draws", type=int, default=400)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    programs = load_programs(args.pairs, args.rewards, args.adapter)
    clean = {t: {i: mi for i, (mi, _) in ps.items()} for t, ps in programs.items()}
    share, total = accuracy(programs, clean)
    count = sum(len(ps) for ps in programs.values())
    print(f"{args.adapter}: {count} programs, {len(programs)} tasks, {total} pairs")
    print(f"against MI: {share:.0%}")
    rng = random.Random(args.seed)
    for reliability in args.reliability:
        draws = sorted(
            accuracy(programs, noisy_labels(programs, reliability, rng))[0]
            for _ in range(args.draws)
        )
        low, high = draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws)) - 1]
        print(
            f"against MI with per-program noise, reliability {reliability}: "
            f"{statistics.fmean(draws):.0%} ({low:.0%} to {high:.0%} over {args.draws} draws)"
        )


if __name__ == "__main__":
    main()
