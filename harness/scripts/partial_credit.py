"""Partial credit for editing trials: a finer score than changes completed.

The scorer gives a trial the number of changes done before the first
failure, so with 3 changes and one trial per sequence a program scores 0
to 3, and most programs tie. Here the step that failed also earns a share
of a point from its hidden tests: existing-behaviour tests count
--existing-weight times as much as new-feature tests, so a regression costs
more than an unfinished feature. Two forms:

- mean:    (new + w * existing) / (1 + w)
- product: new * existing ** w   (nothing for a step with no new-feature
           test passing, however many old tests still pass)

where new and existing are the shares of each category that pass. A trial
scores k + credit (k changes done); a trial that finishes the sequence
scores its length.

Steps that ended "done" have their hidden-test counts in the store. Steps
that ran out of turns were never run against the hidden tests; `backfill`
runs them on the program the editor left (sandbox only, no model) and
appends the counts to runs/<store>/partial_credit/<sandbox key>.jsonl. The
store itself is never changed. It resumes, and infra errors are retried on
the next run.

`analyze` reads the store and that file and reports, per form:
- pair yield: of all pairs of a task's programs (aggregate rule over every
  trial), how many the 0-3 score and the finer score separate;
- signal: whether the finer score on one half of the trials predicts the
  0-3 score on the other half better than the 0-3 score does. Halves are
  rep 0 / rep 1 (with 2+ reps) and one sequence / another. The number that
  matters is the agreement on pairs the 0-3 score ties: 50% means the extra
  detail is noise. Intervals resample the tasks.

Programs are those the scorer uses (passing, up to tasks.max_programs);
a program with an unresolved trial (infra error, unfinished, or a step
without counts) is left out of everything and counted.

Usage (from harness/; the cluster runs both steps in
scripts/partial_credit_nexus.sbatch):
    uv run python scripts/partial_credit.py backfill --config configs/nexus_hist2_eval_maintain.yaml
    uv run python scripts/partial_credit.py analyze --config configs/nexus_hist2_eval_maintain.yaml
    uv run python scripts/partial_credit.py analyze --config CONFIG --existing-weight 3 --out F.md
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import threading
from collections import Counter, defaultdict
from collections.abc import Iterator, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

from harness.collection.collect import Keys, sandbox_owner
from harness.collection.partial_credit import Counts, counts_key, counts_path, read_counts
from harness.collection.partial_credit import credit as mean_credit
from harness.collection.scorer import load_task_record
from harness.config import load_config
from harness.registry import Task, build_writer_prompt, load_tasks, load_template
from harness.sandbox.evaluator import Evaluator
from harness.sandbox.runner import make_runner
from harness.store import FAILED, Checkpoint, Store, TrialKey

FORMULAS = ("mean", "product")
EPS = 1e-9  # fine scores are floats; closer than this is a tie


# --- scoring ------------------------------------------------------------------


def credit(new: float, existing: float, weight: float, formula: str) -> float:
    """Credit in [0, 1] for a failed step from the shares of its hidden
    new-feature and existing-behaviour tests that pass. mean is the form the
    scorer's tie-break uses (collection/partial_credit.py)."""
    if formula == "mean":
        return float(mean_credit(new, existing, weight))
    if formula == "product":
        return float(new * existing**weight)
    raise ValueError(f"unknown formula {formula!r}; known: {FORMULAS}")


Step = tuple[str, Counts | None]  # status, hidden-test counts if known


def trial_scores(
    steps: Mapping[int, Step], length: int, weight: float, formula: str
) -> tuple[int, float] | str:
    """(changes done, finer score), or why the trial can't be scored:
    "infra_error", "incomplete", or "missing" (failed step without counts)."""
    done = 0
    for n in range(1, length + 1):
        entry = steps.get(n)
        if entry is None:
            return "incomplete"
        status, counts = entry
        if status == "infra_error":
            return "infra_error"
        if status == "success":
            done += 1
            continue
        if status not in FAILED:
            raise ValueError(f"unknown step status {status!r}")
        if counts is None:
            return "missing"
        return done, done + credit(*counts.shares(), weight, formula)
    return done, float(done)


# --- the scorer's programs and their trials -------------------------------------


@dataclass(frozen=True)
class Trial:
    task: Task
    candidate_id: str
    sequence_id: str
    rep: int
    checkpoints: tuple[Checkpoint, ...]


def setup(cfg):
    image_id = make_runner(cfg, owner=sandbox_owner(cfg)).existing_image_id()
    if image_id is None:
        raise SystemExit("sandbox image not found; results are keyed by its id")
    return Keys.of(cfg, image_id)


def iter_trials(cfg, store: Store, keys: Keys) -> Iterator[Trial]:
    """Every trial of every program the scorer uses, in task order."""
    template = load_template(cfg.writer.prompt_template)
    tasks = load_tasks(cfg.tasks)
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
            max_samples=cfg.writer.samples_per_task,
        )
        for cand in record.candidates:
            if not cand.initially_passed or cand.over_program_cap:
                continue
            for seq_id in record.sequence_ids:
                for rep in range(cfg.editor.reps):
                    trial = TrialKey(task.id, task.task_version, cand.candidate_id, seq_id, rep,
                                     keys.editor)  # fmt: skip
                    yield Trial(task, cand.candidate_id, seq_id, rep,
                                tuple(store.trial_steps(trial)))  # fmt: skip


def sidecar_path(cfg, keys: Keys) -> Path:
    return counts_path(cfg.runs_dir, keys.sandbox)


def sidecar_key(trial: Trial, c: Checkpoint, editor_hash: str) -> tuple:
    return counts_key(trial.task.id, trial.task.task_version, trial.candidate_id,
                      trial.sequence_id, trial.rep, editor_hash, c.step, c.output_blob)  # fmt: skip


read_sidecar = read_counts


def needs_counts(c: Checkpoint) -> bool:
    return c.status == "budget_exhausted" and c.new_total is None and c.output_blob is not None


# --- backfill -------------------------------------------------------------------


def backfill(cfg, workers: int) -> None:
    keys = setup(cfg)
    path = sidecar_path(cfg, keys)
    path.parent.mkdir(parents=True, exist_ok=True)
    done = read_sidecar(path)
    jobs = []
    with Store(cfg.runs_dir) as store:
        for trial in iter_trials(cfg, store, keys):
            for c in trial.checkpoints:
                key = sidecar_key(trial, c, keys.editor)
                if needs_counts(c) and key not in done:
                    step = trial.task.sequence(trial.sequence_id).steps[c.step - 1]
                    jobs.append((key, step, store.get_blob(c.output_blob)))
    print(f"{len(done)} steps already have counts; {len(jobs)} to run", flush=True)
    runner = make_runner(cfg, owner=sandbox_owner(cfg))
    evaluator = Evaluator(runner, workers=2)  # each step runs its two categories at once
    lock, stats = threading.Lock(), Counter()

    def run(job) -> None:
        key, step, program = job
        result = evaluator.check_step(program, step)
        with lock:
            if result.status == "infra_error":
                stats["infra_error"] += 1
                print(f"infra error ({result.infra_cause}) on {key[:3]} step {key[6]}", flush=True)
                return
            counts = Counts(result.new_feature.passed, result.new_feature.total,
                            result.existing.passed, result.existing.total)  # fmt: skip
            row = {"key": list(key), "counts": counts.__dict__, "status": result.status}
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
            stats[result.status] += 1
            n = sum(stats.values())
            if n % 10 == 0 or n == len(jobs):
                print(f"{n}/{len(jobs)}: {dict(stats)}", flush=True)

    _ = runner.image_id  # resolve once, before threads race to it
    with ThreadPoolExecutor(max_workers=max(1, workers // 2)) as pool:
        list(pool.map(run, jobs))
    print(f"done: {dict(stats)}; counts in {path}")
    if stats["infra_error"]:
        sys.exit(1)


# --- analysis -------------------------------------------------------------------


@dataclass(frozen=True)
class ProgramScores:
    task_id: str
    candidate_id: str
    trials: dict[tuple[str, int], tuple[int, float]]  # (sequence, rep) -> (coarse, fine)

    def mean(self, which: Sequence[tuple[str, int]]) -> tuple[float, float]:
        coarse = sum(self.trials[t][0] for t in which) / len(which)
        fine = sum(self.trials[t][1] for t in which) / len(which)
        return coarse, fine


def load_steps(cfg) -> tuple[dict, Counter, dict[str, int]]:
    """task -> candidate -> {(sequence, rep): {step: (status, counts)}};
    where failed steps' counts came from (and how many out-of-turns steps
    pass every hidden test); the sequence length per task."""
    keys = setup(cfg)
    sidecar = read_sidecar(sidecar_path(cfg, keys))
    programs: dict = defaultdict(lambda: defaultdict(dict))
    sources, lengths = Counter(), {}
    with Store(cfg.runs_dir) as store:
        for trial in iter_trials(cfg, store, keys):
            length = len(trial.task.sequences[0].steps)
            if cfg.scorer.max_changes is not None:
                length = min(length, cfg.scorer.max_changes)
            lengths[trial.task.id] = length
            steps = {}
            for c in trial.checkpoints:
                counts = None
                if c.new_total is not None:
                    counts = Counts(c.new_pass, c.new_total, c.existing_pass, c.existing_total)
                    if c.status in FAILED:
                        sources["stored"] += 1
                elif needs_counts(c):
                    counts = sidecar.get(sidecar_key(trial, c, keys.editor))
                    sources["backfilled" if counts else "missing"] += 1
                    if counts and counts.shares() == (1.0, 1.0):
                        sources["out of turns but passing every hidden test"] += 1
                steps[c.step] = (c.status, counts)
            programs[trial.task.id][trial.candidate_id][(trial.sequence_id, trial.rep)] = steps
    return programs, sources, lengths


def score_programs(programs, lengths, weight, formula) -> tuple[dict, Counter]:
    """task -> [ProgramScores], and programs left out by reason."""
    scored, left_out = defaultdict(list), Counter()
    for task_id, cands in programs.items():
        for cid, trials in cands.items():
            results = {t: trial_scores(s, lengths[task_id], weight, formula)
                       for t, s in trials.items()}  # fmt: skip
            bad = [r for r in results.values() if isinstance(r, str)]
            if bad:
                left_out[bad[0]] += 1
                continue
            scored[task_id].append(ProgramScores(task_id, cid, results))
    return scored, left_out


def sign(x: float) -> int:
    return (x > EPS) - (x < -EPS)


def pair_yield(scored, min_step_gap: int) -> list[tuple[str, int]]:
    """Pairs separated under the aggregate rule over every trial."""
    total = Counter()
    for progs in scored.values():
        for a, b in combinations(progs, 2):
            trials = list(a.trials)
            ca, fa = (sum(a.trials[t][i] for t in trials) for i in (0, 1))
            cb, fb = (sum(b.trials[t][i] for t in trials) for i in (0, 1))
            total["compared"] += 1
            gap_c, gap_f = abs(ca - cb), abs(fa - fb)
            total["coarse: separated"] += gap_c > 0
            total[f"coarse: gap >= {min_step_gap} (the scorer's pairs)"] += gap_c >= min_step_gap
            total["fine: separated"] += gap_f > EPS
            for t in (0.25, 0.5, 1.0):
                total[f"fine: gap >= {t}"] += gap_f >= t - EPS
    return list(total.items())


def splits(scored) -> list[tuple[str, list, list]]:
    """(name, predictor trials, target trials)."""
    some = next(p for progs in scored.values() for p in progs)
    seqs = sorted({s for s, _ in some.trials})
    reps = sorted({r for _, r in some.trials})
    out = []
    if len(reps) >= 2:
        for a, b in ((reps[0], reps[1]), (reps[1], reps[0])):
            out.append((f"rep {a} -> rep {b}", [(s, a) for s in seqs], [(s, b) for s in seqs]))
    for a in seqs:
        for b in seqs:
            if a != b:
                out.append((f"{a} -> {b}", [(a, r) for r in reps], [(b, r) for r in reps]))
    return out


GROUPS = ("coarse", "fine", "fine, on coarse ties")


def agreement_counts(progs, pred, target) -> dict[str, Counter]:
    """Per group: pairs whose target (0-3 score on the other half) agrees or
    disagrees with the predictor's order, or ties."""
    out = {g: Counter() for g in GROUPS}
    out["flips"] = Counter()
    for a, b in combinations(progs, 2):
        (ca, fa), (cb, fb) = a.mean(pred), b.mean(pred)
        t = sign(a.mean(target)[0] - b.mean(target)[0])
        c, f = sign(ca - cb), sign(fa - fb)
        if c:
            out["coarse"][verdict(c, t)] += 1
            out["flips"]["fine reverses coarse"] += f == -c
        if f:
            out["fine"][verdict(f, t)] += 1
            if not c:
                out["fine, on coarse ties"][verdict(f, t)] += 1
    return out


def verdict(predicted: int, target: int) -> str:
    return "target tie" if target == 0 else "agree" if predicted == target else "disagree"


def rate(counter: Counter) -> float | None:
    n = counter["agree"] + counter["disagree"]
    return counter["agree"] / n if n else None


def signal(scored, pred, target, bootstrap: int, seed: int) -> tuple[list[tuple], int]:
    """Per group: (group, pooled counts, agreement, 95% interval); and how
    many pairs the fine score orders against the coarse one."""
    per_task = {tid: agreement_counts(progs, pred, target) for tid, progs in scored.items()}
    rows = []
    rng = random.Random(seed)
    tids = sorted(per_task)
    for group in GROUPS:
        pooled = sum((per_task[t][group] for t in tids), Counter())
        draws = []
        for _ in range(bootstrap):
            sample = [tids[rng.randrange(len(tids))] for _ in tids]
            r = rate(sum((per_task[t][group] for t in sample), Counter()))
            if r is not None:
                draws.append(r)
        draws.sort()
        interval = None
        if draws:
            interval = (draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws)) - 1])
        rows.append((group, pooled, rate(pooled), interval))
    flips = sum(per_task[t]["flips"]["fine reverses coarse"] for t in tids)
    return rows, flips


def fmt_rate(r, interval) -> str:
    if r is None:
        return "-"
    if interval is None:
        return f"{r:.0%}"
    return f"{r:.0%} ({interval[0]:.0%} to {interval[1]:.0%})"


def analyze(cfg, weight: float, bootstrap: int, seed: int) -> str:
    programs, sources, lengths = load_steps(cfg)
    lines = [
        f"# Partial credit: {cfg.name}",
        "",
        f"Existing-behaviour tests weigh {weight:g}x new-feature tests. Failed steps: "
        + ", ".join(f"{k} {v}" for k, v in sources.items()),
    ]
    if sources["missing"]:
        lines.append(f"**{sources['missing']} out-of-turns steps have no counts yet; "
                     "run `backfill` first. Their programs are left out.**")  # fmt: skip
    for formula in FORMULAS:
        scored, left_out = score_programs(programs, lengths, weight, formula)
        n = sum(len(p) for p in scored.values())
        lines += ["", f"## Form: {formula}", "",
                  f"{n} programs on {len(scored)} tasks"
                  + (f"; left out: {dict(left_out)}" if left_out else "")]  # fmt: skip
        if not n:
            continue
        lines += ["", "### Pair yield (aggregate rule, every trial)", "",
                  "| | Pairs |", "|---|---:|"]  # fmt: skip
        lines += [f"| {k} | {v} |" for k, v in pair_yield(scored, cfg.scorer.min_step_gap)]
        lines += ["", "### Does the score on one half predict the 0-3 score on the other?", "",
                  "Agreement among pairs the target does not tie; 95% intervals resample tasks.",
                  "", "| Halves | Predictor | Agree | Disagree | Target tie | Agreement |",
                  "|---|---|---:|---:|---:|---:|"]  # fmt: skip
        for name, pred, target in splits(scored):
            rows, flips = signal(scored, pred, target, bootstrap, seed)
            for group, c, r, interval in rows:
                lines.append(f"| {name} | {group} | {c['agree']} | {c['disagree']} | "
                             f"{c['target tie']} | {fmt_rate(r, interval)} |")  # fmt: skip
            if flips:
                lines.append(f"| {name} | (fine reverses a coarse order) | {flips} | | | |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("backfill", help="run hidden tests on out-of-turns steps")
    b.add_argument("--config", required=True)
    b.add_argument("--workers", type=int, default=None,
                   help="sandbox runs at once (default: execution.sandbox_workers)")  # fmt: skip
    a = sub.add_parser("analyze", help="compare the finer score with the 0-3 one")
    a.add_argument("--config", required=True)
    a.add_argument("--existing-weight", type=float, default=2.0)
    a.add_argument("--bootstrap", type=int, default=2000)
    a.add_argument("--seed", type=int, default=20261120)
    a.add_argument("--out", type=Path)
    args = parser.parse_args()
    cfg = load_config(Path(args.config))
    if args.command == "backfill":
        backfill(cfg, args.workers or cfg.execution.sandbox_workers)
        return
    text = analyze(cfg, args.existing_weight, args.bootstrap, args.seed)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
