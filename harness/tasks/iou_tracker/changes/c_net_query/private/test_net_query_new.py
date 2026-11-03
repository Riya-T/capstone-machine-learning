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
    trk.record_iou("alice", "dave", 150)
    # net positions, lent minus borrowed: alice 650, bob -600, carol 100, dave -150
    return trk


def test_net_owed_is_zero_between_users_with_no_ious(tracker):
    assert tracker.get_net_owed("bob", "carol") == 0
    assert tracker.get_net_owed("carol", "bob") == 0


def test_net_owed_is_zero_when_the_directions_cancel_exactly(tracker):
    tracker.record_iou("bob", "alice", 600)
    assert tracker.get_net_owed("alice", "bob") == 0
    assert tracker.get_net_owed("bob", "alice") == 0
    assert tracker.get_net_debts() == [("alice", "dave", 150), ("carol", "alice", 100)]


def test_net_owed_is_antisymmetric(tracker):
    for a, b in [("alice", "bob"), ("alice", "carol"), ("alice", "dave"), ("carol", "dave")]:
        assert tracker.get_net_owed(a, b) == -tracker.get_net_owed(b, a)


def test_net_debts_name_the_user_owed_on_net_as_the_lender(tracker):
    tracker.record_iou("bob", "alice", 1000)  # alice now owes bob 1400, bob owes alice 1000
    assert tracker.get_net_owed("bob", "alice") == 400
    assert tracker.get_net_debts() == [
        ("bob", "alice", 400),
        ("alice", "dave", 150),
        ("carol", "alice", 100),
    ]


def test_net_debts_follow_new_ious(tracker):
    tracker.record_iou("alice", "carol", 300)  # carol now owes alice 200 on net
    assert tracker.get_net_debts() == [
        ("alice", "bob", 600),
        ("alice", "carol", 200),
        ("alice", "dave", 150),
    ]
    tracker.record_iou("carol", "dave", 700)
    assert tracker.get_net_debts() == [
        ("carol", "dave", 700),
        ("alice", "bob", 600),
        ("alice", "carol", 200),
        ("alice", "dave", 150),
    ]


def test_net_debts_are_empty_without_ious():
    trk = IouTracker()
    trk.add_user("alice")
    trk.add_user("bob")
    assert trk.get_net_debts() == []


def test_debtors_list_the_most_negative_net_position_first(tracker):
    tracker.record_iou("carol", "dave", 450)  # dave -600, carol 550
    assert tracker.get_debtors() == ["bob", "dave"]
    tracker.record_iou("alice", "dave", 1)
    assert tracker.get_debtors() == ["dave", "bob"]


def test_creditors_list_the_largest_net_position_first(tracker):
    tracker.record_iou("carol", "dave", 450)  # carol 550
    assert tracker.get_creditors() == ["alice", "carol"]
    tracker.record_iou("carol", "bob", 100)  # carol 650, the same as alice
    assert tracker.get_creditors() == ["alice", "carol"]
    tracker.record_iou("carol", "bob", 1)
    assert tracker.get_creditors() == ["carol", "alice"]


def test_users_with_a_zero_net_position_are_neither_debtors_nor_creditors():
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
    ],
)
def test_net_owed_for_names_that_are_not_users_raises_key_error(tracker, call):
    with pytest.raises(KeyError):
        call(tracker)


def test_net_owed_of_a_user_with_themselves_is_rejected(tracker):
    with pytest.raises(ValueError):
        tracker.get_net_owed("alice", "alice")


def test_net_queries_change_nothing(tracker):
    def snapshot():
        users = tracker.get_users()
        return (
            tracker.get_debts(),
            {
                u: (tracker.get_total_lent(u), tracker.get_total_borrowed(u), tracker.get_history(u))
                for u in users
            },
        )

    before = snapshot()
    tracker.get_net_owed("alice", "bob")
    tracker.get_net_debts()
    tracker.get_debtors()
    tracker.get_creditors()
    assert snapshot() == before
