"""Command line for the pipeline.

Commands (all take --config):
    collect         run writer sampling, initial checks, editing trials and
                    scoring; resumable, and a complete rerun makes no model calls
    validate-tasks  check each task's tests against its references and
                    planted bugs in the sandbox; exit status 1 on any problem
    report          rebuild preferences.jsonl and preferences_report.json from
                    the store, with no model calls (default: <runs_dir>/report)

Usage (from pilot/):
    uv run python -m pipeline collect --config configs/pilot_mock.yaml
    uv run python -m pipeline validate-tasks --config configs/pilot_mock.yaml
    uv run python -m pipeline report --config configs/pilot_mock.yaml [--out DIR]
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from .collect import collect, report, sandbox_owner
from .config import ConfigError, load_config
from .evaluator import Evaluator
from .registry import TaskError, load_tasks
from .runner import SandboxError, SandboxRunner
from .store import StoreError

log = logging.getLogger("pipeline")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m pipeline", description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    for name, text in [
        ("collect", "run the pipeline (resumable)"),
        ("validate-tasks", "check task tests against references and planted bugs"),
        ("report", "rebuild the preference files from the store"),
    ]:
        sub = commands.add_parser(name, help=text)
        sub.add_argument("--config", required=True, type=Path)
        if name == "report":
            sub.add_argument("--out", type=Path, help="output directory")
    args = parser.parse_args(argv)
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    try:
        cfg = load_config(args.config)
        if args.command == "collect":
            collect(cfg)
        elif args.command == "report":
            report(cfg, args.out)
        else:
            return validate_tasks(cfg)
    except (ConfigError, TaskError, StoreError, SandboxError) as exc:
        log.error("%s", exc)
        return 2
    return 0


def validate_tasks(cfg) -> int:
    runner = SandboxRunner(cfg.sandbox, owner=sandbox_owner(cfg))
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
