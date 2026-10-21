"""Public checks for the c_mute change (muted users). Shown to the editor,
never to the writer.

Usage (with chat.py importable, e.g. in the sandbox):
    python -m pytest changes/c_mute/public/test_mute_public.py
"""

import pytest
from chat import ChatServer, UserMuted


def test_a_muted_user_cannot_post():
    srv = ChatServer()
    srv.add_user("alice")
    srv.join("alice", "general")
    srv.mute("alice")
    assert srv.is_muted("alice")
    with pytest.raises(UserMuted):
        srv.post("alice", "general", "hello")
    assert srv.get_messages("general") == []


def test_unmuting_lets_the_user_post_again():
    srv = ChatServer()
    srv.add_user("alice")
    srv.join("alice", "general")
    srv.mute("alice")
    srv.unmute("alice")
    assert not srv.is_muted("alice")
    srv.post("alice", "general", "back")
    assert srv.get_messages("general") == [("alice", "back")]
