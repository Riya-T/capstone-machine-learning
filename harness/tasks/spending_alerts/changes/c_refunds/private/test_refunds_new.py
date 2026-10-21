"""Hidden tests for the c_refunds change (refunding payments).
Never shown to the writer or the editor.

Usage (with spending.py importable, e.g. in the sandbox):
    python -m pytest changes/c_refunds/private/test_refunds_new.py
"""

import pytest
from spending import SpendingError, SpendingTracker

MONTHS = (1, 2)
CATEGORIES = ("food", "rent", "travel")


@pytest.fixture
def tracker():
    tr = SpendingTracker()
    tr.add_account("alice")
    tr.add_account("bob")
    return tr


def state(tr, ids=(1, 2, 3)):
    result = {}
    for account in tr.get_accounts():
        for month in MONTHS:
            result[account, month] = (
                tr.get_total(account, month),
                [tr.get_category_total(account, month, c) for c in CATEGORIES],
                tr.get_alerts(account, month),
            )
    result["refunded"] = [tr.get_refunded(i) for i in ids]
    return result


def test_refund_takes_the_money_out_of_every_total(tracker):
    tracker.record_payment("alice", 1, "food", 1000)
    pid = tracker.record_payment("alice", 1, "food", 400)
    tracker.record_payment("alice", 1, "rent", 2000)
    tracker.refund(pid)
    assert tracker.get_category_total("alice", 1, "food") == 1000
    assert tracker.get_category_total("alice", 1, "rent") == 2000
    assert tracker.get_total("alice", 1) == 3000


def test_refund_in_parts_until_nothing_is_left(tracker):
    pid = tracker.record_payment("alice", 1, "food", 3000)
    tracker.refund(pid, 1000)
    tracker.refund(pid, 500)
    assert tracker.get_refunded(pid) == 1500
    assert tracker.get_total("alice", 1) == 1500
    tracker.refund(pid)
    assert tracker.get_refunded(pid) == 3000
    assert tracker.get_total("alice", 1) == 0


def test_refund_of_exactly_what_is_left(tracker):
    pid = tracker.record_payment("alice", 1, "food", 3000)
    tracker.refund(pid, 2000)
    tracker.refund(pid, 1000)
    assert tracker.get_refunded(pid) == 3000
    assert tracker.get_total("alice", 1) == 0


@pytest.mark.parametrize("amount", [None, 1])
def test_refund_of_a_fully_refunded_payment_raises(tracker, amount):
    pid = tracker.record_payment("alice", 1, "food", 3000)
    tracker.record_payment("alice", 1, "rent", 100)
    tracker.refund(pid)
    before = state(tracker, ids=(1, 2))
    with pytest.raises(SpendingError):
        tracker.refund(pid, amount)
    assert state(tracker, ids=(1, 2)) == before


def test_refund_of_too_much_changes_nothing(tracker):
    pid = tracker.record_payment("alice", 1, "food", 3000)
    tracker.refund(pid, 2500)
    tracker.record_payment("bob", 2, "rent", 70000)
    tracker.record_payment("alice", 2, "travel", 10)
    before = state(tracker)
    with pytest.raises(SpendingError):
        tracker.refund(pid, 501)
    assert state(tracker) == before


@pytest.mark.parametrize("payment_id", [0, 4, -1, "1", None, 1.0])
def test_refund_of_an_unknown_payment_raises_key_error(tracker, payment_id):
    for args in [("alice", 1, "food", 100), ("bob", 1, "rent", 200), ("alice", 2, "food", 300)]:
        tracker.record_payment(*args)
    before = state(tracker)
    with pytest.raises(KeyError):
        tracker.refund(payment_id)
    with pytest.raises(KeyError):
        tracker.get_refunded(payment_id)
    assert state(tracker) == before


@pytest.mark.parametrize("amount", [0, -5, 2.5, "10", True])
def test_refund_with_an_invalid_amount_changes_nothing(tracker, amount):
    for args in [("alice", 1, "food", 100), ("bob", 1, "rent", 200), ("alice", 2, "food", 300)]:
        tracker.record_payment(*args)
    before = state(tracker)
    with pytest.raises(ValueError):
        tracker.refund(1, amount)
    assert state(tracker) == before


def test_refund_errors_come_in_order(tracker):
    pid = tracker.record_payment("alice", 1, "food", 100)
    with pytest.raises(KeyError):
        tracker.refund(99, -1)
    tracker.refund(pid)
    with pytest.raises(ValueError):
        tracker.refund(pid, -1)
    with pytest.raises(ValueError):
        tracker.refund(pid, 0)


def test_refund_can_end_an_alert(tracker):
    pid = tracker.record_payment("alice", 1, "travel", 60000)
    tracker.record_payment("alice", 2, "travel", 55000)
    assert tracker.get_alert_months("alice", "travel") == [1, 2]
    tracker.refund(pid, 10000)
    assert tracker.get_alerts("alice", 1) == []
    assert tracker.get_alert_months("alice", "travel") == [2]


def test_refund_counts_against_a_custom_limit():
    tr = SpendingTracker(alert_threshold=1000)
    tr.add_account("alice")
    pid = tr.record_payment("alice", 1, "food", 1500)
    tr.refund(pid, 400)
    assert tr.get_alerts("alice", 1) == ["food"]
    tr.refund(pid, 100)
    assert tr.get_alerts("alice", 1) == []
    tr.set_category_threshold("food", 999)
    assert tr.get_alerts("alice", 1) == ["food"]


def test_refund_does_not_use_up_payment_ids(tracker):
    first = tracker.record_payment("alice", 1, "food", 100)
    tracker.refund(first)
    assert tracker.record_payment("bob", 1, "food", 100) == 2
    assert tracker.get_refunded(2) == 0


def test_refund_only_touches_its_own_payment(tracker):
    a = tracker.record_payment("alice", 1, "food", 800)
    b = tracker.record_payment("bob", 1, "food", 800)
    tracker.record_payment("alice", 2, "food", 800)
    tracker.refund(a, 300)
    assert tracker.get_category_total("alice", 1, "food") == 500
    assert tracker.get_category_total("alice", 2, "food") == 800
    assert tracker.get_category_total("bob", 1, "food") == 800
    assert tracker.get_refunded(b) == 0
