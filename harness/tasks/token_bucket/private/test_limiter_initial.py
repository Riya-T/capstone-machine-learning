"""Hidden tests for the initial token_bucket spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with limiter.py importable, e.g. in the sandbox):
    python -m pytest private/test_limiter_initial.py
"""

import pytest
from limiter import LimiterError, RateLimited, RateLimiter

BAD_COUNTS = [0, -3, 1.5, "2", None]


@pytest.fixture
def limiter():
    lim = RateLimiter(window=5)
    lim.add_client("alice", allowance=3)
    lim.add_client("bob", allowance=1)
    return lim


def state(lim):
    """Time and every remaining count, to check that a failed call changed nothing."""
    return (lim.get_time(), {c: lim.get_remaining(c) for c in lim.get_clients()})


# --- time and windows ---------------------------------------------------------


def test_time_starts_at_zero_and_ticks_add_up(limiter):
    assert limiter.get_time() == 0
    limiter.tick()
    limiter.tick(3)
    assert limiter.get_time() == 4


@pytest.mark.parametrize("steps", BAD_COUNTS)
def test_invalid_steps_are_rejected(limiter, steps):
    limiter.request("alice")
    before = state(limiter)
    with pytest.raises(ValueError):
        limiter.tick(steps)
    assert state(limiter) == before


@pytest.mark.parametrize("window", BAD_COUNTS)
def test_invalid_windows_are_rejected(window):
    with pytest.raises(ValueError):
        RateLimiter(window=window)


def test_the_last_tick_of_a_window_still_belongs_to_it(limiter):
    limiter.request("bob")
    limiter.tick(4)
    assert limiter.get_remaining("bob") == 0
    with pytest.raises(RateLimited):
        limiter.request("bob")


def test_the_first_tick_of_the_next_window_starts_fresh(limiter):
    limiter.request("bob")
    limiter.tick(5)
    assert limiter.get_remaining("bob") == 1
    limiter.request("bob")
    assert limiter.get_remaining("bob") == 0


def test_a_window_of_one_tick_resets_every_tick():
    lim = RateLimiter(window=1)
    lim.add_client("alice", allowance=1)
    for _ in range(3):
        lim.request("alice")
        with pytest.raises(RateLimited):
            lim.request("alice")
        lim.tick()
    assert lim.get_remaining("alice") == 1


def test_ticking_past_several_windows_at_once(limiter):
    limiter.request("alice")
    limiter.request("alice")
    limiter.tick(23)
    assert limiter.get_time() == 23
    assert limiter.get_remaining("alice") == 3


def test_requests_spread_over_a_window_all_count(limiter):
    limiter.request("alice")
    limiter.tick(2)
    limiter.request("alice")
    limiter.tick(2)
    limiter.request("alice")
    assert limiter.get_remaining("alice") == 0
    with pytest.raises(RateLimited):
        limiter.request("alice")


# --- clients --------------------------------------------------------------------


def test_a_new_client_has_its_whole_allowance(limiter):
    assert limiter.get_remaining("alice") == 3
    assert limiter.get_remaining("bob") == 1


def test_clients_are_listed_in_registration_order():
    lim = RateLimiter(window=5)
    for name in ["carol", "alice", "bob"]:
        lim.add_client(name, allowance=2)
    assert lim.get_clients() == ["carol", "alice", "bob"]


def test_an_empty_client_id_is_rejected():
    lim = RateLimiter(window=5)
    with pytest.raises(ValueError):
        lim.add_client("", allowance=2)
    assert lim.get_clients() == []


@pytest.mark.parametrize("allowance", BAD_COUNTS)
def test_invalid_allowances_are_rejected(allowance):
    lim = RateLimiter(window=5)
    with pytest.raises(ValueError):
        lim.add_client("alice", allowance=allowance)
    assert lim.get_clients() == []


def test_registering_a_client_twice_is_rejected(limiter):
    limiter.request("alice")
    with pytest.raises(LimiterError):
        limiter.add_client("alice", allowance=10)
    assert limiter.get_clients() == ["alice", "bob"]
    assert limiter.get_remaining("alice") == 2


def test_a_bad_allowance_is_reported_before_a_duplicate_id(limiter):
    with pytest.raises(ValueError):
        limiter.add_client("alice", allowance=0)
    assert limiter.get_remaining("alice") == 3


@pytest.mark.parametrize(
    "call",
    [
        lambda lim: lim.request("carol"),
        lambda lim: lim.get_remaining("carol"),
        lambda lim: lim.request(None),
        lambda lim: lim.get_remaining(1),
    ],
)
def test_clients_that_are_not_registered_raise_key_error(limiter, call):
    limiter.request("alice")
    before = state(limiter)
    with pytest.raises(KeyError):
        call(limiter)
    assert state(limiter) == before
    assert limiter.request("alice") == 2


# --- requests -------------------------------------------------------------------


def test_remaining_goes_down_with_each_request(limiter):
    limiter.request("alice")
    assert limiter.get_remaining("alice") == 2
    limiter.request("alice")
    assert limiter.get_remaining("alice") == 1
    limiter.request("alice")
    assert limiter.get_remaining("alice") == 0


def test_clients_do_not_share_an_allowance(limiter):
    limiter.request("alice")
    limiter.request("alice")
    assert limiter.get_remaining("bob") == 1
    limiter.request("bob")
    assert limiter.get_remaining("alice") == 1
    with pytest.raises(RateLimited):
        limiter.request("bob")


def test_a_limited_request_changes_nothing(limiter):
    limiter.request("bob")
    limiter.tick(2)
    before = state(limiter)
    with pytest.raises(RateLimited):
        limiter.request("bob")
    assert state(limiter) == before


def test_a_limited_request_does_not_use_a_receipt_number(limiter):
    assert limiter.request("bob") == 1
    with pytest.raises(RateLimited):
        limiter.request("bob")
    assert limiter.request("alice") == 2


def test_receipts_keep_counting_across_windows(limiter):
    assert limiter.request("bob") == 1
    limiter.tick(5)
    assert limiter.request("bob") == 2
    limiter.tick(5)
    assert limiter.request("alice") == 3


def test_a_client_that_is_not_registered_is_reported_before_the_limit(limiter):
    limiter.request("bob")
    with pytest.raises(KeyError):
        limiter.request("carol")


def test_rate_limited_is_a_limiter_error():
    assert issubclass(RateLimited, LimiterError)


def test_limiters_do_not_share_state():
    first, second = RateLimiter(window=5), RateLimiter(window=5)
    first.add_client("alice", allowance=1)
    first.request("alice")
    first.tick(3)
    assert second.get_clients() == []
    assert second.get_time() == 0
    second.add_client("alice", allowance=1)
    assert second.get_remaining("alice") == 1
    assert second.request("alice") == 1
