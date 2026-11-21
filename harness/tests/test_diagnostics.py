import pytest
from scripts.diagnostics import fractional_trial_score

from harness.store import Checkpoint, TrialKey


def checkpoint(step, status, **counts):
    return Checkpoint(
        trial=TrialKey("task", "version", "candidate", "sequence", 0, "editor"),
        step=step,
        change_id=f"change-{step}",
        status=status,
        output_blob=None,
        **counts,
    )


def test_fractional_trial_score_adds_balanced_partial_credit_and_stops_at_failure():
    steps = [
        checkpoint(1, "success"),
        checkpoint(
            2,
            "fail_new",
            new_pass=1,
            new_total=2,
            existing_pass=8,
            existing_total=10,
        ),
        checkpoint(3, "success"),
    ]

    assert fractional_trial_score(steps, length=3) == pytest.approx(1.65)


def test_fractional_trial_score_gives_no_credit_for_budget_exhaustion():
    steps = [checkpoint(1, "success"), checkpoint(2, "budget_exhausted")]

    assert fractional_trial_score(steps, length=3) == 1


@pytest.mark.parametrize(
    "steps",
    [
        [checkpoint(1, "infra_error")],
        [checkpoint(1, "fail_both", new_pass=0, new_total=1)],
        [],
    ],
)
def test_fractional_trial_score_leaves_unresolved_trials_unscored(steps):
    assert fractional_trial_score(steps, length=1) is None
