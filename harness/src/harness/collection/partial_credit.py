"""Partial credit for a failed editing step, from its hidden-test counts.

A trial's score is the number of changes done before the first failure
(scorer.trial_score). Partial credit adds a share of a point for the step
that failed: existing-behaviour tests count `existing_weight` times as much
as new-feature tests, so a regression costs more than an unfinished
feature:

    credit = (new + w * existing) / (1 + w)

where new and existing are the shares of each category that pass. The
scorer uses it only to break ties of the 0-3 score (scorer.tiebreak);
scripts/partial_credit.py checks whether it carries signal.

Steps that ended "done" have their counts in the store. Steps that ran out
of turns were never run against the hidden tests, so
`scripts/partial_credit.py backfill` runs them and appends the counts to a
file beside the store (runs/<store>/partial_credit/<sandbox key>.jsonl),
which never changes the store itself. Values are exact fractions, so equal
scores compare equal.

Usage:
    counts = read_counts(counts_path(cfg.runs_dir, keys.sandbox))
    c = counts.get(counts_key(task_id, task_version, cid, seq, rep, editor_hash, step, blob))
    credit(*c.shares(), Fraction(2))   # in [0, 1]
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path


@dataclass(frozen=True)
class Counts:
    """Hidden-test results of one step."""

    new_pass: int
    new_total: int
    existing_pass: int
    existing_total: int

    def shares(self) -> tuple[Fraction, Fraction]:
        """Shares passing; a category without tests counts as passing."""
        new = Fraction(self.new_pass, self.new_total) if self.new_total else Fraction(1)
        old = (
            Fraction(self.existing_pass, self.existing_total)
            if self.existing_total
            else Fraction(1)
        )
        return new, old


def credit(new, existing, weight):
    """Credit in [0, 1] for a failed step (mean form; see the module header).
    Exact for Fraction arguments; floats give a float."""
    return (new + weight * existing) / (1 + weight)


def counts_path(runs_dir: Path, sandbox_hash: str) -> Path:
    return Path(runs_dir) / "partial_credit" / f"{sandbox_hash[:16]}.jsonl"


def counts_key(task_id, task_version, candidate_id, sequence_id, rep, editor_hash, step, blob):
    """The backfilled counts of one step: its trial, step and output program."""
    return (task_id, task_version, candidate_id, sequence_id, rep, editor_hash, step, blob)


def read_counts(path: Path) -> dict[tuple, Counts]:
    rows = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            rows[tuple(row["key"])] = Counts(**row["counts"])
    return rows
