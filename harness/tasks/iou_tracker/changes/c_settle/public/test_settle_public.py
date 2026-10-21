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
    assert tracker.get_owed_by("bob") == [("alice", 350), ("carol", 200)]
    assert tracker.get_balance("bob") == -550


def test_paying_a_debt_in_full_removes_it_from_the_lists(tracker):
    tracker.settle("bob", [("carol", 200)])
    assert tracker.get_owed_by("bob") == [("alice", 500)]
    assert tracker.get_owed_to("carol") == []
    assert tracker.get_history("carol") == [("carol", "bob", 200)]


def test_paying_more_than_is_owed_applies_nothing(tracker):
    with pytest.raises(IouError):
        tracker.settle("bob", [("alice", 100), ("carol", 201)])
    assert tracker.get_owed_by("bob") == [("alice", 500), ("carol", 200)]
