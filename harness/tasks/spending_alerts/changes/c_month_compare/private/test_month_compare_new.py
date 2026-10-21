"""Hidden tests for the c_month_compare change (month against month).
Never shown to the writer or the editor.

Usage (with spending.py importable, e.g. in the sandbox):
    python -m pytest changes/c_month_compare/private/test_month_compare_new.py
"""

import pytest
from spending import SpendingTracker


@pytest.fixture
def tracker():
    tr = SpendingTracker()
    tr.add_account("alice")
    tr.add_account("bob")
    return tr


def test_compare_change_can_be_negative(tracker):
    tracker.record_payment("alice", 3, "food", 900)
    tracker.record_payment("alice", 4, "food", 250)
    tracker.record_payment("alice", 4, "food", 50)
    assert tracker.get_month_change("alice", 4, "food") == -600


def test_compare_change_for_a_category_not_paid_this_month(tracker):
    tracker.record_payment("alice", 1, "rent", 4000)
    assert tracker.get_month_change("alice", 2, "rent") == -4000
    assert tracker.get_month_change("alice", 3, "rent") == 0
    assert tracker.get_month_change("alice", 1, "never") == 0


def test_compare_exactly_one_and_a_half_times_is_unusual(tracker):
    tracker.record_payment("alice", 1, "food", 1000)
    tracker.record_payment("alice", 1, "rent", 1000)
    tracker.record_payment("alice", 2, "food", 1500)
    tracker.record_payment("alice", 2, "rent", 1499)
    assert tracker.get_unusual_categories("alice", 2) == ["food"]


def test_compare_odd_amounts_use_whole_numbers(tracker):
    tracker.record_payment("alice", 1, "food", 3)
    tracker.record_payment("alice", 1, "rent", 3)
    tracker.record_payment("alice", 2, "food", 5)  # 10 >= 9
    tracker.record_payment("alice", 2, "rent", 4)  # 8 < 9
    assert tracker.get_unusual_categories("alice", 2) == ["food"]


def test_compare_needs_spending_in_the_previous_month(tracker):
    tracker.record_payment("alice", 1, "food", 100)
    tracker.record_payment("alice", 2, "travel", 90000)
    tracker.record_payment("alice", 2, "food", 150)
    assert tracker.get_unusual_categories("alice", 2) == ["food"]


def test_compare_only_the_month_just_before_counts(tracker):
    tracker.record_payment("alice", 1, "food", 100)
    tracker.record_payment("alice", 3, "food", 1000)
    assert tracker.get_unusual_categories("alice", 3) == []
    assert tracker.get_month_change("alice", 3, "food") == 1000


def test_compare_unusual_follow_the_first_payment_in_the_month(tracker):
    for category in ["food", "rent", "travel"]:
        tracker.record_payment("alice", 1, category, 100)
    tracker.record_payment("alice", 2, "travel", 100)
    tracker.record_payment("alice", 2, "rent", 300)
    tracker.record_payment("alice", 2, "food", 200)
    tracker.record_payment("alice", 2, "travel", 100)
    assert tracker.get_unusual_categories("alice", 2) == ["travel", "rent", "food"]


def test_compare_is_per_account(tracker):
    tracker.record_payment("alice", 1, "food", 100)
    tracker.record_payment("alice", 2, "food", 200)
    tracker.record_payment("bob", 2, "food", 100)
    assert tracker.get_unusual_categories("alice", 2) == ["food"]
    assert tracker.get_unusual_categories("bob", 2) == []
    assert tracker.get_month_change("bob", 2, "food") == 100


def test_compare_does_not_depend_on_the_alert_limit(tracker):
    tracker.record_payment("alice", 1, "food", 40000)
    tracker.record_payment("alice", 2, "food", 45000)
    tracker.record_payment("alice", 1, "fun", 10)
    tracker.record_payment("alice", 2, "fun", 20)
    assert tracker.get_unusual_categories("alice", 2) == ["fun"]
    assert tracker.get_alerts("alice", 2) == []


@pytest.mark.parametrize("month", [0, -1, 1.0, "2", None])
def test_compare_rejects_bad_months(tracker, month):
    with pytest.raises(ValueError):
        tracker.get_month_change("alice", month, "food")
    with pytest.raises(ValueError):
        tracker.get_unusual_categories("alice", month)


def test_compare_errors_come_in_order(tracker):
    with pytest.raises(KeyError):
        tracker.get_month_change("carol", 0, "")
    with pytest.raises(KeyError):
        tracker.get_unusual_categories("carol", 0)
    with pytest.raises(ValueError):
        tracker.get_month_change("alice", 1, "")
    with pytest.raises(ValueError):
        tracker.get_month_change("alice", 1, None)


def test_compare_queries_change_nothing(tracker):
    tracker.record_payment("alice", 1, "food", 100)
    tracker.record_payment("alice", 2, "food", 300)
    tracker.get_month_change("alice", 2, "food")
    tracker.get_unusual_categories("alice", 2)
    assert tracker.get_total("alice", 2) == 300
    assert tracker.get_category_total("alice", 1, "food") == 100
    assert tracker.record_payment("bob", 1, "food", 1) == 3
