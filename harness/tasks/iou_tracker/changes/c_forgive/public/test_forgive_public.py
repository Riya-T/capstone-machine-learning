"""Public checks for the c_forgive change (cancelling an IOU). Shown to the
editor, never to the writer.

Usage (with ious.py importable, e.g. in the sandbox):
    python -m pytest changes/c_forgive/public/test_forgive_public.py
"""

import pytest
from ious import IouError, IouTracker


@pytest.fixture
def tracker():
    trk = IouTracker()
    trk.add_user("alice")
    trk.add_user("bob")
    trk.record_iou("alice", "bob", 300)
    trk.record_iou("bob", "alice", 50)
    trk.record_iou("alice", "bob", 200)
    return trk


def test_the_most_recent_iou_is_cancelled(tracker):
    assert tracker.forgive_last("alice", "bob") == 200
    assert tracker.get_owed("alice", "bob") == 300
    assert tracker.get_ious() == [("alice", "bob", 300), ("bob", "alice", 50)]


def test_of_two_equal_ious_the_later_one_is_cancelled(tracker):
    tracker.record_iou("alice", "bob", 300)
    assert tracker.forgive_last("alice", "bob") == 300
    assert tracker.get_ious() == [
        ("alice", "bob", 300),
        ("bob", "alice", 50),
        ("alice", "bob", 200),
    ]


def test_forgiving_with_nothing_left_raises(tracker):
    tracker.forgive_last("alice", "bob")
    tracker.forgive_last("alice", "bob")
    assert tracker.get_owed("alice", "bob") == 0
    assert tracker.get_owed("bob", "alice") == 50
    with pytest.raises(IouError):
        tracker.forgive_last("alice", "bob")
