"""Public checks for the c_capacity change (limit on concurrent sign-ins).
Shown to the editor, never to the writer.

Usage (with sessions.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/public/test_capacity_public.py
"""

import pytest
from sessions import SessionLimitReached, SessionManager


def test_the_limit_refuses_one_sign_in_too_many():
    man = SessionManager(max_signed_in=1)
    man.register("alice", "hunter2")
    man.register("bob", "secret")
    man.sign_in("alice", "hunter2")
    with pytest.raises(SessionLimitReached):
        man.sign_in("bob", "secret")
    assert man.get_signed_in() == ["alice"]
    assert man.get_max_signed_in() == 1


def test_without_a_limit_everyone_can_sign_in():
    man = SessionManager()
    assert man.get_max_signed_in() is None
    for name in ["alice", "bob", "carol"]:
        man.register(name, "pw")
        man.sign_in(name, "pw")
    assert man.get_signed_in() == ["alice", "bob", "carol"]
