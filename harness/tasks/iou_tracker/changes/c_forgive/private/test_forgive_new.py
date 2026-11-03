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
    users = trk.get_users()
    return {
        "ious": list(trk.get_ious()),
        "owed": {(l, b): trk.get_owed(l, b) for l in users for b in users if l != b},
    }


def test_forgiving_returns_the_amount_and_lowers_the_debt(tracker):
    assert tracker.forgive_last("alice", "bob") == 200
    assert tracker.get_owed("alice", "bob") == 300
    assert tracker.get_owed("bob", "alice") == 50
    assert tracker.get_owed("alice", "carol") == 100


def test_the_cancelled_iou_leaves_the_list(tracker):
    tracker.forgive_last("alice", "bob")
    assert tracker.get_ious() == [
        ("alice", "bob", 300),
        ("bob", "alice", 50),
        ("alice", "carol", 100),
    ]


def test_forgiving_again_cancels_the_next_most_recent_iou(tracker):
    tracker.forgive_last("alice", "bob")
    assert tracker.forgive_last("alice", "bob") == 300
    assert tracker.get_owed("alice", "bob") == 0
    assert tracker.get_ious() == [("bob", "alice", 50), ("alice", "carol", 100)]


def test_the_later_of_two_equal_ious_is_cancelled(tracker):
    tracker.record_iou("carol", "bob", 5)
    tracker.record_iou("alice", "carol", 100)
    assert tracker.forgive_last("alice", "carol") == 100
    assert tracker.get_ious() == [
        ("alice", "bob", 300),
        ("bob", "alice", 50),
        ("alice", "carol", 100),
        ("alice", "bob", 200),
        ("carol", "bob", 5),
    ]
    assert tracker.get_owed("alice", "carol") == 100


def test_the_other_direction_is_never_touched(tracker):
    tracker.forgive_last("alice", "bob")
    tracker.forgive_last("alice", "bob")
    assert tracker.get_owed("bob", "alice") == 50
    assert tracker.get_ious() == [("bob", "alice", 50), ("alice", "carol", 100)]
    before = state(tracker)
    with pytest.raises(IouError):
        tracker.forgive_last("alice", "bob")
    assert state(tracker) == before


def test_forgiving_picks_the_right_pair(tracker):
    assert tracker.forgive_last("alice", "carol") == 100
    assert tracker.get_owed("alice", "carol") == 0
    assert tracker.get_owed("alice", "bob") == 500
    assert tracker.get_ious() == [
        ("alice", "bob", 300),
        ("bob", "alice", 50),
        ("alice", "bob", 200),
    ]
    assert tracker.forgive_last("bob", "alice") == 50
    assert tracker.get_owed("bob", "alice") == 0
    assert tracker.get_ious() == [("alice", "bob", 300), ("alice", "bob", 200)]


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
    assert tracker.get_owed("alice", "carol") == 40
    assert tracker.forgive_last("alice", "carol") == 40
    assert tracker.get_owed("alice", "carol") == 0
    assert tracker.get_ious() == [
        ("alice", "bob", 300),
        ("bob", "alice", 50),
        ("alice", "bob", 200),
    ]


@pytest.mark.parametrize(
    "lender, borrower",
    [("dave", "bob"), ("alice", "dave"), (None, "bob")],
)
def test_names_that_are_not_users_are_rejected(tracker, lender, borrower):
    # A name that is not a user has no IOUs either, so IouError is allowed too.
    before = state(tracker)
    with pytest.raises((KeyError, IouError)):
        tracker.forgive_last(lender, borrower)
    assert state(tracker) == before
