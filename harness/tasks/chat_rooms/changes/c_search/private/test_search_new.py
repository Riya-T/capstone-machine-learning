"""Hidden tests for the c_search change (searching messages). Never shown to
the writer or the editor.

Usage (with chat.py importable, e.g. in the sandbox):
    python -m pytest changes/c_search/private/test_search_new.py
"""

import pytest
from chat import ChatServer


@pytest.fixture
def server():
    srv = ChatServer()
    for name in ["alice", "bob", "carol"]:
        srv.add_user(name)
    srv.join("alice", "general")
    srv.join("bob", "general")
    srv.join("alice", "music")
    srv.join("bob", "music")
    srv.post("alice", "general", "Hello everyone")
    srv.post("bob", "music", "hello from music")
    srv.post("bob", "general", "hello back")
    srv.post("alice", "music", "Any news?")
    srv.post("alice", "general", "no news")
    return srv


def test_no_filters_returns_everything_in_order(server):
    assert server.get_messages("general") == [
        ("alice", "Hello everyone"),
        ("bob", "hello back"),
        ("alice", "no news"),
    ]
    assert server.get_messages("general", by=None, containing=None) == server.get_messages("general")


def test_filter_by_author_keeps_order(server):
    assert server.get_messages("general", by="alice") == [
        ("alice", "Hello everyone"),
        ("alice", "no news"),
    ]
    assert server.get_messages("music", by="bob") == [("bob", "hello from music")]


def test_filter_by_author_with_no_posts_is_empty(server):
    assert server.get_messages("general", by="carol") == []
    server.join("carol", "general")
    assert server.get_messages("general", by="carol") == []


def test_filter_by_substring_is_case_sensitive(server):
    assert server.get_messages("general", containing="hello") == [("bob", "hello back")]
    assert server.get_messages("general", containing="Hello") == [("alice", "Hello everyone")]
    assert server.get_messages("general", containing="news") == [("alice", "no news")]
    assert server.get_messages("general", containing="zzz") == []


def test_an_empty_substring_matches_every_message(server):
    assert server.get_messages("music", containing="") == server.get_messages("music")


def test_both_filters_combine(server):
    assert server.get_messages("general", by="alice", containing="n") == [
        ("alice", "Hello everyone"),
        ("alice", "no news"),
    ]
    assert server.get_messages("general", by="bob", containing="news") == []


@pytest.mark.parametrize("by", ["dave", 1, ""])
def test_an_unknown_author_filter_raises_key_error(server, by):
    with pytest.raises(KeyError):
        server.get_messages("general", by=by)


@pytest.mark.parametrize("containing", [1, 2.5, ["x"], b"x"])
def test_a_non_string_substring_raises_value_error(server, containing):
    with pytest.raises(ValueError):
        server.get_messages("general", containing=containing)


def test_search_error_order(server):
    with pytest.raises(KeyError):
        server.get_messages("nowhere", by="dave", containing=1)
    with pytest.raises(KeyError):
        server.get_messages("general", by="dave", containing=1)


def test_posts_are_ordered_across_rooms(server):
    assert server.get_posts("alice") == [
        ("general", "Hello everyone"),
        ("music", "Any news?"),
        ("general", "no news"),
    ]
    assert server.get_posts("bob") == [("music", "hello from music"), ("general", "hello back")]
    assert server.get_posts("carol") == []


def test_posts_grow_with_new_messages_and_ignore_failed_ones(server):
    with pytest.raises(ValueError):
        server.post("alice", "general", "")
    server.post("alice", "general", "later")
    assert server.get_posts("alice")[-1] == ("general", "later")
    assert len(server.get_posts("alice")) == 4


@pytest.mark.parametrize("username", ["dave", None, 2])
def test_posts_of_unknown_users_raise_key_error(server, username):
    with pytest.raises(KeyError):
        server.get_posts(username)
