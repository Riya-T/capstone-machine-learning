"""Command line for the harness.

Commands (all take --config):
    collect         run the whole pipeline; safe to stop and rerun, and a
                    finished rerun makes no model calls. --until writer,
                    initial or edit stops after that step.
    validate-tasks  check that each task's tests pass its reference solutions
                    and fail its planted bugs; exits with 1 on any problem.
    report          rebuild the preference files from stored results, with
                    no model calls (default output: <runs_dir>/report).

Usage (from harness/):
    uv run python -m harness collect --config configs/mock.yaml [--until initial]
    uv run python -m harness validate-tasks --config configs/mock.yaml
    uv run python -m harness report --config configs/mock.yaml [--out DIR]
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from .collection.collect import collect, report, sandbox_owner
from .config import ConfigError, load_config
from .registry import TaskError, load_tasks
from .sandbox.evaluator import Evaluator
from .sandbox.runner import SandboxError, make_runner
from .store import StoreError

log = logging.getLogger("harness")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m harness", description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    for name, text in [
        ("collect", "run the pipeline (resumable)"),
        ("validate-tasks", "check task tests against references and planted bugs"),
        ("report", "rebuild the preference files from the store"),
    ]:
        sub = commands.add_parser(name, help=text)
        sub.add_argument("--config", required=True, type=Path)
        if name == "collect":
            sub.add_argument(
                "--until",
                choices=("writer", "initial", "edit"),
                default="edit",
                help="stop after this stage (default: edit, the whole pipeline)",
            )
        if name == "report":
            sub.add_argument("--out", type=Path, help="output directory")
    args = parser.parse_args(argv)
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    try:
        cfg = load_config(args.config)
        if args.command == "collect":
            collect(cfg, until=args.until)
        elif args.command == "report":
            report(cfg, args.out)
        else:
            return validate_tasks(cfg)
    except (ConfigError, TaskError, StoreError, SandboxError) as exc:
        log.error("%s", exc)
        return 2
    return 0


def validate_tasks(cfg) -> int:
    runner = make_runner(cfg, owner=sandbox_owner(cfg))
    runner.ensure_image()
    evaluator = Evaluator(runner, workers=cfg.execution.sandbox_workers)
    failed = 0
    for task in load_tasks(cfg.tasks).values():
        problems = evaluator.validate_task(task)
        if problems:
            failed += 1
            log.error("%s: %d problems", task.id, len(problems))
            for problem in problems:
                log.error("  %s", problem)
        else:
            log.info("%s: ok", task.id)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
