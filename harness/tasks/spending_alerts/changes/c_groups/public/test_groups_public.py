"""Public checks for the c_groups change (groups of categories).
Shown to the editor, never to the writer.

Usage (with spending.py importable, e.g. in the sandbox):
    python -m pytest changes/c_groups/public/test_groups_public.py
"""

import pytest
from spending import SpendingTracker


@pytest.fixture
def tracker():
    tr = SpendingTracker()
    tr.add_account("alice")
    tr.record_payment("alice", 1, "food", 1000)
    tr.record_payment("alice", 1, "drinks", 300)
    tr.record_payment("alice", 1, "rent", 90000)
    return tr


def test_group_total_sums_its_categories(tracker):
    tracker.set_group("food", "eating")
    tracker.set_group("drinks", "eating")
    assert tracker.get_group("food") == "eating"
    assert tracker.get_group_total("alice", 1, "eating") == 1300


def test_group_totals_list_every_group_with_spending(tracker):
    tracker.set_group("rent", "home")
    tracker.set_group("food", "eating")
    assert tracker.get_group_totals("alice", 1) == [("home", 90000), ("eating", 1000)]


def test_group_of_a_category_without_one_is_none(tracker):
    assert tracker.get_group("food") is None
