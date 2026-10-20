"""Hidden tests for the c_injuries change (injured list). Never shown to the
writer or the editor.

Usage (with roster.py importable, e.g. in the sandbox):
    python -m pytest changes/c_injuries/private/test_injury_new.py
"""

import pytest
from roster import CapExceeded, Roster


@pytest.fixture
def roster():
    r = Roster(100)
    r.add_player("Ada", "PG", 50)
    r.add_player("Bo", "C", 30)
    return r


def state(r):
    injured = [name for name in r.get_players() if r.is_injured(name)]
    return (
        [r.get_player(name) for name in r.get_players()],
        injured,
        r.get_payroll(),
        r.get_cap_hit(),
    )


def test_nobody_starts_injured(roster):
    assert not roster.is_injured("Ada")
    assert roster.get_cap_hit() == roster.get_payroll() == 80


def test_listing_or_activating_twice_is_harmless(roster):
    roster.place_on_injured_list("Ada")
    roster.place_on_injured_list("Ada")
    assert roster.is_injured("Ada")
    roster.activate("Ada")
    roster.activate("Ada")
    assert not roster.is_injured("Ada")


@pytest.mark.parametrize("method", ["place_on_injured_list", "activate", "is_injured"])
def test_names_not_on_the_roster_raise_key_error(roster, method):
    with pytest.raises(KeyError):
        getattr(roster, method)("Zed")


def test_injured_players_still_count_in_the_payroll(roster):
    roster.place_on_injured_list("Ada")
    assert (roster.get_payroll(), roster.get_cap_hit(), roster.get_cap_space()) == (80, 30, 70)


def test_an_injury_frees_cap_room_for_a_new_player(roster):
    roster.place_on_injured_list("Ada")
    roster.add_player("Cy", "PG", 70)
    assert (roster.get_payroll(), roster.get_cap_hit()) == (150, 100)
    with pytest.raises(CapExceeded):
        roster.add_player("Dee", "SF", 1)


def test_activating_over_the_cap_is_refused(roster):
    roster.place_on_injured_list("Ada")
    roster.add_player("Cy", "PG", 30)  # cap hit 60; Ada's 50 would make it 110
    before = state(roster)
    with pytest.raises(CapExceeded):
        roster.activate("Ada")
    assert state(roster) == before
    assert roster.is_injured("Ada")


def test_activating_within_the_cap_works(roster):
    roster.place_on_injured_list("Ada")
    roster.add_player("Cy", "PG", 20)
    roster.activate("Ada")
    assert roster.get_cap_hit() == 100


def test_injured_players_are_still_on_the_roster(roster):
    roster.place_on_injured_list("Bo")
    assert roster.get_players() == ["Ada", "Bo"]
    assert roster.get_players("C") == ["Bo"]
    assert roster.get_player("Bo")["salary"] == 30


def test_removing_an_injured_player(roster):
    roster.place_on_injured_list("Bo")
    roster.remove_player("Bo")
    assert (roster.get_payroll(), roster.get_cap_hit()) == (50, 50)
    roster.add_player("Bo", "C", 30)
    assert not roster.is_injured("Bo")
    assert roster.get_cap_hit() == 80
