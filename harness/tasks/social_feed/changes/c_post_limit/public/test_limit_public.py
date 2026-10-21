"""Public checks for the c_post_limit change (adjustable length limit).
Shown to the editor, never to the writer.

Usage (with feed.py importable, e.g. in the sandbox):
    python -m pytest changes/c_post_limit/public/test_limit_public.py
"""

import pytest
from feed import SocialFeed


def test_limit_the_feed_limit_applies_to_everyone():
    f = SocialFeed(max_length=10)
    f.add_user("ana")
    assert f.get_max_length("ana") == 10
    f.post("ana", "x" * 10)
    with pytest.raises(ValueError):
        f.post("ana", "x" * 11)


def test_limit_a_user_can_have_their_own_limit():
    f = SocialFeed()
    f.add_user("ana", max_length=500)
    f.add_user("ben")
    f.post("ana", "x" * 500)
    assert f.get_max_length("ben") == 280
    with pytest.raises(ValueError):
        f.post("ben", "x" * 281)
