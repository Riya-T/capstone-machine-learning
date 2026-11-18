"""Hidden tests for the c_transfer change (moving several runners at once).
Never shown to the writer or the editor. They call only the spec's methods
and this change's own, never undo.

Usage (with relay.py importable, e.g. in the sandbox):
    python -m pytest changes/c_transfer/private/test_transfer_new.py
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


# --- moves that work ----------------------------------------------------------------


def test_a_single_runner(meet):
    assert meet.move_runners(["ben"], "crows") == 1
    assert meet.get_lineup("crows") == ["ben"]
    assert meet.get_lineup("hawks") == ["ana", "cy"]


def test_runners_are_added_in_list_order_at_the_end(meet):
    assert meet.move_runners(["cy", "ana"], "owls") == 2
    assert meet.get_lineup("owls") == ["dee", "eli", "cy", "ana"]
    assert meet.get_lineup("hawks") == ["ben"]


def test_runners_may_come_from_different_teams(meet):
    assert meet.move_runners(["eli", "ben", "dee"], "crows") == 3
    assert state(meet) == [
        ("hawks", ["ana", "cy"]),
        ("owls", []),
        ("crows", ["eli", "ben", "dee"]),
    ]


def test_a_whole_lineup_can_be_moved(meet):
    meet.move_runners(["ana", "ben", "cy"], "crows")
    assert meet.get_lineup("hawks") == []
    assert meet.get_teams() == ["hawks", "owls", "crows"]
    meet.add_runner("hawks", "fay")
    assert meet.get_lineup("hawks") == ["fay"]


def test_moved_runners_belong_to_the_new_team(meet):
    meet.move_runners(["ana", "dee"], "crows")
    meet.remove_runner("dee")
    assert meet.get_lineup("crows") == ["ana"]
    meet.move_runner("ana", "owls")
    assert meet.get_lineup("owls") == ["eli", "ana"]


def test_the_list_is_not_changed(meet):
    runners = ["ben", "dee"]
    meet.move_runners(runners, "crows")
    assert runners == ["ben", "dee"]


def test_moves_work_with_the_other_methods(meet):
    meet.move_runners(["dee", "eli"], "hawks")
    assert meet.merge_teams("hawks", "crows") == 5
    assert meet.get_lineup("crows") == ["ana", "ben", "cy", "dee", "eli"]
    assert meet.withdraw_team("crows") == 5
    assert meet.get_teams() == ["owls"]


# --- moves that fail change nothing ---------------------------------------------------


def test_an_unknown_runner_at_the_end_moves_nobody(meet):
    before = state(meet)
    with pytest.raises(KeyError):
        meet.move_runners(["ana", "dee", "zed"], "crows")
    assert state(meet) == before


def test_an_unknown_runner_at_the_start_moves_nobody(meet):
    before = state(meet)
    with pytest.raises(KeyError):
        meet.move_runners(["zed", "ana"], "crows")
    assert state(meet) == before


def test_a_removed_runner_in_the_list_moves_nobody(meet):
    meet.remove_runner("eli")
    before = state(meet)
    with pytest.raises(KeyError):
        meet.move_runners(["ben", "eli"], "crows")
    assert state(meet) == before


def test_a_runner_already_in_the_team_moves_nobody(meet):
    before = state(meet)
    with pytest.raises(ValueError):
        meet.move_runners(["dee", "ana"], "hawks")
    with pytest.raises(ValueError):
        meet.move_runners(["ana", "dee", "eli"], "owls")
    assert state(meet) == before


def test_a_team_not_in_use_moves_nobody(meet):
    meet.merge_teams("crows", "owls")
    before = state(meet)
    with pytest.raises(KeyError):
        meet.move_runners(["ana"], "crows")
    with pytest.raises(KeyError):
        meet.move_runners(["ana", "dee"], "doves")
    assert state(meet) == before


def test_a_failed_call_leaves_the_meet_usable(meet):
    with pytest.raises(KeyError):
        meet.move_runners(["ana", "zed"], "crows")
    assert meet.move_runners(["ana"], "crows") == 1
    assert meet.get_lineup("crows") == ["ana"]
    assert meet.get_lineup("hawks") == ["ben", "cy"]
