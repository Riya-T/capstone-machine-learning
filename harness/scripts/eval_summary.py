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


def summarize(cfg, bootstrap: int = 0, seed: int = 20261105) -> str:
    image_id = make_runner(cfg, owner=sandbox_owner(cfg)).existing_image_id()
    if image_id is None:
        raise SystemExit("sandbox image not found; results are keyed by its id")
    keys = Keys.of(cfg, image_id)
    template = load_template(cfg.writer.prompt_template)
    tasks = load_tasks(cfg.tasks)
    lines = [
        "| Task | Programs | Trials | Changes done before first failure | "
        "First change works | Whole sequence works |",
        "|---|---|---|---|---|---|",
    ]
    totals = Counter()
    endings = Counter()
    left_out = Counter()
    per_task = []  # (mean, first, full) per task with trials, for the bootstrap
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
            if not done:
                lines.append(f"| {task_id} | {programs} | 0 | - | - | - |")
                continue
            mean = sum(done) / len(done)
            first = sum(d >= 1 for d in done) / len(done)
            full = sum(d == length for d in done) / len(done)
            lines.append(
                f"| {task_id} | {programs} | {len(done)} | {mean:.2f} of {length} "
                f"| {first:.0%} | {full:.0%} |"
            )
            totals.update(
                tasks=1, programs=programs, trials=len(done), mean=mean, first=first, full=full
            )
            per_task.append((mean, first, full))
    t = totals["tasks"] or 1
    lines.append(
        f"| **Average over {totals['tasks']} tasks** | {totals['programs']} | "
        f"{totals['trials']} | {totals['mean'] / t:.2f} | {totals['first'] / t:.0%} | "
        f"{totals['full'] / t:.0%} |"
    )
    lines += ["", "Step endings: " + ", ".join(f"{k} {v}" for k, v in endings.most_common())]
    if left_out:
        lines.append("Trials left out: " + ", ".join(f"{k} {v}" for k, v in left_out.items()))
    if bootstrap and per_task:
        lines += ["", *bootstrap_lines(per_task, bootstrap, seed)]
    return "\n".join(lines)


def bootstrap_lines(per_task, n, seed):
    """Percentile 95% intervals of the task averages, resampling tasks (each
    eval task is its own family) with replacement, from the exact per-task
    values."""
    rng = random.Random(seed)
    k = len(per_task)
    means = [[] for _ in range(3)]
    for _ in range(n):
        sample = [per_task[rng.randrange(k)] for _ in range(k)]
        for i in range(3):
            means[i].append(sum(s[i] for s in sample) / k)
    out = [
        f"Task bootstrap ({n} resamples of the {k} tasks, seed {seed}), 95% intervals:",
        "",
        "| Metric | Estimate | 95% interval |",
        "|---|---:|---:|",
    ]
    names = ["Changes done before first failure", "First change works", "Whole sequence works"]
    for i, name in enumerate(names):
        est = sum(s[i] for s in per_task) / k
        lo, hi = sorted(means[i])[int(0.025 * n)], sorted(means[i])[int(0.975 * n) - 1]
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
