"""Editing scores of the history-suite eval writers within tasks and design classes.

Reads the store only. For each writer of the history-suite eval (base, the
prompted control, D with seeds 42, 43 and 44, the second-round writer with
seeds 42, 43 and 44, the correctness-only control) it
puts each edited passing program in a design class (`design_classes.py`)
and prints, per task, the mean score of each class (changes done before
the first failure, mean over sequences and repetitions). Then it compares
one writer's programs of one class with another writer's programs of a
class, on the tasks where both have such programs, with the paired task
bootstrap of `eval_compare.py`. Post hoc for seeds 42 and 43 of D; fixed
before the run for D seed 44 and the second-round writers. See
results/hist2_eval.md.

Usage (from harness/scripts, inside WSL):
    PYTHONPATH=. ../.venv/bin/python hist2_design_within.py
"""

import random
from collections import defaultdict

from design_classes import classify, mean, source
from diagnostics import scored_programs

from harness.config import load_config

CONFIG = "../configs/rtx5070_hist2_eval{}.yaml"
WRITERS = {
    "base": "",
    "prompted": "_hinted",
    "d42": "_hist2_rpo_d",
    "d43": "_hist2_rpo_d_s43",
    "d44": "_hist2_rpo_d_s44",
    "r2": "_hist2_r2a",
    "r2s43": "_hist2_r2a_s43",
    "r2s44": "_hist2_r2a_s44",
    "control": "_hist2_sft",
}
COMPARISONS = (
    ("d42", "plain", "base", "plain"),
    ("d43", "plain", "base", "plain"),
    ("d44", "plain", "base", "plain"),
    ("r2", "plain", "base", "plain"),
    ("r2s43", "plain", "base", "plain"),
    ("r2s44", "plain", "base", "plain"),
    ("control", "plain", "base", "plain"),
    ("d42", "snapshot", "prompted", "snapshot"),
    ("d43", "snapshot", "prompted", "snapshot"),
    ("d44", "snapshot", "prompted", "snapshot"),
    ("r2", "snapshot", "prompted", "snapshot"),
    ("r2s43", "snapshot", "prompted", "snapshot"),
    ("r2s44", "snapshot", "prompted", "snapshot"),
    ("d42", "plain", "prompted", "snapshot"),
    ("d43", "plain", "prompted", "snapshot"),
    ("d44", "plain", "prompted", "snapshot"),
    ("r2", "plain", "prompted", "snapshot"),
    ("r2s43", "plain", "prompted", "snapshot"),
    ("r2s44", "plain", "prompted", "snapshot"),
    ("prompted", "snapshot", "base", "plain"),
)


def class_scores(path):
    """task -> design class -> scores of the edited passing programs."""
    scores, records, programs = scored_programs(load_config(path))
    out = defaultdict(lambda: defaultdict(list))
    for record in records:
        for c in record.candidates:
            reps = scores[record.task_id].get(c.candidate_id)
            if not c.initially_passed or reps is None:
                continue
            kind = classify(source(programs[c.candidate_id]))
            out[record.task_id][kind].append(mean([mean(r) for r in reps]))
    return out


def compare(data, tasks, a, ka, b, kb, n=20000, seed=20261105):
    pairs = [
        (mean(data[a][t][ka]), mean(data[b][t][kb]))
        for t in tasks
        if data[a][t].get(ka) and data[b][t].get(kb)
    ]
    if not pairs:
        return f"{a} {ka} vs {b} {kb}: no shared tasks"
    rng = random.Random(seed)
    boots = sorted(
        mean([x - y for x, y in (pairs[rng.randrange(len(pairs))] for _ in pairs)])
        for _ in range(n)
    )
    lo, hi = boots[int(0.025 * n)], boots[int(0.975 * n) - 1]
    diff = mean([x - y for x, y in pairs])
    return (
        f"{a} {ka} minus {b} {kb}: {diff:+.2f} ({lo:+.2f} to {hi:+.2f}), {len(pairs)} tasks; "
        f"means {mean([x for x, _ in pairs]):.2f} vs {mean([y for _, y in pairs]):.2f}"
    )


def main() -> None:
    data = {w: class_scores(CONFIG.format(s)) for w, s in WRITERS.items()}
    tasks = sorted({t for d in data.values() for t in d})
    print("| Task | " + " | ".join(WRITERS) + " |")
    print("|---|" + "---|" * len(WRITERS))
    for t in tasks:
        cells = [
            ", ".join(f"{k} {mean(v):.2f} ({len(v)})" for k, v in sorted(data[w][t].items())) or "-"
            for w in WRITERS
        ]
        print(f"| {t} | " + " | ".join(cells) + " |")
    print()
    for args in COMPARISONS:
        print(compare(data, tasks, *args))


if __name__ == "__main__":
    main()
