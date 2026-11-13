"""What separates the editor's winners from its losers, and did training move it?

Reads the store and a training file only. Measures static features of each
program (size, functions and classes, Radon's Maintainability Index and
cyclomatic complexity, comments, validation code, duplicated lines, ...),
then:

- per feature, the Spearman correlation with the program's editing score
  within each task, averaged over tasks (programs of --config, pooled);
- a logistic regression on the feature differences of the training pairs
  (--pairs), tested by leaving one task out at a time;
- per feature, how a trained writer's passing programs differ from the base
  writer's on the same tasks (--writer, against the first --config), in
  standard deviations of the base writer's programs.

Intervals resample the tasks.

Usage (from harness/, inside WSL):
    uv run python scripts/winner_features.py --config configs/rtx5070_train.yaml \
        --pairs runs/rtx5070_pc/dpo/pairs_cap8_f23_nocosm.jsonl \
        --base configs/rtx5070_eval.yaml --writer configs/rtx5070_eval_dpo3.yaml
"""

import argparse
import ast
import json
import math
import re
from collections import Counter
from pathlib import Path

import numpy as np
from diagnostics import bootstrap, load_records, pearson, ranks, scored_programs
from radon.complexity import cc_visit
from radon.metrics import mi_visit

from harness.config import load_config

BLOCK = re.compile(r"```python file=\S+\n(.*?)```", re.S)
VALIDATION = re.compile(r"^_*(validate|check|ensure|require|assert|verify)", re.I)


def features(source: str) -> dict[str, float] | None:
    """Static features of a program's Python source, or None if it does not
    parse."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    lines = source.splitlines()
    code = [x for x in lines if x.strip() and not x.strip().startswith("#")]
    comments = sum(x.strip().startswith("#") or " # " in x for x in lines)
    functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)]
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    lengths = [n.end_lineno - n.lineno + 1 for n in functions] or [0]
    docstrings = sum(
        1
        for n in [tree, *functions, *classes]
        if n.body
        and isinstance(n.body[0], ast.Expr)
        and isinstance(n.body[0].value, ast.Constant)
        and isinstance(n.body[0].value.value, str)
    )
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    names = Counter(n.func.id for n in calls if isinstance(n.func, ast.Name))
    bases = [b.id for c in classes for b in c.bases if isinstance(b, ast.Name)]
    args = [a for f in functions for a in f.args.args if a.arg not in ("self", "cls")]
    stripped = [x.strip() for x in code if len(x.strip()) > 20]
    try:
        complexity = [b.complexity for b in cc_visit(source)] or [1]
        mi = mi_visit(source, multi=True)
    except Exception:  # radon fails on a few valid programs
        return None
    return {
        "lines of code": len(code),
        "functions and methods": len(functions),
        "classes": len(classes),
        "mean function length": sum(lengths) / len(lengths),
        "longest function": max(lengths),
        "max nesting depth": nesting(tree),
        "mean cyclomatic complexity": sum(complexity) / len(complexity),
        "max cyclomatic complexity": max(complexity),
        "Radon MI": mi,
        "comment lines share": comments / max(1, len(lines)),
        "docstrings": docstrings,
        "raise statements": sum(isinstance(n, ast.Raise) for n in ast.walk(tree)),
        "isinstance calls": names["isinstance"],
        "validation helpers": sum(bool(VALIDATION.match(f.name)) for f in functions),
        "private helpers": sum(
            f.name.startswith("_") and not f.name.startswith("__") for f in functions
        ),
        "dataclasses": sum(
            any("dataclass" in ast.unparse(d) for d in c.decorator_list) for c in classes
        ),
        "exception classes": sum(b.endswith(("Error", "Exception")) for b in bases),
        "module constants": sum(
            isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id.isupper() for t in n.targets)
            for n in tree.body
        ),
        "if statements": sum(isinstance(n, ast.If) for n in ast.walk(tree)),
        "try blocks": sum(isinstance(n, ast.Try) for n in ast.walk(tree)),
        "comprehensions": sum(
            isinstance(n, ast.ListComp | ast.DictComp | ast.SetComp | ast.GeneratorExp)
            for n in ast.walk(tree)
        ),
        "annotated arguments share": sum(a.annotation is not None for a in args)
        / max(1, len(args)),
        "duplicated lines": sum(c - 1 for c in Counter(stripped).values() if c > 1),
    }


def nesting(node, depth=0) -> int:
    blocks = (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.AsyncFor, ast.AsyncWith)
    deepest = depth
    for child in ast.iter_child_nodes(node):
        deepest = max(deepest, nesting(child, depth + isinstance(child, blocks)))
    return deepest


def program_source(program) -> str:
    return "\n".join(
        data.decode("utf-8", "replace")
        for path, data in sorted(program.items())
        if path.endswith(".py")
    )


def score_correlations(paths, n, seed):
    """Feature -> (mean within-task Spearman correlation with the program's
    mean score, 95% interval, tasks)."""
    per_task = {}
    for path in paths:
        scores, _, programs = scored_programs(load_config(path))
        for task_id, progs in scores.items():
            entry = per_task.setdefault(task_id, {})
            for cid, seqs in progs.items():
                f = features(program_source(programs[cid]))
                if f is not None:
                    entry[cid] = (sum(sum(r) / len(r) for r in seqs) / len(seqs), f)
    out = {}
    names = next(iter(next(v for v in per_task.values() if v).values()))[1].keys()
    for name in names:
        values = []
        for entry in per_task.values():
            if len(entry) < 4:
                continue
            r = pearson(
                ranks([s for s, _ in entry.values()]), ranks([f[name] for _, f in entry.values()])
            )
            if r is not None:
                values.append(r)
        if values:
            lo, hi = bootstrap(values, lambda v: sum(v) / len(v), n, seed)
            out[name] = (sum(values) / len(values), lo, hi, len(values))
    return out


def pair_features(path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        chosen = features("\n".join(BLOCK.findall(row["chosen"])))
        rejected = features("\n".join(BLOCK.findall(row["rejected"])))
        if chosen and rejected:
            rows.append((row["task_id"], chosen, rejected))
    return rows


def fit_logistic(x, y, l2=1.0, steps=500):
    """L2-regularized logistic regression without intercept, by Newton steps."""
    w = np.zeros(x.shape[1])
    for _ in range(steps):
        p = 1 / (1 + np.exp(-x @ w))
        grad = x.T @ (p - y) + l2 * w
        hess = x.T @ (x * (p * (1 - p))[:, None]) + l2 * np.eye(x.shape[1])
        step = np.linalg.solve(hess, grad)
        w -= step
        if np.abs(step).max() < 1e-8:
            break
    return w


def pair_classifier(rows, names):
    """Leave-one-task-out accuracy of a logistic regression on standardized
    feature differences (each pair used both ways round), the per-task
    accuracies, and the weights fitted on all pairs."""
    diffs = np.array([[c[k] - r[k] for k in names] for _, c, r in rows], dtype=float)
    scale = diffs.std(axis=0)
    scale[scale == 0] = 1
    diffs = diffs / scale
    tasks = [t for t, _, _ in rows]
    per_task = {}
    for task in sorted(set(tasks)):
        train = np.array([t != task for t in tasks])
        x = np.vstack([diffs[train], -diffs[train]])
        y = np.concatenate([np.ones(train.sum()), np.zeros(train.sum())])
        w = fit_logistic(x, y)
        test = diffs[~train]
        per_task[task] = [float(v) for v in (test @ w > 0)]
    x = np.vstack([diffs, -diffs])
    y = np.concatenate([np.ones(len(diffs)), np.zeros(len(diffs))])
    return per_task, fit_logistic(x, y), scale


def writer_programs(path):
    """task_id -> feature dicts of the writer's distinct passing programs."""
    records, programs = load_records(load_config(path))
    out = {}
    for record in records:
        rows = []
        for c in record.candidates:
            if c.initially_passed:
                f = features(program_source(programs[c.candidate_id]))
                if f is not None:
                    rows.append(f)
        if rows:
            out[record.task_id] = rows
    return out


def shifts(base, other, names, n, seed):
    """Feature -> (mean over tasks of other minus base mean, in base standard
    deviations pooled within task, 95% interval)."""
    out = {}
    common = sorted(base.keys() & other.keys())
    for name in names:
        variances = [np.var([f[name] for f in base[t]]) for t in common if len(base[t]) > 1]
        sd = math.sqrt(sum(variances) / len(variances)) or 1.0
        per_task = [
            (np.mean([f[name] for f in other[t]]) - np.mean([f[name] for f in base[t]])) / sd
            for t in common
        ]
        lo, hi = bootstrap(per_task, lambda v: sum(v) / len(v), n, seed)
        out[name] = (sum(per_task) / len(per_task), lo, hi)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", type=Path, action="append", required=True,
                        help="programs whose scores the features are correlated with")  # fmt: skip
    parser.add_argument("--pairs", type=Path, help="training file for the pair classifier")
    parser.add_argument("--base", type=Path, help="base writer config for the shifts")
    parser.add_argument("--writer", type=Path, action="append", default=[])
    parser.add_argument("--bootstrap", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20261105)
    args = parser.parse_args()
    n, seed = args.bootstrap, args.seed

    correlations = score_correlations(args.config, n, seed)
    names = list(correlations)
    lines = [
        "Within-task Spearman correlation of each feature with the program's editing score:",
        "",
        "| Feature | Correlation | 95% interval | Tasks |",
        "|---|---:|---:|---:|",
    ]
    for name, (r, lo, hi, k) in sorted(correlations.items(), key=lambda x: -abs(x[1][0])):
        lines.append(f"| {name} | {r:+.2f} | {lo:+.2f} to {hi:+.2f} | {k} |")

    weights = scale = None
    if args.pairs:
        rows = pair_features(args.pairs)
        per_task, weights, scale = pair_classifier(rows, names)
        flat = [v for vs in per_task.values() for v in vs]

        def pooled_share(groups):
            return sum(sum(x) for x in groups) / sum(len(x) for x in groups)

        lo, hi = bootstrap(list(per_task.values()), pooled_share, n, seed)
        lines += [
            "",
            f"Pair classifier ({len(rows)} pairs, {len(per_task)} tasks, leave one task out): "
            f"{sum(flat) / len(flat):.0%} correct (95% interval {lo:.0%} to {hi:.0%}).",
            "Largest weights (on all pairs; positive means the chosen program has more): "
            + ", ".join(f"{names[i]} {weights[i]:+.2f}" for i in np.argsort(-np.abs(weights))[:6])
            + ".",
        ]

    if args.base and args.writer:
        base = writer_programs(args.base)
        for path in args.writer:
            other = writer_programs(path)
            moved = shifts(base, other, names, n, seed)
            lines += [
                "",
                f"{path.stem} against {args.base.stem}, passing programs, in base standard "
                "deviations (mean over tasks):",
                "",
                "| Feature | Shift | 95% interval | Winners have more (correlation) |",
                "|---|---:|---:|---:|",
            ]
            for name, (d, lo, hi) in sorted(moved.items(), key=lambda x: -abs(x[1][0])):
                lines.append(f"| {name} | {d:+.2f} | {lo:+.2f} to {hi:+.2f} | "
                             f"{correlations[name][0]:+.2f} |")  # fmt: skip
            if weights is not None:
                common = sorted(base.keys() & other.keys())

                def logit(rows):
                    x = np.array([[f[k] for k in names] for f in rows], dtype=float) / scale
                    return float(np.mean(x @ weights))

                per_task = [logit(other[t]) - logit(base[t]) for t in common]
                lo, hi = bootstrap(per_task, lambda v: sum(v) / len(v), n, seed)
                lines.append(
                    f"\nPair classifier's score, {path.stem} minus base (mean over tasks): "
                    f"{sum(per_task) / len(per_task):+.2f} ({lo:+.2f} to {hi:+.2f}); "
                    "positive means more like the training winners."
                )
    print("\n".join(lines))


if __name__ == "__main__":
    main()
