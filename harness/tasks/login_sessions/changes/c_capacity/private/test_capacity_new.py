"""Hidden tests for the c_capacity change (limit on concurrent sign-ins).
Never shown to the writer or the editor.

Usage (with sessions.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/private/test_capacity_new.py
"""

import pytest
from sessions import SessionError, SessionLimitReached, SessionManager, WrongPassword

BAD_LIMITS = [-1, 1.5, "2", True, [2]]


@pytest.fixture
def manager():
    man = SessionManager(max_signed_in=2)
    for name in ["alice", "bob", "carol"]:
        man.register(name, "pw")
    return man


def state(man):
    return (man.get_users(), man.get_signed_in(), man.get_max_signed_in())


def test_exactly_the_limit_can_be_signed_in(manager):
    manager.sign_in("alice", "pw")
    manager.sign_in("bob", "pw")
    assert manager.get_signed_in() == ["alice", "bob"]
    before = state(manager)
    with pytest.raises(SessionLimitReached):
        manager.sign_in("carol", "pw")
    assert state(manager) == before


def test_signing_out_frees_a_place(manager):
    manager.sign_in("alice", "pw")
    manager.sign_in("bob", "pw")
    manager.sign_out("alice")
    manager.sign_in("carol", "pw")
    assert manager.get_signed_in() == ["bob", "carol"]


def test_a_limit_of_zero_lets_nobody_in():
    man = SessionManager(max_signed_in=0)
    man.register("alice", "pw")
    with pytest.raises(SessionLimitReached):
        man.sign_in("alice", "pw")
    assert not man.is_signed_in("alice")


@pytest.mark.parametrize("limit", BAD_LIMITS)
def test_invalid_limits_are_rejected_by_the_constructor(limit):
    with pytest.raises(ValueError):
        SessionManager(max_signed_in=limit)


@pytest.mark.parametrize("limit", BAD_LIMITS)
def test_invalid_limits_are_rejected_when_set(manager, limit):
    manager.sign_in("alice", "pw")
    before = state(manager)
    with pytest.raises(ValueError):
        manager.set_max_signed_in(limit)
    assert state(manager) == before


def test_set_max_signed_in_replaces_the_limit(manager):
    manager.set_max_signed_in(3)
    assert manager.get_max_signed_in() == 3
    for name in ["alice", "bob", "carol"]:
        manager.sign_in(name, "pw")
    assert manager.get_signed_in() == ["alice", "bob", "carol"]


def test_the_limit_can_be_lowered_to_exactly_the_current_count(manager):
    manager.sign_in("alice", "pw")
    manager.set_max_signed_in(1)
    assert manager.get_max_signed_in() == 1
    with pytest.raises(SessionLimitReached):
        manager.sign_in("bob", "pw")


def test_a_limit_below_the_current_count_is_rejected(manager):
    manager.sign_in("alice", "pw")
    manager.sign_in("bob", "pw")
    before = state(manager)
    with pytest.raises(SessionError):
        manager.set_max_signed_in(1)
    assert state(manager) == before


def test_none_removes_the_limit(manager):
    manager.set_max_signed_in(None)
    assert manager.get_max_signed_in() is None
    for name in ["alice", "bob", "carol"]:
        manager.sign_in(name, "pw")
    assert len(manager.get_signed_in()) == 3


def test_a_bad_limit_is_reported_before_the_count_check(manager):
    manager.sign_in("alice", "pw")
    manager.sign_in("bob", "pw")
    with pytest.raises(ValueError):
        manager.set_max_signed_in(-1)


def test_other_errors_come_before_the_limit(manager):
    manager.sign_in("alice", "pw")
    manager.sign_in("bob", "pw")
    with pytest.raises(KeyError):
        manager.sign_in("dave", "pw")
    with pytest.raises(WrongPassword):
        manager.sign_in("carol", "wrong")
    try:
        manager.sign_in("alice", "pw")
    except SessionLimitReached:
        pytest.fail("already signed in should come before the limit")
    except SessionError:
        pass
    assert manager.get_signed_in() == ["alice", "bob"]


def test_a_refused_sign_in_leaves_earlier_failures_in_place(manager):
    # The limit check comes last and changes nothing, so it must not reset
    # the failed attempts a correct password would normally clear.
    manager.sign_in("alice", "pw")
    manager.sign_in("bob", "pw")
    for _ in range(2):
        with pytest.raises(WrongPassword):
            manager.sign_in("carol", "wrong")
    with pytest.raises(SessionLimitReached):
        manager.sign_in("carol", "pw")
    assert manager.get_failed_attempts("carol") == 2
    with pytest.raises(WrongPassword):
        manager.sign_in("carol", "wrong")
    assert manager.is_locked("carol")


def test_session_limit_reached_is_a_session_error():
    assert issubclass(SessionLimitReached, SessionError)
