"""Public checks for the c_usage change (usage queries). Shown to the
editor, never to the writer.

Usage (with limiter.py importable, e.g. in the sandbox):
    python -m pytest changes/c_usage/public/test_usage_public.py
"""

import pytest
from limiter import RateLimiter


@pytest.fixture
def limiter():
    lim = RateLimiter(window=10)
    lim.add_client("alice", allowance=5)
    lim.add_client("bob", allowance=5)
    lim.request("alice")
    lim.tick(3)
    lim.request("alice")
    lim.request("bob")
    lim.tick(4)
    lim.request("alice")
    return lim


def test_request_times_are_listed_oldest_first(limiter):
    assert limiter.get_request_times("alice") == [0, 3, 7]
    assert limiter.get_request_times("bob") == [3]


def test_usage_counts_requests_in_a_half_open_range(limiter):
    assert limiter.get_usage("alice", 0, 10) == 3
    assert limiter.get_usage("alice", 3, 7) == 1
    assert limiter.get_usage("bob", 4, 10) == 0


def test_active_clients_are_those_with_a_request_in_the_range(limiter):
    assert limiter.get_active_clients(0, 10) == ["alice", "bob"]
    assert limiter.get_active_clients(4, 10) == ["alice"]
    assert limiter.get_active_clients(8, 10) == []
