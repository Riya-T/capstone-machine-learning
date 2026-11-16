"""Does the size of the editor's successful edits carry over between sequences?

If a program's changes need small edits on one sequence and small edits on
the other, edit size is a lasting property of the program and could serve
as a label. Three measures of each successful step:

- lines changed (added plus removed), as log(1 + lines);
- tokens the editor wrote, as log(1 + tokens);
- existing functions and methods the step modified (body changed or
  removed).

Each is taken relative to the mean of all successful trials of the same
task, sequence and step, and a program's value on a sequence is its mean
over its successful steps and reps (lower: smaller edits than the other
programs needed for the same changes). Per task, the program with the
smallest value on one sequence is compared with the task's mean on the
other, both ways round (negative: its edits stay smaller there too).
Intervals resample the tasks.

Usage (from harness/, inside WSL):
    uv run python scripts/edit_carryover.py --config configs/rtx5070_train.yaml
"""

import argparse
import ast
import math
import random
from collections import defaultdict
from pathlib import Path

from diagnostics import pearson, ranks, scored_programs

from harness.collection.collect import Keys, sandbox_owner
from harness.config import load_config
from harness.registry import load_tasks
from harness.sandbox.runner import make_runner
from harness.store import Store, TrialKey


def mean(xs):
    xs = [x for x in xs if not math.isnan(x)]
    return sum(xs) / len(xs) if xs else math.nan


def functions(program):
    out = {}
    for path, data in program.items():
        try:
            tree = ast.parse(data.decode())
        except SyntaxError:
            return None
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out[f"{path}:{node.name}"] = ast.dump(node)
            elif isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        out[f"{path}:{node.name}.{sub.name}"] = ast.dump(sub)
    return out


def touched(before, after):
    fb, fa = functions(before), functions(after)
    if fb is None or fa is None:
        return None
    return sum(1 for k, v in fb.items() if fa.get(k) != v)


def step_values(cfg, scores, records, programs):
    """measure -> {(task, candidate, sequence index): [(step, value)]}."""
    editor = Keys.of(cfg, make_runner(cfg, owner=sandbox_owner(cfg)).existing_image_id()).editor
    tasks = load_tasks(cfg.tasks)
    out = defaultdict(lambda: defaultdict(list))
    with Store(cfg.runs_dir) as store:
        for record in records:
            task = tasks[record.task_id]
            for cid in scores[record.task_id]:
                for j, seq in enumerate(record.sequence_ids):
                    for rep in range(cfg.editor.reps):
                        trial = TrialKey(task.id, task.task_version, cid, seq, rep, editor)
                        before = programs[cid]
                        for st in store.trial_steps(trial):
                            if st.status != "success" or not st.output_blob:
                                break
                            after = store.get_blob(st.output_blob)
                            key = (record.task_id, cid, j)
                            if st.diff_lines is not None:
                                out["lines changed"][key].append(
                                    (st.step, math.log1p(st.diff_lines))
                                )
                            if st.tokens_out is not None:
                                out["tokens written"][key].append(
                                    (st.step, math.log1p(st.tokens_out))
                                )
                            n = touched(before, after)
                            if n is not None:
                                out["functions modified"][key].append((st.step, float(n)))
                            before = after
    return out


def carryover(raw):
    """Per task: (held-out gain of the program with the smallest value,
    Spearman correlation of the two sequences' values or None)."""
    pooled = defaultdict(list)
    for (t, _, j), xs in raw.items():
        for step, x in xs:
            pooled[t, j, step].append(x)
    step_mean = {k: mean(v) for k, v in pooled.items()}
    by_task = defaultdict(set)
    for t, cid, _ in raw:
        by_task[t].add(cid)
    rows = {}
    for t, cids in by_task.items():
        cids = sorted(c for c in cids if (t, c, 0) in raw and (t, c, 1) in raw)
        if len(cids) < 2:
            continue
        val = {
            (c, j): mean([x - step_mean[t, j, s] for s, x in raw[t, c, j]])
            for c in cids
            for j in (0, 1)
        }
        a, b = [val[c, 0] for c in cids], [val[c, 1] for c in cids]
        ia, ib = min(range(len(a)), key=a.__getitem__), min(range(len(b)), key=b.__getitem__)
        gain = ((b[ia] - mean(b)) + (a[ib] - mean(a))) / 2
        corr = pearson(ranks(a), ranks(b)) if len(cids) >= 3 else None
        rows[t] = (gain, corr)
    return rows


def bootstrap(values, n, seed):
    rng = random.Random(seed)
    values = list(values)
    stats = sorted(mean([rng.choice(values) for _ in values]) for _ in range(n))
    return stats[int(0.025 * n)], stats[int(0.975 * n) - 1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    cfg = load_config(args.config)
    scores, records, programs = scored_programs(cfg)
    values = step_values(cfg, scores, records, programs)
    print("| Measure | Tasks | Smallest on one sequence, on the other (95%) | Spearman A vs B |")
    print("|---|---:|---|---:|")
    for name in ("lines changed", "tokens written", "functions modified"):
        rows = carryover(values[name])
        gains = [g for g, _ in rows.values()]
        corrs = [c for _, c in rows.values() if c is not None]
        low, high = bootstrap(gains, args.bootstrap, args.seed)
        unit = "functions" if name == "functions modified" else "log units"
        print(
            f"| {name} | {len(rows)} | {mean(gains):+.3f} {unit} ({low:+.3f} to {high:+.3f}) "
            f"| {mean(corrs):+.2f} ({len(corrs)} tasks) |"
        )


if __name__ == "__main__":
    main()
