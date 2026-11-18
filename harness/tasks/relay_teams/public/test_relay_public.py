"""Public checks for relay.py.

Usage (with relay.py importable, e.g. in the sandbox):
    python -m pytest public/test_relay_public.py
"""

import pytest
from relay import RelayMeet


@pytest.fixture
def meet():
    m = RelayMeet()
    m.add_team("hawks")
    m.add_team("owls")
    return m


def test_runners_are_listed_in_the_order_they_were_added(meet):
    meet.add_runner("hawks", "cy")
    meet.add_runner("hawks", "ana")
    meet.add_runner("hawks", "ben")
    assert meet.get_lineup("hawks") == ["cy", "ana", "ben"]
    assert meet.get_lineup("owls") == []


def test_a_removed_runner_is_taken_out_of_the_lineup(meet):
    for runner in ["ana", "ben", "cy"]:
        meet.add_runner("hawks", runner)
    meet.remove_runner("ben")
    assert meet.get_lineup("hawks") == ["ana", "cy"]


def test_move_runner_puts_the_runner_at_the_end_of_the_other_team(meet):
    meet.add_runner("hawks", "ana")
    meet.add_runner("hawks", "ben")
    meet.add_runner("owls", "cy")
    meet.move_runner("ana", "owls")
    assert meet.get_lineup("hawks") == ["ben"]
    assert meet.get_lineup("owls") == ["cy", "ana"]


def test_merge_teams_moves_the_runners_in_order_and_removes_the_team(meet):
    meet.add_runner("hawks", "ana")
    meet.add_runner("hawks", "ben")
    meet.add_runner("owls", "cy")
    assert meet.merge_teams("hawks", "owls") == 2
    assert meet.get_lineup("owls") == ["cy", "ana", "ben"]
    assert meet.get_teams() == ["owls"]
    with pytest.raises(KeyError):
        meet.get_lineup("hawks")


def test_withdraw_team_removes_the_team_and_its_runners(meet):
    meet.add_runner("hawks", "ana")
    meet.add_runner("hawks", "ben")
    assert meet.withdraw_team("hawks") == 2
    assert meet.get_teams() == ["owls"]
    with pytest.raises(KeyError):
        meet.remove_runner("ana")
