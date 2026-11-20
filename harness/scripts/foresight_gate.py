"""Foresight gate: do programs written with the task's later changes in view
fare better with the editor than the same writer's plain programs?

Compares two configs on the same tasks and editor: --plain (the writer's
plain prompt) and --foresight (a design hint with $later_changes,
harness/foresight.py). Both are scored with the smaller of their editor
reps, so a plain store collected with more reps reads the same first
trials. Per task it reports how many writer samples pass the initial
checks, how many of the passing foresight programs implement a later change
early (left out of everything after), and the mean score of the edited
programs (changes done before the first failure, per sequence, averaged
over sequences and reps, then over programs). Differences get a paired task
bootstrap over the tasks where both have edited programs. With 2 or more
reps it also reports each group's program share of the score variance
(diagnostics.py), which is what preference pairs can learn from.

Usage (from harness/, inside WSL):
    uv run python scripts/foresight_gate.py --plain configs/rtx5070_pc.yaml \
        --foresight configs/rtx5070_pc_foresight.yaml
"""

import argparse
import dataclasses
import math
from pathlib import Path

from diagnostics import scored_programs, variance_components, variance_sums
from eval_summary import percentile_interval

from harness.config import load_config
from harness.foresight import defined_names, later_change_names
from harness.registry import load_tasks


def mean(xs):
    return sum(xs) / len(xs) if xs else math.nan


def with_reps(cfg, reps):
    return dataclasses.replace(cfg, editor=dataclasses.replace(cfg.editor, reps=reps))


def group(cfg, tasks, drop_early: bool):
    """task_id -> (samples, passing samples, {early program: names},
    {edited program: scores}, passing programs)."""
    scores, records, programs = scored_programs(cfg)
    out = {}
    for record in records:
        names = later_change_names(tasks[record.task_id])
        samples = len(record.parse_failures) + sum(len(c.sample_indices) for c in record.candidates)
        passing = sum(len(c.sample_indices) for c in record.candidates if c.initially_passed)
        early = {
            c.candidate_id: sorted(defined_names(programs[c.candidate_id]) & names)
            for c in record.candidates
            if c.initially_passed and defined_names(programs[c.candidate_id]) & names
        }
        edited = {
            cid: reps
            for cid, reps in scores[record.task_id].items()
            if not (drop_early and cid in early)
        }
        programs_passing = sum(1 for c in record.candidates if c.initially_passed)
        out[record.task_id] = (samples, passing, early, edited, programs_passing)
    return out


def program_mean(seqs):
    return mean([mean(reps) for reps in seqs])


def program_share(groups):
    v = variance_components([variance_sums(g[3]) for g in groups.values() if g[3]])
    if v is None:
        return math.nan
    total = v["program"] + v["program x sequence"] + v["trial"]
    return v["program"] / total if total else math.nan


def fmt(x, spec=".2f"):
    return "–" if isinstance(x, float) and math.isnan(x) else format(x, spec)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--plain", required=True, type=Path)
    parser.add_argument("--foresight", required=True, type=Path)
    parser.add_argument("--bootstrap", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20261105)
    args = parser.parse_args()
    plain_cfg, fs_cfg = load_config(args.plain), load_config(args.foresight)
    reps = min(plain_cfg.editor.reps, fs_cfg.editor.reps)
    tasks = load_tasks(fs_cfg.tasks)
    plain = group(with_reps(plain_cfg, reps), tasks, drop_early=False)
    fs = group(with_reps(fs_cfg, reps), tasks, drop_early=True)

    print(f"Scored with {reps} rep(s) per sequence.\n")
    print("| Task | Plain: passing samples | Foresight: passing samples | Early (left out) "
          "| Plain: edited, mean | Foresight: edited, mean |")  # fmt: skip
    print("|---|---|---|---|---|---|")
    rows = []
    for t in sorted(tasks):
        p, f = plain.get(t), fs.get(t)
        if p is None or f is None:
            continue
        pm = mean([program_mean(s) for s in p[3].values()])
        fm = mean([program_mean(s) for s in f[3].values()])
        early = ", ".join(sorted({n for names in f[2].values() for n in names})) or "–"
        print(f"| {t} | {p[1]}/{p[0]} | {f[1]}/{f[0]} | {len(f[2])} ({early}) | "
              f"{len(p[3])}, {fmt(pm)} | {len(f[3])}, {fmt(fm)} |")  # fmt: skip
        if p[3] and f[3]:
            pr, fr = p[1] / p[0] if p[0] else 0.0, f[1] / f[0] if f[0] else 0.0
            rows.append((pm, fm, fm - pm, pr, fr, fr - pr))

    print(f"\nPaired task bootstrap over the {len(rows)} tasks where both have edited programs "
          f"({args.bootstrap} resamples, seed {args.seed}):\n")  # fmt: skip
    if rows:
        k = len(rows)
        iv = percentile_interval(rows, args.bootstrap, args.seed)
        avg = [sum(r[i] for r in rows) / k for i in range(6)]
        print("| Measure | Plain | Foresight | Difference (95%) |")
        print("|---|---:|---:|---|")
        print(f"| Changes done before first failure (per sequence) | {avg[0]:.2f} | {avg[1]:.2f} "
              f"| {avg[2]:+.2f} ({iv[2][0]:+.2f} to {iv[2][1]:+.2f}) |")  # fmt: skip
        lo, hi = (x * 100 for x in iv[5])
        print(f"| Samples passing the initial checks | {avg[3]:.0%} | {avg[4]:.0%} "
              f"| {avg[5] * 100:+.0f} pts ({lo:+.0f} to {hi:+.0f}) |")  # fmt: skip
    early = sum(len(f[2]) for f in fs.values())
    passing = sum(f[4] for f in fs.values())
    print(f"\nForesight programs that implement a later change early: {early} of {passing} "
          f"passing programs.")  # fmt: skip
    if reps >= 2:
        print(f"Program share of the score variance: plain {fmt(program_share(plain), '.0%')}, "
              f"foresight {fmt(program_share(fs), '.0%')}.")  # fmt: skip


if __name__ == "__main__":
    main()
