"""Hidden tests for the c_groups change (groups of categories).
Never shown to the writer or the editor.

Usage (with spending.py importable, e.g. in the sandbox):
    python -m pytest changes/c_groups/private/test_groups_new.py
"""

import pytest
from spending import SpendingTracker


@pytest.fixture
def tracker():
    tr = SpendingTracker()
    tr.add_account("alice")
    tr.add_account("bob")
    tr.record_payment("alice", 1, "food", 1000)
    tr.record_payment("alice", 1, "drinks", 300)
    tr.record_payment("alice", 1, "rent", 90000)
    tr.record_payment("alice", 2, "food", 200)
    tr.record_payment("bob", 1, "drinks", 50)
    return tr


def test_group_total_adds_up_only_its_own_categories(tracker):
    tracker.set_group("food", "eating")
    tracker.set_group("drinks", "eating")
    tracker.set_group("rent", "home")
    assert tracker.get_group_total("alice", 1, "eating") == 1300
    assert tracker.get_group_total("alice", 1, "home") == 90000
    assert tracker.get_group_total("alice", 2, "eating") == 200
    assert tracker.get_group_total("bob", 1, "eating") == 50


def test_group_moving_a_category_changes_every_month(tracker):
    tracker.set_group("food", "eating")
    tracker.set_group("food", "basics")
    assert tracker.get_group("food") == "basics"
    assert tracker.get_group_total("alice", 1, "eating") == 0
    assert tracker.get_group_total("alice", 1, "basics") == 1000
    assert tracker.get_group_total("alice", 2, "basics") == 200


def test_group_none_takes_a_category_out(tracker):
    tracker.set_group("food", "eating")
    tracker.set_group("drinks", "eating")
    tracker.set_group("food", None)
    assert tracker.get_group("food") is None
    assert tracker.get_group_total("alice", 1, "eating") == 300
    tracker.set_group("rent", None)  # in no group: nothing happens
    assert tracker.get_group("rent") is None


def test_group_totals_follow_the_order_groups_were_named(tracker):
    tracker.set_group("rent", "home")
    tracker.set_group("travel", "trips")
    tracker.set_group("food", "eating")
    tracker.set_group("drinks", "eating")
    assert tracker.get_group_totals("alice", 1) == [("home", 90000), ("eating", 1300)]
    assert tracker.get_group_totals("alice", 2) == [("eating", 200)]
    assert tracker.get_group_totals("alice", 3) == []


def test_group_totals_leave_out_categories_in_no_group(tracker):
    tracker.set_group("drinks", "eating")
    assert tracker.get_group_totals("alice", 1) == [("eating", 300)]
    assert tracker.get_group_totals("bob", 1) == [("eating", 50)]


def test_group_with_no_categories_has_a_total_of_zero(tracker):
    assert tracker.get_group_total("alice", 1, "nothing") == 0
    tracker.set_group("food", "eating")
    tracker.set_group("food", "basics")
    assert tracker.get_group_totals("alice", 1) == [("basics", 1000)]


def test_group_totals_drop_refunded_money(tracker):
    pid = tracker.record_payment("alice", 3, "food", 700)
    tracker.record_payment("alice", 3, "drinks", 100)
    tracker.set_group("food", "eating")
    tracker.set_group("drinks", "eating")
    tracker.refund(pid, 200)
    assert tracker.get_group_total("alice", 3, "eating") == 600
    tracker.refund(pid)
    assert tracker.get_group_totals("alice", 3) == [("eating", 100)]


def test_group_fully_refunded_is_left_out_of_totals(tracker):
    pid = tracker.record_payment("alice", 3, "travel", 5000)
    tracker.set_group("travel", "trips")
    tracker.refund(pid)
    assert tracker.get_group_total("alice", 3, "trips") == 0
    assert tracker.get_group_totals("alice", 3) == []


def test_group_does_not_change_category_totals_or_alerts(tracker):
    tracker.record_payment("alice", 1, "drinks", 49900)
    tracker.set_group("food", "eating")
    tracker.set_group("drinks", "eating")
    assert tracker.get_category_total("alice", 1, "food") == 1000
    assert tracker.get_total("alice", 1) == 141200
    assert tracker.get_alerts("alice", 1) == ["drinks", "rent"]


@pytest.mark.parametrize("bad", ["", 5])
def test_group_rejects_bad_names_and_changes_nothing(tracker, bad):
    tracker.set_group("food", "eating")
    with pytest.raises(ValueError):
        tracker.set_group(bad, "eating")
    with pytest.raises(ValueError):
        tracker.set_group("food", bad)
    with pytest.raises(ValueError):
        tracker.get_group_total("alice", 1, bad)
    with pytest.raises(ValueError):
        tracker.get_group(bad)
    assert tracker.get_group("food") == "eating"
    assert tracker.get_group_totals("alice", 1) == [("eating", 1000)]


def test_group_rejects_a_missing_category(tracker):
    with pytest.raises(ValueError):
        tracker.set_group(None, "eating")
    with pytest.raises(ValueError):
        tracker.get_group_total("alice", 1, None)
    assert tracker.get_group_totals("alice", 1) == []


def test_group_errors_come_in_order(tracker):
    with pytest.raises(KeyError):
        tracker.get_group_total("carol", 0, "")
    with pytest.raises(KeyError):
        tracker.get_group_totals("carol", 0)
    with pytest.raises(ValueError):
        tracker.get_group_total("alice", 0, "eating")
    with pytest.raises(ValueError):
        tracker.get_group_totals("alice", 0)
