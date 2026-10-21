"""Hidden tests for the c_usage change (usage queries). Never shown to the
writer or the editor.

Usage (with limiter.py importable, e.g. in the sandbox):
    python -m pytest changes/c_usage/private/test_usage_new.py
"""

import pytest
from limiter import ClientBlocked, RateLimited, RateLimiter

BAD_BOUNDS = [-1, 1.5, "3", True, None]


@pytest.fixture
def limiter():
    lim = RateLimiter(window=5)
    lim.add_client("alice", allowance=2)
    lim.add_client("bob", allowance=1)
    lim.add_client("carol", allowance=2)
    lim.request("alice")  # t=0
    lim.request("bob")  # t=0
    lim.tick(2)
    lim.request("alice")  # t=2
    lim.tick(3)
    lim.request("alice")  # t=5, a new window
    return lim


def test_a_client_without_requests_has_an_empty_record(limiter):
    assert limiter.get_request_times("carol") == []
    assert limiter.get_usage("carol", 0, 100) == 0


def test_request_times_span_windows_oldest_first(limiter):
    assert limiter.get_request_times("alice") == [0, 2, 5]
    assert limiter.get_request_times("bob") == [0]


def test_requests_at_the_same_time_are_both_listed(limiter):
    limiter.request("carol")
    limiter.request("carol")
    assert limiter.get_request_times("carol") == [5, 5]
    assert limiter.get_usage("carol", 5, 6) == 2


def test_usage_excludes_the_end_of_the_range(limiter):
    assert limiter.get_usage("alice", 0, 5) == 2
    assert limiter.get_usage("alice", 0, 6) == 3
    assert limiter.get_usage("alice", 2, 5) == 1
    assert limiter.get_usage("alice", 3, 5) == 0
    assert limiter.get_usage("alice", 2, 2) == 0
    assert limiter.get_active_clients(0, 0) == []


def test_a_range_past_the_current_time_is_allowed(limiter):
    assert limiter.get_usage("alice", 0, 1000) == 3
    assert limiter.get_active_clients(6, 1000) == []


def test_active_clients_keep_registration_order(limiter):
    limiter.request("carol")
    assert limiter.get_active_clients(0, 10) == ["alice", "bob", "carol"]
    assert limiter.get_active_clients(1, 10) == ["alice", "carol"]
    assert limiter.get_active_clients(0, 1) == ["alice", "bob"]


@pytest.mark.parametrize("client_id", ["dave", None, 1])
def test_unknown_clients_raise_key_error(limiter, client_id):
    with pytest.raises(KeyError):
        limiter.get_request_times(client_id)
    with pytest.raises(KeyError):
        limiter.get_usage(client_id, 0, 5)


@pytest.mark.parametrize("bad", BAD_BOUNDS)
def test_invalid_bounds_are_rejected(limiter, bad):
    with pytest.raises(ValueError):
        limiter.get_usage("alice", bad, 5)
    with pytest.raises(ValueError):
        limiter.get_usage("alice", 0, bad)
    with pytest.raises(ValueError):
        limiter.get_active_clients(bad, 5)
    with pytest.raises(ValueError):
        limiter.get_active_clients(0, bad)


def test_a_start_after_the_end_is_rejected(limiter):
    with pytest.raises(ValueError):
        limiter.get_usage("alice", 6, 5)
    with pytest.raises(ValueError):
        limiter.get_active_clients(6, 5)


def test_unknown_client_is_reported_before_bad_bounds(limiter):
    with pytest.raises(KeyError):
        limiter.get_usage("dave", 6, 5)


def test_refused_requests_never_appear(limiter):
    limiter.request("bob")  # t=5, bob's one request of this window
    with pytest.raises(RateLimited):
        limiter.request("bob")
    limiter.block("carol")
    with pytest.raises(ClientBlocked):
        limiter.request("carol")
    with pytest.raises(KeyError):
        limiter.request("dave")
    assert limiter.get_request_times("bob") == [0, 5]
    assert limiter.get_request_times("carol") == []
    assert limiter.get_usage("bob", 5, 6) == 1
    assert limiter.get_active_clients(5, 6) == ["alice", "bob"]


def test_queries_do_not_change_the_limiter(limiter):
    limiter.get_usage("alice", 0, 10)
    limiter.get_active_clients(0, 10)
    assert limiter.get_time() == 5
    assert limiter.get_remaining("alice") == 1
    assert limiter.request("carol") == 5
