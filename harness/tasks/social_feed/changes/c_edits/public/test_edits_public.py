"""Public checks for the c_edits change (versioned edits). Shown to the
editor, never to the writer.

Usage (with feed.py importable, e.g. in the sandbox):
    python -m pytest changes/c_edits/public/test_edits_public.py
"""

import pytest
from feed import SocialFeed, VersionConflict


def test_edits_replace_the_text_and_count_versions():
    f = SocialFeed()
    f.add_user("ana")
    post_id = f.post("ana", "helo")
    assert f.get_version(post_id) == 1
    f.edit(post_id, "hello", expected_version=1)
    assert f.get_text(post_id) == "hello"
    assert f.get_version(post_id) == 2
    assert f.get_revisions(post_id) == ["helo", "hello"]


def test_edits_from_a_stale_version_are_refused():
    f = SocialFeed()
    f.add_user("ana")
    post_id = f.post("ana", "one")
    f.edit(post_id, "two")
    with pytest.raises(VersionConflict):
        f.edit(post_id, "three", expected_version=1)
    assert f.get_text(post_id) == "two"
