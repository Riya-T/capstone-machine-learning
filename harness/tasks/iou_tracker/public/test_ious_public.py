"""Public checks for ious.py.

Usage (with ious.py importable, e.g. in the sandbox):
    python -m pytest public/test_ious_public.py
"""

import pytest
from ious import IouTracker


@pytest.fixture
def tracker():
    trk = IouTracker()
    trk.add_user("alice")
    trk.add_user("bob")
    trk.add_user("carol")
    return trk


def test_the_borrower_owes_the_lender(tracker):
    tracker.record_iou("alice", "bob", 500)
    assert tracker.get_owed("alice", "bob") == 500
    assert tracker.get_owed("bob", "alice") == 0
    assert tracker.get_debts() == [("alice", "bob", 500)]


def test_ious_between_the_same_pair_make_one_debt(tracker):
    tracker.record_iou("alice", "bob", 300)
    tracker.record_iou("alice", "bob", 200)
    assert tracker.get_owed("alice", "bob") == 500
    assert tracker.get_debts() == [("alice", "bob", 500)]


def test_totals_add_up_what_each_user_lent_and_borrowed(tracker):
    tracker.record_iou("alice", "bob", 500)
    tracker.record_iou("carol", "alice", 200)
    assert tracker.get_total_lent("alice") == 500
    assert tracker.get_total_borrowed("alice") == 200
    assert tracker.get_total_lent("bob") == 0
    assert tracker.get_total_borrowed("bob") == 500
    assert tracker.get_total_lent("carol") == 200
    assert tracker.get_total_borrowed("carol") == 0


def test_debts_in_both_directions_are_kept_apart(tracker):
    tracker.record_iou("alice", "bob", 1000)
    tracker.record_iou("bob", "alice", 400)
    assert tracker.get_owed("alice", "bob") == 1000
    assert tracker.get_owed("bob", "alice") == 400
    assert tracker.get_debts() == [("alice", "bob", 1000), ("bob", "alice", 400)]


def test_history_lists_each_iou_in_the_order_recorded(tracker):
    tracker.record_iou("alice", "bob", 300)
    tracker.record_iou("carol", "alice", 50)
    tracker.record_iou("alice", "bob", 200)
    assert tracker.get_owed("alice", "bob") == 500
    assert tracker.get_history("alice") == [
        ("alice", "bob", 300),
        ("carol", "alice", 50),
        ("alice", "bob", 200),
    ]
    assert tracker.get_history("bob") == [("alice", "bob", 300), ("alice", "bob", 200)]


def test_amounts_must_be_positive(tracker):
    with pytest.raises(ValueError):
        tracker.record_iou("alice", "bob", 0)
    with pytest.raises(ValueError):
        tracker.record_iou("alice", "bob", -50)


def test_unknown_user_raises_key_error(tracker):
    with pytest.raises(KeyError):
        tracker.record_iou("alice", "dave", 10)
    with pytest.raises(KeyError):
        tracker.get_total_lent("dave")
    with pytest.raises(KeyError):
        tracker.get_total_borrowed("dave")
