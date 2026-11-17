"""Which single changes does the program decide?

The variance split of scripts/diagnostics.py pools every task and the whole
sequence. This looks at one change at a time: for the first step of each
(task, sequence), which every trial attempts, it gives each program's
number of working repetitions and a one-way program share (random-effects
ANOVA on 0/1 outcomes, programs random). A step where some programs always
pass and the others always fail has a share near 1; a step every program
passes, or every program fails, has no variance to split.

Usage (from harness/, inside WSL):
    uv run python scripts/step_effects.py --config configs/rtx5070_train.yaml
"""

import argparse
from pathlib import Path

from diagnostics import first_change_measures, scored_programs

from harness.config import load_config
from harness.registry import load_tasks


def program_share(groups):
    """One-way random-effects program share for equal-size groups, or None
    when there is nothing to split."""
    k, n = len(groups), len(groups[0])
    if k < 2 or n < 2:
        return None
    means = [sum(g) / n for g in groups]
    grand = sum(means) / k
    msb = n * sum((m - grand) ** 2 for m in means) / (k - 1)
    msw = sum((x - m) ** 2 for g, m in zip(groups, means, strict=True) for x in g) / (k * (n - 1))
    between = max((msb - msw) / n, 0.0)
    total = between + msw
    return between / total if total > 0 else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    cfg = load_config(args.config)
    tasks = load_tasks(cfg.tasks)
    scores, records, _ = scored_programs(cfg)
    works = first_change_measures(cfg, scores, records)["first change works"]
    rows = []
    for record in records:
        per = works.get(record.task_id, {})
        if len(per) < 2:
            continue
        for j, seq in enumerate(record.sequence_ids):
            groups = [per[c][j] for c in per]
            change = tasks[record.task_id].sequence(seq).steps[0].change
            request = change.request.strip().splitlines()[0]
            rows.append(
                (
                    program_share(groups),
                    record.task_id,
                    seq,
                    sorted(int(sum(g)) for g in groups),
                    f"[{change.kind}] {request[:80]}",
                )
            )
    rows.sort(key=lambda r: -1 if r[0] is None else r[0], reverse=True)
    shares = [r[0] for r in rows if r[0] is not None]
    print(f"{len(rows)} first steps of tasks with 2 or more programs")
    print(f"- no variance (every program the same): {len(rows) - len(shares)}")
    print(f"- program share 0: {sum(s == 0 for s in shares)}")
    print(f"- program share above 0 and below 25%: {sum(0 < s < 0.25 for s in shares)}")
    print(f"- program share 25% or more: {sum(s >= 0.25 for s in shares)}")
    print(f"- program share 50% or more: {sum(s >= 0.5 for s in shares)}")
    print()
    print("| Program share | Task | Sequence | Working reps per program | First change |")
    print("|---:|---|---|---|---|")
    for share, task_id, seq, counts, change in rows:
        cell = "–" if share is None else f"{share:.0%}"
        print(f"| {cell} | {task_id} | {seq} | {' '.join(map(str, counts))} | {change} |")


if __name__ == "__main__":
    main()
