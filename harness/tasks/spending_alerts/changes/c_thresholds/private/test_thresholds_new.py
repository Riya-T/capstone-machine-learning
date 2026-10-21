"""Hidden tests for the c_thresholds change (adjustable alert limits).
Never shown to the writer or the editor.

Usage (with spending.py importable, e.g. in the sandbox):
    python -m pytest changes/c_thresholds/private/test_thresholds_new.py
"""

import pytest
from spending import SpendingTracker

BAD_THRESHOLDS = [-1, 2.5, "100", True]


def make(**kwargs):
    tr = SpendingTracker(**kwargs)
    tr.add_account("alice")
    tr.add_account("bob")
    return tr


def test_threshold_default_keeps_the_old_rule():
    tr = make()
    tr.record_payment("alice", 1, "food", 50000)
    tr.record_payment("alice", 2, "food", 50001)
    assert tr.get_alerts("alice", 1) == []
    assert tr.get_alerts("alice", 2) == ["food"]
    assert tr.get_alert_months("alice", "food") == [2]


def test_threshold_from_the_constructor_applies_to_every_category():
    tr = make(alert_threshold=2000)
    tr.record_payment("alice", 1, "food", 2001)
    tr.record_payment("alice", 1, "rent", 2000)
    tr.record_payment("alice", 1, "travel", 5000)
    assert tr.get_alerts("alice", 1) == ["food", "travel"]
    assert tr.get_threshold("anything") == 2000


def test_threshold_equal_to_the_total_is_not_over():
    tr = make(alert_threshold=700)
    tr.set_category_threshold("rent", 900)
    tr.record_payment("alice", 1, "food", 700)
    tr.record_payment("alice", 1, "rent", 900)
    assert tr.get_alerts("alice", 1) == []
    tr.record_payment("alice", 1, "rent", 1)
    assert tr.get_alerts("alice", 1) == ["rent"]


def test_threshold_of_one_category_leaves_the_others_alone():
    tr = make(alert_threshold=1000)
    tr.set_category_threshold("rent", 100000)
    tr.record_payment("alice", 1, "rent", 90000)
    tr.record_payment("alice", 1, "food", 1001)
    assert tr.get_threshold("rent") == 100000
    assert tr.get_threshold("food") == 1000
    assert tr.get_alerts("alice", 1) == ["food"]


def test_threshold_can_be_lower_than_the_default():
    tr = make()
    tr.set_category_threshold("fun", 10000)
    tr.record_payment("alice", 1, "fun", 15000)
    tr.record_payment("alice", 1, "food", 15000)
    assert tr.get_alerts("alice", 1) == ["fun"]


def test_threshold_of_a_category_applies_to_every_account():
    tr = make()
    tr.set_category_threshold("food", 100)
    tr.record_payment("alice", 1, "food", 150)
    tr.record_payment("bob", 1, "food", 150)
    assert tr.get_alerts("alice", 1) == ["food"]
    assert tr.get_alerts("bob", 1) == ["food"]


def test_threshold_change_applies_to_earlier_months_and_alert_months():
    tr = make()
    tr.record_payment("alice", 1, "rent", 120000)
    tr.record_payment("alice", 2, "rent", 80000)
    tr.record_payment("alice", 3, "rent", 40000)
    assert tr.get_alert_months("alice", "rent") == [1, 2]
    tr.set_category_threshold("rent", 100000)
    assert tr.get_alert_months("alice", "rent") == [1]
    assert tr.get_alerts("alice", 2) == []
    tr.set_category_threshold("rent", 30000)
    assert tr.get_alert_months("alice", "rent") == [1, 2, 3]
    assert tr.get_alerts("alice", 3) == ["rent"]


def test_threshold_none_restores_the_default():
    tr = make(alert_threshold=5000)
    tr.set_category_threshold("rent", 100000)
    tr.record_payment("alice", 1, "rent", 6000)
    assert tr.get_alerts("alice", 1) == []
    tr.set_category_threshold("rent", None)
    assert tr.get_threshold("rent") == 5000
    assert tr.get_alerts("alice", 1) == ["rent"]
    tr.set_category_threshold("never-set", None)  # nothing to remove
    assert tr.get_threshold("never-set") == 5000


def test_threshold_of_zero_alerts_on_any_spending():
    tr = make(alert_threshold=0)
    tr.record_payment("alice", 4, "food", 1)
    assert tr.get_alerts("alice", 4) == ["food"]
    assert tr.get_alert_months("alice", "food") == [4]
    assert tr.get_alerts("alice", 5) == []


@pytest.mark.parametrize("threshold", BAD_THRESHOLDS + [None])
def test_threshold_invalid_constructor_values_are_rejected(threshold):
    with pytest.raises(ValueError):
        SpendingTracker(alert_threshold=threshold)


@pytest.mark.parametrize("threshold", BAD_THRESHOLDS)
def test_threshold_invalid_category_values_change_nothing(threshold):
    tr = make()
    tr.set_category_threshold("rent", 70000)
    with pytest.raises(ValueError):
        tr.set_category_threshold("rent", threshold)
    with pytest.raises(ValueError):
        tr.set_category_threshold("food", threshold)
    assert tr.get_threshold("rent") == 70000
    assert tr.get_threshold("food") == 50000


@pytest.mark.parametrize("category", ["", None, 3])
def test_threshold_methods_reject_bad_categories(category):
    tr = make()
    with pytest.raises(ValueError):
        tr.set_category_threshold(category, 100)
    with pytest.raises(ValueError):
        tr.set_category_threshold(category, -1)
    with pytest.raises(ValueError):
        tr.get_threshold(category)
