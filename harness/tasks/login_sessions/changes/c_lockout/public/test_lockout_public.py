"""Public checks for the c_lockout change (account lockout). Shown to the
editor, never to the writer.

Usage (with sessions.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lockout/public/test_lockout_public.py
"""

import pytest
from sessions import AccountLocked, SessionManager, WrongPassword


def test_three_wrong_passwords_lock_the_account():
    man = SessionManager()
    man.register("alice", "hunter2")
    for _ in range(3):
        with pytest.raises(WrongPassword):
            man.sign_in("alice", "nope")
    assert man.is_locked("alice")
    assert man.get_failed_attempts("alice") == 3
    with pytest.raises(AccountLocked):
        man.sign_in("alice", "hunter2")
    assert not man.is_signed_in("alice")


def test_unlocking_lets_the_user_back_in():
    man = SessionManager()
    man.register("alice", "hunter2")
    for _ in range(3):
        with pytest.raises(WrongPassword):
            man.sign_in("alice", "nope")
    man.unlock("alice")
    assert not man.is_locked("alice")
    assert man.get_failed_attempts("alice") == 0
    man.sign_in("alice", "hunter2")
    assert man.is_signed_in("alice")
