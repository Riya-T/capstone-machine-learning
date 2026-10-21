"""Public checks for spending.py.

Usage (with spending.py importable, e.g. in the sandbox):
    python -m pytest public/test_spending_public.py
"""

import pytest
from spending import SpendingTracker


@pytest.fixture
def tracker():
    tr = SpendingTracker()
    tr.add_account("alice")
    tr.add_account("bob")
    return tr


def test_payment_ids_start_at_one(tracker):
    assert tracker.record_payment("alice", 1, "food", 1200) == 1
    assert tracker.record_payment("bob", 1, "food", 800) == 2


def test_totals_by_month_and_category(tracker):
    tracker.record_payment("alice", 1, "food", 1200)
    tracker.record_payment("alice", 1, "rent", 90000)
    tracker.record_payment("alice", 2, "food", 700)
    assert tracker.get_total("alice", 1) == 91200
    assert tracker.get_category_total("alice", 1, "food") == 1200
    assert tracker.get_category_total("alice", 2, "rent") == 0


def test_a_category_over_the_limit_is_an_alert(tracker):
    tracker.record_payment("alice", 1, "food", 20000)
    tracker.record_payment("alice", 1, "travel", 60000)
    assert tracker.get_alerts("alice", 1) == ["travel"]
    assert tracker.get_alerts("alice", 2) == []


def test_alert_months_lists_each_month_over_the_limit(tracker):
    tracker.record_payment("alice", 1, "travel", 60000)
    tracker.record_payment("alice", 2, "travel", 100)
    tracker.record_payment("alice", 3, "travel", 75000)
    assert tracker.get_alert_months("alice", "travel") == [1, 3]


def test_amounts_must_be_positive(tracker):
    with pytest.raises(ValueError):
        tracker.record_payment("alice", 1, "food", 0)
    with pytest.raises(ValueError):
        tracker.record_payment("alice", 1, "food", -50)


def test_unknown_account_raises_key_error(tracker):
    with pytest.raises(KeyError):
        tracker.get_total("carol", 1)
