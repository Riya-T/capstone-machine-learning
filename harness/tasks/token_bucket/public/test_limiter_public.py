"""Public checks for limiter.py.

Usage (with limiter.py importable, e.g. in the sandbox):
    python -m pytest public/test_limiter_public.py
"""

import pytest
from limiter import RateLimited, RateLimiter


@pytest.fixture
def limiter():
    lim = RateLimiter(window=10)
    lim.add_client("alice", allowance=3)
    lim.add_client("bob", allowance=1)
    return lim


def test_a_request_uses_up_one_of_the_allowance(limiter):
    assert limiter.get_remaining("alice") == 3
    limiter.request("alice")
    assert limiter.get_remaining("alice") == 2


def test_too_many_requests_in_one_window_raise(limiter):
    limiter.request("bob")
    with pytest.raises(RateLimited):
        limiter.request("bob")
    assert limiter.get_remaining("bob") == 0


def test_a_new_window_restores_the_allowance(limiter):
    limiter.request("bob")
    limiter.tick(9)
    assert limiter.get_time() == 9
    assert limiter.get_remaining("bob") == 0
    limiter.tick()
    assert limiter.get_time() == 10
    assert limiter.get_remaining("bob") == 1


def test_receipts_count_requests_over_all_clients(limiter):
    assert limiter.request("alice") == 1
    assert limiter.request("bob") == 2
    assert limiter.request("alice") == 3


def test_steps_must_be_positive(limiter):
    with pytest.raises(ValueError):
        limiter.tick(0)
    assert limiter.get_time() == 0


def test_unknown_client_raises_key_error(limiter):
    with pytest.raises(KeyError):
        limiter.request("carol")
    with pytest.raises(KeyError):
        limiter.get_remaining("carol")
