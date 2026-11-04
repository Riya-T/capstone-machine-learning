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


def state(trk):
    """Every IOU and every amount owed, to check that a failed call changed nothing."""
    users = trk.get_users()
    return {
        "users": list(users),
        "ious": list(trk.get_ious()),
        "owed": {(l, b): trk.get_owed(l, b) for l in users for b in users if l != b},
    }


# --- users ------------------------------------------------------------------


def test_a_new_tracker_has_no_ious(tracker):
    assert tracker.get_ious() == []
    assert tracker.get_owed("alice", "bob") == 0
    assert tracker.get_owed("bob", "alice") == 0


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
    assert state(tracker) == before


def test_a_user_added_later_can_lend_and_borrow(tracker):
    tracker.record_iou("alice", "bob", 100)
    tracker.add_user("dave")
    tracker.record_iou("dave", "alice", 30)
    tracker.record_iou("bob", "dave", 20)
    assert tracker.get_owed("dave", "alice") == 30
    assert tracker.get_owed("bob", "dave") == 20
    assert tracker.get_owed("dave", "carol") == 0
    assert tracker.get_ious() == [("alice", "bob", 100), ("dave", "alice", 30), ("bob", "dave", 20)]


@pytest.mark.parametrize(
    "lender, borrower",
    [("dave", "bob"), ("alice", "dave"), (None, "bob"), ("alice", None)],
)
def test_names_that_are_not_users_raise_key_error(tracker, lender, borrower):
    tracker.record_iou("alice", "bob", 50)
    before = state(tracker)
    with pytest.raises(KeyError):
        tracker.record_iou(lender, borrower, 10)
    assert state(tracker) == before


@pytest.mark.parametrize(
    "lender, borrower",
    [("dave", "bob"), ("alice", "dave"), (None, "bob"), ("alice", None)],
)
def test_owed_with_a_name_that_is_not_a_user(tracker, lender, borrower):
    # The spec says KeyError; returning 0 is accepted too.
    tracker.record_iou("alice", "bob", 50)
    before = state(tracker)
    try:
        owed = tracker.get_owed(lender, borrower)
    except KeyError:
        pass
    else:
        assert owed == 0
    assert state(tracker) == before


# --- ious -------------------------------------------------------------------


def test_each_iou_is_listed_once_in_the_order_recorded(tracker):
    tracker.record_iou("bob", "carol", 70)
    tracker.record_iou("alice", "bob", 300)
    tracker.record_iou("carol", "alice", 50)
    assert tracker.get_ious() == [
        ("bob", "carol", 70),
        ("alice", "bob", 300),
        ("carol", "alice", 50),
    ]


def test_repeated_ious_are_listed_separately(tracker):
    tracker.record_iou("alice", "bob", 100)
    tracker.record_iou("carol", "bob", 40)
    tracker.record_iou("alice", "bob", 100)
    assert tracker.get_ious() == [
        ("alice", "bob", 100),
        ("carol", "bob", 40),
        ("alice", "bob", 100),
    ]


def test_a_user_cannot_lend_to_themselves(tracker):
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


def test_failed_calls_add_no_iou(tracker):
    tracker.record_iou("alice", "bob", 10)
    for call in (
        lambda: tracker.record_iou("alice", "bob", 0),
        lambda: tracker.record_iou("alice", "alice", 5),
        lambda: tracker.record_iou("alice", "dave", 5),
        lambda: tracker.record_iou("dave", "alice", 5),
    ):
        with pytest.raises((ValueError, KeyError)):
            call()
    assert tracker.get_ious() == [("alice", "bob", 10)]
    assert tracker.get_owed("alice", "bob") == 10


# --- owed -------------------------------------------------------------------


def test_ious_between_the_same_pair_add_up(tracker):
    tracker.record_iou("alice", "bob", 300)
    tracker.record_iou("alice", "bob", 200)
    tracker.record_iou("alice", "bob", 5)
    assert tracker.get_owed("alice", "bob") == 505
    assert tracker.get_owed("bob", "alice") == 0


def test_users_with_no_ious_between_them_owe_nothing(tracker):
    tracker.record_iou("alice", "bob", 300)
    assert tracker.get_owed("bob", "alice") == 0
    assert tracker.get_owed("alice", "carol") == 0
    assert tracker.get_owed("carol", "alice") == 0
    assert tracker.get_owed("carol", "bob") == 0


def test_owed_counts_only_its_own_lender_and_borrower(tracker):
    tracker.record_iou("alice", "bob", 300)
    tracker.record_iou("alice", "carol", 40)
    tracker.record_iou("carol", "bob", 7)
    assert tracker.get_owed("alice", "bob") == 300
    assert tracker.get_owed("alice", "carol") == 40
    assert tracker.get_owed("carol", "bob") == 7


def test_debts_in_the_two_directions_are_kept_apart(tracker):
    tracker.record_iou("alice", "bob", 1000)
    tracker.record_iou("bob", "alice", 400)
    tracker.record_iou("alice", "bob", 100)
    tracker.record_iou("bob", "alice", 2000)
    assert tracker.get_owed("alice", "bob") == 1100
    assert tracker.get_owed("bob", "alice") == 2400


def test_owed_is_the_sum_of_the_listed_ious(tracker):
    for lender, borrower, amount in [
        ("alice", "bob", 700),
        ("bob", "carol", 100),
        ("carol", "alice", 30),
        ("alice", "carol", 5),
        ("bob", "alice", 60),
    ]:
        tracker.record_iou(lender, borrower, amount)
    users = tracker.get_users()
    for l in users:
        for b in users:
            if l != b:
                expected = sum(a for x, y, a in tracker.get_ious() if (x, y) == (l, b))
                assert tracker.get_owed(l, b) == expected


def test_the_example_from_the_spec(tracker):
    tracker.record_iou("alice", "bob", 300)
    tracker.record_iou("carol", "alice", 50)
    tracker.record_iou("alice", "bob", 200)
    tracker.record_iou("bob", "alice", 100)
    expected = [
        ("alice", "bob", 300),
        ("carol", "alice", 50),
        ("alice", "bob", 200),
        ("bob", "alice", 100),
    ]
    assert tracker.get_ious() == expected
    assert tracker.get_owed("alice", "bob") == 500
    assert tracker.get_owed("bob", "alice") == 100
    assert tracker.get_owed("carol", "alice") == 50
    assert tracker.get_owed("alice", "carol") == 0
    with pytest.raises(ValueError):
        tracker.record_iou("bob", "bob", 10)
    with pytest.raises(ValueError):
        tracker.record_iou("alice", "bob", 0)
    assert tracker.get_ious() == expected


def test_trackers_do_not_share_users():
    first, second = IouTracker(), IouTracker()
    first.add_user("alice")
    first.add_user("bob")
    first.record_iou("alice", "bob", 5)
    assert second.get_users() == []
    second.add_user("alice")
    second.add_user("bob")
    assert second.get_owed("alice", "bob") == 0
    assert second.get_ious() == []
