"""Hidden tests for the c_position_limits change (position limits). Never
shown to the writer or the editor.

Usage (with roster.py importable, e.g. in the sandbox):
    python -m pytest changes/c_position_limits/private/test_limits_new.py
"""

import pytest
from roster import CapExceeded, Roster, RosterError

BIG_CAP = 10**6  # leaves the cap out of these tests unless a test says otherwise


@pytest.fixture
def roster():
    r = Roster(BIG_CAP, position_limits={"C": 2, "PG": 1})
    r.add_player("Bo", "C", 10)
    r.add_player("Ada", "PG", 10)
    return r


def state(r):
    return [r.get_player(name) for name in r.get_players()], r.get_payroll()


def test_no_limits_by_default():
    r = Roster(BIG_CAP)
    for n in range(4):
        r.add_player(f"C{n}", "C", 10)
    assert len(r.get_players("C")) == 4


def test_a_position_can_be_filled_up_to_its_limit(roster):
    roster.add_player("Dee", "C", 10)
    assert roster.get_players("C") == ["Bo", "Dee"]
    before = state(roster)
    with pytest.raises(RosterError):
        roster.add_player("Eve", "C", 10)
    assert state(roster) == before


def test_removing_a_player_frees_the_place(roster):
    roster.remove_player("Ada")
    roster.add_player("Cy", "PG", 10)
    assert roster.get_players("PG") == ["Cy"]


def test_a_limit_of_zero_closes_a_position():
    r = Roster(BIG_CAP, position_limits={"SF": 0})
    with pytest.raises(RosterError):
        r.add_player("Ada", "SF", 10)
    assert r.get_players() == []


@pytest.mark.parametrize(
    "limits",
    [{"QB": 1}, {"C": -1}, {"C": 1.5}, {"C": True}, {"C": "1"}, [("C", 1)], "C"],
)
def test_invalid_limits_are_rejected(limits):
    with pytest.raises(ValueError):
        Roster(BIG_CAP, position_limits=limits)


def test_a_full_position_is_reported_before_the_cap():
    r = Roster(100, position_limits={"C": 1})
    r.add_player("Bo", "C", 90)
    with pytest.raises(RosterError) as raised:
        r.add_player("Dee", "C", 50)
    assert not isinstance(raised.value, CapExceeded)


def test_earlier_checks_still_come_first(roster):
    with pytest.raises(ValueError):
        roster.add_player("Eve", "PG", -1)  # bad salary before a full position
    with pytest.raises(RosterError):
        roster.add_player("Ada", "PG", 10)  # duplicate name, whether or not PG is full


def test_a_trade_may_swap_players_at_a_full_position(roster):
    roster.trade(["Ada"], [("Cy", "PG", 10)])
    assert roster.get_players("PG") == ["Cy"]


def test_a_trade_that_overfills_a_position_changes_nothing(roster):
    before = state(roster)
    with pytest.raises(RosterError):
        roster.trade([], [("Cy", "PG", 10)])
    with pytest.raises(RosterError):
        roster.trade(["Ada"], [("Dee", "C", 10), ("Eve", "C", 10)])
    assert state(roster) == before


def test_a_trade_overfilling_a_position_is_reported_before_the_cap():
    r = Roster(100, position_limits={"C": 1})
    r.add_player("Bo", "C", 50)
    with pytest.raises(RosterError) as raised:
        r.trade([], [("Dee", "C", 60)])
    assert not isinstance(raised.value, CapExceeded)
