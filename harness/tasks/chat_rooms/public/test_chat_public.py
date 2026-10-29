"""Public checks for chat.py.

Usage (with chat.py importable, e.g. in the sandbox):
    python -m pytest public/test_chat_public.py
"""

import pytest
from chat import ChatError, ChatServer


@pytest.fixture
def server():
    srv = ChatServer()
    srv.add_user("alice")
    srv.add_user("bob")
    return srv


def test_joining_creates_the_room_and_adds_the_member(server):
    server.join("alice", "general")
    server.join("bob", "general")
    assert server.get_rooms() == ["general"]
    assert server.get_members("general") == ["alice", "bob"]
    assert server.get_messages("general") == []


def test_posting_then_reading(server):
    server.join("alice", "general")
    server.post("alice", "general", "hello")
    server.post("alice", "general", "anyone here?")
    assert server.get_messages("general") == [("alice", "hello"), ("alice", "anyone here?")]


def test_non_members_cannot_post(server):
    server.join("alice", "general")
    with pytest.raises(ChatError):
        server.post("bob", "general", "hi")
    assert server.get_messages("general") == []


def test_unknown_room_raises_key_error(server):
    with pytest.raises(KeyError):
        server.get_members("nowhere")
    with pytest.raises(KeyError):
        server.get_messages("nowhere")


def test_rooms_are_listed_in_creation_order(server):
    server.join("alice", "music")
    server.join("bob", "general")
    server.join("alice", "general")
    assert server.get_rooms() == ["music", "general"]
    server.leave("alice", "music")
    assert server.get_members("music") == []
    assert server.get_rooms() == ["music", "general"]
