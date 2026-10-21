"""Hidden tests for the c_net_query change (net views of the debts). Never
shown to the writer or the editor.

Usage (with ious.py importable, e.g. in the sandbox):
    python -m pytest changes/c_net_query/private/test_net_query_new.py
"""

import pytest
from ious import IouTracker


@pytest.fixture
def tracker():
    trk = IouTracker()
    for name in ["alice", "bob", "carol", "dave"]:
        trk.add_user(name)
    trk.record_iou("alice", "bob", 1000)
    trk.record_iou("bob", "alice", 400)
    trk.record_iou("carol", "alice", 100)
    trk.record_iou("alice", "dave", 100)
    return trk


def test_net_owed_is_zero_between_users_with_no_ious(tracker):
    assert tracker.get_net_owed("bob", "carol") == 0
    assert tracker.get_net_owed("carol", "bob") == 0


def test_net_owed_is_zero_when_the_directions_cancel_exactly(tracker):
    tracker.record_iou("bob", "alice", 600)
    assert tracker.get_net_owed("alice", "bob") == 0
    assert tracker.get_net_owed("bob", "alice") == 0
    assert tracker.get_net_owed_to("alice") == [("dave", 100)]


def test_net_owed_is_antisymmetric(tracker):
    for a, b in [("alice", "bob"), ("alice", "carol"), ("carol", "dave")]:
        assert tracker.get_net_owed(a, b) == -tracker.get_net_owed(b, a)


def test_net_owed_to_lists_largest_first_with_ties_in_user_order(tracker):
    tracker.record_iou("alice", "carol", 700)  # carol now owes alice 600 on net
    assert tracker.get_net_owed_to("alice") == [("bob", 600), ("carol", 600), ("dave", 100)]
    tracker.record_iou("alice", "dave", 500)
    assert tracker.get_net_owed_to("alice") == [("bob", 600), ("carol", 600), ("dave", 600)]
    tracker.record_iou("alice", "dave", 1)
    assert tracker.get_net_owed_to("alice") == [("dave", 601), ("bob", 600), ("carol", 600)]


def test_debtors_list_the_most_negative_balance_first(tracker):
    # balances: alice 600, bob -600, carol 100, dave -100
    tracker.record_iou("carol", "dave", 500)  # dave -600, carol 600
    assert tracker.get_debtors() == ["bob", "dave"]
    tracker.record_iou("alice", "dave", 1)
    assert tracker.get_debtors() == ["dave", "bob"]


def test_creditors_list_the_largest_balance_first(tracker):
    tracker.record_iou("carol", "dave", 500)
    assert tracker.get_creditors() == ["alice", "carol"]
    tracker.record_iou("carol", "bob", 1)
    assert tracker.get_creditors() == ["carol", "alice"]


def test_users_with_a_zero_balance_are_neither_debtors_nor_creditors():
    trk = IouTracker()
    trk.add_user("alice")
    trk.add_user("bob")
    assert trk.get_debtors() == []
    assert trk.get_creditors() == []
    trk.record_iou("alice", "bob", 100)
    trk.record_iou("bob", "alice", 100)
    assert trk.get_debtors() == []
    assert trk.get_creditors() == []


@pytest.mark.parametrize(
    "call",
    [
        lambda trk: trk.get_net_owed("erin", "alice"),
        lambda trk: trk.get_net_owed("alice", "erin"),
        lambda trk: trk.get_net_owed(None, "alice"),
        lambda trk: trk.get_net_owed_to("erin"),
        lambda trk: trk.get_net_owed_to(1),
    ],
)
def test_net_queries_for_names_that_are_not_users_raise_key_error(tracker, call):
    with pytest.raises(KeyError):
        call(tracker)


def test_net_owed_of_a_user_with_themselves_is_rejected(tracker):
    with pytest.raises(ValueError):
        tracker.get_net_owed("alice", "alice")
    with pytest.raises(KeyError):
        tracker.get_net_owed("erin", "erin")


def test_net_queries_change_nothing(tracker):
    before = {u: (tracker.get_balance(u), tracker.get_history(u)) for u in tracker.get_users()}
    tracker.get_net_owed("alice", "bob")
    tracker.get_net_owed_to("alice")
    tracker.get_debtors()
    tracker.get_creditors()
    assert {u: (tracker.get_balance(u), tracker.get_history(u)) for u in tracker.get_users()} == before
