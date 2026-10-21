"""Public checks for sessions.py.

Usage (with sessions.py importable, e.g. in the sandbox):
    python -m pytest public/test_sessions_public.py
"""

import pytest
from sessions import SessionManager, WrongPassword


@pytest.fixture
def manager():
    man = SessionManager()
    man.register("alice", "hunter2")
    man.register("bob", "secret")
    return man


def test_signing_in_then_checking(manager):
    manager.sign_in("alice", "hunter2")
    assert manager.is_signed_in("alice")
    assert not manager.is_signed_in("bob")


def test_signing_out_again(manager):
    manager.sign_in("alice", "hunter2")
    manager.sign_out("alice")
    assert not manager.is_signed_in("alice")


def test_wrong_password_is_refused(manager):
    with pytest.raises(WrongPassword):
        manager.sign_in("alice", "secret")
    assert not manager.is_signed_in("alice")


def test_signed_in_users_are_listed_in_registration_order(manager):
    manager.sign_in("bob", "secret")
    manager.sign_in("alice", "hunter2")
    assert manager.get_signed_in() == ["alice", "bob"]
    assert manager.get_users() == ["alice", "bob"]


def test_unknown_user_raises_key_error(manager):
    with pytest.raises(KeyError):
        manager.sign_in("carol", "x")
    with pytest.raises(KeyError):
        manager.is_signed_in("carol")
