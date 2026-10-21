"""Hidden tests for the c_refund change (refunding a request). Never shown
to the writer or the editor.

Usage (with limiter.py importable, e.g. in the sandbox):
    python -m pytest changes/c_refund/private/test_refund_new.py
"""

import pytest
from limiter import LimiterError, RateLimited, RateLimiter


@pytest.fixture
def limiter():
    lim = RateLimiter(window=5)
    lim.add_client("alice", allowance=2)
    lim.add_client("bob", allowance=1)
    lim.request("alice")  # receipt 1
    lim.request("bob")  # receipt 2
    lim.request("alice")  # receipt 3
    return lim


def state(lim):
    return (
        lim.get_time(),
        {c: (lim.get_remaining(c), lim.get_receipts(c)) for c in lim.get_clients()},
    )


def test_receipts_are_listed_per_client_oldest_first(limiter):
    assert limiter.get_receipts("alice") == [1, 3]
    assert limiter.get_receipts("bob") == [2]


def test_a_refund_frees_one_request_in_the_current_window(limiter):
    with pytest.raises(RateLimited):
        limiter.request("alice")
    limiter.refund(1)
    assert limiter.get_remaining("alice") == 1
    assert limiter.get_receipts("alice") == [3]
    assert limiter.request("alice") == 4
    assert limiter.get_remaining("alice") == 0


def test_refunding_every_request_restores_the_whole_allowance(limiter):
    limiter.refund(3)
    limiter.refund(1)
    assert limiter.get_remaining("alice") == 2
    assert limiter.get_receipts("alice") == []
    assert limiter.get_remaining("bob") == 0


def test_a_refund_only_affects_its_own_client(limiter):
    limiter.refund(2)
    assert limiter.get_remaining("bob") == 1
    assert limiter.get_remaining("alice") == 0
    assert limiter.get_receipts("alice") == [1, 3]


def test_a_request_from_an_earlier_window_can_be_refunded(limiter):
    limiter.tick(5)
    assert limiter.get_remaining("alice") == 2
    limiter.refund(1)
    assert limiter.get_remaining("alice") == 2
    assert limiter.get_receipts("alice") == [3]


def test_a_refund_does_not_leak_into_a_later_window(limiter):
    limiter.refund(1)
    limiter.tick(5)
    limiter.request("alice")
    limiter.request("alice")
    with pytest.raises(RateLimited):
        limiter.request("alice")


@pytest.mark.parametrize("receipt", [0, 4, -1, None, "1", 1.5])
def test_unknown_receipts_are_rejected(limiter, receipt):
    before = state(limiter)
    with pytest.raises(KeyError):
        limiter.refund(receipt)
    assert state(limiter) == before


def test_refunding_twice_is_rejected_and_changes_nothing(limiter):
    limiter.refund(3)
    before = state(limiter)
    with pytest.raises(LimiterError):
        limiter.refund(3)
    assert state(limiter) == before


def test_refunded_receipt_numbers_are_not_reused(limiter):
    limiter.refund(3)
    assert limiter.request("alice") == 4
    limiter.refund(4)
    assert limiter.request("alice") == 5
    assert limiter.get_receipts("alice") == [1, 5]


def test_a_refund_does_not_change_the_time(limiter):
    limiter.tick(2)
    limiter.refund(2)
    assert limiter.get_time() == 2


@pytest.mark.parametrize("client_id", ["carol", None, 1])
def test_receipts_of_unknown_clients_raise_key_error(limiter, client_id):
    with pytest.raises(KeyError):
        limiter.get_receipts(client_id)


def test_a_limited_request_does_not_create_a_receipt_to_refund(limiter):
    with pytest.raises(RateLimited):
        limiter.request("bob")
    with pytest.raises(KeyError):
        limiter.refund(4)
