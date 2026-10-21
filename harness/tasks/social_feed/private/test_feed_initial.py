"""Hidden tests for the initial social_feed spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with feed.py importable, e.g. in the sandbox):
    python -m pytest private/test_feed_initial.py
"""

import pytest
from feed import FeedError, SocialFeed

USERS = ["ana", "ben", "cy"]
BAD_TEXTS = ["", "x" * 281, None, 5, ["hi"]]


@pytest.fixture
def feed():
    f = SocialFeed()
    for name in USERS:
        f.add_user(name)
    return f


def state(f, posts=()):
    """Every following list, timeline and the given texts, to check that a
    failed call changed nothing."""
    users = {u: (f.get_following(u), f.get_timeline(u)) for u in USERS}
    return users, [f.get_text(p) for p in posts]


# --- users ------------------------------------------------------------------


def test_a_new_user_follows_nobody_and_sees_nothing(feed):
    assert feed.get_following("ana") == []
    assert feed.get_timeline("ana") == []


@pytest.mark.parametrize("bad_name", [""])
def test_invalid_user_names_are_rejected(bad_name):
    f = SocialFeed()
    with pytest.raises(ValueError):
        f.add_user(bad_name)
    with pytest.raises(KeyError):
        f.get_timeline(bad_name)


def test_adding_a_user_twice_is_rejected(feed):
    feed.post("ana", "hello")
    feed.follow("ana", "ben")
    before = state(feed, [1])
    with pytest.raises(FeedError):
        feed.add_user("ana")
    assert state(feed, [1]) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda f: f.post("dee", "hi"),
        lambda f: f.follow("dee", "ana"),
        lambda f: f.follow("ana", "dee"),
        lambda f: f.unfollow("dee", "ana"),
        lambda f: f.unfollow("ana", "dee"),
        lambda f: f.get_following("dee"),
        lambda f: f.get_timeline("dee"),
        lambda f: f.get_timeline(None),
        lambda f: f.post(1, "hi"),
    ],
)
def test_users_that_were_not_added_raise_key_error(feed, call):
    feed.post("ana", "hello")
    before = state(feed, [1])
    with pytest.raises(KeyError):
        call(feed)
    assert state(feed, [1]) == before


# --- posts ------------------------------------------------------------------


def test_ids_count_up_over_all_users(feed):
    assert [feed.post(u, "hi " + u) for u in ["cy", "ana", "cy", "ben"]] == [1, 2, 3, 4]
    assert [feed.get_text(i) for i in [1, 2, 3, 4]] == ["hi cy", "hi ana", "hi cy", "hi ben"]


def test_texts_at_the_edges_of_the_length_rule(feed):
    long_id = feed.post("ana", "y" * 280)
    short_id = feed.post("ana", "y")
    assert feed.get_text(long_id) == "y" * 280
    assert feed.get_text(short_id) == "y"


@pytest.mark.parametrize("text", BAD_TEXTS)
def test_invalid_texts_are_rejected_and_change_nothing(feed, text):
    feed.post("ana", "kept")
    before = state(feed, [1])
    with pytest.raises(ValueError):
        feed.post("ana", text)
    assert state(feed, [1]) == before


def test_a_failed_post_does_not_use_up_an_id(feed):
    feed.post("ana", "one")
    with pytest.raises(ValueError):
        feed.post("ana", "")
    with pytest.raises(KeyError):
        feed.post("dee", "lost")
    assert feed.post("ben", "two") == 2


def test_an_unknown_author_is_reported_before_a_bad_text(feed):
    with pytest.raises(KeyError):
        feed.post("dee", "")
    with pytest.raises(KeyError):
        feed.post(None, None)


@pytest.mark.parametrize("post_id", [0, 2, -1, "1", None])
def test_unknown_post_ids_raise_key_error(feed, post_id):
    feed.post("ana", "only one")
    with pytest.raises(KeyError):
        feed.get_text(post_id)


def test_feeds_do_not_share_users_or_ids():
    first, second = SocialFeed(), SocialFeed()
    first.add_user("ana")
    first.post("ana", "hi")
    with pytest.raises(KeyError):
        second.get_timeline("ana")
    second.add_user("ana")
    assert second.post("ana", "hi again") == 1


# --- following --------------------------------------------------------------


def test_following_is_listed_in_follow_order(feed):
    feed.follow("ana", "cy")
    feed.follow("ana", "ben")
    assert feed.get_following("ana") == ["cy", "ben"]
    assert feed.get_following("cy") == []


def test_following_again_moves_to_the_end(feed):
    feed.follow("ana", "ben")
    feed.follow("ana", "cy")
    feed.unfollow("ana", "ben")
    feed.follow("ana", "ben")
    assert feed.get_following("ana") == ["cy", "ben"]


def test_following_yourself_is_rejected(feed):
    before = state(feed)
    with pytest.raises(ValueError):
        feed.follow("ana", "ana")
    assert state(feed) == before


def test_following_someone_twice_changes_nothing(feed):
    feed.follow("ana", "ben")
    before = state(feed)
    with pytest.raises(FeedError):
        feed.follow("ana", "ben")
    assert state(feed) == before


def test_unfollowing_someone_not_followed_is_rejected(feed):
    feed.follow("ben", "ana")  # the other direction does not count
    before = state(feed)
    with pytest.raises(FeedError):
        feed.unfollow("ana", "ben")
    with pytest.raises(FeedError):
        feed.unfollow("ana", "ana")
    assert state(feed) == before


def test_follow_errors_come_in_order(feed):
    with pytest.raises(KeyError):
        feed.follow("dee", "dee")
    feed.follow("ana", "ben")
    with pytest.raises(KeyError):
        feed.follow("ana", "dee")
    with pytest.raises(KeyError):
        feed.unfollow("dee", "dee")


def test_feed_error_is_not_a_key_or_value_error():
    assert not issubclass(FeedError, (KeyError, ValueError))


# --- timeline ---------------------------------------------------------------


def test_timeline_mixes_authors_oldest_first(feed):
    feed.follow("ana", "ben")
    feed.follow("ana", "cy")
    ids = [feed.post(u, "post by " + u) for u in ["cy", "ana", "ben", "cy", "ana"]]
    assert feed.get_timeline("ana") == ids
    assert feed.get_timeline("cy") == [1, 4]


def test_timeline_includes_posts_from_before_the_follow(feed):
    feed.post("ben", "early")
    feed.post("ana", "mine")
    feed.follow("ana", "ben")
    assert feed.get_timeline("ana") == [1, 2]


def test_following_is_one_way_and_not_passed_on(feed):
    feed.follow("ana", "ben")
    feed.follow("ben", "cy")
    feed.post("ana", "from ana")
    feed.post("cy", "from cy")
    assert feed.get_timeline("ben") == [2]  # ana's post is not in it: no follow back
    assert feed.get_timeline("ana") == [1]  # cy's post is not in it: ben's follow is his


def test_unfollow_takes_posts_out_of_the_timeline(feed):
    feed.follow("ana", "ben")
    feed.follow("ana", "cy")
    feed.post("ben", "b")
    feed.post("cy", "c")
    feed.unfollow("ana", "ben")
    assert feed.get_timeline("ana") == [2]
    feed.follow("ana", "ben")
    assert feed.get_timeline("ana") == [1, 2]
