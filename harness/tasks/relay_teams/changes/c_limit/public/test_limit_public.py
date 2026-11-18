"""Public checks for the c_limit change (a limit on lineup size). Shown to the
editor, never to the writer.

Usage (with relay.py importable, e.g. in the sandbox):
    python -m pytest changes/c_limit/public/test_limit_public.py
"""

import pytest
from relay import RelayMeet, TeamFull


@pytest.fixture
def meet():
    m = RelayMeet(max_runners=2)
    m.add_team("hawks")
    m.add_team("owls")
    return m


def test_a_lineup_can_be_filled_up_to_the_limit(meet):
    meet.add_runner("hawks", "ana")
    meet.add_runner("hawks", "ben")
    assert meet.get_lineup("hawks") == ["ana", "ben"]
    assert meet.get_max_runners() == 2
    assert RelayMeet().get_max_runners() is None


def test_adding_past_the_limit_raises(meet):
    meet.add_runner("hawks", "ana")
    meet.add_runner("hawks", "ben")
    with pytest.raises(TeamFull):
        meet.add_runner("hawks", "cy")
    assert meet.get_lineup("hawks") == ["ana", "ben"]


def test_merging_past_the_limit_raises(meet):
    meet.add_runner("hawks", "ana")
    meet.add_runner("hawks", "ben")
    meet.add_runner("owls", "cy")
    with pytest.raises(TeamFull):
        meet.merge_teams("owls", "hawks")
    assert meet.get_teams() == ["hawks", "owls"]
    assert meet.get_lineup("owls") == ["cy"]
