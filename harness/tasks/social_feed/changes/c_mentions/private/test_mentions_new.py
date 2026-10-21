"""Hidden tests for the c_mentions change (finding mentions). Never shown to
the writer or the editor.

Usage (with feed.py importable, e.g. in the sandbox):
    python -m pytest changes/c_mentions/private/test_mentions_new.py
"""

import pytest
from feed import SocialFeed


@pytest.fixture
def feed():
    f = SocialFeed()
    for name in ["ana", "ben", "cy"]:
        f.add_user(name)
    return f


@pytest.mark.parametrize(
    "text, mentions_ana",
    [
        ("@ana", True),
        ("hi @ana", True),
        ("@ana\tand\n@ben", True),
        ("hi @ana!", False),
        ("@Ana", False),
        ("@an", False),
        ("@anabel", False),
        ("mail@ana", False),
        ("ana", False),
        ("@ ana", False),
    ],
)
def test_mentions_only_whole_words_count(feed, text, mentions_ana):
    post_id = feed.post("ben", text)
    assert feed.get_mentions("ana") == ([post_id] if mentions_ana else [])


def test_mentions_are_listed_oldest_first_and_once(feed):
    feed.post("ben", "@ana @ana @ana")
    feed.post("cy", "nothing here")
    feed.post("cy", "cc @ana")
    feed.post("ana", "note to self @ana")
    assert feed.get_mentions("ana") == [1, 3, 4]


def test_mentions_do_not_depend_on_follows(feed):
    feed.follow("ana", "ben")
    feed.post("cy", "@ana you do not follow me")
    assert feed.get_mentions("ana") == [1]
    assert feed.get_timeline("ana") == []


def test_mentions_a_user_who_joins_later_is_found(feed):
    feed.post("ben", "waiting for @dee to join")
    with pytest.raises(KeyError):
        feed.get_mentions("dee")
    assert feed.get_mentioned(1) == []
    feed.add_user("dee")
    assert feed.get_mentions("dee") == [1]
    assert feed.get_mentioned(1) == ["dee"]


def test_mentions_posts_by_blocked_users_are_left_out(feed):
    feed.post("ben", "@ana one")
    feed.post("cy", "@ana two")
    feed.block("ana", "ben")
    assert feed.get_mentions("ana") == [2]
    feed.unblock("ana", "ben")
    assert feed.get_mentions("ana") == [1, 2]


def test_mentions_being_blocked_does_not_hide_mentions(feed):
    feed.post("ana", "@ben hello")
    feed.block("ana", "ben")  # ana blocked ben; ben did not block ana
    assert feed.get_mentions("ben") == [1]
    assert feed.get_mentions("ben", author="ana") == [1]


def test_mentions_author_filter(feed):
    feed.post("ben", "@cy a")
    feed.post("ana", "@cy b")
    feed.post("ben", "@cy c")
    assert feed.get_mentions("cy", author="ben") == [1, 3]
    assert feed.get_mentions("cy", author="cy") == []
    assert feed.get_mentions("cy", author=None) == [1, 2, 3]
    feed.block("cy", "ben")
    assert feed.get_mentions("cy", author="ben") == []


def test_mentions_get_mentioned_keeps_first_mention_order(feed):
    post_id = feed.post("ana", "@cy @nobody @ben @cy @ana")
    assert feed.get_mentioned(post_id) == ["cy", "ben", "ana"]
    assert feed.get_mentioned(feed.post("ana", "no names")) == []


def test_mentions_unknown_names_and_ids_raise_key_error(feed):
    feed.post("ana", "@ben")
    for call in (
        lambda: feed.get_mentions("dee"),
        lambda: feed.get_mentions(None),
        lambda: feed.get_mentions("ben", author="dee"),
        lambda: feed.get_mentioned(2),
        lambda: feed.get_mentioned(0),
        lambda: feed.get_mentioned("1"),
    ):
        with pytest.raises(KeyError):
            call()


def test_mentions_work_with_long_posts_under_a_custom_limit():
    f = SocialFeed(max_length=1000)
    f.add_user("ana")
    f.add_user("ben")
    f.post("ben", "x " * 400 + "@ana")
    assert f.get_mentions("ana") == [1]
