"""Tests for the partial-credit score of scripts/partial_credit.py.

Usage:
    uv run pytest tests/test_partial_credit.py
"""

import pytest
from scripts.partial_credit import (
    Counts,
    ProgramScores,
    agreement_counts,
    credit,
    pair_yield,
    trial_scores,
)


def test_existing_tests_weigh_more_in_both_forms():
    # A regression (1 of 4 old tests failing) costs more than the same
    # share of the new feature missing.
    for formula in ("mean", "product"):
        regression = credit(1.0, 0.75, 2, formula)
        unfinished = credit(0.75, 1.0, 2, formula)
        assert regression < unfinished, formula


def test_credit_values():
    assert credit(0.5, 1.0, 2, "mean") == pytest.approx(2.5 / 3)
    assert credit(0.5, 0.5, 2, "product") == pytest.approx(0.125)
    assert credit(0.0, 1.0, 2, "product") == 0.0
    with pytest.raises(ValueError):
        credit(1, 1, 2, "nope")


def test_counts_without_tests_count_as_passing():
    assert Counts(0, 0, 3, 4).shares() == (1.0, 0.75)


def test_trial_scores():
    half = Counts(1, 2, 4, 4)
    ok = ("success", None)
    assert trial_scores({1: ok, 2: ("fail_new", half), 3: ok}, 3, 2, "mean") == (
        1, pytest.approx(1 + 2.5 / 3))  # fmt: skip
    assert trial_scores({1: ok, 2: ok, 3: ok}, 3, 2, "mean") == (3, 3.0)
    assert trial_scores({1: ("budget_exhausted", None)}, 3, 2, "mean") == "missing"
    assert trial_scores({1: ok}, 3, 2, "mean") == "incomplete"
    assert trial_scores({1: ("infra_error", None)}, 3, 2, "mean") == "infra_error"
    # The change-count ablation truncates: a success at the last counted step.
    assert trial_scores({1: ok, 2: ("fail_new", half)}, 1, 2, "mean") == (1, 1.0)


def prog(cid, s1, s2):
    """One rep; s1 and s2 are (coarse, fine) for sequences s1 and s2."""
    return ProgramScores("t", cid, {("s1", 0): s1, ("s2", 0): s2})


def test_agreement_splits_coarse_ties_from_coarse_orders():
    a = prog("a", (0, 0.9), (1, 1.5))
    b = prog("b", (0, 0.2), (0, 0.4))  # tied with a on s1 coarse; fine says a
    c = prog("c", (1, 1.1), (0, 0.1))  # coarse says c over a and b on s1
    out = agreement_counts([a, b, c], [("s1", 0)], [("s2", 0)])
    # a-b: coarse tie, fine a > b, target (s2 coarse) a > b: agrees.
    assert out["fine, on coarse ties"] == {"agree": 1}
    # a-c and b-c: coarse c first; target: a beats c, b ties c.
    assert out["coarse"] == {"disagree": 1, "target tie": 1}
    assert out["flips"]["fine reverses coarse"] == 0


def test_pair_yield_counts_coarse_ties_the_fine_score_separates():
    progs = {"t": [prog("a", (0, 0.9), (0, 0.6)), prog("b", (0, 0.2), (0, 0.4))]}
    rows = dict(pair_yield(progs, min_step_gap=1))
    assert rows["compared"] == 1
    assert rows["coarse: separated"] == 0
    assert rows["fine: separated"] == 1
    assert rows["fine: gap >= 0.5"] == 1
    assert rows["fine: gap >= 1.0"] == 0
