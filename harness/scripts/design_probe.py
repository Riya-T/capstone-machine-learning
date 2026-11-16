"""Edit hand-written variants of a task's program through its change sequences.

Checks whether a design choice changes how often the editor manages a task's
changes, apart from the writer: each variant directory holds a complete
program for the task's initial spec (it must pass the initial checks), and
every sequence runs --reps times per variant, stopping at the first failed
step like a collection trial. The editor and sandbox come from --config.
Model answers are cached in --store (a separate store, never the
collection's), so a rerun with the same variants replays them.

Usage (from harness/, inside WSL; the variants used so far are in
results/design_probe/):
    .venv/bin/python scripts/design_probe.py --config configs/rtx5070_pilot.yaml \\
        --task sample_freezers --variant state=results/design_probe/sample_freezers/state \\
        --variant log=results/design_probe/sample_freezers/log --reps 6 \\
        --store /home/pc/design_probe/store
"""

from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from pathlib import Path

from harness.collection.editor import Editor
from harness.config import load_config
from harness.models.backends import CachedBackend, derive_seed, make_backend
from harness.registry import load_tasks
from harness.sandbox.evaluator import Evaluator
from harness.sandbox.runner import make_runner
from harness.store import Store


def read_program(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts
    }


def failed_tests(result) -> list[str]:
    return [c.node_id.split("::")[-1] for c in result.cases if c.outcome != "passed"]


def run_trial(editor, evaluator, backend, program, sequence) -> list[dict]:
    """One trial: the sequence's steps in order, up to the first failure."""
    current = editor.view(program)
    steps = []
    for step in sequence.steps:
        outcome = editor.edit(backend, current, step)
        row = {"change": step.change.id, "turns": outcome.turns, "reason": outcome.reason}
        if outcome.status != "done":
            steps.append(row | {"status": outcome.status})
            break
        evaluation = evaluator.check_step(outcome.program, step)
        steps.append(
            row
            | {
                "status": evaluation.status,
                "new": f"{evaluation.new_feature.passed}/{evaluation.new_feature.total}",
                "failed": failed_tests(evaluation.new_feature) + failed_tests(evaluation.existing),
            }
        )
        if evaluation.status != "success":
            break
        current = outcome.program
    return steps


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--task", required=True)
    parser.add_argument("--variant", required=True, action="append", metavar="NAME=DIR")
    parser.add_argument("--sequence", action="append", help="sequence ids (default: all)")
    parser.add_argument("--reps", type=int, default=6)
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--out", type=Path, help="JSONL file for every trial")
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING)

    cfg = load_config(args.config)
    task = load_tasks(cfg.tasks)[args.task]
    runner = make_runner(cfg, owner="design-probe")
    runner.ensure_image()
    evaluator = Evaluator(runner, workers=cfg.execution.sandbox_workers)
    editor = Editor(cfg.editor, evaluator)
    sequences = [s for s in task.sequences if not args.sequence or s.id in args.sequence]
    out = args.out.open("a", encoding="utf-8") if args.out else None

    with Store(args.store) as store:
        for spec in args.variant:
            name, _, path = spec.partition("=")
            program = read_program(Path(path))
            initial = evaluator.check_initial(program, task)
            if not initial.passed:
                print(
                    f"{name}: fails the initial checks:",
                    failed_tests(initial.public) + failed_tests(initial.initial),
                )
                continue
            for sequence in sequences:
                done = []
                for rep in range(args.reps):
                    seed = derive_seed(cfg.seed, task.id, name, sequence.id, rep, "editor")
                    backend = CachedBackend(make_backend(cfg.editor.backend, seed), store)
                    steps = run_trial(editor, evaluator, backend, program, sequence)
                    score = sum(s["status"] == "success" for s in steps)
                    done.append(score)
                    print(
                        f"{name} {sequence.id} rep {rep}: {score} | "
                        + " ; ".join(
                            f"{s['change']} {s['status']} {s.get('new', '')}"
                            f" {','.join(s.get('failed', [])[:4])}"
                            for s in steps
                        ),
                        flush=True,
                    )
                    if out:
                        row = {
                            "task": task.id,
                            "variant": name,
                            "sequence": sequence.id,
                            "rep": rep,
                            "score": score,
                            "steps": steps,
                        }
                        out.write(json.dumps(row) + "\n")
                        out.flush()
                if done:
                    print(
                        f"== {name} {sequence.id}: mean {sum(done) / len(done):.2f} "
                        f"changes, {dict(sorted(Counter(done).items()))}",
                        flush=True,
                    )


if __name__ == "__main__":
    main()
