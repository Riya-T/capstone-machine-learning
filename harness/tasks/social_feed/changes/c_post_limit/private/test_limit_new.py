"""Hidden tests for the c_post_limit change (adjustable length limit). Never
shown to the writer or the editor.

Usage (with feed.py importable, e.g. in the sandbox):
    python -m pytest changes/c_post_limit/private/test_limit_new.py
"""

import pytest
from feed import FeedError, SocialFeed

BAD_LIMITS = [0, -1, True, 1.5, "280"]


@pytest.fixture
def feed():
    f = SocialFeed(max_length=20)
    f.add_user("ana")
    f.add_user("ben", max_length=5)
    return f


def test_limit_the_default_is_280():
    f = SocialFeed()
    f.add_user("ana")
    assert f.get_max_length("ana") == 280
    f.post("ana", "x" * 280)
    with pytest.raises(ValueError):
        f.post("ana", "x" * 281)


def test_limit_feed_and_user_limits_side_by_side(feed):
    assert (feed.get_max_length("ana"), feed.get_max_length("ben")) == (20, 5)
    feed.post("ana", "x" * 20)
    feed.post("ben", "x" * 5)
    for author, text in [("ana", "x" * 21), ("ben", "x" * 6)]:
        with pytest.raises(ValueError):
            feed.post(author, text)
    assert feed.get_timeline("ana") == [1]
    assert feed.get_timeline("ben") == [2]
    assert feed.post("ana", "next") == 3


@pytest.mark.parametrize("limit", BAD_LIMITS + [None])
def test_limit_invalid_feed_limits_are_rejected(limit):
    with pytest.raises(ValueError):
        SocialFeed(max_length=limit)


@pytest.mark.parametrize("limit", BAD_LIMITS)
def test_limit_invalid_user_limits_add_no_user(feed, limit):
    with pytest.raises(ValueError):
        feed.add_user("cy", max_length=limit)
    with pytest.raises(KeyError):
        feed.get_max_length("cy")
    feed.add_user("cy")
    assert feed.get_max_length("cy") == 20


def test_limit_a_bad_limit_is_reported_before_a_taken_name(feed):
    with pytest.raises(ValueError):
        feed.add_user("ana", max_length=0)
    with pytest.raises(FeedError):
        feed.add_user("ana", max_length=50)
    assert feed.get_max_length("ana") == 20


def test_limit_set_max_length_replaces_and_none_restores(feed):
    feed.set_max_length("ana", 3)
    assert feed.get_max_length("ana") == 3
    with pytest.raises(ValueError):
        feed.post("ana", "four")
    feed.set_max_length("ben", 100)
    feed.post("ben", "x" * 100)
    feed.set_max_length("ben", None)
    assert feed.get_max_length("ben") == 20
    feed.set_max_length("ana", None)
    feed.post("ana", "x" * 20)


@pytest.mark.parametrize("limit", BAD_LIMITS)
def test_limit_set_max_length_rejects_bad_limits(feed, limit):
    with pytest.raises(ValueError):
        feed.set_max_length("ben", limit)
    assert feed.get_max_length("ben") == 5


def test_limit_unknown_users_raise_key_error_first(feed):
    with pytest.raises(KeyError):
        feed.get_max_length("cy")
    with pytest.raises(KeyError):
        feed.set_max_length("cy", 0)
    with pytest.raises(KeyError):
        feed.set_max_length(None, 10)


def test_limit_existing_posts_survive_a_lower_limit(feed):
    first = feed.post("ana", "x" * 20)
    feed.set_max_length("ana", 2)
    assert feed.get_text(first) == "x" * 20
    assert feed.get_timeline("ana") == [first]


def test_limit_feeds_keep_their_own_limits():
    small, large = SocialFeed(max_length=4), SocialFeed(max_length=400)
    small.add_user("ana")
    large.add_user("ana")
    large.post("ana", "x" * 400)
    assert small.get_max_length("ana") == 4
    with pytest.raises(ValueError):
        small.post("ana", "x" * 5)
