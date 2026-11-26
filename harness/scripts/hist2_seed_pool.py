"""Mean over training seeds, per task, for two groups of history-suite eval writers.

For each task, a group's score is the mean over its writers of each writer's
task score (changes done before the first failure over its edited passing
programs, as in eval_compare.py; and per writer sample, a sample failing the
initial checks counting 0, as in /home/pc/uncond.py). Only tasks where every
writer of both groups has an edited program count for the first measure;
every task counts for the second. The difference of the two groups gets the
paired task bootstrap of eval_compare.py. Fixed before the run of the
second-round seeds (docs/progress_report.md, "Second-round seeds").

Usage (from harness/scripts, inside WSL):
    PYTHONPATH=. ../.venv/bin/python hist2_seed_pool.py \
        --group r2=_hist2_r2a,_hist2_r2a_s43,_hist2_r2a_s44 \
        --group d=_hist2_rpo_d,_hist2_rpo_d_s43,_hist2_rpo_d_s44

With --config ../configs/rtx5070_eval{}.yaml the same pooling runs on the
original testbed's eval writers (e.g. --group base=base
--group dpo3=_dpo3,_dpo3_s2,_dpo3_s3).
"""

import argparse

from eval_summary import percentile_interval, task_results

from harness.config import load_config

CONFIG = "../configs/rtx5070_hist2_eval{}.yaml"


def per_sample(row):
    if row is None or not row["samples"] or not row["trials"]:
        return 0.0
    return row["passing_samples"] / row["samples"] * row["mean"]


def load(suffixes, config=CONFIG):
    return [
        {r["task_id"]: r for r in task_results(load_config(config.format(s)))[0]} for s in suffixes
    ]


def line(name, diffs, n, seed):
    k = len(diffs)
    (_, _), (_, _), (lo, hi) = percentile_interval(diffs, n, seed)
    a = sum(d[0] for d in diffs) / k
    b = sum(d[1] for d in diffs) / k
    return (
        f"{name}: {k} tasks. Second {b:.2f}, first {a:.2f}, "
        f"difference {b - a:+.2f} (95% {lo:+.2f} to {hi:+.2f})"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--group", action="append", required=True, help="NAME=suffix,suffix,...")
    parser.add_argument("--bootstrap", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20261105)
    parser.add_argument(
        "--config", default=CONFIG, help="config path pattern; {} takes each suffix"
    )
    args = parser.parse_args()
    if len(args.group) != 2:
        parser.error("give exactly two groups: --group FIRST=... --group SECOND=...")
    groups = []
    for g in args.group:
        name, suffixes = g.split("=", 1)
        suffixes = ["" if s == "base" else s for s in suffixes.split(",")]
        groups.append((name, load(suffixes, args.config)))
    tasks = sorted(set().union(*(rows.keys() for _, g in groups for rows in g)))
    edited, sample = [], []
    for t in tasks:
        means = []
        for _, g in groups:
            rows = [r.get(t) for r in g]
            means.append(
                None
                if any(r is None or not r["trials"] for r in rows)
                else sum(r["mean"] for r in rows) / len(rows)
            )
        if None not in means:
            edited.append((means[0], means[1], means[1] - means[0]))
        ps = [sum(per_sample(r.get(t)) for r in g) / len(g) for _, g in groups]
        sample.append((ps[0], ps[1], ps[1] - ps[0]))
    print(f"{groups[1][0]} minus {groups[0][0]}, mean over each group's writers per task")
    print(line("Changes done before first failure", edited, args.bootstrap, args.seed))
    print(line("Per writer sample", sample, args.bootstrap, args.seed))


if __name__ == "__main__":
    main()
