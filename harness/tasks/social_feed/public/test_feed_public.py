"""Public checks for feed.py.

Usage (with feed.py importable, e.g. in the sandbox):
    python -m pytest public/test_feed_public.py
"""

import pytest
from feed import FeedError, SocialFeed


@pytest.fixture
def feed():
    f = SocialFeed()
    f.add_user("ana")
    f.add_user("ben")
    return f


def test_posts_get_ids_counting_up(feed):
    assert feed.post("ana", "first") == 1
    assert feed.post("ben", "second") == 2
    assert feed.get_text(1) == "first"


def test_timeline_has_own_and_followed_posts(feed):
    feed.post("ben", "from ben")
    feed.post("ana", "from ana")
    feed.follow("ana", "ben")
    assert feed.get_timeline("ana") == [1, 2]
    assert feed.get_timeline("ben") == [1]


def test_unfollow_removes_posts_from_the_timeline(feed):
    feed.post("ben", "from ben")
    feed.follow("ana", "ben")
    assert feed.get_following("ana") == ["ben"]
    feed.unfollow("ana", "ben")
    assert feed.get_following("ana") == []
    assert feed.get_timeline("ana") == []


def test_texts_must_have_1_to_280_characters(feed):
    feed.post("ana", "x" * 280)
    with pytest.raises(ValueError):
        feed.post("ana", "")
    with pytest.raises(ValueError):
        feed.post("ana", "x" * 281)


def test_following_twice_raises(feed):
    feed.follow("ana", "ben")
    with pytest.raises(FeedError):
        feed.follow("ana", "ben")


def test_an_unknown_user_raises_key_error(feed):
    with pytest.raises(KeyError):
        feed.get_timeline("cy")
