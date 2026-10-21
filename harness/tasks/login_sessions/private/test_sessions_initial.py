"""Hidden tests for the initial login_sessions spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with sessions.py importable, e.g. in the sandbox):
    python -m pytest private/test_sessions_initial.py
"""

import pytest
from sessions import SessionError, SessionManager, WrongPassword

BAD_TEXT = ["", None, 7, 1.5, ["alice"]]


@pytest.fixture
def manager():
    man = SessionManager()
    man.register("alice", "hunter2")
    man.register("bob", "secret")
    return man


def state(man):
    """Users and who is signed in, to check that a failed call changed nothing."""
    return (man.get_users(), man.get_signed_in())


# --- users ------------------------------------------------------------------


def test_new_users_are_not_signed_in(manager):
    assert not manager.is_signed_in("alice")
    assert not manager.is_signed_in("bob")
    assert manager.get_signed_in() == []


def test_users_are_listed_in_registration_order():
    man = SessionManager()
    for name in ["carol", "alice", "bob"]:
        man.register(name, "pw")
    assert man.get_users() == ["carol", "alice", "bob"]


@pytest.mark.parametrize("username", BAD_TEXT)
def test_invalid_usernames_are_rejected(username):
    man = SessionManager()
    with pytest.raises(ValueError):
        man.register(username, "pw")
    assert man.get_users() == []


@pytest.mark.parametrize("password", BAD_TEXT)
def test_invalid_passwords_are_rejected(password):
    man = SessionManager()
    with pytest.raises(ValueError):
        man.register("alice", password)
    assert man.get_users() == []


def test_registering_a_taken_name_is_rejected(manager):
    manager.sign_in("alice", "hunter2")
    with pytest.raises(SessionError):
        manager.register("alice", "other")
    assert manager.get_users() == ["alice", "bob"]
    assert manager.is_signed_in("alice")
    manager.sign_out("alice")
    with pytest.raises(WrongPassword):
        manager.sign_in("alice", "other")


def test_a_bad_username_is_reported_before_a_bad_password():
    man = SessionManager()
    with pytest.raises(ValueError):
        man.register("", "")


def test_a_bad_password_is_reported_before_a_taken_name(manager):
    with pytest.raises(ValueError):
        manager.register("alice", "")


@pytest.mark.parametrize(
    "call",
    [
        lambda man: man.sign_in("carol", "pw"),
        lambda man: man.sign_out("carol"),
        lambda man: man.is_signed_in("carol"),
        lambda man: man.sign_in(None, "pw"),
        lambda man: man.is_signed_in(1),
        lambda man: man.sign_out(None),
    ],
)
def test_unregistered_users_raise_key_error(manager, call):
    manager.sign_in("alice", "hunter2")
    before = state(manager)
    with pytest.raises(KeyError):
        call(manager)
    assert state(manager) == before


# --- signing in and out -----------------------------------------------------


def test_sign_in_and_sign_out_change_the_status(manager):
    manager.sign_in("alice", "hunter2")
    manager.sign_in("bob", "secret")
    assert manager.get_signed_in() == ["alice", "bob"]
    manager.sign_out("alice")
    assert not manager.is_signed_in("alice")
    assert manager.is_signed_in("bob")
    assert manager.get_signed_in() == ["bob"]


def test_a_user_can_sign_in_again_after_signing_out(manager):
    manager.sign_in("alice", "hunter2")
    manager.sign_out("alice")
    manager.sign_in("alice", "hunter2")
    assert manager.is_signed_in("alice")


def test_each_user_has_their_own_password(manager):
    with pytest.raises(WrongPassword):
        manager.sign_in("bob", "hunter2")
    manager.sign_in("bob", "secret")
    assert manager.get_signed_in() == ["bob"]


def test_a_wrong_password_changes_nothing(manager):
    manager.sign_in("bob", "secret")
    before = state(manager)
    with pytest.raises(WrongPassword):
        manager.sign_in("alice", "Hunter2")
    assert state(manager) == before


def test_signing_in_twice_is_rejected(manager):
    manager.sign_in("alice", "hunter2")
    before = state(manager)
    with pytest.raises(SessionError):
        manager.sign_in("alice", "hunter2")
    assert state(manager) == before
    manager.sign_out("alice")
    assert not manager.is_signed_in("alice")


def test_already_signed_in_is_reported_before_a_wrong_password(manager):
    manager.sign_in("alice", "hunter2")
    try:
        manager.sign_in("alice", "nope")
    except WrongPassword:
        pytest.fail("already signed in should come before the password check")
    except SessionError:
        pass
    assert manager.is_signed_in("alice")


def test_signing_out_a_user_who_is_not_signed_in_is_rejected(manager):
    manager.sign_in("bob", "secret")
    before = state(manager)
    with pytest.raises(SessionError):
        manager.sign_out("alice")
    assert state(manager) == before
    manager.sign_out("bob")
    with pytest.raises(SessionError):
        manager.sign_out("bob")


def test_signed_in_list_keeps_registration_order_whatever_the_sign_in_order():
    man = SessionManager()
    for name in ["carol", "alice", "bob"]:
        man.register(name, "pw")
    man.sign_in("bob", "pw")
    man.sign_in("carol", "pw")
    assert man.get_signed_in() == ["carol", "bob"]
    man.sign_in("alice", "pw")
    assert man.get_signed_in() == ["carol", "alice", "bob"]


def test_wrong_password_is_a_session_error():
    assert issubclass(WrongPassword, SessionError)


def test_managers_do_not_share_users():
    first, second = SessionManager(), SessionManager()
    first.register("alice", "pw")
    first.sign_in("alice", "pw")
    assert second.get_users() == []
    second.register("alice", "other")
    assert not second.is_signed_in("alice")
    assert first.is_signed_in("alice")
