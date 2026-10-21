"""Hidden tests for the c_activity change (activity log). Never shown to the
writer or the editor.

Usage (with sessions.py importable, e.g. in the sandbox):
    python -m pytest changes/c_activity/private/test_activity_new.py
"""

import pytest
from sessions import SessionError, SessionManager, WrongPassword


@pytest.fixture
def manager():
    man = SessionManager()
    man.register("alice", "hunter2")
    man.register("bob", "secret")
    man.register("carol", "pw")
    return man


def test_new_users_have_no_events(manager):
    assert manager.get_activity("alice") == []
    assert manager.get_activity("alice", kind="sign_in") == []
    assert manager.get_users_by_activity() == ["alice", "bob", "carol"]


def test_each_kind_of_event_is_recorded_in_order(manager):
    manager.sign_in("alice", "hunter2")
    manager.sign_out("alice")
    with pytest.raises(WrongPassword):
        manager.sign_in("alice", "x")
    manager.sign_in("alice", "hunter2")
    assert manager.get_activity("alice") == ["sign_in", "sign_out", "failed_sign_in", "sign_in"]


def test_events_are_kept_per_user(manager):
    manager.sign_in("alice", "hunter2")
    with pytest.raises(WrongPassword):
        manager.sign_in("bob", "x")
    assert manager.get_activity("alice") == ["sign_in"]
    assert manager.get_activity("bob") == ["failed_sign_in"]
    assert manager.get_activity("carol") == []


def test_filtering_by_kind_keeps_only_that_kind(manager):
    for _ in range(2):
        with pytest.raises(WrongPassword):
            manager.sign_in("alice", "x")
    manager.sign_in("alice", "hunter2")
    manager.sign_out("alice")
    manager.sign_in("alice", "hunter2")
    assert manager.get_activity("alice", kind="failed_sign_in") == ["failed_sign_in"] * 2
    assert manager.get_activity("alice", kind="sign_in") == ["sign_in", "sign_in"]
    assert manager.get_activity("alice", kind="sign_out") == ["sign_out"]
    assert manager.get_activity("alice", None) == manager.get_activity("alice")


def test_refused_calls_leave_no_event(manager):
    manager.sign_in("alice", "hunter2")
    for call in (
        lambda: manager.sign_in("alice", "hunter2"),  # already signed in
        lambda: manager.sign_in("alice", "x"),  # already signed in, wrong pw
        lambda: manager.sign_out("bob"),  # not signed in
        lambda: manager.sign_in("dave", "x"),  # unknown
        lambda: manager.register("bob", "again"),
    ):
        with pytest.raises((SessionError, KeyError)):
            call()
    assert manager.get_activity("alice") == ["sign_in"]
    assert manager.get_activity("bob") == []


@pytest.mark.parametrize("username", ["dave", None, 2])
def test_activity_of_unregistered_users_raises_key_error(manager, username):
    with pytest.raises(KeyError):
        manager.get_activity(username)


@pytest.mark.parametrize("kind", ["signin", "", "login", 1, ["sign_in"]])
def test_unknown_kinds_are_rejected(manager, kind):
    with pytest.raises(ValueError):
        manager.get_activity("alice", kind=kind)


def test_unknown_user_is_reported_before_a_bad_kind(manager):
    with pytest.raises(KeyError):
        manager.get_activity("dave", kind="login")


def test_ranking_counts_every_kind_of_event(manager):
    for _ in range(3):
        with pytest.raises(WrongPassword):
            manager.sign_in("carol", "x")
    manager.sign_in("alice", "hunter2")
    manager.sign_out("alice")
    manager.sign_in("bob", "secret")
    assert manager.get_users_by_activity() == ["carol", "alice", "bob"]


def test_ranking_breaks_ties_by_registration_order(manager):
    manager.sign_in("carol", "pw")
    manager.sign_in("alice", "hunter2")
    assert manager.get_users_by_activity() == ["alice", "carol", "bob"]
    manager.sign_in("bob", "secret")
    assert manager.get_users_by_activity() == ["alice", "bob", "carol"]
