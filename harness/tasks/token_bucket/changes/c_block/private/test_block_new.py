"""Hidden tests for the c_block change (blocked clients). Never shown to the
writer or the editor.

Usage (with limiter.py importable, e.g. in the sandbox):
    python -m pytest changes/c_block/private/test_block_new.py
"""

import pytest
from limiter import ClientBlocked, LimiterError, RateLimited, RateLimiter


@pytest.fixture
def limiter():
    lim = RateLimiter(window=5)
    lim.add_client("alice", allowance=3)
    lim.add_client("bob", allowance=1)
    lim.request("alice")
    return lim


def state(lim):
    return (lim.get_time(), {c: lim.get_remaining(c) for c in lim.get_clients()})


def test_clients_start_unblocked(limiter):
    assert not limiter.is_blocked("alice")
    assert not limiter.is_blocked("bob")


def test_blocking_or_unblocking_twice_is_harmless(limiter):
    limiter.block("alice")
    limiter.block("alice")
    assert limiter.is_blocked("alice")
    assert not limiter.is_blocked("bob")
    limiter.unblock("alice")
    limiter.unblock("alice")
    assert not limiter.is_blocked("alice")


@pytest.mark.parametrize("method", ["block", "unblock", "is_blocked"])
@pytest.mark.parametrize("client_id", ["carol", None, 1])
def test_clients_that_are_not_registered_cannot_be_blocked(limiter, method, client_id):
    with pytest.raises(KeyError):
        getattr(limiter, method)(client_id)


def test_a_request_from_a_blocked_client_changes_nothing(limiter):
    limiter.block("alice")
    before = state(limiter)
    with pytest.raises(ClientBlocked):
        limiter.request("alice")
    assert state(limiter) == before
    limiter.unblock("alice")
    assert limiter.get_remaining("alice") == 2


def test_a_blocked_request_does_not_use_a_receipt_number(limiter):
    limiter.block("alice")
    with pytest.raises(ClientBlocked):
        limiter.request("alice")
    assert limiter.request("bob") == 2
    limiter.unblock("alice")
    assert limiter.request("alice") == 3


def test_remaining_is_zero_while_blocked_and_restored_after(limiter):
    limiter.block("alice")
    assert limiter.get_remaining("alice") == 0
    assert limiter.get_remaining("bob") == 1
    limiter.unblock("alice")
    assert limiter.get_remaining("alice") == 2


def test_earlier_requests_still_count_after_unblocking(limiter):
    limiter.request("alice")
    limiter.block("alice")
    limiter.unblock("alice")
    assert limiter.get_remaining("alice") == 1
    limiter.request("alice")
    with pytest.raises(RateLimited):
        limiter.request("alice")


def test_a_new_window_still_refreshes_a_blocked_client_once_unblocked(limiter):
    limiter.block("alice")
    limiter.tick(5)
    assert limiter.get_remaining("alice") == 0
    limiter.unblock("alice")
    assert limiter.get_remaining("alice") == 3


def test_blocked_is_reported_before_rate_limited(limiter):
    limiter.request("bob")
    limiter.block("bob")
    with pytest.raises(ClientBlocked):
        limiter.request("bob")


def test_unknown_client_is_reported_before_blocked(limiter):
    limiter.block("alice")
    with pytest.raises(KeyError):
        limiter.request("carol")


def test_blocking_does_not_touch_time_or_receipts(limiter):
    limiter.block("bob")
    limiter.unblock("bob")
    assert limiter.get_time() == 0
    assert limiter.request("bob") == 2


def test_client_blocked_is_a_limiter_error_but_not_rate_limited():
    assert issubclass(ClientBlocked, LimiterError)
    assert not issubclass(ClientBlocked, RateLimited)
