"""Hidden tests for the c_trades change (trades). Never shown to the writer
or the editor.

Usage (with roster.py importable, e.g. in the sandbox):
    python -m pytest changes/c_trades/private/test_trade_new.py
"""

import pytest
from roster import CapExceeded, Roster, RosterError


@pytest.fixture
def roster():
    r = Roster(100)
    r.add_player("Ada", "PG", 40)
    r.add_player("Bo", "C", 35)
    r.add_player("Cy", "SF", 20)
    return r  # payroll 95


def state(r):
    return [r.get_player(name) for name in r.get_players()], r.get_payroll()


def test_incoming_players_join_at_the_end_in_order(roster):
    roster.trade(["Bo"], [("Dee", "C", 10), ("Eve", "SG", 5)])
    assert roster.get_players() == ["Ada", "Cy", "Dee", "Eve"]
    assert roster.get_player("Eve") == {"name": "Eve", "position": "SG", "salary": 5}
    assert roster.get_payroll() == 75


def test_the_cap_is_judged_after_the_outgoing_players_leave(roster):
    # 95 + 45 is over the cap, but Ada's 40 leaves: 55 + 45 = 100 fits.
    roster.trade(["Ada"], [("Dee", "PG", 45)])
    assert (roster.get_payroll(), roster.get_cap_space()) == (100, 0)


def test_one_side_of_a_trade_may_be_empty(roster):
    roster.trade(["Cy"], [])
    assert roster.get_players() == ["Ada", "Bo"]
    roster.trade([], [("Dee", "SF", 25)])
    assert roster.get_players() == ["Ada", "Bo", "Dee"]
    roster.trade([], [])
    assert roster.get_players() == ["Ada", "Bo", "Dee"]


def test_a_player_may_come_straight_back(roster):
    roster.trade(["Ada"], [("Ada", "SG", 10)])
    assert roster.get_players() == ["Bo", "Cy", "Ada"]
    assert roster.get_player("Ada")["salary"] == 10


def test_an_outgoing_name_not_on_the_roster_raises_key_error(roster):
    before = state(roster)
    with pytest.raises(KeyError):
        roster.trade(["Ada", "Zed"], [("Dee", "C", 5)])
    assert state(roster) == before


def test_an_outgoing_name_listed_twice_is_rejected(roster):
    before = state(roster)
    with pytest.raises(ValueError):
        roster.trade(["Ada", "Ada"], [])
    assert state(roster) == before


@pytest.mark.parametrize("player", [("", "C", 5), ("Dee", "QB", 5), ("Dee", "C", 0)])
def test_invalid_incoming_players_are_rejected(roster, player):
    before = state(roster)
    with pytest.raises(ValueError):
        roster.trade(["Cy"], [player])
    assert state(roster) == before


def test_incoming_names_must_be_new(roster):
    before = state(roster)
    with pytest.raises(RosterError):
        roster.trade(["Cy"], [("Dee", "C", 5), ("Dee", "PG", 5)])
    with pytest.raises(RosterError):
        roster.trade(["Cy"], [("Bo", "PG", 5)])  # Bo stays on the roster
    assert state(roster) == before


def test_a_trade_over_the_cap_changes_nothing(roster):
    before = state(roster)
    with pytest.raises(CapExceeded):
        roster.trade(["Cy"], [("Dee", "C", 26)])
    assert state(roster) == before


def test_problems_are_reported_in_order(roster):
    with pytest.raises(KeyError):
        roster.trade(["Zed", "Zed"], [("", "QB", 0)])
    with pytest.raises(ValueError):
        roster.trade(["Ada", "Ada"], [("Bo", "C", 1000)])
    with pytest.raises(ValueError):
        roster.trade([], [("Bo", "QB", 1000)])
    with pytest.raises(RosterError) as raised:
        roster.trade([], [("Bo", "C", 1000)])
    assert not isinstance(raised.value, CapExceeded)


def test_existing_players_keep_their_details(roster):
    roster.trade(["Bo"], [("Dee", "C", 10)])
    assert roster.get_player("Ada") == {"name": "Ada", "position": "PG", "salary": 40}
    with pytest.raises(KeyError):
        roster.get_player("Bo")
