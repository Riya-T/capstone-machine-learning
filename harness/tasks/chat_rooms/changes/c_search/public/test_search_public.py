"""Public checks for the c_search change (searching messages). Shown to the
editor, never to the writer.

Usage (with chat.py importable, e.g. in the sandbox):
    python -m pytest changes/c_search/public/test_search_public.py
"""

from chat import ChatServer


def make_server():
    srv = ChatServer()
    srv.add_user("alice")
    srv.add_user("bob")
    srv.join("alice", "general")
    srv.join("bob", "general")
    srv.join("alice", "music")
    srv.post("alice", "general", "hello all")
    srv.post("bob", "general", "hello alice")
    srv.post("alice", "music", "any jazz fans?")
    srv.post("alice", "general", "bye")
    return srv


def test_filtering_a_room_by_author_and_text():
    srv = make_server()
    assert srv.get_messages("general", by="alice") == [("alice", "hello all"), ("alice", "bye")]
    assert srv.get_messages("general", containing="hello") == [
        ("alice", "hello all"),
        ("bob", "hello alice"),
    ]
    assert srv.get_messages("general", by="bob", containing="hello") == [("bob", "hello alice")]
    assert srv.get_messages("general") == [
        ("alice", "hello all"),
        ("bob", "hello alice"),
        ("alice", "bye"),
    ]


def test_posts_of_one_user_across_rooms():
    srv = make_server()
    assert srv.get_posts("alice") == [
        ("general", "hello all"),
        ("music", "any jazz fans?"),
        ("general", "bye"),
    ]
    assert srv.get_posts("bob") == [("general", "hello alice")]
