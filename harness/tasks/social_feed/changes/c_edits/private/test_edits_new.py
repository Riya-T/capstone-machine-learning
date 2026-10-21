"""Hidden tests for the c_edits change (versioned edits). Never shown to the
writer or the editor.

Usage (with feed.py importable, e.g. in the sandbox):
    python -m pytest changes/c_edits/private/test_edits_new.py
"""

import pytest
from feed import FeedError, SocialFeed, VersionConflict


@pytest.fixture
def feed():
    f = SocialFeed()
    f.add_user("ana")
    f.add_user("ben")
    f.follow("ben", "ana")
    f.post("ana", "first draft")  # id 1
    f.post("ben", "unrelated")  # id 2
    return f


def state(f):
    posts = {p: (f.get_text(p), f.get_version(p), f.get_revisions(p)) for p in (1, 2)}
    return posts, f.get_timeline("ana"), f.get_timeline("ben")


def test_edits_new_posts_start_at_version_one(feed):
    assert feed.get_version(1) == 1
    assert feed.get_revisions(1) == ["first draft"]


def test_edits_keep_id_and_timeline_place(feed):
    feed.post("ana", "later post")
    feed.edit(1, "second draft")
    assert feed.get_timeline("ben") == [1, 2, 3]
    assert feed.get_timeline("ana") == [1, 3]
    assert feed.get_text(1) == "second draft"
    assert feed.post("ana", "new") == 4


def test_edits_each_edit_adds_a_revision_and_a_version(feed):
    feed.edit(1, "second draft")
    feed.edit(1, "third draft", expected_version=2)
    feed.edit(1, "final", expected_version=None)
    assert feed.get_version(1) == 4
    assert feed.get_revisions(1) == ["first draft", "second draft", "third draft", "final"]
    assert feed.get_version(2) == 1


def test_edits_an_edit_to_the_same_text_still_counts(feed):
    feed.edit(1, "first draft")
    assert feed.get_version(1) == 2
    assert feed.get_revisions(1) == ["first draft", "first draft"]


@pytest.mark.parametrize("text", ["", "x" * 281, None, 7])
def test_edits_bad_texts_are_rejected_and_change_nothing(feed, text):
    before = state(feed)
    with pytest.raises(ValueError):
        feed.edit(1, text)
    assert state(feed) == before


def test_edits_texts_of_280_characters_are_allowed(feed):
    feed.edit(1, "y" * 280)
    assert feed.get_text(1) == "y" * 280


@pytest.mark.parametrize("expected", [0, 2, 5])
def test_edits_a_wrong_version_conflicts_and_changes_nothing(feed, expected):
    before = state(feed)
    with pytest.raises(VersionConflict):
        feed.edit(1, "changed", expected_version=expected)
    assert state(feed) == before


@pytest.mark.parametrize("post_id", [0, 3, "1", None])
def test_edits_unknown_posts_raise_key_error(feed, post_id):
    before = state(feed)
    for call in (
        lambda: feed.edit(post_id, "text"),
        lambda: feed.get_version(post_id),
        lambda: feed.get_revisions(post_id),
    ):
        with pytest.raises(KeyError):
            call()
    assert state(feed) == before


def test_edits_error_order(feed):
    with pytest.raises(KeyError):
        feed.edit(9, "", expected_version=7)
    with pytest.raises(ValueError):
        feed.edit(1, "", expected_version=7)


def test_edits_two_editors_one_wins(feed):
    seen = feed.get_version(1)
    feed.edit(1, "from the phone", expected_version=seen)
    with pytest.raises(VersionConflict):
        feed.edit(1, "from the laptop", expected_version=seen)
    assert feed.get_revisions(1) == ["first draft", "from the phone"]


def test_edits_version_conflict_is_a_feed_error():
    assert issubclass(VersionConflict, FeedError)
