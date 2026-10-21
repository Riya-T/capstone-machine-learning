"""Hidden tests for the c_settle change (paying back several lenders at
once). Never shown to the writer or the editor.

Usage (with ious.py importable, e.g. in the sandbox):
    python -m pytest changes/c_settle/private/test_settle_new.py
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
    trk.record_iou("alice", "bob", 500)
    trk.record_iou("carol", "bob", 200)
    trk.record_iou("bob", "alice", 50)
    return trk


def state(trk):
    return {
        u: (trk.get_balance(u), trk.get_owed_to(u), trk.get_owed_by(u), trk.get_history(u))
        for u in trk.get_users()
    }


def test_several_lenders_are_paid_in_one_call(tracker):
    tracker.settle("bob", [("alice", 100), ("carol", 200)])
    assert tracker.get_owed_by("bob") == [("alice", 400)]
    assert tracker.get_owed_to("alice") == [("bob", 400)]
    assert tracker.get_owed_to("carol") == []
    assert tracker.get_balance("bob") == -350
    assert tracker.get_balance("carol") == 0


def test_a_payment_leaves_the_debt_in_the_other_direction_alone(tracker):
    tracker.settle("bob", [("alice", 500)])
    assert tracker.get_owed_by("bob") == [("carol", 200)]
    assert tracker.get_owed_to("bob") == [("alice", 50)]
    assert tracker.get_owed_by("alice") == [("bob", 50)]


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
    assert state(tracker) == before


def test_payments_add_nothing_to_history(tracker):
    tracker.settle("bob", [("alice", 500), ("carol", 200)])
    assert tracker.get_history("bob") == [
        ("alice", "bob", 500),
        ("carol", "bob", 200),
        ("bob", "alice", 50),
    ]
    assert tracker.get_history("carol") == [("carol", "bob", 200)]


def test_an_empty_list_does_nothing(tracker):
    before = state(tracker)
    tracker.settle("bob", [])
    assert state(tracker) == before


def test_new_ious_after_paying_off_start_the_debt_again(tracker):
    tracker.settle("bob", [("carol", 200)])
    tracker.record_iou("carol", "bob", 30)
    assert tracker.get_owed_by("bob") == [("alice", 500), ("carol", 30)]


def test_a_borrower_that_is_not_a_user_raises_key_error(tracker):
    before = state(tracker)
    with pytest.raises(KeyError):
        tracker.settle("dave", [("alice", 10)])
    with pytest.raises(KeyError):
        tracker.settle(None, [])
    assert state(tracker) == before


@pytest.mark.parametrize(
    "payments",
    [[("dave", 10)], [("alice", 10), ("dave", 10)], [(None, 10)]],
)
def test_a_lender_that_is_not_a_user_raises_key_error(tracker, payments):
    before = state(tracker)
    with pytest.raises(KeyError):
        tracker.settle("bob", payments)
    assert state(tracker) == before


@pytest.mark.parametrize("amount", BAD_AMOUNTS)
def test_invalid_payment_amounts_are_rejected(tracker, amount):
    before = state(tracker)
    with pytest.raises(ValueError):
        tracker.settle("bob", [("alice", 10), ("carol", amount)])
    assert state(tracker) == before


def test_a_user_cannot_pay_themselves(tracker):
    before = state(tracker)
    with pytest.raises(ValueError):
        tracker.settle("bob", [("bob", 10)])
    assert state(tracker) == before


def test_a_lender_listed_twice_is_rejected(tracker):
    before = state(tracker)
    with pytest.raises(ValueError):
        tracker.settle("bob", [("alice", 100), ("carol", 50), ("alice", 100)])
    assert state(tracker) == before


def test_input_problems_are_reported_before_an_oversized_payment(tracker):
    # The first payment is too large in each case, but a later input problem wins.
    with pytest.raises(KeyError):
        tracker.settle("bob", [("alice", 1000), ("dave", 1)])
    with pytest.raises(ValueError):
        tracker.settle("bob", [("alice", 1000), ("carol", 0)])
    with pytest.raises(ValueError):
        tracker.settle("bob", [("alice", 1000), ("bob", 1)])
    with pytest.raises(ValueError):
        tracker.settle("bob", [("alice", 1000), ("carol", 1), ("carol", 1)])


def test_an_unknown_lender_is_reported_before_a_bad_amount(tracker):
    with pytest.raises(KeyError):
        tracker.settle("bob", [("dave", -1)])
    with pytest.raises(KeyError):
        tracker.settle("dave", [("alice", -1)])
