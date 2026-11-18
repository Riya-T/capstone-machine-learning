"""Which designs a writer's programs use, and how each design fared in editing.

Reads the store only. Each distinct program a config's writer produced is
put in one class by a static look at its code:

- `log`: it records its operations. Some attribute whose name speaks of
  history (ops, operations, history, log, events, journal, actions,
  transactions, commands, changes, undo) is appended to outside `__init__`.
- `snapshot`: it copies its whole state (`copy.deepcopy` or `copy.copy`)
  in a method that is not a getter.
- `plain`: neither.

Per writer it reports the share of each class among the programs that
passed the initial checks, and, for the programs the editor worked on, each
class's score (changes done before the first failure, mean over sequences
and repetitions) against its task's mean. History-suite tasks
(tasks/HISTORY_SUITE.md) reward the first two in their undo change.

Usage (from harness/, inside WSL):
    uv run python scripts/design_classes.py --writer base=configs/rtx5070_hist_dev.yaml \
        --writer hints=configs/rtx5070_hist_dev_hints.yaml
"""

import argparse
import ast
import math
import re
from collections import defaultdict
from pathlib import Path

from diagnostics import bootstrap, scored_programs

from harness.config import load_config

CLASSES = ("log", "snapshot", "plain")
HISTORY = re.compile(
    r"(^|_)(ops?|operations?|history|hist|logs?|events?|journal|actions?|transactions?"
    r"|commands?|changes?|undo\w*)($|_)",
    re.IGNORECASE,
)


def source(program) -> str:
    """A stored program (file name -> bytes) as one string of code."""
    if isinstance(program, dict):
        return "\n".join(source(v) for v in program.values())
    return program.decode("utf-8", "replace") if isinstance(program, bytes) else str(program)


def classify(code: str) -> str:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return "plain"
    appended = defaultdict(set)  # attribute -> methods that append to it
    copies = False
    for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
        for method in (n for n in cls.body if isinstance(n, ast.FunctionDef)):
            getter = method.name.startswith("get_") or method.name == "__init__"
            for node in ast.walk(method):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                target = node.func.value
                if (
                    method.name != "__init__"
                    and node.func.attr in ("append", "extend")
                    and isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    appended[target.attr].add(method.name)
                if node.func.attr in ("deepcopy", "copy") and not getter:
                    copies |= isinstance(target, ast.Name) and target.id == "copy"
        for node in ast.walk(cls):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                copies |= node.func.id == "deepcopy"
    if any(HISTORY.search(attr) for attr in appended):
        return "log"
    return "snapshot" if copies else "plain"


def mean(xs):
    return sum(xs) / len(xs) if xs else math.nan


def fmt(x, sign=False):
    return "–" if math.isnan(x) else f"{x:+.2f}" if sign else f"{x:.2f}"


def writer_rows(cfg, n, seed):
    scores, records, programs = scored_programs(cfg)
    passed = defaultdict(int)
    edited = defaultdict(lambda: defaultdict(list))  # class -> task -> scores
    task_scores = defaultdict(list)
    for record in records:
        for c in record.candidates:
            if not c.initially_passed:
                continue
            kind = classify(source(programs[c.candidate_id]))
            passed[kind] += 1
            reps = scores[record.task_id].get(c.candidate_id)
            if reps is not None:
                score = mean([mean(r) for r in reps])
                edited[kind][record.task_id].append(score)
                task_scores[record.task_id].append(score)
    total = sum(passed.values())
    rows = []
    for kind in CLASSES:
        per_task = {
            t: [s - mean(task_scores[t]) for s in edited[kind][t]]
            for t in task_scores
            if edited[kind][t]
        }

        def gap(values):
            return mean([d for ds in values for d in ds])

        low, high = bootstrap(per_task.values(), gap, n, seed) if per_task else (math.nan,) * 2
        count = sum(len(v) for v in edited[kind].values())
        all_scores = [s for v in edited[kind].values() for s in v]
        rows.append(
            f"{kind} | {passed[kind]} of {total} ({passed[kind] / total:.0%}) | {count} | "
            f"{fmt(mean(all_scores))} | {fmt(gap(per_task.values()), True)} "
            f"({fmt(low, True)} to {fmt(high, True)})"
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--writer", action="append", required=True, help="label=config")
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    print(
        "| Writer | Design | Passing programs | Edited | Mean score "
        "| Against its task's mean (95%) |"
    )
    print("|---|---|---:|---:|---:|---|")
    for spec in args.writer:
        label, path = spec.split("=", 1)
        for row in writer_rows(load_config(Path(path)), args.bootstrap, args.seed):
            print(f"| {label} | {row} |")


if __name__ == "__main__":
    main()
