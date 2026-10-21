"""Public checks for the c_activity change (activity log). Shown to the
editor, never to the writer.

Usage (with sessions.py importable, e.g. in the sandbox):
    python -m pytest changes/c_activity/public/test_activity_public.py
"""

import pytest
from sessions import SessionManager, WrongPassword


def test_events_are_recorded_oldest_first():
    man = SessionManager()
    man.register("alice", "hunter2")
    with pytest.raises(WrongPassword):
        man.sign_in("alice", "nope")
    man.sign_in("alice", "hunter2")
    man.sign_out("alice")
    assert man.get_activity("alice") == ["failed_sign_in", "sign_in", "sign_out"]
    assert man.get_activity("alice", kind="sign_in") == ["sign_in"]


def test_users_are_ranked_by_number_of_events():
    man = SessionManager()
    man.register("alice", "pw")
    man.register("bob", "pw")
    man.sign_in("bob", "pw")
    man.sign_out("bob")
    man.sign_in("alice", "pw")
    assert man.get_users_by_activity() == ["bob", "alice"]
