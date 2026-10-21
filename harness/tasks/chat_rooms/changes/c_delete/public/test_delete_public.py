"""Public checks for the c_delete change (deleting messages). Shown to the
editor, never to the writer.

Usage (with chat.py importable, e.g. in the sandbox):
    python -m pytest changes/c_delete/public/test_delete_public.py
"""

import pytest
from chat import ChatError, ChatServer


def test_post_returns_ids_that_count_up():
    srv = ChatServer()
    srv.add_user("alice")
    srv.join("alice", "general")
    srv.join("alice", "music")
    assert srv.post("alice", "general", "one") == 1
    assert srv.post("alice", "music", "two") == 2
    assert srv.post("alice", "general", "three") == 3
    assert srv.get_message_ids("general") == [1, 3]


def test_deleting_removes_the_message_once():
    srv = ChatServer()
    srv.add_user("alice")
    srv.join("alice", "general")
    first = srv.post("alice", "general", "one")
    srv.post("alice", "general", "two")
    srv.delete_message(first)
    assert srv.get_messages("general") == [("alice", "two")]
    assert srv.get_message_ids("general") == [2]
    with pytest.raises(ChatError):
        srv.delete_message(first)
