"""Do a run's programs still pass the initial checks once obscured?

The readability control (`editor.view_transform: obscure`,
`collection/view.py`) renames private names, data attributes and local
variables, which a test that reads a data attribute directly would notice.
This runs the initial checks (in the sandbox) on the obscured version of
every program the scorer uses in --config's store, and prints any that
fail, how many names of each kind changed, and one program before and
after.

Usage (from harness/, inside WSL):
    uv run python scripts/obscure_check.py --config configs/rtx5070_pc.yaml
"""

import argparse
import re
from pathlib import Path

from diagnostics import scored_programs

from harness.collection.view import obscure
from harness.config import load_config
from harness.registry import load_tasks
from harness.sandbox.evaluator import Evaluator
from harness.sandbox.runner import make_runner


def failed(result) -> list[str]:
    cases = result.public.cases + result.initial.cases
    return [c.node_id.split("::")[-1] for c in cases if c.outcome != "passed"]


def renamed(program) -> dict[str, int]:
    """Distinct new names of each kind in the obscured program."""
    text = b"\n".join(obscure(program).values()).decode("utf-8", "replace")
    kinds = {"private names": r"\b_x\d+\b", "data attributes": r"\.a\d+\b", "locals": r"\bv\d+\b"}
    return {kind: len(set(re.findall(pattern, text))) for kind, pattern in kinds.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    cfg = load_config(args.config)
    scores, _, programs = scored_programs(cfg)
    tasks = load_tasks(cfg.tasks)
    runner = make_runner(cfg, owner="obscure-check")
    runner.ensure_image()
    evaluator = Evaluator(runner, workers=cfg.execution.sandbox_workers)
    n = bad = 0
    totals = {}
    for task_id, scored in sorted(scores.items()):
        for cid in scored:
            n += 1
            for kind, count in renamed(programs[cid]).items():
                totals[kind] = totals.get(kind, 0) + count
            result = evaluator.check_initial(obscure(programs[cid]), tasks[task_id])
            if not result.passed:
                bad += 1
                print(f"FAIL {task_id} {cid[:8]}: {', '.join(failed(result)[:5])}")
    print(f"{n} programs, {bad} fail the initial checks once obscured")
    print(
        "Mean names renamed per program: "
        + ", ".join(f"{k} {v / n:.1f}" for k, v in totals.items())
    )
    task_id, scored = sorted(scores.items())[0]
    program = programs[next(iter(scored))]
    for title, shown in (("before", program), ("after", obscure(program))):
        for path, data in shown.items():
            print(f"\n--- {task_id} {path} ({title})\n{data.decode('utf-8', 'replace')}")


if __name__ == "__main__":
    main()
