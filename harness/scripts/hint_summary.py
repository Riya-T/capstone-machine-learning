"""Per design hint: how the programs drawn with it fared in editing.

For a config whose writer draws samples with design hints
(writer.design_hints; sample i gets hint i mod the number of hints), each
distinct program counts for the hint of the first sample that produced it.
Per hint it reports the programs that passed the initial checks, the
programs the editor worked on, and their score (changes done before the
first failure, averaged over sequences and reps), both as a mean and against
the mean of their task's edited programs. The last is what matters for
training: a hint whose programs beat their task's average is a design the
editor finds easier to change, and a writer trained on the pairs would move
towards it. Intervals resample the tasks.

Usage (from harness/, inside WSL):
    uv run python scripts/hint_summary.py --config configs/rtx5070_pc_hints.yaml
"""

import argparse
import math
from collections import defaultdict
from pathlib import Path

from diagnostics import bootstrap, scored_programs

from harness.config import load_config


def mean(xs):
    return sum(xs) / len(xs) if xs else math.nan


def fmt(x, sign=False):
    return "–" if math.isnan(x) else f"{x:+.2f}" if sign else f"{x:.2f}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    cfg = load_config(args.config)
    hints = cfg.writer.design_hints or ("",)
    scores, records, _ = scored_programs(cfg)

    passed = defaultdict(int)
    # hint -> task -> scores of its edited programs; task -> every edited score
    edited = defaultdict(lambda: defaultdict(list))
    task_scores = defaultdict(list)
    for record in records:
        for c in record.candidates:
            hint = min(c.sample_indices) % len(hints)
            passed[hint] += bool(c.initially_passed)
            reps = scores[record.task_id].get(c.candidate_id)
            if reps is not None:
                score = mean([mean(r) for r in reps])
                edited[hint][record.task_id].append(score)
                task_scores[record.task_id].append(score)

    tasks = sorted(task_scores)
    print(f"{len(tasks)} tasks; score = changes done per sequence, mean over sequences and reps")
    print("| Hint | Passed initially | Edited | Mean score | Against its task's mean (95%) |")
    print("|---|---:|---:|---:|---|")
    for h, hint in enumerate(hints):
        per_task = {
            t: [s - mean(task_scores[t]) for s in edited[h][t]] for t in tasks if edited[h][t]
        }

        def gap(values):
            return mean([d for ds in values for d in ds])

        low, high = bootstrap(per_task.values(), gap, args.bootstrap, args.seed)
        all_scores = [s for t in tasks for s in edited[h][t]]
        label = (hint[:50] + "…") if len(hint) > 50 else (hint or "(none)")
        print(
            f"| {h}: {label} | {passed[h]} | {len(all_scores)} | {fmt(mean(all_scores))} "
            f"| {fmt(gap(per_task.values()), True)} ({fmt(low, True)} to {fmt(high, True)}) |"
        )

    print("\nMean score per task and hint:")
    print("| Task | " + " | ".join(str(h) for h in range(len(hints))) + " | All |")
    print("|---|" + "---:|" * (len(hints) + 1))
    for t in tasks:
        cells = [fmt(mean(edited[h][t])) for h in range(len(hints))]
        print(f"| {t} | " + " | ".join(cells) + f" | {fmt(mean(task_scores[t]))} |")


if __name__ == "__main__":
    main()
