"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor. They call only the spec's methods and undo, since they run in
both sequences.

Usage (with relay.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
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
    return [(name, m.get_lineup(name)) for name in m.get_teams()]


# --- each call can be undone ----------------------------------------------------


def test_undo_of_add_runner(meet):
    before = state(meet)
    meet.add_runner("crows", "fay")
    meet.undo()
    assert state(meet) == before
    meet.add_runner("hawks", "fay")
    assert meet.get_lineup("hawks") == ["ana", "ben", "cy", "fay"]


def test_undo_of_remove_runner_puts_the_runner_back_in_place(meet):
    before = state(meet)
    meet.remove_runner("ben")
    meet.undo()
    assert state(meet) == before
    assert meet.get_lineup("hawks") == ["ana", "ben", "cy"]


def test_a_runner_put_back_by_undo_is_in_the_team_again(meet):
    meet.remove_runner("ana")
    meet.undo()
    meet.move_runner("ana", "crows")
    assert meet.get_lineup("crows") == ["ana"]
    assert meet.get_lineup("hawks") == ["ben", "cy"]


def test_undo_of_move_runner_puts_the_runner_back_at_the_old_position(meet):
    before = state(meet)
    meet.move_runner("ana", "owls")
    assert meet.get_lineup("owls") == ["dee", "eli", "ana"]
    meet.undo()
    assert state(meet) == before
    assert meet.get_lineup("hawks") == ["ana", "ben", "cy"]


def test_one_undo_takes_back_a_whole_merge(meet):
    before = state(meet)
    assert meet.merge_teams("hawks", "owls") == 3
    meet.undo()
    assert state(meet) == before
    assert meet.get_teams() == ["hawks", "owls", "crows"]
    assert meet.get_lineup("owls") == ["dee", "eli"]


def test_undo_of_a_merge_puts_the_team_back_at_its_place(meet):
    meet.add_team("doves")
    before = state(meet)
    meet.merge_teams("owls", "doves")
    assert meet.get_teams() == ["hawks", "crows", "doves"]
    meet.undo()
    assert meet.get_teams() == ["hawks", "owls", "crows", "doves"]
    assert state(meet) == before


def test_a_team_brought_back_from_a_merge_is_in_use_again(meet):
    meet.merge_teams("hawks", "crows")
    meet.undo()
    meet.add_runner("hawks", "fay")
    assert meet.get_lineup("hawks") == ["ana", "ben", "cy", "fay"]
    assert meet.get_lineup("crows") == []
    with pytest.raises(RelayError):
        meet.add_team("hawks")
    assert meet.merge_teams("hawks", "owls") == 4
    assert meet.get_teams() == ["owls", "crows"]


def test_one_undo_takes_back_a_whole_withdrawal(meet):
    before = state(meet)
    assert meet.withdraw_team("hawks") == 3
    meet.undo()
    assert state(meet) == before
    assert meet.get_teams() == ["hawks", "owls", "crows"]


def test_withdrawn_runners_brought_back_are_in_the_team_again(meet):
    meet.withdraw_team("owls")
    meet.undo()
    with pytest.raises(RelayError):
        meet.add_team("owls")
    meet.move_runner("eli", "crows")
    assert meet.get_lineup("owls") == ["dee"]
    assert meet.get_lineup("crows") == ["eli"]


def test_runners_added_after_a_withdrawal_are_undone_before_it(meet):
    meet.withdraw_team("owls")
    meet.add_runner("crows", "fay")
    meet.undo()
    assert meet.get_lineup("crows") == []
    meet.undo()
    assert meet.get_lineup("owls") == ["dee", "eli"]
    assert meet.get_teams() == ["hawks", "owls", "crows"]


def test_undo_of_add_team_removes_it_and_frees_the_name(meet):
    meet.add_team("doves")
    meet.undo()
    assert meet.get_teams() == ["hawks", "owls", "crows"]
    with pytest.raises(KeyError):
        meet.get_lineup("doves")
    meet.add_team("doves")
    assert meet.get_teams() == ["hawks", "owls", "crows", "doves"]
    assert meet.get_lineup("doves") == []


def test_undoing_a_merge_and_a_withdrawal_in_a_row(meet):
    before = state(meet)
    meet.merge_teams("hawks", "crows")
    meet.withdraw_team("crows")
    assert state(meet) == [("owls", ["dee", "eli"])]
    meet.undo()
    assert state(meet) == [("owls", ["dee", "eli"]), ("crows", ["ana", "ben", "cy"])]
    meet.undo()
    assert state(meet) == before


# --- calls on empty teams --------------------------------------------------------


def test_merging_or_withdrawing_an_empty_team_can_be_undone(meet):
    meet.add_runner("owls", "fay")
    assert meet.merge_teams("crows", "owls") == 0
    meet.undo()
    assert meet.get_teams() == ["hawks", "owls", "crows"]
    assert meet.withdraw_team("crows") == 0
    meet.undo()
    assert meet.get_teams() == ["hawks", "owls", "crows"]
    meet.undo()
    assert meet.get_lineup("owls") == ["dee", "eli"]


# --- what is and is not recorded --------------------------------------------------


def test_each_undo_goes_one_call_further_back():
    m = RelayMeet()
    calls = [
        lambda: m.add_team("hawks"),
        lambda: m.add_team("owls"),
        lambda: m.add_runner("hawks", "ana"),
        lambda: m.add_runner("hawks", "ben"),
        lambda: m.add_runner("owls", "cy"),
        lambda: m.add_team("crows"),
        lambda: m.add_runner("hawks", "dee"),
        lambda: m.move_runner("ana", "owls"),
        lambda: m.remove_runner("ben"),
        lambda: m.add_runner("crows", "fay"),
        lambda: m.merge_teams("hawks", "owls"),
        lambda: m.add_team("doves"),
        lambda: m.move_runner("cy", "doves"),
        lambda: m.withdraw_team("crows"),
        lambda: m.merge_teams("doves", "owls"),
    ]
    states = [state(m)]
    for call in calls:
        call()
        states.append(state(m))
    assert state(m) == [("owls", ["ana", "dee", "cy"])]
    for expected in reversed(states[:-1]):
        m.undo()
        assert state(m) == expected
    with pytest.raises(RelayError):
        m.undo()
    assert m.get_teams() == []


def test_failed_calls_are_not_recorded(meet):
    meet.add_runner("crows", "fay")
    for call in (
        lambda: meet.add_team("hawks"),
        lambda: meet.add_runner("doves", "zed"),
        lambda: meet.remove_runner("zed"),
        lambda: meet.move_runner("ana", "hawks"),
        lambda: meet.move_runner("zed", "owls"),
        lambda: meet.merge_teams("hawks", "hawks"),
        lambda: meet.merge_teams("doves", "hawks"),
        lambda: meet.withdraw_team("doves"),
    ):
        with pytest.raises((ValueError, KeyError, RelayError)):
            call()
    meet.undo()  # fay joining the crows
    assert meet.get_lineup("crows") == []
    assert meet.get_lineup("hawks") == ["ana", "ben", "cy"]


def test_get_calls_are_not_recorded(meet):
    meet.add_runner("crows", "fay")
    meet.get_lineup("crows")
    meet.get_teams()
    meet.undo()
    assert meet.get_lineup("crows") == []
    assert meet.get_lineup("owls") == ["dee", "eli"]


def test_there_is_no_redo():
    m = RelayMeet()
    m.add_team("hawks")
    m.add_runner("hawks", "ana")
    m.undo()
    m.undo()
    assert m.get_teams() == []
    with pytest.raises(RelayError):
        m.undo()


def test_new_calls_after_an_undo_are_undone_first(meet):
    meet.add_runner("crows", "fay")
    meet.undo()
    meet.add_runner("crows", "gus")
    meet.undo()
    assert meet.get_lineup("crows") == []
    meet.undo()  # eli joining the owls in the fixture
    assert meet.get_lineup("owls") == ["dee"]
    assert meet.get_lineup("hawks") == ["ana", "ben", "cy"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    m = RelayMeet()
    with pytest.raises(RelayError):
        m.undo()
    m.add_team("hawks")
    m.undo()
    with pytest.raises(RelayError):
        m.undo()
    assert m.get_teams() == []
    m.add_team("hawks")
    m.add_runner("hawks", "ana")
    assert m.get_lineup("hawks") == ["ana"]


def test_the_whole_fixture_can_be_undone(meet):
    for _ in range(8):
        meet.undo()
    assert meet.get_teams() == []
    with pytest.raises(RelayError):
        meet.undo()
