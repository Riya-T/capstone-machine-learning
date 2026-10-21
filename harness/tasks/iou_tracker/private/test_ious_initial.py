"""Hidden tests for the initial iou_tracker spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with ious.py importable, e.g. in the sandbox):
    python -m pytest private/test_ious_initial.py
"""

import pytest
from ious import IouError, IouTracker

BAD_AMOUNTS = [0, -5, 1.5, "10", None]


@pytest.fixture
def tracker():
    trk = IouTracker()
    trk.add_user("alice")
    trk.add_user("bob")
    trk.add_user("carol")
    return trk


def state(trk):
    """Every debt and history, to check that a failed call changed nothing."""
    return {
        u: (trk.get_balance(u), trk.get_owed_to(u), trk.get_owed_by(u), trk.get_history(u))
        for u in trk.get_users()
    }


# --- users ------------------------------------------------------------------


def test_a_new_user_owes_nothing_and_is_owed_nothing(tracker):
    assert tracker.get_balance("alice") == 0
    assert tracker.get_owed_to("alice") == []
    assert tracker.get_owed_by("alice") == []
    assert tracker.get_history("alice") == []


def test_users_are_listed_in_the_order_added():
    trk = IouTracker()
    for name in ["carol", "alice", "bob"]:
        trk.add_user(name)
    assert trk.get_users() == ["carol", "alice", "bob"]


@pytest.mark.parametrize("bad_name", [""])
def test_invalid_names_are_rejected(bad_name):
    trk = IouTracker()
    with pytest.raises(ValueError):
        trk.add_user(bad_name)
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
        lambda trk: trk.get_owed_to("dave"),
        lambda trk: trk.get_owed_by("dave"),
        lambda trk: trk.get_balance("dave"),
        lambda trk: trk.get_history("dave"),
        lambda trk: trk.get_balance(None),
        lambda trk: trk.get_balance(1),
        lambda trk: trk.record_iou(None, "bob", 10),
    ],
)
def test_names_that_are_not_users_raise_key_error(tracker, call):
    tracker.record_iou("alice", "bob", 50)
    before = state(tracker)
    with pytest.raises(KeyError):
        call(tracker)
    assert state(tracker) == before


# --- ious -------------------------------------------------------------------


def test_ious_between_the_same_pair_add_up(tracker):
    tracker.record_iou("alice", "bob", 300)
    tracker.record_iou("alice", "bob", 200)
    assert tracker.get_owed_to("alice") == [("bob", 500)]
    assert tracker.get_owed_by("bob") == [("alice", 500)]
    assert tracker.get_balance("alice") == 500
    assert tracker.get_balance("bob") == -500


def test_owed_to_lists_largest_amount_first(tracker):
    tracker.record_iou("alice", "bob", 100)
    tracker.record_iou("alice", "carol", 250)
    assert tracker.get_owed_to("alice") == [("carol", 250), ("bob", 100)]


def test_owed_to_breaks_ties_by_the_order_users_were_added(tracker):
    tracker.record_iou("alice", "carol", 100)
    tracker.record_iou("alice", "bob", 100)
    assert tracker.get_owed_to("alice") == [("bob", 100), ("carol", 100)]


def test_owed_by_lists_largest_amount_first_with_ties_in_user_order(tracker):
    tracker.record_iou("carol", "alice", 300)
    tracker.record_iou("bob", "alice", 300)
    assert tracker.get_owed_by("alice") == [("bob", 300), ("carol", 300)]
    tracker.record_iou("carol", "alice", 1)
    assert tracker.get_owed_by("alice") == [("carol", 301), ("bob", 300)]


def test_users_that_owe_nothing_are_not_listed(tracker):
    tracker.record_iou("alice", "bob", 100)
    assert tracker.get_owed_to("alice") == [("bob", 100)]
    assert tracker.get_owed_by("carol") == []
    assert tracker.get_owed_to("carol") == []


def test_debts_in_the_two_directions_are_kept_apart(tracker):
    tracker.record_iou("alice", "bob", 1000)
    tracker.record_iou("bob", "alice", 400)
    assert tracker.get_owed_to("alice") == [("bob", 1000)]
    assert tracker.get_owed_by("alice") == [("bob", 400)]
    assert tracker.get_owed_to("bob") == [("alice", 400)]
    assert tracker.get_owed_by("bob") == [("alice", 1000)]


def test_balance_can_be_negative(tracker):
    tracker.record_iou("alice", "bob", 700)
    tracker.record_iou("bob", "carol", 100)
    assert tracker.get_balance("alice") == 700
    assert tracker.get_balance("bob") == -600
    assert tracker.get_balance("carol") == -100


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


def test_an_unknown_user_is_reported_before_a_bad_amount(tracker):
    with pytest.raises(KeyError):
        tracker.record_iou("dave", "bob", -1)
    with pytest.raises(KeyError):
        tracker.record_iou("alice", "dave", -1)


def test_an_unknown_user_is_reported_before_the_same_name_check(tracker):
    with pytest.raises(KeyError):
        tracker.record_iou("dave", "dave", 10)


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
    tracker.record_iou("alice", "bob", 100)
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
    assert second.get_balance("alice") == 0
    assert second.get_history("alice") == []
