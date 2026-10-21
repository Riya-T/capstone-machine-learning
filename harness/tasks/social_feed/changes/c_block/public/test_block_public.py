"""Public checks for the c_block change (blocking users). Shown to the
editor, never to the writer.

Usage (with feed.py importable, e.g. in the sandbox):
    python -m pytest changes/c_block/public/test_block_public.py
"""

import pytest
from feed import Blocked, SocialFeed


def test_block_ends_the_follow_and_refuses_a_new_one():
    f = SocialFeed()
    f.add_user("ana")
    f.add_user("ben")
    f.follow("ben", "ana")
    f.block("ana", "ben")
    assert f.is_blocked("ana", "ben")
    assert f.get_following("ben") == []
    with pytest.raises(Blocked):
        f.follow("ben", "ana")


def test_block_unblocking_allows_following_again():
    f = SocialFeed()
    f.add_user("ana")
    f.add_user("ben")
    f.block("ana", "ben")
    f.unblock("ana", "ben")
    assert not f.is_blocked("ana", "ben")
    f.follow("ben", "ana")
    assert f.get_following("ben") == ["ana"]
