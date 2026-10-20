"""Hidden tests for the initial team_roster spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with roster.py importable, e.g. in the sandbox):
    python -m pytest private/test_roster_initial.py
"""

import pytest
from roster import POSITIONS, CapExceeded, Roster, RosterError


@pytest.fixture
def roster():
    r = Roster(100)
    r.add_player("Ada", "PG", 30)
    r.add_player("Bo", "C", 25)
    r.add_player("Cy", "PG", 20)
    return r


def state(r):
    return [r.get_player(name) for name in r.get_players()], r.get_payroll()


def test_positions_constant():
    assert tuple(POSITIONS) == ("PG", "SG", "SF", "PF", "C")


def test_a_new_roster_is_empty():
    r = Roster(500)
    assert (r.get_players(), r.get_payroll(), r.get_cap_space()) == ([], 0, 500)


@pytest.mark.parametrize("cap", [0, -1, 1.5, "100", None])
def test_invalid_caps_are_rejected(cap):
    with pytest.raises(ValueError):
        Roster(cap)


# --- adding players ---------------------------------------------------------


def test_players_are_listed_in_the_order_added(roster):
    assert roster.get_players() == ["Ada", "Bo", "Cy"]
    assert roster.get_players("PG") == ["Ada", "Cy"]
    assert roster.get_players("SF") == []


def test_a_player_added_again_moves_to_the_end(roster):
    roster.remove_player("Ada")
    roster.add_player("Ada", "SF", 5)
    assert roster.get_players() == ["Bo", "Cy", "Ada"]
    assert roster.get_player("Ada")["position"] == "SF"


@pytest.mark.parametrize("name", [""])
def test_invalid_names_are_rejected(roster, name):
    before = state(roster)
    with pytest.raises(ValueError):
        roster.add_player(name, "PG", 10)
    assert state(roster) == before


@pytest.mark.parametrize("position", ["QB", "pg", "", None])
def test_invalid_positions_are_rejected(roster, position):
    before = state(roster)
    with pytest.raises(ValueError):
        roster.add_player("Dee", position, 10)
    assert state(roster) == before


@pytest.mark.parametrize("salary", [0, -1, 1.5, "10", None])
def test_invalid_salaries_are_rejected(roster, salary):
    before = state(roster)
    with pytest.raises(ValueError):
        roster.add_player("Dee", "SF", salary)
    assert state(roster) == before


def test_a_name_cannot_be_on_the_roster_twice(roster):
    before = state(roster)
    with pytest.raises(RosterError):
        roster.add_player("Ada", "SF", 5)
    assert state(roster) == before


def test_the_payroll_may_reach_the_cap_exactly(roster):
    roster.add_player("Dee", "SF", 25)
    assert (roster.get_payroll(), roster.get_cap_space()) == (100, 0)


def test_going_over_the_cap_changes_nothing(roster):
    before = state(roster)
    with pytest.raises(CapExceeded):
        roster.add_player("Dee", "SF", 26)
    assert state(roster) == before


def test_problems_are_reported_in_order(roster):
    roster.add_player("Dee", "SF", 25)  # the payroll is now at the cap
    with pytest.raises(ValueError):
        roster.add_player("Ada", "QB", 10)  # bad position before the duplicate
    with pytest.raises(ValueError):
        roster.add_player("Eve", "SF", -1)  # bad salary before the cap
    with pytest.raises(RosterError) as raised:
        roster.add_player("Ada", "SF", 1000)  # duplicate before the cap
    assert not isinstance(raised.value, CapExceeded)


def test_cap_exceeded_is_a_roster_error():
    assert issubclass(CapExceeded, RosterError)


# --- reading and removing ---------------------------------------------------


@pytest.mark.parametrize("name", ["Zed", None, 1])
def test_names_not_on_the_roster_raise_key_error(roster, name):
    before = state(roster)
    with pytest.raises(KeyError):
        roster.get_player(name)
    with pytest.raises(KeyError):
        roster.remove_player(name)
    assert state(roster) == before


def test_removing_a_player(roster):
    roster.remove_player("Bo")
    assert roster.get_players() == ["Ada", "Cy"]
    assert (roster.get_payroll(), roster.get_cap_space()) == (50, 50)


@pytest.mark.parametrize("position", ["QB", "pg", ""])
def test_filtering_by_an_unknown_position_is_rejected(roster, position):
    with pytest.raises(ValueError):
        roster.get_players(position)


def test_rosters_do_not_share_players():
    first, second = Roster(100), Roster(100)
    first.add_player("Ada", "PG", 90)
    assert second.get_players() == []
    second.add_player("Ada", "C", 90)
    assert first.get_player("Ada")["position"] == "PG"
