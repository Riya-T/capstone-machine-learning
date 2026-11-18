"""Hidden tests for the initial relay_teams spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with relay.py importable, e.g. in the sandbox):
    python -m pytest private/test_relay_initial.py
"""

import pytest
from relay import RelayError, RelayMeet


@pytest.fixture
def meet():
    m = RelayMeet()
    for name in ["hawks", "owls", "crows"]:
        m.add_team(name)
    for runner in ["ana", "ben", "cy"]:
        m.add_runner("hawks", runner)
    m.add_runner("owls", "dee")
    m.add_runner("owls", "eli")
    return m


def state(m):
    """Every team in order with its lineup, to check that a failed call
    changed nothing."""
    return [(name, m.get_lineup(name)) for name in m.get_teams()]


# --- teams ----------------------------------------------------------------------


def test_a_new_team_has_an_empty_lineup():
    m = RelayMeet()
    m.add_team("hawks")
    assert m.get_lineup("hawks") == []


def test_teams_are_listed_in_the_order_added():
    m = RelayMeet()
    for name in ["owls", "hawks", "crows"]:
        m.add_team(name)
    assert m.get_teams() == ["owls", "hawks", "crows"]


def test_a_new_meet_has_no_teams():
    assert RelayMeet().get_teams() == []


def test_adding_a_name_in_use_is_rejected(meet):
    before = state(meet)
    with pytest.raises(RelayError):
        meet.add_team("hawks")
    assert state(meet) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda m: m.add_runner("doves", "zed"),
        lambda m: m.move_runner("ana", "doves"),
        lambda m: m.merge_teams("doves", "hawks"),
        lambda m: m.merge_teams("hawks", "doves"),
        lambda m: m.withdraw_team("doves"),
        lambda m: m.get_lineup("doves"),
    ],
)
def test_teams_that_were_never_added_raise_key_error(meet, call):
    before = state(meet)
    with pytest.raises(KeyError):
        call(meet)
    assert state(meet) == before


@pytest.mark.parametrize("how", ["merged", "withdrawn"])
@pytest.mark.parametrize(
    "call",
    [
        lambda m: m.add_runner("crows", "zed"),
        lambda m: m.move_runner("ana", "crows"),
        lambda m: m.merge_teams("crows", "hawks"),
        lambda m: m.merge_teams("hawks", "crows"),
        lambda m: m.withdraw_team("crows"),
        lambda m: m.get_lineup("crows"),
    ],
)
def test_a_merged_or_withdrawn_team_is_not_in_use(meet, call, how):
    if how == "merged":
        meet.merge_teams("crows", "owls")  # crows is empty
    else:
        meet.withdraw_team("crows")
    before = state(meet)
    with pytest.raises(KeyError):
        call(meet)
    assert state(meet) == before


# --- adding and removing runners --------------------------------------------------


def test_add_runner_puts_the_runner_at_the_end(meet):
    meet.add_runner("owls", "fay")
    meet.add_runner("crows", "gus")
    assert meet.get_lineup("owls") == ["dee", "eli", "fay"]
    assert meet.get_lineup("crows") == ["gus"]
    assert meet.get_lineup("hawks") == ["ana", "ben", "cy"]


def test_remove_runner_keeps_the_others_in_order(meet):
    meet.remove_runner("ana")
    assert meet.get_lineup("hawks") == ["ben", "cy"]
    meet.remove_runner("cy")
    assert meet.get_lineup("hawks") == ["ben"]


def test_remove_runner_finds_the_runner_in_any_team(meet):
    meet.remove_runner("eli")
    assert meet.get_lineup("owls") == ["dee"]
    assert meet.get_lineup("hawks") == ["ana", "ben", "cy"]


def test_removing_a_runner_in_no_team_raises_key_error(meet):
    meet.remove_runner("eli")
    before = state(meet)
    with pytest.raises(KeyError):
        meet.remove_runner("eli")
    with pytest.raises(KeyError):
        meet.remove_runner("zed")
    assert state(meet) == before


# --- moving runners -----------------------------------------------------------------


def test_move_runner_appends_to_the_other_team(meet):
    meet.move_runner("ben", "owls")
    assert meet.get_lineup("hawks") == ["ana", "cy"]
    assert meet.get_lineup("owls") == ["dee", "eli", "ben"]
    meet.move_runner("dee", "crows")
    assert meet.get_lineup("crows") == ["dee"]


def test_a_moved_runner_belongs_to_the_new_team(meet):
    meet.move_runner("ana", "crows")
    meet.remove_runner("ana")
    assert meet.get_lineup("crows") == []
    assert meet.get_lineup("hawks") == ["ben", "cy"]


def test_moving_a_runner_to_their_own_team_is_rejected(meet):
    before = state(meet)
    with pytest.raises(ValueError):
        meet.move_runner("ben", "hawks")
    assert state(meet) == before


def test_moving_a_runner_in_no_team_raises_key_error(meet):
    before = state(meet)
    with pytest.raises(KeyError):
        meet.move_runner("zed", "owls")
    assert state(meet) == before


# --- merging and withdrawing ---------------------------------------------------------


def test_merge_teams_appends_the_runners_in_order(meet):
    assert meet.merge_teams("hawks", "owls") == 3
    assert meet.get_lineup("owls") == ["dee", "eli", "ana", "ben", "cy"]
    assert meet.get_teams() == ["owls", "crows"]


def test_merging_into_an_empty_team(meet):
    assert meet.merge_teams("owls", "crows") == 2
    assert meet.get_lineup("crows") == ["dee", "eli"]
    assert meet.get_teams() == ["hawks", "crows"]


def test_merging_an_empty_team_moves_nobody(meet):
    assert meet.merge_teams("crows", "hawks") == 0
    assert meet.get_teams() == ["hawks", "owls"]
    assert meet.get_lineup("hawks") == ["ana", "ben", "cy"]


def test_merged_runners_belong_to_the_team_they_were_merged_into(meet):
    meet.merge_teams("owls", "hawks")
    meet.remove_runner("dee")
    assert meet.get_lineup("hawks") == ["ana", "ben", "cy", "eli"]
    meet.move_runner("eli", "crows")
    assert meet.get_lineup("crows") == ["eli"]


def test_merging_a_team_into_itself_is_rejected(meet):
    before = state(meet)
    with pytest.raises(ValueError):
        meet.merge_teams("hawks", "hawks")
    with pytest.raises(ValueError):
        meet.merge_teams("crows", "crows")
    assert state(meet) == before


def test_withdraw_team_removes_the_team_and_its_runners(meet):
    assert meet.withdraw_team("hawks") == 3
    assert meet.get_teams() == ["owls", "crows"]
    assert meet.get_lineup("owls") == ["dee", "eli"]
    for runner in ["ana", "ben", "cy"]:
        with pytest.raises(KeyError):
            meet.remove_runner(runner)


def test_the_other_teams_still_work_after_a_withdrawal(meet):
    meet.withdraw_team("owls")
    meet.add_runner("crows", "fay")
    meet.move_runner("ana", "crows")
    assert meet.get_lineup("crows") == ["fay", "ana"]
    assert meet.get_lineup("hawks") == ["ben", "cy"]


def test_withdrawing_an_empty_team_removes_nobody(meet):
    assert meet.withdraw_team("crows") == 0
    assert meet.get_teams() == ["hawks", "owls"]


def test_the_other_teams_keep_their_order(meet):
    meet.add_team("doves")
    meet.merge_teams("owls", "doves")
    assert meet.get_teams() == ["hawks", "crows", "doves"]
    meet.withdraw_team("hawks")
    assert meet.get_teams() == ["crows", "doves"]


# --- general ---------------------------------------------------------------------------


def test_meets_do_not_share_teams():
    first, second = RelayMeet(), RelayMeet()
    first.add_team("hawks")
    first.add_runner("hawks", "ana")
    assert second.get_teams() == []
    second.add_team("hawks")
    second.add_runner("hawks", "ana")
    assert second.get_lineup("hawks") == ["ana"]
