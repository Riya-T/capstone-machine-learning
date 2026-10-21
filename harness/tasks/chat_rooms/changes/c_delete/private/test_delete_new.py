"""Hidden tests for the c_delete change (deleting messages). Never shown to
the writer or the editor.

Usage (with chat.py importable, e.g. in the sandbox):
    python -m pytest changes/c_delete/private/test_delete_new.py
"""

import pytest
from chat import ChatError, ChatServer


@pytest.fixture
def server():
    srv = ChatServer()
    srv.add_user("alice")
    srv.add_user("bob")
    srv.join("alice", "general")
    srv.join("bob", "general")
    srv.join("alice", "music")
    return srv


def state(srv):
    return {
        r: (srv.get_members(r), srv.get_messages(r), srv.get_message_ids(r))
        for r in srv.get_rooms()
    }


def test_the_first_message_gets_id_one(server):
    assert server.post("alice", "general", "hi") == 1
    assert server.get_message_ids("general") == [1]


def test_ids_are_shared_across_rooms_and_users(server):
    ids = [
        server.post("alice", "general", "a"),
        server.post("bob", "general", "b"),
        server.post("alice", "music", "c"),
        server.post("alice", "general", "d"),
    ]
    assert ids == [1, 2, 3, 4]
    assert server.get_message_ids("general") == [1, 2, 4]
    assert server.get_message_ids("music") == [3]


def test_failed_posts_use_no_id(server):
    with pytest.raises(ValueError):
        server.post("alice", "general", "")
    with pytest.raises(ChatError):
        server.post("bob", "music", "hi")
    assert server.post("alice", "general", "ok") == 1


def test_deleting_keeps_the_order_of_the_rest(server):
    server.post("alice", "general", "a")
    second = server.post("bob", "general", "b")
    server.post("alice", "general", "c")
    server.delete_message(second)
    assert server.get_messages("general") == [("alice", "a"), ("alice", "c")]
    assert server.get_message_ids("general") == [1, 3]


def test_deleting_touches_only_its_own_room(server):
    server.post("alice", "general", "a")
    in_music = server.post("alice", "music", "b")
    server.delete_message(in_music)
    assert server.get_messages("general") == [("alice", "a")]
    assert server.get_messages("music") == []
    assert server.get_message_ids("music") == []


def test_ids_are_not_reused_after_a_deletion(server):
    first = server.post("alice", "general", "a")
    server.delete_message(first)
    assert server.post("alice", "general", "b") == 2
    assert server.get_message_ids("general") == [2]


def test_deleting_twice_is_rejected(server):
    first = server.post("alice", "general", "a")
    server.post("alice", "general", "b")
    server.delete_message(first)
    before = state(server)
    with pytest.raises(ChatError):
        server.delete_message(first)
    assert state(server) == before


@pytest.mark.parametrize("message_id", [0, 5, -1, "1", None, 1.5])
def test_ids_never_given_out_raise_key_error(server, message_id):
    server.post("alice", "general", "a")
    before = state(server)
    with pytest.raises(KeyError):
        server.delete_message(message_id)
    assert state(server) == before


def test_messages_can_be_deleted_after_the_author_leaves(server):
    first = server.post("bob", "general", "bye")
    server.leave("bob", "general")
    server.delete_message(first)
    assert server.get_messages("general") == []


def test_all_messages_of_a_room_can_be_deleted(server):
    ids = [server.post("alice", "general", t) for t in ["a", "b", "c"]]
    for mid in ids:
        server.delete_message(mid)
    assert server.get_messages("general") == []
    assert server.get_message_ids("general") == []
    assert server.get_rooms() == ["general", "music"]


@pytest.mark.parametrize("room", ["nowhere", None, 3])
def test_message_ids_of_unknown_rooms_raise_key_error(server, room):
    with pytest.raises(KeyError):
        server.get_message_ids(room)
