"""Hidden tests for the c_limit change (a limit on lineup size). Never shown
to the writer or the editor. They call only the spec's methods and this
change's own, never undo.

Usage (with relay.py importable, e.g. in the sandbox):
    python -m pytest changes/c_limit/private/test_limit_new.py
"""

import pytest
from relay import RelayError, RelayMeet, TeamFull


@pytest.fixture
def meet():
    m = RelayMeet(max_runners=3)
    for name in ["hawks", "owls", "crows"]:
        m.add_team(name)
    for runner in ["ana", "ben", "cy"]:
        m.add_runner("hawks", runner)
    m.add_runner("owls", "dee")
    m.add_runner("owls", "eli")
    return m


def state(m):
    return [(name, m.get_lineup(name)) for name in m.get_teams()]


# --- the limit itself -----------------------------------------------------------------


def test_the_limit_is_kept(meet):
    assert meet.get_max_runners() == 3


def test_the_limit_can_be_given_by_position():
    assert RelayMeet(4).get_max_runners() == 4


def test_without_a_limit_lineups_can_grow_freely():
    m = RelayMeet()
    m.add_team("hawks")
    for i in range(50):
        m.add_runner("hawks", f"runner{i}")
    assert m.get_max_runners() is None
    assert len(m.get_lineup("hawks")) == 50


@pytest.mark.parametrize("limit", [0, -2])
def test_a_limit_of_0_or_less_is_rejected(limit):
    with pytest.raises(ValueError):
        RelayMeet(max_runners=limit)


def test_team_full_is_a_relay_error():
    assert issubclass(TeamFull, RelayError)


# --- adding ---------------------------------------------------------------------------


def test_adding_up_to_the_limit_is_allowed(meet):
    meet.add_runner("owls", "fay")
    assert meet.get_lineup("owls") == ["dee", "eli", "fay"]


def test_adding_past_the_limit_raises_and_changes_nothing(meet):
    before = state(meet)
    with pytest.raises(TeamFull):
        meet.add_runner("hawks", "fay")
    assert state(meet) == before
    meet.add_runner("crows", "fay")
    assert meet.get_lineup("crows") == ["fay"]


def test_the_limit_is_the_same_for_every_team(meet):
    for runner in ["fay", "gus", "hal"]:
        meet.add_runner("crows", runner)
    with pytest.raises(TeamFull):
        meet.add_runner("crows", "ivy")
    assert meet.get_lineup("crows") == ["fay", "gus", "hal"]


def test_removing_a_runner_frees_a_place(meet):
    meet.remove_runner("ben")
    meet.add_runner("hawks", "fay")
    assert meet.get_lineup("hawks") == ["ana", "cy", "fay"]


# --- moving ---------------------------------------------------------------------------


def test_moving_into_a_team_with_room_is_allowed(meet):
    meet.move_runner("ana", "owls")
    assert meet.get_lineup("owls") == ["dee", "eli", "ana"]
    assert meet.get_lineup("hawks") == ["ben", "cy"]


def test_moving_into_a_full_team_raises_and_changes_nothing(meet):
    before = state(meet)
    with pytest.raises(TeamFull):
        meet.move_runner("dee", "hawks")
    assert state(meet) == before


def test_moving_out_of_a_full_team_is_never_limited(meet):
    meet.move_runner("cy", "crows")
    meet.move_runner("dee", "hawks")
    assert meet.get_lineup("hawks") == ["ana", "ben", "dee"]
    assert meet.get_lineup("crows") == ["cy"]


# --- merging and withdrawing ----------------------------------------------------------


def test_merging_up_to_the_limit_is_allowed(meet):
    meet.add_runner("crows", "fay")
    assert meet.merge_teams("crows", "owls") == 1
    assert meet.get_lineup("owls") == ["dee", "eli", "fay"]
    assert meet.get_teams() == ["hawks", "owls"]


def test_merging_past_the_limit_moves_nobody_and_keeps_the_team(meet):
    meet.add_runner("crows", "fay")
    meet.add_runner("crows", "gus")
    before = state(meet)
    with pytest.raises(TeamFull):
        meet.merge_teams("crows", "owls")
    with pytest.raises(TeamFull):
        meet.merge_teams("owls", "hawks")
    with pytest.raises(TeamFull):
        meet.merge_teams("hawks", "crows")
    assert state(meet) == before
    assert meet.get_teams() == ["hawks", "owls", "crows"]


def test_merging_a_full_team_into_an_empty_one_is_allowed(meet):
    assert meet.merge_teams("hawks", "crows") == 3
    assert meet.get_lineup("crows") == ["ana", "ben", "cy"]
    with pytest.raises(TeamFull):
        meet.add_runner("crows", "fay")


def test_withdrawing_is_never_limited(meet):
    assert meet.withdraw_team("hawks") == 3
    meet.add_runner("crows", "fay")
    meet.add_runner("owls", "gus")
    with pytest.raises(TeamFull):
        meet.add_runner("owls", "hal")
    assert meet.get_lineup("owls") == ["dee", "eli", "gus"]
