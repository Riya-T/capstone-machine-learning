"""Scorer: turns editing results into DPO preference pairs.

A program's score on one trial is how many changes in a row the editor
completed before the first failure (failed hidden tests, or out of
budget). Its score for a sequence is the mean over repetitions.

Two programs from the same task are compared over their sequence scores:
- strict: better in every sequence;
- weak_dominance: at least as good in every sequence, better in one;
- aggregate: a higher mean over the sequences, whatever each one says.
Ties, and under the first two rules comparisons that are better in one
sequence but worse in another, give no pair. Neither does a win by fewer
than scorer.min_step_gap changes in total over all sequences and reps:
with 3 reps, a one-change gap is one trial going differently, which is
often noise.

With scorer.tiebreak set, partial credit (partial_credit.py) breaks the
rule's ties: two programs the rule ties are paired, the one with more
credit chosen, if their credit totals over all trials differ by at least
tiebreak.min_gap. Pairs the rule decides are never changed. Partial credit
needs the hidden-test counts of every failed step, backfilled for steps
that ran out of turns (load_task_record's extra_counts).

Setting scorer.rule to "partial_credit" instead ranks candidates by their
full weighted score, with its own scorer.partial_credit.min_gap. The default
coarse rules and tie-break behavior are unchanged.

Pairing modes: all_pairs (every comparison) or best_vs_worst (the best
program against the worst, per task). A per-task cap keeps the pairs with
the biggest score gaps. Every rule and mode is computed for the report;
the configured one gives the training pairs. Every program or comparison
left out is counted by reason (failed initially, duplicate, infra error,
unfinished, tie, inconsistent, too close, over the cap); tie-broken pairs
are counted too.

Usage:
    scorer = Scorer(cfg.scorer, editor_reps=cfg.editor.reps)
    record = load_task_record(store, task, prompt, writer_hash=..., sandbox_hash=...,
                              editor_hash=..., editor_reps=cfg.editor.reps)
    result = scorer.build([record], load_program=store.get_blob)
    write_outputs(result, run_dir)   # preferences.jsonl, preferences_report.json
"""

from __future__ import annotations

import ast
import hashlib
import json
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from typing import Literal

from ..config import ConfigError, ScorerConfig
from ..models.parser import render_program
from ..registry import Task, prompt_version
from ..store import FAILED, Store, TrialKey
from .partial_credit import Counts, counts_key, credit

Verdict = Literal["a", "b", "tie", "inconsistent"]
TrialScore = int | Literal["infra_error", "incomplete"]
PAIRING_MODES = ("all_pairs", "best_vs_worst")
# What can happen to a writer sample: scored, or excluded for one reason.
SAMPLE_FATES = (
    "eligible", "initially_failing", "duplicate", "infra_error", "incomplete", "over_program_cap"
)  # fmt: skip


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


def aggregate(a: Sequence[Fraction], b: Sequence[Fraction]) -> Verdict:
    """The higher mean over sequences wins, even if one sequence disagrees:
    one noisy score per program, so a task's pairs never contradict."""
    total_a, total_b = sum(a, Fraction(0)), sum(b, Fraction(0))
    if total_a == total_b:
        return "tie"
    return "a" if total_a > total_b else "b"


# The extension point: a rule maps two candidates' per-sequence means to a
# verdict. Tiebreaker rules would be added here.
RULES: dict[str, Callable[[Sequence[Fraction], Sequence[Fraction]], Verdict]] = {
    "strict": strict,
    "weak_dominance": weak_dominance,
    "aggregate": aggregate,
    "partial_credit": aggregate,
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
    # model_calls keys of the writer answers, in sample order.
    call_keys: tuple[str, ...] = ()
    # (sequence_id, rep) -> cause code, for trials with an infra_error step.
    infra_causes: Mapping[tuple[str, int], str] = field(default_factory=dict)
    # (sequence_id, rep) -> {step: why the editor stopped}, e.g. max_turns or
    # prompt_too_large for budget_exhausted steps.
    end_reasons: Mapping[tuple[str, int], Mapping[int, str]] = field(default_factory=dict)
    # A passing program after the first tasks.max_programs: never edited.
    over_program_cap: bool = False
    # (sequence_id, rep) -> {step: hidden-test counts} of failed steps whose
    # counts are known (stored, or backfilled via extra_counts).
    step_counts: Mapping[tuple[str, int], Mapping[int, Counts]] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskRecord:
    task_id: str
    prompt: str  # the writer prompt, the DPO prompt
    sequence_ids: tuple[str, ...]
    sequence_length: int
    # One entry per writer answer that didn't parse: its parse category and
    # reason, e.g. "truncated/max_tokens" or "malformed/unlabeled_block".
    parse_failures: tuple[str, ...]
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
    max_sequences: int | None = None,
    max_programs: int | None = None,
    extra_counts: Mapping[tuple, Counts] | None = None,
    max_samples: int | None = None,
) -> TaskRecord:
    """Gather a task's candidates, initial checks and trials from the store.
    Only the first `max_samples` writer samples are read (the config's
    samples_per_task; None: every stored sample), only the first
    `max_sequences` sequences are used (None: all), and only the first
    `max_programs` passing programs in sample order; later passing programs
    are marked over_program_cap. extra_counts: backfilled hidden-test counts
    (partial_credit.read_counts) for failed steps the store has none for."""
    sequences = task.sequences[:max_sequences]
    samples = store.candidates(task.id, prompt_version(prompt), writer_hash, limit=max_samples)
    by_program: dict[str, list] = {}
    parse_failures = []
    for sample in samples:
        if sample.candidate_id is None:
            # Stored as "category/reason: detail" (parser.ParseFailure).
            parse_failures.append((sample.parse_error or "unknown").split(":", 1)[0])
        else:
            by_program.setdefault(sample.candidate_id, []).append(sample)

    candidates = []
    n_passed = 0
    for cid, group in by_program.items():  # in order of first sample, as collect edits them
        group.sort(key=lambda sample: sample.key.sample_idx)
        check = store.get_initial_check(task.id, task.task_version, cid, sandbox_hash)
        passed = bool(check and check.passed)
        n_passed += passed
        over_cap = passed and max_programs is not None and n_passed > max_programs
        trials, causes, reasons, step_counts = {}, {}, {}, {}
        for sequence in sequences:
            for rep in range(editor_reps):
                key = TrialKey(task.id, task.task_version, cid, sequence.id, rep, editor_hash)
                steps = store.trial_steps(key)
                if steps:
                    trials[(sequence.id, rep)] = {c.step: c.status for c in steps}
                    reasons[(sequence.id, rep)] = {c.step: c.end_reason or "" for c in steps}
                for c in steps:
                    if c.status == "infra_error":
                        causes[(sequence.id, rep)] = c.infra_cause or "unknown"
                    if c.status not in FAILED:
                        continue
                    if c.new_total is not None:
                        counts = Counts(c.new_pass, c.new_total, c.existing_pass, c.existing_total)
                    else:
                        counts = (extra_counts or {}).get(
                            counts_key(
                                task.id,
                                task.task_version,
                                cid,
                                sequence.id,
                                rep,
                                editor_hash,
                                c.step,
                                c.output_blob,
                            )  # fmt: skip
                        )
                    if counts is not None:
                        step_counts.setdefault((sequence.id, rep), {})[c.step] = counts
        candidates.append(
            CandidateRecord(
                cid,
                tuple(sample.key.sample_idx for sample in group),
                check and check.passed,
                trials,
                call_keys=tuple(sample.call_key for sample in group if sample.call_key),
                infra_causes=causes,
                end_reasons=reasons,
                over_program_cap=over_cap,
                step_counts=step_counts,
            )
        )
    return TaskRecord(
        task_id=task.id,
        prompt=prompt,
        sequence_ids=tuple(s.id for s in sequences),
        sequence_length=len(task.sequences[0].steps),
        parse_failures=tuple(sorted(parse_failures)),
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
    # Full partial scores, present only for the partial_credit rule.
    partial_rep_scores: tuple[tuple[Fraction, ...], ...] | None = None
    # Partial-credit total over every trial (tie-break or full-score rule).
    credit_total: Fraction | None = None

    @property
    def means(self) -> tuple[Fraction, ...]:
        # Exact fractions, so equal means compare equal (no float rounding).
        return tuple(Fraction(sum(reps), len(reps)) for reps in self.rep_scores)

    @property
    def aggregate(self) -> Fraction:
        return self.aggregate_for("aggregate")

    def means_for(self, rule: str) -> tuple[Fraction, ...]:
        scores = self.scores_for(rule)
        return tuple(Fraction(sum(reps), len(reps)) for reps in scores)

    def scores_for(self, rule: str) -> tuple[tuple[int | Fraction, ...], ...]:
        if rule == "partial_credit":
            if self.partial_rep_scores is None:
                raise ValueError("partial-credit scores were not computed")
            return self.partial_rep_scores
        return self.rep_scores

    def aggregate_for(self, rule: str) -> Fraction:
        means = self.means_for(rule)
        return sum(means, Fraction(0)) / len(means)

    def agreement(self, rule: str = "aggregate") -> list[float]:
        """Per sequence: the share of reps that got the most common score."""
        return [max(Counter(reps).values()) / len(reps) for reps in self.scores_for(rule)]


@dataclass(frozen=True)
class Comparison:
    a: CandidateScores
    b: CandidateScores
    verdict: Verdict
    tiebroken: bool = False  # a tie of the rule, decided by partial credit
    rule: str = "aggregate"

    @property
    def margin(self) -> Fraction:
        return sum(
            (
                abs(x - y)
                for x, y in zip(
                    self.a.means_for(self.rule), self.b.means_for(self.rule), strict=True
                )
            ),
            Fraction(0),
        )

    @property
    def step_gap(self) -> int | Fraction:
        """Absolute total-score gap for partial credit; coarse change-count gap otherwise."""
        if self.rule == "partial_credit":
            assert self.a.credit_total is not None and self.b.credit_total is not None
            return abs(self.a.credit_total - self.b.credit_total)
        return sum(
            abs(sum(x) - sum(y)) for x, y in zip(self.a.rep_scores, self.b.rep_scores, strict=True)
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
        if cfg.rule == "partial_credit" and cfg.partial_credit is None:
            raise ConfigError("scorer.partial_credit: required when scorer.rule is partial_credit")
        if cfg.rule != "partial_credit" and cfg.partial_credit is not None:
            raise ConfigError(
                "scorer.partial_credit: only valid when scorer.rule is partial_credit"
            )
        if cfg.rule == "partial_credit" and cfg.tiebreak is not None:
            raise ConfigError("scorer.tiebreak: cannot be combined with the partial_credit rule")
        tb = cfg.tiebreak
        # Exact, so a total equal to the gap counts as reaching it.
        self.tiebreak = None if tb is None else (
            Fraction(str(tb.min_gap)), Fraction(str(tb.existing_weight))
        )  # fmt: skip
        pc = cfg.partial_credit
        self.partial_credit = None if pc is None else (
            Fraction(str(pc.min_gap)), Fraction(str(pc.existing_weight))
        )  # fmt: skip

    # -- per task --

    def score_task(self, task: TaskRecord) -> tuple[list[CandidateScores], Counter, Counter]:
        """Eligible candidates with their scores, per-sample exclusion counts
        (each writer sample gets exactly one fate), and a breakdown of
        initially_failing by parse category and reason and of infra_error by
        cause, keyed "<reason>/<detail>"."""
        excluded: Counter = Counter()
        detail: Counter = Counter()
        excluded["initially_failing"] += len(task.parse_failures)
        detail.update(f"initially_failing/{failure}" for failure in task.parse_failures)
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
                detail["initially_failing/failed_initial_tests"] += 1
                continue
            if c.over_program_cap:
                excluded["over_program_cap"] += 1
                continue
            scores = [
                [trial_score(c.trials.get((seq, rep), {}), length) for rep in self.reps]
                for seq in task.sequence_ids
            ]
            flat = [s for reps in scores for s in reps]
            if "infra_error" in flat:
                excluded["infra_error"] += 1
                # The cause of the first unresolved trial, in sequence/rep order.
                first = next(
                    (seq, rep)
                    for seq, reps in zip(task.sequence_ids, scores, strict=True)
                    for rep, score in zip(self.reps, reps, strict=True)
                    if score == "infra_error"
                )
                detail[f"infra_error/{c.infra_causes.get(first, 'unknown')}"] += 1
            elif "incomplete" in flat:
                excluded["incomplete"] += 1
            else:
                partial_scores = None
                total = None
                if self.partial_credit is not None:
                    partial_scores = self._partial_score_grid(
                        c, task, length, self.partial_credit[1]
                    )
                    total = sum(
                        (score for reps in partial_scores for score in reps), Fraction(0)
                    )
                elif self.tiebreak is not None:
                    total = self._credit_total(c, task, length)
                eligible.append(
                    CandidateScores(
                        c.candidate_id, tuple(map(tuple, scores)), partial_scores, total
                    )
                )
                detail.update(self._step_endings(c, task, length))
        return eligible, excluded, detail

    def _credit_total(self, c: CandidateRecord, task: TaskRecord, length: int) -> Fraction:
        """Changes done plus partial credit for the failed step, summed over
        the scored trials. A failed step without counts is an error: the
        tie-break would otherwise depend on which steps were backfilled."""
        assert self.tiebreak is not None
        weight = self.tiebreak[1]
        return sum(
            (score for reps in self._partial_score_grid(c, task, length, weight) for score in reps),
            Fraction(0),
        )

    def _partial_score_grid(
        self, c: CandidateRecord, task: TaskRecord, length: int, weight: Fraction
    ) -> tuple[tuple[Fraction, ...], ...]:
        """Completed changes plus credit on the first failed change."""
        grid = []
        for seq in task.sequence_ids:
            sequence_scores = []
            for rep in self.reps:
                done = trial_score(c.trials[(seq, rep)], length)
                assert isinstance(done, int)  # unresolved trials were excluded
                score = Fraction(done)
                if done < length:
                    counts = c.step_counts.get((seq, rep), {}).get(done + 1)
                    if counts is None:
                        raise ValueError(
                            f"{task.task_id} {c.candidate_id[:12]} {seq} rep {rep} step "
                            f"{done + 1}: no hidden-test counts for partial scoring; run "
                            "scripts/partial_credit.py backfill"
                        )
                    score += credit(*counts.shares(), weight)
                sequence_scores.append(score)
            grid.append(tuple(sequence_scores))
        return tuple(grid)

    def _step_endings(self, c: CandidateRecord, task: TaskRecord, length: int) -> Counter:
        """How each scored step ended, keyed "step_endings/<ending>": the step
        status, with budget_exhausted split by the editor's reason (e.g.
        budget_exhausted/prompt_too_large: the program no longer fit the
        prompt). Steps after a trial's first failure never ran.

        Also keyed "editor_endings/<reason>": how the editor ended each of
        those steps (done, checks_passed, max_turns, ...), whatever the
        hidden tests then decided."""
        endings: Counter = Counter()
        for seq in task.sequence_ids:
            for rep in self.reps:
                steps = c.trials.get((seq, rep), {})
                reasons = c.end_reasons.get((seq, rep), {})
                for step in range(1, length + 1):
                    status = steps[step]
                    reason = reasons.get(step) or "unknown"
                    if status == "budget_exhausted":
                        status = f"budget_exhausted/{reason}"
                    endings[f"step_endings/{status}"] += 1
                    endings[f"editor_endings/{reason}"] += 1
                    if steps[step] != "success":
                        break
        return endings

    def compare(self, scored: list[CandidateScores], rule: str, mode: str) -> list[Comparison]:
        """Comparisons for one task, in a deterministic order."""
        decide = RULES[rule]
        ordered = sorted(scored, key=lambda s: s.candidate_id)
        if mode == "all_pairs":
            chosen = list(combinations(ordered, 2))
        elif mode == "best_vs_worst":
            if len(ordered) < 2:
                return []
            best = min(ordered, key=lambda s: (-s.aggregate_for(rule), s.candidate_id))
            rest = [s for s in ordered if s is not best]
            worst = min(rest, key=lambda s: (s.aggregate_for(rule), s.candidate_id))
            chosen = [(best, worst)]
        else:
            raise ValueError(f"unknown pairing mode {mode!r}")
        return [
            Comparison(a, b, decide(a.means_for(rule), b.means_for(rule)), rule=rule)
            for a, b in chosen
        ]

    def labeled(self, comparisons: list[Comparison]) -> tuple[list[Comparison], Counter]:
        """Keep decided comparisons (chosen first) won by at least
        the active rule's gap, and ties broken by partial credit (scorer.tiebreak);
        apply the per-task cap by largest margin (a tie-broken pair keeps the
        rule's margin); and count what was dropped, and the tie-broken pairs."""
        dropped: Counter = Counter()
        decided = []
        for c in comparisons:
            if c.verdict == "tie" and self.tiebreak is not None:
                assert c.a.credit_total is not None and c.b.credit_total is not None
                gap = c.a.credit_total - c.b.credit_total
                if abs(gap) >= self.tiebreak[0]:
                    a, b = (c.a, c.b) if gap > 0 else (c.b, c.a)
                    decided.append(Comparison(a, b, "a", tiebroken=True))
                    dropped["tiebroken"] += 1
                else:
                    dropped["tie"] += 1
            elif c.verdict in ("tie", "inconsistent"):
                dropped[c.verdict] += 1
            else:
                min_gap = self.cfg.min_step_gap
                if c.rule == "partial_credit":
                    assert self.partial_credit is not None
                    min_gap = self.partial_credit[0]
                if c.step_gap < min_gap:
                    dropped["too_close"] += 1
                else:
                    decided.append(
                        c if c.verdict == "a" else Comparison(c.b, c.a, "a", rule=c.rule)
                    )
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
            "primary": {
                "rule": self.cfg.rule,
                "pairing_mode": self.cfg.pairing_mode,
                "min_step_gap": self.cfg.min_step_gap,
                "tiebreak": None
                if self.cfg.tiebreak is None
                else {
                    "min_gap": self.cfg.tiebreak.min_gap,
                    "existing_weight": self.cfg.tiebreak.existing_weight,
                },  # fmt: skip
                "partial_credit": None
                if self.cfg.partial_credit is None
                else {
                    "min_gap": self.cfg.partial_credit.min_gap,
                    "existing_weight": self.cfg.partial_credit.existing_weight,
                },
            },
            "ablation": {"max_changes": self.cfg.max_changes, "reps": list(self.reps)},
            "samples": Counter(),
            "samples_detail": Counter(),
            "step_endings": Counter(),
            "editor_endings": Counter(),
            "combinations": {},
            "tasks": {},
            "candidates": {},
        }
        per_task = []
        agreements: list[float] = []
        for task in sorted(tasks, key=lambda t: t.task_id):
            scored, excluded, detail = self.score_task(task)
            endings = Counter({k: v for k, v in detail.items() if k.startswith("step_endings/")})
            editor_endings = Counter(
                {k: v for k, v in detail.items() if k.startswith("editor_endings/")}
            )
            detail = detail - endings - editor_endings
            report["editor_endings"].update(editor_endings)
            report["samples"].update(excluded)
            report["samples_detail"].update(detail)
            report["step_endings"].update(endings)
            report["samples"]["eligible"] += len(scored)
            agreements += [a for s in scored for a in s.agreement(self.cfg.rule)]
            report["tasks"][task.task_id] = {
                "eligible": len(scored),
                "excluded": {reason: excluded[reason] for reason in SAMPLE_FATES[1:]},
                "excluded_detail": _nest(detail),
                "step_endings": _nest(endings).get("step_endings", {}),
                "score_histogram": _histograms(scored, task),
            }
            per_task.append((task, scored))
            report["candidates"][task.task_id] = candidate_stats(task, load_program)

        pairs: list[dict] = []
        rules = RULES if self.cfg.rule == "partial_credit" else {
            name: decide for name, decide in RULES.items() if name != "partial_credit"
        }
        for rule in rules:
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
                    "too_close": counts["too_close"],
                    "over_cap": counts["over_cap"],
                    "tie_rate": counts["tie"] / compared if compared else None,
                    "inconsistent_rate": counts["inconsistent"] / compared if compared else None,
                }
                if self.tiebreak is not None:  # reports without it stay as they were
                    report["combinations"][f"{rule}/{mode}"]["tiebroken"] = counts["tiebroken"]
        report["rep_agreement"] = sum(agreements) / len(agreements) if agreements else None
        # Every fate listed, zeros included, so reports compare at a glance.
        report["samples"] = {fate: report["samples"][fate] for fate in SAMPLE_FATES}
        report["samples_detail"] = _nest(report["samples_detail"])
        report["step_endings"] = _nest(report["step_endings"]).get("step_endings", {})
        report["editor_endings"] = _nest(report["editor_endings"]).get("editor_endings", {})
        return ScoreResult(pairs, report)

    def _pair(self, task: TaskRecord, c: Comparison, load_program) -> dict:
        records = {r.candidate_id: r for r in task.candidates}
        pair = {
            "task_id": task.task_id,
            "prompt": task.prompt,
            # The DPO completions: each program in the writer's output format.
            "chosen": render_program(dict(load_program(c.a.candidate_id))),
            "rejected": render_program(dict(load_program(c.b.candidate_id))),
            "chosen_id": c.a.candidate_id,
            "rejected_id": c.b.candidate_id,
            "rule": self.cfg.rule,
            "pairing_mode": self.cfg.pairing_mode,
            "strict_subset": strict(c.a.means_for(c.rule), c.b.means_for(c.rule)) == "a",
            "chosen_scores": _json_scores(c.a.scores_for(c.rule)),
            "rejected_scores": _json_scores(c.b.scores_for(c.rule)),
            "margin": str(c.margin),
            # The recorded writer answers behind each program (model_calls keys).
            "chosen_call_keys": list(records[c.a.candidate_id].call_keys),
            "rejected_call_keys": list(records[c.b.candidate_id].call_keys),
        }
        if self.tiebreak is not None:  # pairs without it stay as they were
            pair["tiebroken"] = c.tiebroken
            pair["chosen_credit"] = str(c.a.credit_total)
            pair["rejected_credit"] = str(c.b.credit_total)
        if c.rule == "partial_credit":
            pair["chosen_coarse_scores"] = [list(r) for r in c.a.rep_scores]
            pair["rejected_coarse_scores"] = [list(r) for r in c.b.rep_scores]
            pair["chosen_partial_credit_total"] = str(c.a.credit_total)
            pair["rejected_partial_credit_total"] = str(c.b.credit_total)
        return pair


def _json_scores(scores: Sequence[Sequence[int | Fraction]]) -> list[list[int | float]]:
    return [
        [
            float(score) if isinstance(score, Fraction) and score.denominator != 1 else int(score)
            for score in reps
        ]
        for reps in scores
    ]


def _nest(detail: Counter) -> dict[str, dict[str, int]]:
    """{"infra_error/backend_error": 2} -> {"infra_error": {"backend_error": 2}}."""
    nested: dict[str, dict[str, int]] = {}
    for key in sorted(detail):
        reason, _, cause = key.partition("/")
        nested.setdefault(reason, {})[cause] = detail[key]
    return nested


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


MIN_DISTINCT_PASSING = 3  # fewer gives the editor too little to tell apart


def candidate_stats(task: TaskRecord, load_program) -> dict:
    """How a task's writer samples turned out, for judging candidate
    diversity. distinct_normalized ignores comments, docstrings and
    formatting; it is a diagnostic only and never removes a candidate."""
    checked = [c for c in task.candidates if c.initially_passed is not None]
    passing = [c for c in task.candidates if c.initially_passed]
    stats = {
        "samples": len(task.parse_failures) + sum(len(c.sample_indices) for c in task.candidates),
        "parse_failures": dict(sorted(Counter(task.parse_failures).items())),
        "distinct": len(task.candidates),
        "distinct_normalized": len(
            {structure_key(load_program(c.candidate_id)) for c in task.candidates}
        ),
        "initial_checked": len(checked),
        "passed_initial": len(passing),  # distinct programs
        "passed_initial_samples": sum(len(c.sample_indices) for c in passing),
        "passed_initial_normalized": len(
            {structure_key(load_program(c.candidate_id)) for c in passing}
        ),
    }
    if not stats["samples"]:
        stats["flag"] = "no samples yet"
    elif len(checked) < len(task.candidates):
        stats["flag"] = "initial checks pending"
    elif len(passing) < MIN_DISTINCT_PASSING:
        stats["flag"] = f"fewer than {MIN_DISTINCT_PASSING} distinct passing programs"
    else:
        stats["flag"] = None
    return stats


def structure_key(program: Mapping[str, bytes]) -> str:
    """A hash of the program's syntax trees with docstrings removed, so two
    programs that differ only in comments, docstrings or formatting get the
    same key. A file that doesn't parse is compared as raw text."""
    parts = []
    for path in sorted(program):
        source = program[path]
        try:
            tree = ast.parse(source)
        except (SyntaxError, ValueError):
            parts.append(f"{path}\0{source.decode('utf-8', 'replace')}")
            continue
        for node in ast.walk(tree):
            body = getattr(node, "body", None)
            if (
                isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                and body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                node.body = body[1:] or [ast.Pass()]
        parts.append(f"{path}\0{ast.dump(tree, include_attributes=False)}")
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def summary_table(report: dict) -> str:
    """The numbers to look at first, as plain text."""
    out = ["Candidates"]
    out.append(
        f"  {'task':<20}{'samples':>8}{'parse fail':>11}{'distinct':>9}{'(norm.)':>8}"
        f"{'passed':>7}{'(norm.)':>8}  flag"
    )
    for task_id, c in sorted(report["candidates"].items()):
        fails = sum(c["parse_failures"].values())
        out.append(
            f"  {task_id:<20}{c['samples']:>8}{fails:>11}{c['distinct']:>9}"
            f"{c['distinct_normalized']:>8}{c['passed_initial']:>7}"
            f"{c['passed_initial_normalized']:>8}  {c['flag'] or ''}"
        )
        if c["parse_failures"]:
            reasons = ", ".join(f"{k} {v}" for k, v in c["parse_failures"].items())
            out.append(f"  {'':<20}parse failures: {reasons}")
    samples = ", ".join(f"{k} {v}" for k, v in report["samples"].items())
    out += ["", f"Samples: {samples}"]

    primary_cfg = report["primary"]
    if primary_cfg["rule"] == "partial_credit":
        primary = (
            f"{primary_cfg['rule']}/{primary_cfg['pairing_mode']}, min partial-credit gap "
            f"{primary_cfg['partial_credit']['min_gap']:g}"
        )
    else:
        primary = "{rule}/{pairing_mode}, min step gap {min_step_gap}".format(**primary_cfg)
    out += ["", f"Preference pairs (primary: {primary})"]
    out.append(
        f"  {'rule/pairing':<30}{'pairs':>6}{'compared':>9}{'tie rate':>10}{'inconsistent':>13}"
        f"{'too close':>10}"
    )
    for name, combo in report["combinations"].items():

        def rate(value):
            return "-" if value is None else f"{value:.2f}"

        out.append(
            f"  {name:<30}{combo['pair_yield']:>6}{combo['compared']:>9}"
            f"{rate(combo['tie_rate']):>10}{rate(combo['inconsistent_rate']):>13}"
            f"{combo['too_close']:>10}"
        )
    tiebreak = report["primary"].get("tiebreak")
    if tiebreak:
        broken = report["combinations"][
            f"{report['primary']['rule']}/{report['primary']['pairing_mode']}"
        ]["tiebroken"]
        out.append(
            f"  primary pairs from ties broken by partial credit: {broken} "
            f"(min gap {tiebreak['min_gap']:g}, existing tests x{tiebreak['existing_weight']:g})"
        )
    elif primary_cfg["rule"] == "partial_credit":
        partial = primary_cfg["partial_credit"]
        out.append(
            f"  full partial-credit score (existing tests x{partial['existing_weight']:g})"
        )
    agreement = report["rep_agreement"]
    out += ["", f"Rep agreement: {'-' if agreement is None else f'{agreement:.2f}'}"]
    endings = ", ".join(f"{k} {v}" for k, v in report["step_endings"].items()) or "-"
    out.append(f"Step endings: {endings}")
    editor = ", ".join(f"{k} {v}" for k, v in report["editor_endings"].items()) or "-"
    out.append(f"Editor endings: {editor}")
    for task_id, t in sorted(report["tasks"].items()):
        histograms = "; ".join(f"{seq} {counts}" for seq, counts in t["score_histogram"].items())
        out.append(f"Score histogram {task_id} (trials scoring 0, 1, ...): {histograms or '-'}")
    return "\n".join(out)


def write_outputs(result: ScoreResult, run_dir: Path) -> None:
    """preferences.jsonl (one training pair per line), preferences_report.json
    (yields, rates and exclusion counts) and summary.txt (summary_table)."""
    run_dir.mkdir(parents=True, exist_ok=True)
    with open(run_dir / "preferences.jsonl", "w", encoding="utf-8") as f:
        for pair in result.pairs:
            f.write(json.dumps(pair, sort_keys=True) + "\n")
    (run_dir / "preferences_report.json").write_text(
        json.dumps(result.report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (run_dir / "summary.txt").write_text(summary_table(result.report) + "\n", encoding="utf-8")
