"""Scorer and preference builder: turns editing outcomes into DPO pairs.

Per the proposal, a candidate's score on one trial (one change sequence, one
repetition) is the number of consecutive changes the editor completed before
its first failure. A step fails if the new-feature or the existing-behavior
tests fail, or if the editor ran out of budget. Per sequence, a candidate's
score is the mean over its repetitions.

Two candidates of the same task are compared by a preference rule over their
per-sequence means:
- strict: preferred only if higher in every sequence. Equal in any sequence
  is a tie.
- weak_dominance: preferred if at least as high in every sequence and higher
  in at least one. Equal everywhere is a tie.
Under both, higher in one sequence and lower in another is inconsistent. Ties
and inconsistent comparisons give no pair. New rules are added to RULES only.

Pairs are formed by a pairing mode:
- all_pairs: every two eligible candidates of a task;
- best_vs_worst: per task, the highest against the lowest aggregate score
  (mean of sequence means), ties broken by lowest candidate_id so reruns
  build identical pairs.
A per-task cap then keeps the pairs with the largest margins.

Every rule x mode combination is computed side by side for the report; the
configured one (scorer.rule, scorer.pairing_mode) gives the training pairs,
each flagged with whether strict agrees (the high-confidence subset).

Every excluded sample or comparison is counted by reason. Samples:
initially_failing (including answers that didn't parse), duplicate (same
program as an earlier sample), infra_error (a trial with an unresolved
infrastructure failure), incomplete (a trial or check not finished yet).
Comparisons: tie, inconsistent, over_cap.

Usage:
    scorer = Scorer(cfg.scorer, editor_reps=cfg.editor.reps)
    record = load_task_record(store, task, prompt, writer_hash=..., sandbox_hash=...,
                              editor_hash=..., editor_reps=cfg.editor.reps)
    result = scorer.build([record], load_program=store.get_blob)
    write_outputs(result, run_dir)   # preferences.jsonl, preferences_report.json
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from typing import Literal

from .config import ConfigError, ScorerConfig
from .parser import render_program
from .registry import Task, prompt_version
from .store import FAILED, Store, TrialKey

Verdict = Literal["a", "b", "tie", "inconsistent"]
TrialScore = int | Literal["infra_error", "incomplete"]
PAIRING_MODES = ("all_pairs", "best_vs_worst")


# --- rules ------------------------------------------------------------------


def _signs(a: Sequence[Fraction], b: Sequence[Fraction]) -> list[int]:
    return [(x > y) - (x < y) for x, y in zip(a, b, strict=True)]


def strict(a: Sequence[Fraction], b: Sequence[Fraction]) -> Verdict:
    signs = _signs(a, b)
    if 1 in signs and -1 in signs:
        return "inconsistent"
    if 0 in signs:
        return "tie"
    return "a" if signs[0] == 1 else "b"


def weak_dominance(a: Sequence[Fraction], b: Sequence[Fraction]) -> Verdict:
    signs = _signs(a, b)
    if 1 in signs and -1 in signs:
        return "inconsistent"
    if 1 in signs:
        return "a"
    if -1 in signs:
        return "b"
    return "tie"


# The extension point: a rule maps two candidates' per-sequence means to a
# verdict. Pooled-margin or tiebreaker rules would be added here.
RULES: dict[str, Callable[[Sequence[Fraction], Sequence[Fraction]], Verdict]] = {
    "strict": strict,
    "weak_dominance": weak_dominance,
}


# --- inputs -----------------------------------------------------------------


@dataclass(frozen=True)
class CandidateRecord:
    """Everything the scorer needs about one distinct program."""

    candidate_id: str
    sample_indices: tuple[int, ...]  # writer samples that produced this program
    initially_passed: bool | None  # None: no initial check recorded yet
    # (sequence_id, rep) -> {step: status}; a missing trial is incomplete.
    trials: Mapping[tuple[str, int], Mapping[int, str]] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskRecord:
    task_id: str
    prompt: str  # the writer prompt, the DPO prompt
    sequence_ids: tuple[str, ...]
    sequence_length: int
    unparseable_samples: int
    candidates: tuple[CandidateRecord, ...]


def load_task_record(
    store: Store,
    task: Task,
    prompt: str,
    *,
    writer_hash: str,
    sandbox_hash: str,
    editor_hash: str,
    editor_reps: int,
) -> TaskRecord:
    """Gather a task's candidates, initial checks and trials from the store."""
    samples = store.candidates(task.id, prompt_version(prompt), writer_hash)
    by_program: dict[str, list[int]] = {}
    unparseable = 0
    for sample in samples:
        if sample.candidate_id is None:
            unparseable += 1
        else:
            by_program.setdefault(sample.candidate_id, []).append(sample.key.sample_idx)

    candidates = []
    for cid, indices in by_program.items():
        check = store.get_initial_check(task.id, task.task_version, cid, sandbox_hash)
        trials = {}
        for sequence in task.sequences:
            for rep in range(editor_reps):
                key = TrialKey(task.id, task.task_version, cid, sequence.id, rep, editor_hash)
                steps = store.trial_steps(key)
                if steps:
                    trials[(sequence.id, rep)] = {c.step: c.status for c in steps}
        candidates.append(
            CandidateRecord(cid, tuple(sorted(indices)), check and check.passed, trials)
        )
    return TaskRecord(
        task_id=task.id,
        prompt=prompt,
        sequence_ids=tuple(s.id for s in task.sequences),
        sequence_length=len(task.sequences[0].steps),
        unparseable_samples=unparseable,
        candidates=tuple(candidates),
    )


# --- scoring ----------------------------------------------------------------


def trial_score(steps: Mapping[int, str], length: int) -> TrialScore:
    """Consecutive successful steps before the first failure, counting only
    the first `length` steps (the change-count ablation truncates here).
    budget_exhausted is a failure. An infrastructure error or a missing step
    before the first failure leaves the trial unresolved, never scored."""
    score = 0
    for step in range(1, length + 1):
        status = steps.get(step)
        if status is None:
            return "incomplete"
        if status == "infra_error":
            return "infra_error"
        if status in FAILED:
            return score
        if status != "success":
            raise ValueError(f"unknown step status {status!r}")
        score += 1
    return score


@dataclass(frozen=True)
class CandidateScores:
    candidate_id: str
    rep_scores: tuple[tuple[int, ...], ...]  # per sequence, per rep

    @property
    def means(self) -> tuple[Fraction, ...]:
        # Exact fractions, so equal means compare equal (no float rounding).
        return tuple(Fraction(sum(reps), len(reps)) for reps in self.rep_scores)

    @property
    def aggregate(self) -> Fraction:
        means = self.means
        return sum(means, Fraction(0)) / len(means)

    def agreement(self) -> list[float]:
        """Per sequence: the share of reps that got the most common score."""
        return [max(Counter(reps).values()) / len(reps) for reps in self.rep_scores]


@dataclass(frozen=True)
class Comparison:
    a: CandidateScores
    b: CandidateScores
    verdict: Verdict

    @property
    def margin(self) -> Fraction:
        return sum(
            (abs(x - y) for x, y in zip(self.a.means, self.b.means, strict=True)), Fraction(0)
        )


@dataclass
class ScoreResult:
    pairs: list[dict]  # training pairs under the configured rule and mode
    report: dict


class Scorer:
    def __init__(self, cfg: ScorerConfig, editor_reps: int) -> None:
        if cfg.rule not in RULES:
            raise ConfigError(f"scorer.rule: unknown rule {cfg.rule!r}; known: {sorted(RULES)}")
        reps = cfg.reps if cfg.reps is not None else tuple(range(editor_reps))
        if not reps or max(reps) >= editor_reps:
            raise ConfigError(f"scorer.reps: {reps} must be rep indices below {editor_reps}")
        self.cfg = cfg
        self.reps = tuple(reps)

    # -- per task --

    def score_task(self, task: TaskRecord) -> tuple[list[CandidateScores], Counter]:
        """Eligible candidates with their scores, and per-sample exclusion
        counts. Each writer sample gets exactly one fate."""
        excluded: Counter = Counter()
        excluded["initially_failing"] += task.unparseable_samples
        length = task.sequence_length
        if self.cfg.max_changes is not None:
            length = min(length, self.cfg.max_changes)

        eligible = []
        for c in sorted(task.candidates, key=lambda c: c.candidate_id):
            excluded["duplicate"] += len(c.sample_indices) - 1
            if c.initially_passed is None:
                excluded["incomplete"] += 1
                continue
            if not c.initially_passed:
                excluded["initially_failing"] += 1
                continue
            scores = [
                [trial_score(c.trials.get((seq, rep), {}), length) for rep in self.reps]
                for seq in task.sequence_ids
            ]
            flat = [s for reps in scores for s in reps]
            if "infra_error" in flat:
                excluded["infra_error"] += 1
            elif "incomplete" in flat:
                excluded["incomplete"] += 1
            else:
                eligible.append(CandidateScores(c.candidate_id, tuple(map(tuple, scores))))
        return eligible, excluded

    def compare(self, scored: list[CandidateScores], rule: str, mode: str) -> list[Comparison]:
        """Comparisons for one task, in a deterministic order."""
        decide = RULES[rule]
        ordered = sorted(scored, key=lambda s: s.candidate_id)
        if mode == "all_pairs":
            chosen = list(combinations(ordered, 2))
        elif mode == "best_vs_worst":
            if len(ordered) < 2:
                return []
            best = min(ordered, key=lambda s: (-s.aggregate, s.candidate_id))
            rest = [s for s in ordered if s is not best]
            worst = min(rest, key=lambda s: (s.aggregate, s.candidate_id))
            chosen = [(best, worst)]
        else:
            raise ValueError(f"unknown pairing mode {mode!r}")
        return [Comparison(a, b, decide(a.means, b.means)) for a, b in chosen]

    def labeled(self, comparisons: list[Comparison]) -> tuple[list[Comparison], Counter]:
        """Keep decided comparisons (chosen first), apply the per-task cap by
        largest margin, and count what was dropped."""
        dropped: Counter = Counter()
        decided = []
        for c in comparisons:
            if c.verdict in ("tie", "inconsistent"):
                dropped[c.verdict] += 1
            else:
                decided.append(c if c.verdict == "a" else Comparison(c.b, c.a, "a"))
        decided.sort(key=lambda c: (-c.margin, c.a.candidate_id, c.b.candidate_id))
        cap = self.cfg.per_task_cap
        if cap is not None and len(decided) > cap:
            dropped["over_cap"] += len(decided) - cap
            decided = decided[:cap]
        return decided, dropped

    # -- whole run --

    def build(
        self, tasks: Sequence[TaskRecord], load_program: Callable[[str], Mapping[str, bytes]]
    ) -> ScoreResult:
        report: dict = {
            "primary": {"rule": self.cfg.rule, "pairing_mode": self.cfg.pairing_mode},
            "ablation": {"max_changes": self.cfg.max_changes, "reps": list(self.reps)},
            "samples": Counter(),
            "combinations": {},
            "tasks": {},
        }
        per_task = []
        agreements: list[float] = []
        for task in sorted(tasks, key=lambda t: t.task_id):
            scored, excluded = self.score_task(task)
            report["samples"].update(excluded)
            report["samples"]["eligible"] += len(scored)
            agreements += [a for s in scored for a in s.agreement()]
            report["tasks"][task.task_id] = {
                "eligible": len(scored),
                "excluded": dict(sorted(excluded.items())),
                "score_histogram": _histograms(scored, task),
            }
            per_task.append((task, scored))

        pairs: list[dict] = []
        for rule in RULES:
            for mode in PAIRING_MODES:
                counts: Counter = Counter()
                for task, scored in per_task:
                    comparisons = self.compare(scored, rule, mode)
                    kept, dropped = self.labeled(comparisons)
                    counts["compared"] += len(comparisons)
                    counts["labeled"] += len(kept)
                    counts.update(dropped)
                    if (rule, mode) == (self.cfg.rule, self.cfg.pairing_mode):
                        pairs += [self._pair(task, c, load_program) for c in kept]
                compared = counts["compared"]
                report["combinations"][f"{rule}/{mode}"] = {
                    "pair_yield": counts["labeled"],
                    "compared": compared,
                    "tie": counts["tie"],
                    "inconsistent": counts["inconsistent"],
                    "over_cap": counts["over_cap"],
                    "tie_rate": counts["tie"] / compared if compared else None,
                    "inconsistent_rate": counts["inconsistent"] / compared if compared else None,
                }
        report["rep_agreement"] = sum(agreements) / len(agreements) if agreements else None
        report["samples"] = dict(sorted(report["samples"].items()))
        return ScoreResult(pairs, report)

    def _pair(self, task: TaskRecord, c: Comparison, load_program) -> dict:
        return {
            "task_id": task.task_id,
            "prompt": task.prompt,
            # The DPO completions: each program in the writer's output format.
            "chosen": render_program(dict(load_program(c.a.candidate_id))),
            "rejected": render_program(dict(load_program(c.b.candidate_id))),
            "chosen_id": c.a.candidate_id,
            "rejected_id": c.b.candidate_id,
            "rule": self.cfg.rule,
            "pairing_mode": self.cfg.pairing_mode,
            "strict_subset": strict(c.a.means, c.b.means) == "a",
            "chosen_scores": [list(r) for r in c.a.rep_scores],
            "rejected_scores": [list(r) for r in c.b.rep_scores],
            "margin": str(c.margin),
        }


def _histograms(scored: list[CandidateScores], task: TaskRecord) -> dict[str, list[int]]:
    """Per sequence: how many trials scored 0, 1, ..., L. All mass at 0 or at
    L flags a task that is too hard or too easy for the editor."""
    out = {}
    for i, seq in enumerate(task.sequence_ids):
        counts = [0] * (task.sequence_length + 1)
        for s in scored:
            for score in s.rep_scores[i]:
                counts[score] += 1
        out[seq] = counts
    return out


def write_outputs(result: ScoreResult, run_dir: Path) -> None:
    """preferences.jsonl (one training pair per line) and
    preferences_report.json (yields, rates and exclusion counts)."""
    run_dir.mkdir(parents=True, exist_ok=True)
    with open(run_dir / "preferences.jsonl", "w", encoding="utf-8") as f:
        for pair in result.pairs:
            f.write(json.dumps(pair, sort_keys=True) + "\n")
    (run_dir / "preferences_report.json").write_text(
        json.dumps(result.report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
