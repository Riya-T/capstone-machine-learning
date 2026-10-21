"""Hidden tests for the initial spending_alerts spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with spending.py importable, e.g. in the sandbox):
    python -m pytest private/test_spending_initial.py
"""

import pytest
from spending import SpendingError, SpendingTracker

MONTHS = (1, 2, 3)
CATEGORIES = ("food", "rent", "travel")
BAD_MONTHS = [0, -1, 1.0, "1", None]
BAD_CATEGORIES = ["", None, 3]
BAD_AMOUNTS = [0, -5, 2.5, "10", None]


@pytest.fixture
def tracker():
    tr = SpendingTracker()
    tr.add_account("alice")
    tr.add_account("bob")
    return tr


def state(tr):
    """Every total and alert, to check that a failed call changed nothing."""
    result = {}
    for account in tr.get_accounts():
        for month in MONTHS:
            result[account, month] = (
                tr.get_total(account, month),
                [tr.get_category_total(account, month, c) for c in CATEGORIES],
                tr.get_alerts(account, month),
            )
    return result


# --- accounts ---------------------------------------------------------------


def test_new_account_has_no_spending(tracker):
    assert tracker.get_total("alice", 1) == 0
    assert tracker.get_category_total("alice", 1, "food") == 0
    assert tracker.get_alerts("alice", 1) == []
    assert tracker.get_alert_months("alice", "food") == []


def test_accounts_are_listed_in_the_order_added():
    tr = SpendingTracker()
    for name in ["carol", "alice", "bob"]:
        tr.add_account(name)
    assert tr.get_accounts() == ["carol", "alice", "bob"]


@pytest.mark.parametrize("bad_id", ["", None, 7])
def test_invalid_account_ids_are_rejected(bad_id):
    tr = SpendingTracker()
    with pytest.raises(ValueError):
        tr.add_account(bad_id)
    assert tr.get_accounts() == []


def test_adding_an_existing_account_is_rejected(tracker):
    tracker.record_payment("alice", 1, "food", 100)
    with pytest.raises(SpendingError):
        tracker.add_account("alice")
    assert tracker.get_accounts() == ["alice", "bob"]
    assert tracker.get_total("alice", 1) == 100


@pytest.mark.parametrize(
    "call",
    [
        lambda tr: tr.record_payment("carol", 1, "food", 10),
        lambda tr: tr.get_total("carol", 1),
        lambda tr: tr.get_category_total("carol", 1, "food"),
        lambda tr: tr.get_alerts("carol", 1),
        lambda tr: tr.get_alert_months("carol", "food"),
        lambda tr: tr.get_total(None, 1),
        lambda tr: tr.get_total(1, 1),
    ],
)
def test_unknown_accounts_raise_key_error(tracker, call):
    tracker.record_payment("alice", 1, "food", 100)
    before = state(tracker)
    with pytest.raises(KeyError):
        call(tracker)
    assert state(tracker) == before


# --- payments ---------------------------------------------------------------


def test_payment_ids_count_up_over_all_accounts(tracker):
    ids = [
        tracker.record_payment("alice", 1, "food", 100),
        tracker.record_payment("bob", 2, "rent", 200),
        tracker.record_payment("alice", 1, "food", 300),
    ]
    assert ids == [1, 2, 3]


def test_a_failed_payment_uses_up_no_id(tracker):
    assert tracker.record_payment("alice", 1, "food", 100) == 1
    with pytest.raises(ValueError):
        tracker.record_payment("alice", 1, "food", 0)
    with pytest.raises(KeyError):
        tracker.record_payment("carol", 1, "food", 10)
    assert tracker.record_payment("alice", 1, "food", 100) == 2


def test_totals_add_up_per_month(tracker):
    tracker.record_payment("alice", 1, "food", 1000)
    tracker.record_payment("alice", 1, "rent", 2500)
    tracker.record_payment("alice", 2, "food", 400)
    tracker.record_payment("alice", 1, "food", 150)
    assert tracker.get_total("alice", 1) == 3650
    assert tracker.get_total("alice", 2) == 400
    assert tracker.get_total("alice", 3) == 0


def test_category_totals_are_per_month_and_category(tracker):
    tracker.record_payment("alice", 1, "food", 1000)
    tracker.record_payment("alice", 2, "food", 400)
    tracker.record_payment("alice", 1, "food", 150)
    tracker.record_payment("alice", 1, "rent", 2500)
    assert tracker.get_category_total("alice", 1, "food") == 1150
    assert tracker.get_category_total("alice", 2, "food") == 400
    assert tracker.get_category_total("alice", 1, "rent") == 2500
    assert tracker.get_category_total("alice", 2, "rent") == 0
    assert tracker.get_category_total("alice", 1, "never") == 0


def test_large_month_numbers_are_allowed(tracker):
    tracker.record_payment("alice", 240, "food", 10)
    assert tracker.get_total("alice", 240) == 10


def test_accounts_do_not_share_spending(tracker):
    tracker.record_payment("alice", 1, "food", 60000)
    assert tracker.get_total("bob", 1) == 0
    assert tracker.get_category_total("bob", 1, "food") == 0
    assert tracker.get_alerts("bob", 1) == []
    assert tracker.get_alert_months("bob", "food") == []


@pytest.mark.parametrize(
    "args",
    [(m, "food", 10) for m in BAD_MONTHS]
    + [(1, c, 10) for c in BAD_CATEGORIES]
    + [(1, "food", a) for a in BAD_AMOUNTS],
)
def test_invalid_payments_are_rejected(tracker, args):
    tracker.record_payment("alice", 1, "food", 100)
    before = state(tracker)
    with pytest.raises(ValueError):
        tracker.record_payment("alice", *args)
    assert state(tracker) == before
    assert tracker.record_payment("alice", 1, "food", 1) == 2


def test_an_unknown_account_is_reported_before_bad_values(tracker):
    with pytest.raises(KeyError):
        tracker.record_payment("carol", 0, "", -1)
    with pytest.raises(KeyError):
        tracker.get_category_total("carol", 0, "")
    with pytest.raises(KeyError):
        tracker.get_alert_months("carol", "")


@pytest.mark.parametrize("month", BAD_MONTHS)
def test_queries_reject_bad_months(tracker, month):
    for call in (
        lambda: tracker.get_total("alice", month),
        lambda: tracker.get_category_total("alice", month, "food"),
        lambda: tracker.get_alerts("alice", month),
    ):
        with pytest.raises(ValueError):
            call()


@pytest.mark.parametrize("category", BAD_CATEGORIES)
def test_queries_reject_bad_categories(tracker, category):
    with pytest.raises(ValueError):
        tracker.get_category_total("alice", 1, category)
    with pytest.raises(ValueError):
        tracker.get_alert_months("alice", category)


# --- alerts -----------------------------------------------------------------


def test_one_payment_over_the_limit_is_an_alert(tracker):
    tracker.record_payment("alice", 1, "travel", 50001)
    assert tracker.get_alerts("alice", 1) == ["travel"]


def test_exactly_the_limit_is_not_an_alert(tracker):
    tracker.record_payment("alice", 1, "travel", 50000)
    assert tracker.get_alerts("alice", 1) == []
    assert tracker.get_alert_months("alice", "travel") == []
    tracker.record_payment("alice", 1, "travel", 1)
    assert tracker.get_alerts("alice", 1) == ["travel"]


def test_small_payments_add_up_to_an_alert(tracker):
    for _ in range(5):
        tracker.record_payment("alice", 2, "food", 10000)
    assert tracker.get_alerts("alice", 2) == []
    tracker.record_payment("alice", 2, "food", 5)
    assert tracker.get_alerts("alice", 2) == ["food"]


def test_alerts_follow_the_first_payment_in_the_month(tracker):
    tracker.record_payment("alice", 1, "rent", 60000)  # month 1: rent first
    tracker.record_payment("alice", 2, "food", 100)
    tracker.record_payment("alice", 2, "travel", 30000)
    tracker.record_payment("alice", 2, "rent", 70000)
    tracker.record_payment("alice", 2, "travel", 30000)
    tracker.record_payment("alice", 2, "food", 60000)
    assert tracker.get_alerts("alice", 2) == ["food", "travel", "rent"]
    assert tracker.get_alerts("alice", 1) == ["rent"]


def test_payments_in_different_months_do_not_add_up(tracker):
    tracker.record_payment("alice", 1, "travel", 40000)
    tracker.record_payment("alice", 2, "travel", 40000)
    assert tracker.get_alerts("alice", 1) == []
    assert tracker.get_alerts("alice", 2) == []
    assert tracker.get_alert_months("alice", "travel") == []


def test_alert_months_are_smallest_first(tracker):
    tracker.record_payment("alice", 5, "travel", 60000)
    tracker.record_payment("alice", 2, "travel", 60000)
    tracker.record_payment("alice", 9, "travel", 60000)
    tracker.record_payment("alice", 4, "travel", 10)
    tracker.record_payment("alice", 3, "food", 60000)
    assert tracker.get_alert_months("alice", "travel") == [2, 5, 9]
    assert tracker.get_alert_months("alice", "food") == [3]


def test_alert_months_list_each_month_once(tracker):
    for _ in range(3):
        tracker.record_payment("alice", 1, "travel", 30000)
    assert tracker.get_alert_months("alice", "travel") == [1]


def test_queries_change_nothing(tracker):
    tracker.record_payment("alice", 1, "travel", 60000)
    before = state(tracker)
    tracker.get_alert_months("alice", "travel")
    tracker.get_alerts("alice", 3)
    assert state(tracker) == before
    assert tracker.record_payment("alice", 1, "food", 1) == 2


def test_trackers_do_not_share_accounts():
    first, second = SpendingTracker(), SpendingTracker()
    first.add_account("alice")
    first.record_payment("alice", 1, "food", 5)
    assert second.get_accounts() == []
    second.add_account("alice")
    assert second.get_total("alice", 1) == 0
    assert second.record_payment("alice", 1, "food", 5) == 1
