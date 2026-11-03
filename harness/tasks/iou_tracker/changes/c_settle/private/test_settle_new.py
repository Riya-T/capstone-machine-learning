"""Hidden tests for the c_settle change (paying back several lenders at
once). Never shown to the writer or the editor.

Usage (with ious.py importable, e.g. in the sandbox):
    python -m pytest changes/c_settle/private/test_settle_new.py
"""

import pytest
from ious import IouError, IouTracker

BAD_AMOUNTS = [0, -5]
IOUS = [("alice", "bob", 500), ("carol", "bob", 200), ("bob", "alice", 50)]


@pytest.fixture
def tracker():
    trk = IouTracker()
    trk.add_user("alice")
    trk.add_user("bob")
    trk.add_user("carol")
    for lender, borrower, amount in IOUS:
        trk.record_iou(lender, borrower, amount)
    return trk


def owed(trk):
    users = trk.get_users()
    return {(l, b): trk.get_owed(l, b) for l in users for b in users if l != b}


def state(trk):
    return {"ious": list(trk.get_ious()), "owed": owed(trk)}


def test_several_lenders_are_paid_in_one_call(tracker):
    tracker.settle("bob", [("alice", 100), ("carol", 200)])
    assert tracker.get_owed("alice", "bob") == 400
    assert tracker.get_owed("carol", "bob") == 0
    assert tracker.get_owed("bob", "alice") == 50


def test_payments_leave_the_list_of_ious_alone(tracker):
    tracker.settle("bob", [("alice", 500), ("carol", 50)])
    assert tracker.get_ious() == IOUS
    assert tracker.get_owed("alice", "bob") == 0
    assert tracker.get_owed("carol", "bob") == 150


def test_a_payment_leaves_the_debt_in_the_other_direction_alone(tracker):
    tracker.settle("bob", [("alice", 500)])
    assert tracker.get_owed("alice", "bob") == 0
    assert tracker.get_owed("bob", "alice") == 50
    tracker.settle("alice", [("bob", 20)])
    assert tracker.get_owed("bob", "alice") == 30
    assert tracker.get_owed("alice", "bob") == 0


def test_payments_change_only_their_own_pair(tracker):
    before = owed(tracker)
    tracker.settle("bob", [("carol", 75)])
    after = owed(tracker)
    assert after[("carol", "bob")] == 125
    del before[("carol", "bob")], after[("carol", "bob")]
    assert after == before


def test_payments_in_several_calls_add_up(tracker):
    tracker.settle("bob", [("alice", 200)])
    tracker.settle("bob", [("alice", 250)])
    assert tracker.get_owed("alice", "bob") == 50
    before = state(tracker)
    with pytest.raises(IouError):
        tracker.settle("bob", [("alice", 51)])
    assert state(tracker) == before
    tracker.settle("bob", [("alice", 50)])
    assert tracker.get_owed("alice", "bob") == 0


def test_one_oversized_payment_blocks_the_whole_list(tracker):
    before = state(tracker)
    with pytest.raises(IouError):
        tracker.settle("bob", [("alice", 100), ("carol", 201)])
    assert state(tracker) == before
    with pytest.raises(IouError):
        tracker.settle("bob", [("carol", 201), ("alice", 100)])
    assert state(tracker) == before


def test_paying_a_lender_who_is_owed_nothing_is_too_large(tracker):
    before = state(tracker)
    with pytest.raises(IouError):
        tracker.settle("carol", [("alice", 1)])
    with pytest.raises(IouError):
        tracker.settle("alice", [("carol", 1)])
    assert state(tracker) == before


def test_an_empty_list_does_nothing(tracker):
    before = state(tracker)
    tracker.settle("bob", [])
    assert state(tracker) == before


def test_new_ious_after_paying_off_start_the_debt_again(tracker):
    tracker.settle("bob", [("carol", 200)])
    tracker.record_iou("carol", "bob", 30)
    assert tracker.get_owed("carol", "bob") == 30
    assert tracker.get_ious() == IOUS + [("carol", "bob", 30)]
    tracker.settle("bob", [("carol", 30)])
    assert tracker.get_owed("carol", "bob") == 0


def test_a_borrower_that_is_not_a_user_raises_key_error(tracker):
    before = state(tracker)
    with pytest.raises(KeyError):
        tracker.settle("dave", [])
    with pytest.raises(KeyError):
        tracker.settle(None, [])
    assert state(tracker) == before


@pytest.mark.parametrize(
    "payments",
    [[("dave", 10)], [("alice", 10), ("dave", 10)], [(None, 10)]],
)
def test_a_lender_that_is_not_a_user_is_rejected(tracker, payments):
    # A lender who is not a user is owed nothing either, so IouError is allowed too.
    before = state(tracker)
    with pytest.raises((KeyError, IouError)):
        tracker.settle("bob", payments)
    assert state(tracker) == before


@pytest.mark.parametrize("amount", BAD_AMOUNTS)
def test_invalid_payment_amounts_are_rejected(tracker, amount):
    before = state(tracker)
    with pytest.raises(ValueError):
        tracker.settle("bob", [("alice", 10), ("carol", amount)])
    assert state(tracker) == before


def test_a_lender_listed_twice_is_rejected(tracker):
    before = state(tracker)
    with pytest.raises(ValueError):
        tracker.settle("bob", [("alice", 100), ("carol", 50), ("alice", 100)])
    assert state(tracker) == before
