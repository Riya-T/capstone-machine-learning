"""Per-task editing results for one writer on the tasks of a config.

Reads the store only (no model, no container). For each task it takes the
same programs the scorer uses (passing programs, up to max_programs, in
sample order) and reports, over their trials (sequence x rep):

- changes done before the first failure (mean, out of the sequence length);
- how often the first change works;
- how often the whole sequence works.

Trials with an infrastructure error or not finished yet are left out and
counted separately. The averages give every task the same weight. With
--bootstrap N it also gives 95% intervals by resampling the tasks.
`scripts/eval_compare.py` compares two writers task by task.

Usage (from harness/, inside WSL):
    uv run python scripts/eval_summary.py --config configs/rtx5070_eval.yaml
    uv run python scripts/eval_summary.py --config configs/rtx5070_eval.yaml --out results.md
    uv run python scripts/eval_summary.py --config configs/rtx5070_eval.yaml --bootstrap 20000
"""

import argparse
import random
from collections import Counter
from pathlib import Path

from harness.collection.collect import Keys, sandbox_owner
from harness.collection.scorer import load_task_record
from harness.config import load_config
from harness.registry import build_writer_prompt, load_tasks, load_template
from harness.sandbox.runner import make_runner
from harness.store import Store

METRICS = ("mean", "first", "full")
METRIC_NAMES = ("Changes done before first failure", "First change works", "Whole sequence works")


def task_results(cfg):
    """One dict per task (task_id, length, programs, trials, mean, first,
    full, samples, passing_samples), plus the step endings and the trials
    left out. Tasks without finished trials get trials 0 and no metrics."""
    image_id = make_runner(cfg, owner=sandbox_owner(cfg)).existing_image_id()
    if image_id is None:
        raise SystemExit("sandbox image not found; results are keyed by its id")
    keys = Keys.of(cfg, image_id)
    template = load_template(cfg.writer.prompt_template)
    tasks = load_tasks(cfg.tasks)
    rows, endings, left_out = [], Counter(), Counter()
    with Store(cfg.runs_dir) as store:
        for task_id in sorted(tasks):
            task = tasks[task_id]
            record = load_task_record(
                store,
                task,
                build_writer_prompt(task.writer_view(), template),
                writer_hash=keys.writer,
                sandbox_hash=keys.sandbox,
                editor_hash=keys.editor,
                editor_reps=cfg.editor.reps,
                max_sequences=cfg.tasks.max_sequences,
                max_programs=cfg.tasks.max_programs,
            )
            length = record.sequence_length
            samples = len(record.parse_failures) + sum(
                len(c.sample_indices) for c in record.candidates
            )
            passing = sum(len(c.sample_indices) for c in record.candidates if c.initially_passed)
            done, programs = [], 0
            for cand in record.candidates:
                if not cand.initially_passed or cand.over_program_cap:
                    continue
                programs += 1
                for seq_id in record.sequence_ids:
                    for rep in range(cfg.editor.reps):
                        steps = cand.trials.get((seq_id, rep), {})
                        statuses = [steps.get(n) for n in range(1, length + 1)]
                        if "infra_error" in statuses:
                            left_out["infra_error"] += 1
                            continue
                        n = 0
                        while n < length and statuses[n] == "success":
                            n += 1
                        if n < length and statuses[n] is None:
                            left_out["not finished"] += 1
                            continue
                        done.append(n)
                        endings.update(s for s in statuses if s)
            row = dict(task_id=task_id, length=length, programs=programs, trials=len(done),
                       samples=samples, passing_samples=passing)  # fmt: skip
            if done:
                row.update(
                    mean=sum(done) / len(done),
                    first=sum(d >= 1 for d in done) / len(done),
                    full=sum(d == length for d in done) / len(done),
                )
            rows.append(row)
    return rows, endings, left_out


def summarize(cfg, bootstrap: int = 0, seed: int = 20261105) -> str:
    rows, endings, left_out = task_results(cfg)
    lines = [
        "| Task | Programs | Trials | Changes done before first failure | "
        "First change works | Whole sequence works |",
        "|---|---|---|---|---|---|",
    ]
    scored = [r for r in rows if r["trials"]]
    for r in rows:
        if not r["trials"]:
            lines.append(f"| {r['task_id']} | {r['programs']} | 0 | - | - | - |")
            continue
        lines.append(
            f"| {r['task_id']} | {r['programs']} | {r['trials']} | {r['mean']:.2f} of "
            f"{r['length']} | {r['first']:.0%} | {r['full']:.0%} |"
        )
    t = len(scored) or 1
    avg = {m: sum(r[m] for r in scored) / t for m in METRICS}
    lines.append(
        f"| **Average over {len(scored)} tasks** | {sum(r['programs'] for r in rows)} | "
        f"{sum(r['trials'] for r in rows)} | {avg['mean']:.2f} | {avg['first']:.0%} | "
        f"{avg['full']:.0%} |"
    )
    lines += ["", "Step endings: " + ", ".join(f"{k} {v}" for k, v in endings.most_common())]
    if left_out:
        lines.append("Trials left out: " + ", ".join(f"{k} {v}" for k, v in left_out.items()))
    if bootstrap and scored:
        per_task = [tuple(r[m] for m in METRICS) for r in scored]
        lines += ["", *bootstrap_lines(per_task, bootstrap, seed)]
    return "\n".join(lines)


def percentile_interval(values, n, seed):
    """Percentile 95% intervals of the averages of each column of `values`
    (one tuple per task), resampling the tasks with replacement n times."""
    rng = random.Random(seed)
    k = len(values)
    means = [[] for _ in values[0]]
    for _ in range(n):
        sample = [values[rng.randrange(k)] for _ in range(k)]
        for i in range(len(means)):
            means[i].append(sum(s[i] for s in sample) / k)
    out = []
    for column in means:
        column.sort()
        out.append((column[int(0.025 * n)], column[int(0.975 * n) - 1]))
    return out


def bootstrap_lines(per_task, n, seed):
    """Percentile 95% intervals of the task averages, resampling tasks (each
    eval task is its own family) with replacement, from the exact per-task
    values."""
    k = len(per_task)
    out = [
        f"Task bootstrap ({n} resamples of the {k} tasks, seed {seed}), 95% intervals:",
        "",
        "| Metric | Estimate | 95% interval |",
        "|---|---:|---:|",
    ]
    intervals = percentile_interval(per_task, n, seed)
    for i, (name, (lo, hi)) in enumerate(zip(METRIC_NAMES, intervals, strict=True)):
        est = sum(s[i] for s in per_task) / k
        fmt = "{:.2f}" if i == 0 else "{:.0%}"
        out.append(f"| {name} | {fmt.format(est)} | {fmt.format(lo)}–{fmt.format(hi)} |")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", type=Path, help="also write the table to this file")
    parser.add_argument("--bootstrap", type=int, default=0, help="task bootstrap resamples")
    parser.add_argument("--seed", type=int, default=20261105, help="bootstrap seed")
    args = parser.parse_args()
    text = summarize(load_config(args.config), args.bootstrap, args.seed)
    print(text)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
