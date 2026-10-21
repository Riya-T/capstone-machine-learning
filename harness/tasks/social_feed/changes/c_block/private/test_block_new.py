"""Hidden tests for the c_block change (blocking users). Never shown to the
writer or the editor.

Usage (with feed.py importable, e.g. in the sandbox):
    python -m pytest changes/c_block/private/test_block_new.py
"""

import pytest
from feed import Blocked, FeedError, SocialFeed

USERS = ["ana", "ben", "cy"]


@pytest.fixture
def feed():
    f = SocialFeed()
    for name in USERS:
        f.add_user(name)
    f.follow("ana", "ben")
    f.follow("ben", "ana")
    f.follow("cy", "ana")
    f.post("ben", "hi from ben")
    return f


def state(f):
    return {u: (f.get_following(u), f.get_timeline(u), f.get_blocked(u)) for u in USERS}


def test_block_nobody_is_blocked_at_first(feed):
    assert not feed.is_blocked("ana", "ben")
    assert feed.get_blocked("ana") == []


def test_block_is_one_sided_as_a_flag(feed):
    feed.block("ana", "ben")
    assert feed.is_blocked("ana", "ben")
    assert not feed.is_blocked("ben", "ana")
    assert feed.get_blocked("ben") == []


def test_block_ends_follows_in_both_directions(feed):
    feed.block("ana", "ben")
    assert feed.get_following("ana") == []
    assert feed.get_following("ben") == []
    assert feed.get_following("cy") == ["ana"]
    assert feed.get_timeline("ana") == []


@pytest.mark.parametrize(
    "follower, followee", [("ana", "ben"), ("ben", "ana")], ids=["blocker", "blocked"]
)
def test_block_follow_is_refused_both_ways_and_changes_nothing(feed, follower, followee):
    feed.block("ana", "ben")
    before = state(feed)
    with pytest.raises(Blocked):
        feed.follow(follower, followee)
    assert state(feed) == before


def test_block_blocking_twice_or_unblocking_a_stranger_does_nothing(feed):
    feed.block("ana", "cy")
    feed.block("ana", "ben")
    feed.block("ana", "cy")
    assert feed.get_blocked("ana") == ["cy", "ben"]
    feed.unblock("ana", "ben")
    feed.unblock("ana", "ben")
    feed.unblock("ben", "cy")
    assert feed.get_blocked("ana") == ["cy"]
    assert feed.get_blocked("ben") == []


def test_block_unblocking_does_not_restore_follows(feed):
    feed.block("ben", "ana")
    feed.unblock("ben", "ana")
    assert feed.get_following("ana") == []
    assert feed.get_following("ben") == []
    feed.follow("ana", "ben")
    assert feed.get_following("ana") == ["ben"]


def test_block_both_blocks_must_be_lifted(feed):
    feed.block("ana", "ben")
    feed.block("ben", "ana")
    feed.unblock("ana", "ben")
    with pytest.raises(Blocked):
        feed.follow("ana", "ben")
    feed.unblock("ben", "ana")
    feed.follow("ana", "ben")


def test_block_blocking_yourself_is_rejected(feed):
    before = state(feed)
    with pytest.raises(ValueError):
        feed.block("ana", "ana")
    assert state(feed) == before


@pytest.mark.parametrize("method", ["block", "unblock", "is_blocked"])
def test_block_unknown_users_raise_key_error(feed, method):
    before = state(feed)
    with pytest.raises(KeyError):
        getattr(feed, method)("dee", "ana")
    with pytest.raises(KeyError):
        getattr(feed, method)("ana", "dee")
    with pytest.raises(KeyError):
        getattr(feed, method)("dee", "dee")
    assert state(feed) == before
    with pytest.raises(KeyError):
        feed.get_blocked("dee")


def test_block_bad_follows_are_reported_before_blocked(feed):
    feed.block("ana", "ben")
    with pytest.raises(KeyError):
        feed.follow("ben", "dee")
    with pytest.raises(ValueError):
        feed.follow("ben", "ben")


def test_block_blocked_is_a_feed_error():
    assert issubclass(Blocked, FeedError)


def test_block_posts_stay_and_blocked_users_still_post(feed):
    feed.block("ana", "ben")
    new_id = feed.post("ben", "still here")
    assert feed.get_text(1) == "hi from ben"
    assert feed.get_timeline("ben") == [1, new_id]
