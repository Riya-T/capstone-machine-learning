"""Public checks for the c_mentions change (finding mentions). Shown to the
editor, never to the writer.

Usage (with feed.py importable, e.g. in the sandbox):
    python -m pytest changes/c_mentions/public/test_mentions_public.py
"""

from feed import SocialFeed


def test_mentions_are_found_by_whole_word():
    f = SocialFeed()
    f.add_user("ana")
    f.add_user("ben")
    f.post("ben", "lunch with @ana today")
    f.post("ben", "@ana!")
    f.post("ana", "thanks @ben")
    assert f.get_mentions("ana") == [1]
    assert f.get_mentioned(3) == ["ben"]


def test_mentions_can_be_filtered_by_author():
    f = SocialFeed()
    for name in ["ana", "ben", "cy"]:
        f.add_user(name)
    f.post("ben", "hey @ana")
    f.post("cy", "@ana hello")
    assert f.get_mentions("ana", author="cy") == [2]
