"""Hidden tests for the c_mute change (muted users). Never shown to the
writer or the editor.

Usage (with chat.py importable, e.g. in the sandbox):
    python -m pytest changes/c_mute/private/test_mute_new.py
"""

import pytest
from chat import ChatError, ChatServer, UserMuted


@pytest.fixture
def server():
    srv = ChatServer()
    srv.add_user("alice")
    srv.add_user("bob")
    srv.join("alice", "general")
    srv.join("bob", "general")
    srv.join("alice", "music")
    srv.post("alice", "general", "first")
    return srv


def state(srv):
    return {r: (srv.get_members(r), srv.get_messages(r)) for r in srv.get_rooms()}


def test_users_start_unmuted(server):
    assert not server.is_muted("alice")
    assert not server.is_muted("bob")


def test_muting_twice_or_unmuting_twice_is_harmless(server):
    server.mute("alice")
    server.mute("alice")
    assert server.is_muted("alice")
    server.unmute("alice")
    server.unmute("alice")
    assert not server.is_muted("alice")
    assert not server.is_muted("bob")


@pytest.mark.parametrize("method", ["mute", "unmute", "is_muted"])
@pytest.mark.parametrize("username", ["carol", None, 4])
def test_mute_methods_reject_unknown_users(server, method, username):
    with pytest.raises(KeyError):
        getattr(server, method)(username)


def test_a_muted_post_changes_nothing_in_any_room(server):
    server.mute("alice")
    before = state(server)
    with pytest.raises(UserMuted):
        server.post("alice", "general", "hi")
    with pytest.raises(UserMuted):
        server.post("alice", "music", "hi")
    assert state(server) == before


def test_muting_is_per_user(server):
    server.mute("alice")
    server.post("bob", "general", "still here")
    assert server.get_messages("general") == [("alice", "first"), ("bob", "still here")]


def test_earlier_messages_of_a_muted_user_stay(server):
    server.mute("alice")
    assert server.get_messages("general") == [("alice", "first")]


def test_a_muted_user_can_still_join_and_leave(server):
    server.mute("bob")
    server.join("bob", "music")
    assert server.get_members("music") == ["alice", "bob"]
    server.leave("bob", "general")
    assert server.get_members("general") == ["alice"]
    assert server.is_muted("bob")


def test_other_errors_are_reported_before_muted(server):
    server.mute("bob")
    with pytest.raises(KeyError):
        server.post("carol", "general", "hi")
    with pytest.raises(KeyError):
        server.post("bob", "nowhere", "hi")
    with pytest.raises(ValueError):
        server.post("bob", "general", "")
    # bob is not in "music": membership comes before the mute check.
    try:
        server.post("bob", "music", "hi")
    except UserMuted:
        pytest.fail("membership should be checked before muting")
    except ChatError:
        pass
    assert server.get_messages("music") == []


def test_muting_adds_nothing_to_rooms(server):
    before = state(server)
    server.mute("alice")
    server.unmute("alice")
    assert state(server) == before
    assert server.get_rooms() == ["general", "music"]


def test_user_muted_is_a_chat_error():
    assert issubclass(UserMuted, ChatError)
