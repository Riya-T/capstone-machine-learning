"""Where an editor-view ablation differs from the normal run, program by program.

Reads the store only. Takes pairs of configs (normal, ablation) that differ
only in `editor.view_transform`. For the programs each writer's eval edits
(the ones `eval_summary.py` uses) it reports:

- how many programs the view changes (for strip_comments: programs with
  comments or docstrings), and how many bytes of their .py files it removes;
- whether every trial of an unchanged program is identical to the normal
  run's, step by step (status and output program). It should be: the editor
  gets the same prompt with the same seed, so the replies come from the
  store;
- changes done before the first failure on the changed programs, normal
  against ablation, trial by trial. The averages give every task the same
  weight, and the interval resamples the tasks (a paired task bootstrap).

With several pairs it adds a row that pools the changed programs of all of
them.

Usage (from harness/, inside WSL):
    uv run python scripts/ablation_compare.py \
        configs/rtx5070_eval.yaml configs/rtx5070_eval_nocomments.yaml \
        configs/rtx5070_eval_maintain.yaml configs/rtx5070_eval_maintain_nocomments.yaml
"""

import argparse
from collections import defaultdict
from dataclasses import replace
from pathlib import Path

from eval_summary import percentile_interval

from harness.collection.collect import Keys, sandbox_owner
from harness.collection.scorer import load_task_record
from harness.collection.view import make_view
from harness.config import load_config
from harness.registry import build_writer_prompt, load_tasks, load_template
from harness.sandbox.runner import make_runner
from harness.store import Store, TrialKey


def compare_pair(normal_cfg, ablation_cfg):
    """Counts for one writer, and task -> [(normal, ablation)] scores of the
    trials of the programs the view changes."""
    image_id = make_runner(normal_cfg, owner=sandbox_owner(normal_cfg)).existing_image_id()
    if image_id is None:
        raise SystemExit("sandbox image not found; results are keyed by its id")
    keys, ablation_keys = Keys.of(normal_cfg, image_id), Keys.of(ablation_cfg, image_id)
    if keys.writer != ablation_keys.writer or keys.editor == ablation_keys.editor:
        raise SystemExit("the two configs must share the writer and differ in the editor")
    view = make_view(ablation_cfg.editor.view_transform)
    template = load_template(normal_cfg.writer.prompt_template)
    tasks = load_tasks(normal_cfg.tasks)
    counts = defaultdict(int)
    scores = defaultdict(list)
    with Store(normal_cfg.runs_dir) as store:
        for task_id in sorted(tasks):
            task = tasks[task_id]
            record = load_task_record(
                store,
                task,
                build_writer_prompt(task.writer_view(), template),
                writer_hash=keys.writer,
                sandbox_hash=keys.sandbox,
                editor_hash=keys.editor,
                editor_reps=normal_cfg.editor.reps,
                max_sequences=normal_cfg.tasks.max_sequences,
                max_programs=normal_cfg.tasks.max_programs,
            )
            for cand in record.candidates:
                if not cand.initially_passed or cand.over_program_cap:
                    continue
                program = store.get_blob(cand.candidate_id)
                shown = view(program)
                changed = shown != program
                counts["programs"] += 1
                counts["changed"] += changed
                counts["bytes"] += sum(len(v) for p, v in program.items() if p.endswith(".py"))
                counts["removed"] += sum(len(program[p]) - len(shown[p]) for p in program)
                for seq_id in record.sequence_ids:
                    for rep in range(normal_cfg.editor.reps):
                        trial = TrialKey(task.id, task.task_version, cand.candidate_id, seq_id, rep,
                                         keys.editor)  # fmt: skip
                        normal = store.trial_steps(trial)
                        ablation = store.trial_steps(
                            replace(trial, editor_cfg_hash=ablation_keys.editor)
                        )
                        a = score(normal, record.sequence_length)
                        b = score(ablation, record.sequence_length)
                        if a is None or b is None:
                            counts["left out"] += 1
                        elif changed:
                            counts["changed trials"] += 1
                            scores[task_id].append((a, b))
                        else:
                            counts["unchanged trials"] += 1
                            counts["identical"] += steps_of(normal) == steps_of(ablation)
    return counts, scores


def score(steps, length):
    """Changes done before the first failure, or None for a trial with an
    infrastructure error or not finished yet."""
    statuses = {c.step: c.status for c in steps}
    if "infra_error" in statuses.values():
        return None
    n = 0
    while n < length and statuses.get(n + 1) == "success":
        n += 1
    if n < length and n + 1 not in statuses:
        return None
    return n


def steps_of(steps):
    return [(c.step, c.status, c.output_blob) for c in steps]


def effect(scores, n, seed):
    """(tasks, trials, normal mean, ablation mean, (lo, hi)) with every task
    weighted the same; None without changed programs."""
    if not scores:
        return None
    per_task = []
    for pairs in scores.values():
        a = sum(p[0] for p in pairs) / len(pairs)
        b = sum(p[1] for p in pairs) / len(pairs)
        per_task.append((a, b, b - a))
    k = len(per_task)
    interval = percentile_interval(per_task, n, seed)[2]
    trials = sum(len(p) for p in scores.values())
    return k, trials, sum(t[0] for t in per_task) / k, sum(t[1] for t in per_task) / k, interval


def effect_cells(e):
    if e is None:
        return "– | – | – | –"
    k, trials, a, b, (lo, hi) = e
    return f"{k} tasks, {trials} trials | {a:.2f} → {b:.2f} | {b - a:+.2f} | {lo:+.2f} to {hi:+.2f}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("configs", nargs="+", type=Path, help="normal, ablation, in pairs")
    parser.add_argument("--bootstrap", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20261105)
    args = parser.parse_args()
    if len(args.configs) % 2:
        parser.error("configs come in pairs: normal, ablation")
    lines = [
        "| Writer config | Programs changed by the view | Bytes removed | Unchanged programs: "
        "trials identical to the normal run | Changed programs | Changes done before first "
        "failure, normal → ablation | Difference | 95% interval |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    pooled = defaultdict(list)
    left_out = 0
    for normal_path, ablation_path in zip(args.configs[::2], args.configs[1::2], strict=True):
        counts, scores = compare_pair(load_config(normal_path), load_config(ablation_path))
        for task_id, pairs in scores.items():
            pooled[task_id].extend(pairs)
        left_out += counts["left out"]
        share = counts["removed"] / counts["bytes"]
        lines.append(
            f"| {normal_path.stem} | {counts['changed']} of {counts['programs']} | "
            f"{counts['removed']:,} of {counts['bytes']:,} ({share:.2%}) | "
            f"{counts['identical']} of {counts['unchanged trials']} | "
            f"{effect_cells(effect(scores, args.bootstrap, args.seed))} |"
        )
    if len(args.configs) > 2:
        cells = effect_cells(effect(pooled, args.bootstrap, args.seed))
        lines.append(f"| all pooled | | | | {cells} |")
    lines += [
        "",
        f"Paired task bootstrap ({args.bootstrap} resamples, seed {args.seed}); every task "
        f"weighted the same. Trials left out (infrastructure error or not finished in either run): "
        f"{left_out}.",
    ]
    print("\n".join(lines))


if __name__ == "__main__":
    main()
