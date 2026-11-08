"""Compare two writers task by task on the same eval tasks.

Reads the store only. For each task present in both runs it takes the
per-task results of `eval_summary.py` and reports the difference (second
minus first) of each measure, plus how often the writer's samples pass the
initial checks. The intervals resample the tasks with replacement and keep
each task's pair together (a paired task bootstrap), so differences between
tasks don't count as differences between writers.

Usage (from harness/, inside WSL):
    uv run python scripts/eval_compare.py --base configs/rtx5070_eval.yaml \
        --other configs/rtx5070_eval_maintain.yaml --bootstrap 20000
"""

import argparse
from pathlib import Path

from eval_summary import METRIC_NAMES, METRICS, percentile_interval, task_results

from harness.config import load_config


def compare(base_cfg, other_cfg, n: int, seed: int) -> str:
    base = {r["task_id"]: r for r in task_results(base_cfg)[0] if r["trials"]}
    other = {r["task_id"]: r for r in task_results(other_cfg)[0] if r["trials"]}
    common = sorted(base.keys() & other.keys())
    lines = [
        "| Task | Initial pass (base → other) | Changes done before first failure | "
        "First change works | Whole sequence works |",
        "|---|---|---|---|---|",
    ]
    diffs = []
    for t in common:
        b, o = base[t], other[t]
        diffs.append(tuple(o[m] - b[m] for m in METRICS) + (rate(o) - rate(b),))
        lines.append(
            f"| {t} | {b['passing_samples']}/{b['samples']} → {o['passing_samples']}/"
            f"{o['samples']} | {b['mean']:.2f} → {o['mean']:.2f} | {b['first']:.0%} → "
            f"{o['first']:.0%} | {b['full']:.0%} → {o['full']:.0%} |"
        )
    k = len(diffs)
    intervals = percentile_interval(diffs, n, seed)
    lines += [
        "",
        f"Paired task bootstrap of the difference (other minus base; {n} resamples of the "
        f"{k} tasks, seed {seed}):",
        "",
        "| Metric | Base | Other | Difference | 95% interval |",
        "|---|---:|---:|---:|---:|",
    ]
    names = [*METRIC_NAMES, "Writer samples passing the initial checks"]
    keys = [*METRICS, None]
    for i, (name, key) in enumerate(zip(names, keys, strict=True)):
        bval = sum((base[t][key] if key else rate(base[t])) for t in common) / k
        oval = sum((other[t][key] if key else rate(other[t])) for t in common) / k
        lo, hi = intervals[i]
        if i == 0:
            lines.append(f"| {name} | {bval:.2f} | {oval:.2f} | {oval - bval:+.2f} | "
                         f"{lo:+.2f} to {hi:+.2f} |")  # fmt: skip
        else:
            lines.append(f"| {name} | {bval:.0%} | {oval:.0%} | {(oval - bval) * 100:+.0f} pts | "
                         f"{lo * 100:+.0f} to {hi * 100:+.0f} pts |")  # fmt: skip
    return "\n".join(lines)


def rate(row) -> float:
    return row["passing_samples"] / row["samples"] if row["samples"] else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--other", required=True, type=Path)
    parser.add_argument("--bootstrap", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20261105)
    parser.add_argument("--out", type=Path, help="also write the tables to this file")
    args = parser.parse_args()
    text = compare(load_config(args.base), load_config(args.other), args.bootstrap, args.seed)
    print(text)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
