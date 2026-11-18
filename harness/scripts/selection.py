"""Best-of-k selection by the editor: pick by one change sequence, score on the other.

Reads the store only. For each writer config, per task, among every subset
of k of the programs the scorer uses (passing, distinct, at most
max_programs), the program with the best mean on sequence A over `probe`
repetitions is scored on sequence B (its mean over all of B's repetitions)
and compared with the mean of all the task's programs on B, which is what a
program picked at random would get. Both ways round, averaged; tied best
programs share the place. Sequence B's changes and trials never take part
in the pick, so a gain means the editor's results on some changes find
programs that are easier to change in other ways too. With probe 1, each
repetition of A in turn is the probe, averaged.

Writers are given as label=config. The mean over writers gives each task
one value (the mean of its writers' gains). Intervals resample the tasks.

Usage (from harness/, inside WSL):
    uv run python scripts/selection.py --writer base=configs/rtx5070_eval.yaml \
        --writer dpo3=configs/rtx5070_eval_dpo3.yaml --out results/selection.md
"""

import argparse
import statistics
from itertools import combinations
from pathlib import Path

from diagnostics import bootstrap, scored_programs

from harness.config import load_config

KS = (2, 4, 8)
PROBES = (1, 3)


def best_score(select, score):
    """Mean `score` of the programs tied for the best `select`."""
    top = max(select)
    picked = [s for p, s in zip(select, score, strict=True) if p == top]
    return sum(picked) / len(picked)


def task_gain(programs, k, probe):
    """Held-out gain of best-of-k (k capped at the task's programs) with a
    probe of `probe` repetitions, or None for a task without 2 programs
    and 2 sequences."""
    seqs = list(programs.values())
    if len(seqs) < 2 or len(seqs[0]) < 2:
        return None
    k = min(k, len(seqs))
    gains = []
    for a, b in ((0, 1), (1, 0)):
        score = [statistics.fmean(p[b]) for p in seqs]
        mean = statistics.fmean(score)
        reps = len(seqs[0][a])
        probes = [range(reps)] if probe >= reps else [[r] for r in range(reps)]
        for chosen in probes:
            select = [statistics.fmean(p[a][r] for r in chosen) for p in seqs]
            for subset in combinations(range(len(seqs)), k):
                gains.append(
                    best_score([select[i] for i in subset], [score[i] for i in subset]) - mean
                )
    return statistics.fmean(gains)


def average_program(scores):
    """Mean over tasks of the mean over programs of the sequence means."""
    per_task = [
        statistics.fmean(statistics.fmean(statistics.fmean(s) for s in seqs) for seqs in p.values())
        for p in scores.values()
        if p
    ]
    return statistics.fmean(per_task)


def interval(values, n, seed):
    return bootstrap(values, statistics.fmean, n, seed)


def report(writers, n, seed):
    gains = {
        label: {
            (k, probe): {
                t: g for t, p in scores.items() if (g := task_gain(p, k, probe)) is not None
            }
            for k in KS
            for probe in PROBES
        }
        for label, scores in writers.items()
    }
    lines = [
        "Held-out gain of picking the best of k programs by one sequence, scored on",
        "the other (changes per sequence, against a program picked at random):",
        "",
        "| Writer | Average program | "
        + " | ".join(f"Best of {k}, probe {p} rep{'s' * (p > 1)}" for k in KS for p in PROBES)
        + " |",
        "|---|---:|" + "---:|" * (len(KS) * len(PROBES)),
    ]
    for label, scores in writers.items():
        cells = []
        for k in KS:
            for probe in PROBES:
                values = list(gains[label][k, probe].values())
                lo, hi = interval(values, n, seed)
                cells.append(f"{statistics.fmean(values):+.2f} ({lo:+.2f} to {hi:+.2f})")
        lines.append(f"| {label} | {average_program(scores):.2f} | " + " | ".join(cells) + " |")
    if len(writers) > 1:
        cells = []
        for k in KS:
            for probe in PROBES:
                tasks = set.intersection(*(set(g[k, probe]) for g in gains.values()))
                values = [
                    statistics.fmean(g[k, probe][t] for g in gains.values()) for t in sorted(tasks)
                ]
                lo, hi = interval(values, n, seed)
                cells.append(f"{statistics.fmean(values):+.2f} ({lo:+.2f} to {hi:+.2f})")
        lines.append(f"| Mean over the {len(writers)} writers | | " + " | ".join(cells) + " |")

    k, probe = max(KS), max(PROBES)
    lines += [
        "",
        f"Per task, best of {k} with a {probe}-repetition probe (tasks with fewer programs",
        "use all of them):",
        "",
        "| Writer | Tasks up / down / same | Without the task with the largest gain "
        "| Largest gains |",
        "|---|---:|---:|---|",
    ]
    for label, g in gains.items():
        per_task = g[k, probe]
        up = sum(v > 1e-9 for v in per_task.values())
        down = sum(v < -1e-9 for v in per_task.values())
        top = max(per_task, key=per_task.get)
        rest = [v for t, v in per_task.items() if t != top]
        lo, hi = interval(rest, n, seed)
        largest = ", ".join(
            f"{t} {v:+.2f}" for t, v in sorted(per_task.items(), key=lambda x: -x[1])[:3]
        )
        lines.append(
            f"| {label} | {up} / {down} / {len(per_task) - up - down} | "
            f"{statistics.fmean(rest):+.2f} ({lo:+.2f} to {hi:+.2f}) | {largest} |"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--writer", action="append", required=True, help="label=config")
    parser.add_argument("--bootstrap", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20261105)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    writers = {}
    for spec in args.writer:
        label, path = spec.split("=", 1)
        writers[label] = scored_programs(load_config(Path(path)))[0]
    text = report(writers, args.bootstrap, args.seed)
    print(text)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
