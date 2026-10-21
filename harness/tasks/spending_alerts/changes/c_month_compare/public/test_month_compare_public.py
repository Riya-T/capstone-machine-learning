"""Public checks for the c_month_compare change (month against month).
Shown to the editor, never to the writer.

Usage (with spending.py importable, e.g. in the sandbox):
    python -m pytest changes/c_month_compare/public/test_month_compare_public.py
"""

import pytest
from spending import SpendingTracker


@pytest.fixture
def tracker():
    tr = SpendingTracker()
    tr.add_account("alice")
    return tr


def test_compare_change_from_the_previous_month(tracker):
    tracker.record_payment("alice", 1, "food", 1000)
    tracker.record_payment("alice", 2, "food", 1600)
    assert tracker.get_month_change("alice", 2, "food") == 600


def test_compare_month_one_starts_from_zero(tracker):
    tracker.record_payment("alice", 1, "food", 1000)
    assert tracker.get_month_change("alice", 1, "food") == 1000
    assert tracker.get_unusual_categories("alice", 1) == []


def test_compare_half_again_as_much_is_unusual(tracker):
    tracker.record_payment("alice", 1, "food", 1000)
    tracker.record_payment("alice", 1, "rent", 1000)
    tracker.record_payment("alice", 2, "rent", 1200)
    tracker.record_payment("alice", 2, "food", 2000)
    assert tracker.get_unusual_categories("alice", 2) == ["food"]
