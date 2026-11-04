"""Public checks for the c_settle change (paying back several lenders at
once). Shown to the editor, never to the writer.

Usage (with ious.py importable, e.g. in the sandbox):
    python -m pytest changes/c_settle/public/test_settle_public.py
"""

import pytest
from ious import IouError, IouTracker


@pytest.fixture
def tracker():
    trk = IouTracker()
    trk.add_user("alice")
    trk.add_user("bob")
    trk.add_user("carol")
    trk.record_iou("alice", "bob", 500)
    trk.record_iou("carol", "bob", 200)
    return trk


def test_paying_part_of_a_debt_reduces_it(tracker):
    tracker.settle("bob", [("alice", 150)])
    assert tracker.get_owed("alice", "bob") == 350
    assert tracker.get_owed("carol", "bob") == 200


def test_paying_a_debt_in_full_keeps_its_ious_listed(tracker):
    tracker.settle("bob", [("carol", 200), ("alice", 1)])
    assert tracker.get_owed("carol", "bob") == 0
    assert tracker.get_owed("alice", "bob") == 499
    assert tracker.get_ious() == [("alice", "bob", 500), ("carol", "bob", 200)]


def test_paying_more_than_is_owed_applies_nothing(tracker):
    with pytest.raises(IouError):
        tracker.settle("bob", [("alice", 100), ("carol", 201)])
    assert tracker.get_owed("alice", "bob") == 500
    assert tracker.get_owed("carol", "bob") == 200


def test_a_lender_can_be_paid_again_in_a_later_call(tracker):
    tracker.settle("bob", [("alice", 300)])
    tracker.settle("bob", [("alice", 150)])
    assert tracker.get_owed("alice", "bob") == 50
    with pytest.raises(IouError):
        tracker.settle("bob", [("alice", 60)])
    assert tracker.get_owed("alice", "bob") == 50


def test_a_lender_listed_twice_in_one_call_is_rejected(tracker):
    with pytest.raises(ValueError):
        tracker.settle("bob", [("alice", 100), ("alice", 50)])
    assert tracker.get_owed("alice", "bob") == 500
