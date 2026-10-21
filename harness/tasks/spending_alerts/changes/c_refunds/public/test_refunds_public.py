"""Public checks for the c_refunds change (refunding payments).
Shown to the editor, never to the writer.

Usage (with spending.py importable, e.g. in the sandbox):
    python -m pytest changes/c_refunds/public/test_refunds_public.py
"""

import pytest
from spending import SpendingError, SpendingTracker


@pytest.fixture
def tracker():
    tr = SpendingTracker()
    tr.add_account("alice")
    return tr


def test_refund_of_a_whole_payment(tracker):
    pid = tracker.record_payment("alice", 1, "food", 3000)
    tracker.refund(pid)
    assert tracker.get_total("alice", 1) == 0
    assert tracker.get_refunded(pid) == 3000


def test_refund_of_part_of_a_payment(tracker):
    pid = tracker.record_payment("alice", 1, "food", 3000)
    tracker.refund(pid, 1000)
    assert tracker.get_category_total("alice", 1, "food") == 2000
    assert tracker.get_refunded(pid) == 1000


def test_refund_of_more_than_is_left_raises(tracker):
    pid = tracker.record_payment("alice", 1, "food", 3000)
    with pytest.raises(SpendingError):
        tracker.refund(pid, 3001)
    assert tracker.get_total("alice", 1) == 3000
