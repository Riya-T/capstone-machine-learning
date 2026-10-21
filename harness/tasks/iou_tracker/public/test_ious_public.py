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


def test_an_iou_shows_up_on_both_sides(tracker):
    tracker.record_iou("alice", "bob", 500)
    assert tracker.get_owed_to("alice") == [("bob", 500)]
    assert tracker.get_owed_by("bob") == [("alice", 500)]
    assert tracker.get_owed_to("bob") == []
    assert tracker.get_owed_by("alice") == []


def test_balance_is_owed_to_minus_owed_by(tracker):
    tracker.record_iou("alice", "bob", 500)
    tracker.record_iou("carol", "alice", 200)
    assert tracker.get_balance("alice") == 300
    assert tracker.get_balance("bob") == -500
    assert tracker.get_balance("carol") == 200


def test_debts_in_both_directions_are_kept_apart(tracker):
    tracker.record_iou("alice", "bob", 1000)
    tracker.record_iou("bob", "alice", 400)
    assert tracker.get_owed_to("alice") == [("bob", 1000)]
    assert tracker.get_owed_by("alice") == [("bob", 400)]
    assert tracker.get_balance("alice") == 600


def test_history_lists_ious_oldest_first(tracker):
    tracker.record_iou("alice", "bob", 300)
    tracker.record_iou("alice", "carol", 100)
    assert tracker.get_history("alice") == [("alice", "bob", 300), ("alice", "carol", 100)]


def test_amounts_must_be_positive(tracker):
    with pytest.raises(ValueError):
        tracker.record_iou("alice", "bob", 0)
    with pytest.raises(ValueError):
        tracker.record_iou("alice", "bob", -50)


def test_unknown_user_raises_key_error(tracker):
    with pytest.raises(KeyError):
        tracker.get_balance("dave")
