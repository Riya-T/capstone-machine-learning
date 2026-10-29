"""Hidden tests for the initial chat_rooms spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with chat.py importable, e.g. in the sandbox):
    python -m pytest private/test_chat_initial.py
"""

import pytest
from chat import ChatError, ChatServer

BAD_TEXT = ["", None, 7, 1.5, ["x"]]


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
    """Every room's members and messages, to check that a failed call changed nothing."""
    return {r: (srv.get_members(r), srv.get_messages(r)) for r in srv.get_rooms()}


# --- users ------------------------------------------------------------------


@pytest.mark.parametrize("username", BAD_TEXT)
def test_invalid_usernames_are_rejected(username):
    srv = ChatServer()
    with pytest.raises(ValueError):
        srv.add_user(username)


def test_adding_a_user_twice_is_rejected(server):
    before = state(server)
    with pytest.raises(ChatError):
        server.add_user("alice")
    assert state(server) == before
    assert server.get_members("general") == ["alice", "bob"]


@pytest.mark.parametrize(
    "call",
    [
        lambda srv: srv.join("carol", "general"),
        lambda srv: srv.leave("carol", "general"),
        lambda srv: srv.post("carol", "general", "hi"),
        lambda srv: srv.join(None, "general"),
        lambda srv: srv.post(1, "general", "hi"),
    ],
)
def test_unknown_users_raise_key_error(server, call):
    before = state(server)
    with pytest.raises(KeyError):
        call(server)
    assert state(server) == before


# --- rooms ------------------------------------------------------------------


def test_a_new_room_has_one_member_and_no_messages(server):
    server.join("bob", "games")
    assert server.get_rooms() == ["general", "music", "games"]
    assert server.get_members("games") == ["bob"]
    assert server.get_messages("games") == []


@pytest.mark.parametrize("room", BAD_TEXT)
def test_invalid_room_names_are_rejected(server, room):
    before = state(server)
    with pytest.raises(ValueError):
        server.join("alice", room)
    assert state(server) == before


def test_joining_the_same_room_twice_is_rejected(server):
    before = state(server)
    with pytest.raises(ChatError):
        server.join("alice", "general")
    assert state(server) == before


def test_members_are_listed_in_join_order(server):
    server.join("bob", "music")
    assert server.get_members("music") == ["alice", "bob"]
    server.leave("alice", "music")
    server.join("alice", "music")
    assert server.get_members("music") == ["bob", "alice"]


def test_leaving_removes_only_that_membership(server):
    server.leave("alice", "general")
    assert server.get_members("general") == ["bob"]
    assert server.get_members("music") == ["alice"]


def test_an_empty_room_still_exists_with_its_messages(server):
    server.post("alice", "music", "la la")
    server.leave("alice", "music")
    assert server.get_members("music") == []
    assert server.get_rooms() == ["general", "music"]
    assert server.get_messages("music") == [("alice", "la la")]


def test_leaving_a_room_one_is_not_in_is_rejected(server):
    before = state(server)
    with pytest.raises(ChatError):
        server.leave("bob", "music")
    assert state(server) == before
    server.leave("alice", "music")
    with pytest.raises(ChatError):
        server.leave("alice", "music")


@pytest.mark.parametrize(
    "call",
    [
        lambda srv: srv.leave("alice", "nowhere"),
        lambda srv: srv.post("alice", "nowhere", "hi"),
        lambda srv: srv.get_members("nowhere"),
        lambda srv: srv.get_messages("nowhere"),
        lambda srv: srv.get_members(None),
        lambda srv: srv.get_messages(3),
    ],
)
def test_unknown_rooms_raise_key_error(server, call):
    before = state(server)
    with pytest.raises(KeyError):
        call(server)
    assert state(server) == before
    assert server.get_rooms() == ["general", "music"]


def test_an_unknown_user_is_reported_before_an_unknown_room(server):
    with pytest.raises(KeyError):
        server.leave("carol", "nowhere")
    with pytest.raises(KeyError):
        server.post("carol", "nowhere", "hi")


def test_a_bad_room_name_is_reported_before_the_membership_check(server):
    # alice is a member of "general"; an empty name is still a ValueError.
    with pytest.raises(ValueError):
        server.join("alice", "")


# --- messages ---------------------------------------------------------------


def test_messages_are_listed_oldest_first_per_room(server):
    server.post("alice", "general", "one")
    server.post("bob", "general", "two")
    server.post("alice", "music", "three")
    server.post("alice", "general", "four")
    assert server.get_messages("general") == [("alice", "one"), ("bob", "two"), ("alice", "four")]
    assert server.get_messages("music") == [("alice", "three")]


def test_messages_stay_after_the_author_leaves(server):
    server.post("bob", "general", "bye")
    server.leave("bob", "general")
    assert server.get_messages("general") == [("bob", "bye")]


@pytest.mark.parametrize("text", BAD_TEXT)
def test_invalid_texts_are_rejected(server, text):
    before = state(server)
    with pytest.raises(ValueError):
        server.post("alice", "general", text)
    assert state(server) == before


def test_posting_without_membership_is_rejected(server):
    before = state(server)
    with pytest.raises(ChatError):
        server.post("bob", "music", "hi")
    assert state(server) == before
    server.leave("alice", "music")
    with pytest.raises(ChatError):
        server.post("alice", "music", "hi")


def test_a_bad_text_is_reported_before_the_membership_check(server):
    with pytest.raises(ValueError):
        server.post("bob", "music", "")


def test_servers_do_not_share_state():
    first, second = ChatServer(), ChatServer()
    first.add_user("alice")
    first.join("alice", "general")
    assert second.get_rooms() == []
    with pytest.raises(KeyError):
        second.join("alice", "general")
