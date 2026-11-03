"""Hidden tests for the initial iou_tracker spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with ious.py importable, e.g. in the sandbox):
    python -m pytest private/test_ious_initial.py
"""

import pytest
from ious import IouError, IouTracker

BAD_AMOUNTS = [0, -5]


@pytest.fixture
def tracker():
    trk = IouTracker()
    trk.add_user("alice")
    trk.add_user("bob")
    trk.add_user("carol")
    return trk


def totals(trk, name):
    return (trk.get_total_lent(name), trk.get_total_borrowed(name))


def state(trk):
    """Every debt, total and history, to check that a failed call changed nothing."""
    users = trk.get_users()
    return {
        "debts": trk.get_debts(),
        "owed": {(l, b): trk.get_owed(l, b) for l in users for b in users if l != b},
        "users": {u: (totals(trk, u), trk.get_history(u)) for u in users},
    }


# --- users ------------------------------------------------------------------


def test_a_new_user_has_no_ious(tracker):
    assert totals(tracker, "alice") == (0, 0)
    assert tracker.get_owed("alice", "bob") == 0
    assert tracker.get_owed("bob", "alice") == 0
    assert tracker.get_debts() == []
    assert tracker.get_history("alice") == []


def test_users_are_listed_in_the_order_added():
    trk = IouTracker()
    for name in ["carol", "alice", "bob"]:
        trk.add_user(name)
    assert trk.get_users() == ["carol", "alice", "bob"]


def test_an_empty_name_is_rejected():
    trk = IouTracker()
    with pytest.raises(ValueError):
        trk.add_user("")
    assert trk.get_users() == []


def test_adding_a_user_twice_is_rejected(tracker):
    tracker.record_iou("alice", "bob", 100)
    before = state(tracker)
    with pytest.raises(IouError):
        tracker.add_user("alice")
    assert tracker.get_users() == ["alice", "bob", "carol"]
    assert state(tracker) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda trk: trk.record_iou("dave", "bob", 10),
        lambda trk: trk.record_iou("alice", "dave", 10),
        lambda trk: trk.get_owed("dave", "bob"),
        lambda trk: trk.get_owed("alice", "dave"),
        lambda trk: trk.get_total_lent("dave"),
        lambda trk: trk.get_total_borrowed("dave"),
        lambda trk: trk.get_history("dave"),
        lambda trk: trk.get_total_lent(None),
        lambda trk: trk.get_total_borrowed(None),
        lambda trk: trk.get_history(None),
    ],
)
def test_names_that_are_not_users_raise_key_error(tracker, call):
    tracker.record_iou("alice", "bob", 50)
    before = state(tracker)
    with pytest.raises(KeyError):
        call(tracker)
    assert state(tracker) == before


# --- ious and debts ---------------------------------------------------------


def test_ious_between_the_same_pair_add_up(tracker):
    tracker.record_iou("alice", "bob", 300)
    tracker.record_iou("alice", "bob", 200)
    assert tracker.get_owed("alice", "bob") == 500
    assert tracker.get_owed("bob", "alice") == 0
    assert tracker.get_debts() == [("alice", "bob", 500)]


def test_users_with_no_ious_between_them_owe_nothing(tracker):
    tracker.record_iou("alice", "bob", 300)
    assert tracker.get_owed("bob", "alice") == 0
    assert tracker.get_owed("alice", "carol") == 0
    assert tracker.get_owed("carol", "bob") == 0


def test_debts_list_the_largest_amount_first(tracker):
    tracker.record_iou("alice", "bob", 100)
    tracker.record_iou("carol", "alice", 250)
    tracker.record_iou("bob", "carol", 175)
    assert tracker.get_debts() == [
        ("carol", "alice", 250),
        ("bob", "carol", 175),
        ("alice", "bob", 100),
    ]


def test_debts_are_reordered_as_amounts_change(tracker):
    tracker.record_iou("carol", "alice", 300)
    tracker.record_iou("bob", "alice", 200)
    assert tracker.get_debts() == [("carol", "alice", 300), ("bob", "alice", 200)]
    tracker.record_iou("bob", "alice", 101)
    assert tracker.get_debts() == [("bob", "alice", 301), ("carol", "alice", 300)]


def test_debts_in_the_two_directions_are_kept_apart(tracker):
    tracker.record_iou("alice", "bob", 1000)
    tracker.record_iou("bob", "alice", 400)
    tracker.record_iou("alice", "bob", 100)
    assert tracker.get_owed("alice", "bob") == 1100
    assert tracker.get_owed("bob", "alice") == 400
    assert tracker.get_debts() == [("alice", "bob", 1100), ("bob", "alice", 400)]


def test_a_user_cannot_owe_themselves(tracker):
    tracker.record_iou("alice", "bob", 100)
    before = state(tracker)
    with pytest.raises(ValueError):
        tracker.record_iou("alice", "alice", 50)
    assert state(tracker) == before


@pytest.mark.parametrize("amount", BAD_AMOUNTS)
def test_invalid_amounts_are_rejected(tracker, amount):
    tracker.record_iou("alice", "bob", 100)
    before = state(tracker)
    with pytest.raises(ValueError):
        tracker.record_iou("alice", "bob", amount)
    assert state(tracker) == before


# --- totals -----------------------------------------------------------------


def test_totals_add_up_repeated_ious(tracker):
    tracker.record_iou("alice", "bob", 300)
    tracker.record_iou("alice", "bob", 200)
    assert totals(tracker, "alice") == (500, 0)
    assert totals(tracker, "bob") == (0, 500)
    assert totals(tracker, "carol") == (0, 0)


def test_totals_add_up_every_other_user(tracker):
    tracker.record_iou("alice", "bob", 700)
    tracker.record_iou("bob", "carol", 100)
    tracker.record_iou("carol", "alice", 30)
    tracker.record_iou("alice", "carol", 5)
    assert totals(tracker, "alice") == (705, 30)
    assert totals(tracker, "bob") == (100, 700)
    assert totals(tracker, "carol") == (30, 105)


def test_lent_and_borrowed_are_never_netted(tracker):
    tracker.record_iou("alice", "bob", 1000)
    tracker.record_iou("bob", "alice", 400)
    assert totals(tracker, "alice") == (1000, 400)
    assert totals(tracker, "bob") == (400, 1000)


def test_the_example_from_the_spec(tracker):
    tracker.record_iou("alice", "bob", 300)
    tracker.record_iou("carol", "alice", 50)
    tracker.record_iou("alice", "bob", 200)
    tracker.record_iou("bob", "alice", 100)
    assert tracker.get_owed("alice", "bob") == 500
    assert tracker.get_owed("bob", "alice") == 100
    assert tracker.get_owed("alice", "carol") == 0
    assert tracker.get_debts() == [
        ("alice", "bob", 500),
        ("bob", "alice", 100),
        ("carol", "alice", 50),
    ]
    assert [totals(tracker, u) for u in ["alice", "bob", "carol"]] == [
        (500, 150),
        (100, 500),
        (50, 0),
    ]
    assert tracker.get_history("alice") == [
        ("alice", "bob", 300),
        ("carol", "alice", 50),
        ("alice", "bob", 200),
        ("bob", "alice", 100),
    ]
    assert tracker.get_history("bob") == [
        ("alice", "bob", 300),
        ("alice", "bob", 200),
        ("bob", "alice", 100),
    ]
    assert tracker.get_history("carol") == [("carol", "alice", 50)]


# --- history ----------------------------------------------------------------


def test_history_includes_both_sides_of_an_iou(tracker):
    tracker.record_iou("alice", "bob", 300)
    tracker.record_iou("carol", "alice", 50)
    tracker.record_iou("bob", "alice", 20)
    assert tracker.get_history("alice") == [
        ("alice", "bob", 300),
        ("carol", "alice", 50),
        ("bob", "alice", 20),
    ]
    assert tracker.get_history("bob") == [("alice", "bob", 300), ("bob", "alice", 20)]
    assert tracker.get_history("carol") == [("carol", "alice", 50)]


def test_history_leaves_out_ious_between_other_users(tracker):
    tracker.record_iou("alice", "bob", 300)
    assert tracker.get_history("carol") == []


def test_history_keeps_repeated_ious_separate(tracker):
    tracker.record_iou("alice", "bob", 100)
    tracker.record_iou("carol", "bob", 40)
    tracker.record_iou("alice", "bob", 100)
    assert tracker.get_history("bob") == [
        ("alice", "bob", 100),
        ("carol", "bob", 40),
        ("alice", "bob", 100),
    ]
    assert tracker.get_history("alice") == [("alice", "bob", 100), ("alice", "bob", 100)]


def test_failed_calls_add_nothing_to_history(tracker):
    tracker.record_iou("alice", "bob", 10)
    for call in (
        lambda: tracker.record_iou("alice", "bob", 0),
        lambda: tracker.record_iou("alice", "alice", 5),
        lambda: tracker.record_iou("alice", "dave", 5),
    ):
        with pytest.raises((ValueError, KeyError)):
            call()
    assert tracker.get_history("alice") == [("alice", "bob", 10)]
    assert tracker.get_history("bob") == [("alice", "bob", 10)]


def test_trackers_do_not_share_users():
    first, second = IouTracker(), IouTracker()
    first.add_user("alice")
    first.add_user("bob")
    first.record_iou("alice", "bob", 5)
    assert second.get_users() == []
    second.add_user("alice")
    second.add_user("bob")
    assert second.get_owed("alice", "bob") == 0
    assert second.get_debts() == []
    assert totals(second, "alice") == (0, 0)
    assert second.get_history("alice") == []
