"""Hidden tests for the c_forgive change (cancelling an IOU). Never shown to
the writer or the editor.

Usage (with ious.py importable, e.g. in the sandbox):
    python -m pytest changes/c_forgive/private/test_forgive_new.py
"""

import pytest
from ious import IouError, IouTracker


@pytest.fixture
def tracker():
    trk = IouTracker()
    trk.add_user("alice")
    trk.add_user("bob")
    trk.add_user("carol")
    trk.record_iou("alice", "bob", 300)
    trk.record_iou("bob", "alice", 50)
    trk.record_iou("alice", "carol", 100)
    trk.record_iou("alice", "bob", 200)
    return trk


def state(trk):
    return {
        u: (trk.get_balance(u), trk.get_owed_to(u), trk.get_owed_by(u), trk.get_history(u))
        for u in trk.get_users()
    }


def test_forgiving_returns_the_amount_and_lowers_the_debt(tracker):
    assert tracker.forgive_last("alice", "bob") == 200
    assert tracker.get_owed_to("alice") == [("bob", 300), ("carol", 100)]
    assert tracker.get_owed_by("bob") == [("alice", 300)]
    assert tracker.get_balance("alice") == 350
    assert tracker.get_balance("bob") == -250


def test_the_cancelled_iou_leaves_both_histories(tracker):
    tracker.forgive_last("alice", "bob")
    assert tracker.get_history("alice") == [
        ("alice", "bob", 300),
        ("bob", "alice", 50),
        ("alice", "carol", 100),
    ]
    assert tracker.get_history("bob") == [("alice", "bob", 300), ("bob", "alice", 50)]
    assert tracker.get_history("carol") == [("alice", "carol", 100)]


def test_forgiving_again_cancels_the_next_most_recent_iou(tracker):
    tracker.forgive_last("alice", "bob")
    assert tracker.forgive_last("alice", "bob") == 300
    assert tracker.get_owed_to("alice") == [("carol", 100)]
    assert tracker.get_owed_by("bob") == []
    assert tracker.get_history("bob") == [("bob", "alice", 50)]


def test_the_other_direction_is_never_touched(tracker):
    tracker.forgive_last("alice", "bob")
    tracker.forgive_last("alice", "bob")
    assert tracker.get_owed_to("bob") == [("alice", 50)]
    assert tracker.get_owed_by("alice") == [("bob", 50)]
    before = state(tracker)
    with pytest.raises(IouError):
        tracker.forgive_last("alice", "bob")
    assert state(tracker) == before


def test_forgiving_picks_the_right_pair(tracker):
    assert tracker.forgive_last("alice", "carol") == 100
    assert tracker.get_owed_to("alice") == [("bob", 500)]
    assert tracker.get_history("carol") == []
    assert tracker.forgive_last("bob", "alice") == 50
    assert tracker.get_owed_by("alice") == []


def test_forgiving_with_no_iou_between_the_pair_changes_nothing(tracker):
    before = state(tracker)
    with pytest.raises(IouError):
        tracker.forgive_last("carol", "alice")
    with pytest.raises(IouError):
        tracker.forgive_last("bob", "carol")
    assert state(tracker) == before


def test_a_new_iou_after_forgiving_can_be_forgiven_too(tracker):
    tracker.forgive_last("alice", "carol")
    tracker.record_iou("alice", "carol", 40)
    assert tracker.forgive_last("alice", "carol") == 40
    assert tracker.get_owed_to("alice") == [("bob", 500)]


@pytest.mark.parametrize(
    "lender, borrower",
    [("dave", "bob"), ("alice", "dave"), (None, "bob"), ("alice", 1)],
)
def test_names_that_are_not_users_raise_key_error(tracker, lender, borrower):
    before = state(tracker)
    with pytest.raises(KeyError):
        tracker.forgive_last(lender, borrower)
    assert state(tracker) == before


def test_forgiving_yourself_is_rejected(tracker):
    before = state(tracker)
    with pytest.raises(ValueError):
        tracker.forgive_last("alice", "alice")
    assert state(tracker) == before


def test_an_unknown_user_is_reported_before_the_same_name_check(tracker):
    with pytest.raises(KeyError):
        tracker.forgive_last("dave", "dave")


def test_the_same_name_is_reported_before_a_missing_iou(tracker):
    # carol has never lent to anyone, so IouError would also apply.
    with pytest.raises(ValueError):
        tracker.forgive_last("carol", "carol")
