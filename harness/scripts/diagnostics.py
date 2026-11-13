"""How much room the eval leaves, and how stable the editing labels are.

Reads the store only. For the programs a config's editor worked on (the
scorer's eligible programs: passing, distinct, at most max_programs per
task), it reports:

- Headroom: per task, pick the program that did best on one change
  sequence and score it on the other sequence, against the task's average
  there (both ways round, averaged). This is the largest gain on held-out
  changes any writer could show by favouring its better samples; picking the
  best by both sequences at once (in-sample) is shown as an upper bound.
- Stability: for every pair of programs of a task, does the program that
  wins on sequence A also win on sequence B? Compared with how often two
  repetitions of the same sequence agree, so the noise of one trial is
  visible next to the difference between sequences. With --pairs, the same
  for the pairs of a training file.
- Variance components: how much of the variance of one trial's score
  within a task belongs to the program, to the program on that particular
  sequence, and to the trial (the editor's randomness), and how reliably a
  program's mean score measures its program part with more sequences or
  reps. With --measures, the same for other measures of the first change
  (editor calls, reply tokens, lines changed, share of hidden tests passed).

Scores are changes done before the first failure, per sequence (the main
measure averages the sequences). Intervals resample the tasks.

Usage (from harness/, inside WSL):
    uv run python scripts/diagnostics.py --config configs/rtx5070_train.yaml \
        --pairs runs/rtx5070_pc/dpo/pairs_cap8_f23_nocosm.jsonl
    uv run python scripts/diagnostics.py --config configs/rtx5070_eval.yaml
    uv run python scripts/diagnostics.py --config configs/rtx5070_eval.yaml \
        --config configs/rtx5070_eval_dpo3.yaml   # programs of both writers, pooled
"""

import argparse
import json
import math
import random
from collections import Counter
from itertools import combinations
from pathlib import Path

from harness.collection.collect import Keys, sandbox_owner
from harness.collection.scorer import Scorer, load_task_record
from harness.config import load_config
from harness.registry import build_writer_prompt, load_tasks, load_template
from harness.sandbox.runner import make_runner
from harness.store import Store, TrialKey


def load_records(cfg):
    """The config's task records (its writer's samples and its editor's
    trials) and every distinct program of them, by candidate id."""
    image_id = make_runner(cfg, owner=sandbox_owner(cfg)).existing_image_id()
    if image_id is None:
        raise SystemExit("sandbox image not found; results are keyed by its id")
    keys = Keys.of(cfg, image_id)
    template = load_template(cfg.writer.prompt_template)
    tasks = load_tasks(cfg.tasks)
    records, programs = [], {}
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
            records.append(record)
            for c in record.candidates:
                programs[c.candidate_id] = store.get_blob(c.candidate_id)
    return records, programs


def scored_programs(cfg):
    """task_id -> {candidate_id: per-sequence, per-rep scores} of the
    programs the scorer uses, plus the task records and programs."""
    records, programs = load_records(cfg)
    scorer = Scorer(cfg.scorer, cfg.editor.reps)
    scores = {}
    for record in records:
        eligible = scorer.score_task(record)[0]
        scores[record.task_id] = {c.candidate_id: c.rep_scores for c in eligible}
    return scores, records, programs


def top_k_gain(select, score, k):
    """Mean `score` of the k programs best on `select` (ties broken at
    random, so tied programs share the boundary places), minus the mean of
    all programs' `score`."""
    order = sorted(range(len(select)), key=lambda i: -select[i])
    weights = [0.0] * len(select)
    place = 0
    while place < k:
        tied = [i for i in order if select[i] == select[order[place]]]
        share = min(len(tied), k - place) / len(tied)
        for i in tied:
            weights[i] = share
        place += len(tied)
    return sum(w * s for w, s in zip(weights, score, strict=True)) / k - sum(score) / len(score)


def headroom(scores):
    """Per task with at least 2 programs and 2 sequences: (held-out gain of
    the best program, held-out gain of the top half, in-sample gain of the
    best program)."""
    rows = {}
    for task_id, programs in scores.items():
        if len(programs) < 2:
            continue
        means = [[sum(reps) / len(reps) for reps in seqs] for seqs in programs.values()]
        if len(means[0]) < 2:
            continue
        a = [m[0] for m in means]
        b = [m[1] for m in means]
        both = [(x + y) / 2 for x, y in zip(a, b, strict=True)]
        half = math.ceil(len(means) / 2)
        best = (top_k_gain(a, b, 1) + top_k_gain(b, a, 1)) / 2
        top_half = (top_k_gain(a, b, half) + top_k_gain(b, a, half)) / 2
        rows[task_id] = (best, top_half, top_k_gain(both, both, 1))
    return rows


def sign(x):
    return (x > 0) - (x < 0)


def stability(scores):
    """Per task, counts of agreeing and disagreeing decisions:
    "cross_sum" (winner on A by all reps vs winner on B), "cross_sum_gap2"
    (the same for A wins by at least 2 changes over the reps),
    "cross_rep" (one rep of A vs one rep of B) and "within_rep" (two reps of
    the same sequence)."""
    out = {}
    for task_id, programs in scores.items():
        counts = Counter()
        for p, q in combinations(programs.values(), 2):
            if len(p) < 2:
                continue
            da, db = sum(p[0]) - sum(q[0]), sum(p[1]) - sum(q[1])
            for name, ok in (("cross_sum", da != 0), ("cross_sum_gap2", abs(da) >= 2)):
                if ok:
                    counts[name, "decided"] += 1
                    if db:
                        counts[name, "both"] += 1
                        counts[name, "agree"] += sign(da) == sign(db)
            reps = range(len(p[0]))
            for r1 in reps:
                for r2 in reps:
                    x, y = sign(p[0][r1] - q[0][r1]), sign(p[1][r2] - q[1][r2])
                    if x and y:
                        counts["cross_rep", "both"] += 1
                        counts["cross_rep", "agree"] += x == y
            for s in range(len(p)):
                for r1, r2 in combinations(reps, 2):
                    x, y = sign(p[s][r1] - q[s][r1]), sign(p[s][r2] - q[s][r2])
                    if x and y:
                        counts["within_rep", "both"] += 1
                        counts["within_rep", "agree"] += x == y
        out[task_id] = counts
    return out


def rank_correlation(scores):
    """Mean over tasks (at least 3 programs, scores not all equal) of the
    Spearman correlation between programs' sequence-A and sequence-B means."""
    values = []
    for programs in scores.values():
        means = [[sum(reps) / len(reps) for reps in seqs] for seqs in programs.values()]
        if len(means) < 3 or len(means[0]) < 2:
            continue
        a, b = ranks([m[0] for m in means]), ranks([m[1] for m in means])
        r = pearson(a, b)
        if r is not None:
            values.append(r)
    return sum(values) / len(values) if values else float("nan"), len(values)


def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    out = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            out[order[k]] = (i + j) / 2
        i = j + 1
    return out


def pearson(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((y - mb) ** 2 for y in b)
    if not va or not vb:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b, strict=True)) / math.sqrt(va * vb)


def variance_sums(programs):
    """Sums of squares and degrees of freedom of a task's programs x
    sequences x reps scores (two-way layout with repetitions), or None if
    the task has fewer than 2 programs."""
    data = [[list(reps) for reps in seqs] for seqs in programs.values()]
    n, s = len(data), len(data[0]) if data else 0
    if n < 2 or s < 2:
        return None
    r = len(data[0][0])
    cell = [[sum(reps) / r for reps in seqs] for seqs in data]
    prog = [sum(c) / s for c in cell]
    seq = [sum(cell[p][j] for p in range(n)) / n for j in range(s)]
    grand = sum(prog) / n
    ss_p = r * s * sum((m - grand) ** 2 for m in prog)
    ss_ps = r * sum(
        (cell[p][j] - prog[p] - seq[j] + grand) ** 2 for p in range(n) for j in range(s)
    )
    ss_e = sum((x - cell[p][j]) ** 2 for p in range(n) for j in range(s) for x in data[p][j])
    return {"p": (ss_p, n - 1), "ps": (ss_ps, (n - 1) * (s - 1)),
            "e": (ss_e, n * s * (r - 1)), "s": s, "r": r}  # fmt: skip


def variance_components(sums):
    """Pooled within-task variance components of a score: the program
    (what stays with a program whatever the changes), program x sequence
    (how a program suits one particular sequence) and trial (the editor's
    randomness), from the expected mean squares with programs and sequences
    random. Negative estimates are set to 0."""
    sums = [x for x in sums if x is not None]
    if not sums:
        return None
    ms = {}
    for key in ("p", "ps", "e"):
        ms[key] = sum(x[key][0] for x in sums) / sum(x[key][1] for x in sums)
    s, r = sums[0]["s"], sums[0]["r"]
    return {
        "program": max(0.0, (ms["p"] - ms["ps"]) / (r * s)),
        "program x sequence": max(0.0, (ms["ps"] - ms["e"]) / r),
        "trial": ms["e"],
        "s": s,
        "r": r,
    }


def reliability(v, sequences, reps):
    """Share of the variance of a program's mean over `sequences` x `reps`
    trials that is its lasting program component."""
    noise = v["program x sequence"] / sequences + v["trial"] / (sequences * reps)
    return v["program"] / (v["program"] + noise) if v["program"] + noise else float("nan")


def bootstrap(per_task, statistic, n, seed):
    """Percentile 95% interval of statistic(list of per-task values),
    resampling the tasks with replacement."""
    rng = random.Random(seed)
    values = list(per_task)
    stats = sorted(statistic([rng.choice(values) for _ in values]) for _ in range(n))
    return stats[int(0.025 * n)], stats[int(0.975 * n) - 1]


def ratio(key):
    def statistic(counts_list):
        both = sum(c[key, "both"] for c in counts_list)
        return sum(c[key, "agree"] for c in counts_list) / both if both else float("nan")

    return statistic


def pair_file_stability(path):
    """How a training file's pairs split by sequence: the chosen program
    wins, ties or loses on each sequence (reps summed)."""
    counts = Counter()
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        chosen, rejected = row["chosen_scores"], row["rejected_scores"]
        signs = sorted(
            (sign(sum(c) - sum(r)) for c, r in zip(chosen, rejected, strict=True)), reverse=True
        )
        counts[tuple(signs)] += 1
    return counts


def first_change_measures(cfg, scores, records):
    """measure -> task_id -> {candidate_id: per-sequence, per-rep values}
    for measures of the first change, which every trial attempts."""
    image_id = make_runner(cfg, owner=sandbox_owner(cfg)).existing_image_id()
    editor = Keys.of(cfg, image_id).editor
    tasks = load_tasks(cfg.tasks)
    out = {}
    with Store(cfg.runs_dir) as store:
        for record in records:
            task = tasks[record.task_id]
            for cid in scores[record.task_id]:
                for j, seq in enumerate(record.sequence_ids):
                    for rep in range(cfg.editor.reps):
                        trial = TrialKey(task.id, task.task_version, cid, seq, rep, editor)
                        first = store.trial_steps(trial)[0]
                        tests = (first.new_total or 0) + (first.existing_total or 0)
                        passed = (first.new_pass or 0) + (first.existing_pass or 0)
                        values = {
                            "first change works": float(first.status == "success"),
                            "editor calls": first.n_calls,
                            "reply tokens": first.tokens_out,
                            "lines changed": first.diff_lines or 0,
                            "hidden tests passed (share)": passed / tests if tests else 0.0,
                        }
                        for name, value in values.items():
                            program = out.setdefault(name, {}).setdefault(record.task_id, {})
                            program.setdefault(cid, [[] for _ in record.sequence_ids])
                            program[cid][j].append(float(value))
    return out


def measure_lines(per_measure):
    lines = [
        "Variance components of other measures of the first change:",
        "",
        "| Measure | Mean | Program share | Program x sequence | Trial | Reliability |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, per_task in per_measure.items():
        v = variance_components(variance_sums(p) for p in per_task.values())
        total = v["program"] + v["program x sequence"] + v["trial"]
        values = [x for p in per_task.values() for seqs in p.values() for r in seqs for x in r]
        lines.append(
            f"| {name} | {sum(values) / len(values):.2f} | {v['program'] / total:.0%} | "
            f"{v['program x sequence'] / total:.0%} | {v['trial'] / total:.0%} | "
            f"{reliability(v, v['s'], v['r']):.2f} |"
        )
    return lines


def report(scores, n, seed, pairs=None):
    lines = []
    rows = headroom(scores)
    k = len(rows)
    lines += [
        f"Headroom ({k} tasks with at least 2 programs; changes per sequence):",
        "",
        "| Picked by | Gain over the task average | 95% interval |",
        "|---|---:|---:|",
    ]
    names = (
        "Best program on the other sequence (held out)",
        "Top half on the other sequence (held out)",
        "Best program on both sequences (in-sample, upper bound)",
    )
    for i, name in enumerate(names):
        mean = sum(r[i] for r in rows.values()) / k
        lo, hi = bootstrap([r[i] for r in rows.values()], lambda v: sum(v) / len(v), n, seed)
        lines.append(f"| {name} | {mean:+.2f} | {lo:+.2f} to {hi:+.2f} |")
    per_task = ", ".join(f"{t} {r[0]:+.2f}" for t, r in sorted(rows.items()))
    lines += ["", f"Held-out best program per task: {per_task}.", ""]

    counts = stability(scores)
    total = sum(counts.values(), Counter())
    lines += [
        "Stability (pairs of programs of the same task):",
        "",
        "| Decision compared | Pairs decided on both | Agree | 95% interval |",
        "|---|---:|---:|---:|",
    ]
    labels = (
        ("within_rep", "One repetition vs another, same sequence"),
        ("cross_rep", "One repetition of sequence A vs one of sequence B"),
        ("cross_sum", "Winner on sequence A (all reps) vs on sequence B"),
        ("cross_sum_gap2", "Same, A won by at least 2 changes"),
    )
    for key, label in labels:
        both = total[key, "both"]
        if not both:
            continue
        lo, hi = bootstrap(counts.values(), ratio(key), n, seed)
        lines.append(
            f"| {label} | {both} | {total[key, 'agree'] / both:.0%} | {lo:.0%} to {hi:.0%} |"
        )
    for key in ("cross_sum", "cross_sum_gap2"):
        decided = total[key, "decided"]
        if decided:
            tied = decided - total[key, "both"]
            lines.append(f"\n{key}: sequence B ties in {tied} of the {decided} pairs A decides.")
    rho, m = rank_correlation(scores)
    lines += ["", f"Spearman correlation of sequence-A and sequence-B means: {rho:+.2f} "
              f"(mean over {m} tasks)."]  # fmt: skip

    sums = {t: variance_sums(p) for t, p in scores.items()}
    v = variance_components(sums.values())
    if v is not None:
        total_var = v["program"] + v["program x sequence"] + v["trial"]

        def program_share(sample):
            c = variance_components(sample)
            denominator = c["program"] + c["program x sequence"] + c["trial"]
            return c["program"] / denominator if denominator else float("nan")

        lo, hi = bootstrap([x for x in sums.values() if x], program_share, n, seed)
        lines += [
            "",
            "Variance of one trial's score within a task (pooled over tasks):",
            "",
            "| Component | Variance | Share |",
            "|---|---:|---:|",
        ]
        for key in ("program", "program x sequence", "trial"):
            lines.append(f"| {key} | {v[key]:.3f} | {v[key] / total_var:.0%} |")
        lines += [
            "",
            f"Program share 95% interval: {lo:.0%} to {hi:.0%}.",
            "Reliability of a program's mean score as a measure of its program component: "
            + ", ".join(
                f"{s} sequences x {r} reps {reliability(v, s, r):.2f}"
                for s, r in ((v["s"], v["r"]), (v["s"], 10), (4, v["r"]), (8, 1), (8, 3))
            )
            + ".",
        ]
    if pairs is not None:
        split = pair_file_stability(pairs)
        total_pairs = sum(split.values())
        names = {(1, 1): "wins on both", (1, 0): "wins on one, ties on the other",
                 (1, -1): "wins on one, loses on the other", (0, 0): "ties on both"}  # fmt: skip
        lines += ["", f"Training pairs ({pairs.name}, {total_pairs} pairs), chosen program:", ""]
        for key, count in sorted(split.items(), reverse=True):
            label = names.get(key, str(key))
            lines.append(f"- {label}: {count} ({count / total_pairs:.0%})")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", required=True, type=Path, action="append",
                        help="repeat to pool the programs of several writers")  # fmt: skip
    parser.add_argument("--pairs", type=Path, help="a training file to split by sequence")
    parser.add_argument("--measures", action="store_true",
                        help="also other measures of the first change (one config)")  # fmt: skip
    parser.add_argument("--bootstrap", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20261105)
    args = parser.parse_args()
    pooled = {}
    for path in args.config:
        cfg = load_config(path)
        scores, records, _ = scored_programs(cfg)
        for task_id, programs in scores.items():
            pooled.setdefault(task_id, {}).update(programs)
    print(report(pooled, args.bootstrap, args.seed, args.pairs))
    if args.measures:
        print("\n" + "\n".join(measure_lines(first_change_measures(cfg, scores, records))))


if __name__ == "__main__":
    main()
