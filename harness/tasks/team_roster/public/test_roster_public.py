"""Public checks for roster.py.

Usage (with roster.py importable, e.g. in the sandbox):
    python -m pytest public/test_roster_public.py
"""

import pytest
from roster import CapExceeded, Roster


def test_adding_players_uses_cap_space():
    roster = Roster(100)
    roster.add_player("Ada", "PG", 30)
    roster.add_player("Bo", "C", 25)
    assert roster.get_payroll() == 55
    assert roster.get_cap_space() == 45


def test_player_returns_the_details():
    roster = Roster(100)
    roster.add_player("Ada", "PG", 30)
    assert roster.get_player("Ada") == {"name": "Ada", "position": "PG", "salary": 30}


def test_going_over_the_cap_raises():
    roster = Roster(100)
    roster.add_player("Ada", "PG", 80)
    with pytest.raises(CapExceeded):
        roster.add_player("Bo", "C", 21)
    assert sorted(roster.get_players()) == ["Ada"]


def test_players_can_be_filtered_by_position():
    roster = Roster(100)
    roster.add_player("Ada", "PG", 10)
    roster.add_player("Bo", "C", 10)
    roster.add_player("Cy", "PG", 10)
    assert sorted(roster.get_players("PG")) == ["Ada", "Cy"]


def test_unknown_positions_are_rejected():
    roster = Roster(100)
    with pytest.raises(ValueError):
        roster.add_player("Ada", "QB", 10)


def test_removing_a_player_frees_cap_space():
    roster = Roster(100)
    roster.add_player("Ada", "PG", 30)
    roster.remove_player("Ada")
    assert roster.get_cap_space() == 100
    with pytest.raises(KeyError):
        roster.get_player("Ada")
