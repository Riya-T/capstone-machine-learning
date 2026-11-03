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
    assert tracker.get_ious() == [("alice", "bob", 500)]


def test_ious_are_listed_oldest_first(tracker):
    tracker.record_iou("alice", "bob", 300)
    tracker.record_iou("carol", "alice", 50)
    tracker.record_iou("alice", "bob", 200)
    assert tracker.get_ious() == [
        ("alice", "bob", 300),
        ("carol", "alice", 50),
        ("alice", "bob", 200),
    ]


def test_owed_is_the_sum_of_the_ious_from_lender_to_borrower(tracker):
    tracker.record_iou("alice", "bob", 300)
    tracker.record_iou("carol", "bob", 40)
    tracker.record_iou("alice", "bob", 200)
    assert tracker.get_owed("alice", "bob") == 500
    assert tracker.get_owed("carol", "bob") == 40
    assert tracker.get_owed("alice", "carol") == 0


def test_the_two_directions_are_counted_apart(tracker):
    tracker.record_iou("alice", "bob", 1000)
    tracker.record_iou("bob", "alice", 400)
    assert tracker.get_owed("alice", "bob") == 1000
    assert tracker.get_owed("bob", "alice") == 400


def test_amounts_must_be_positive(tracker):
    with pytest.raises(ValueError):
        tracker.record_iou("alice", "bob", 0)
    with pytest.raises(ValueError):
        tracker.record_iou("alice", "bob", -50)
    assert tracker.get_ious() == []


def test_unknown_user_raises_key_error(tracker):
    with pytest.raises(KeyError):
        tracker.record_iou("alice", "dave", 10)
    with pytest.raises(KeyError):
        tracker.record_iou("dave", "alice", 10)
