"""Public checks for the c_trades change (trades). Shown to the editor,
never to the writer.

Usage (with roster.py importable, e.g. in the sandbox):
    python -m pytest changes/c_trades/public/test_trade_public.py
"""

import pytest
from roster import CapExceeded, Roster


def test_a_one_for_one_trade():
    roster = Roster(100)
    roster.add_player("Ada", "PG", 30)
    roster.trade(["Ada"], [("Bo", "C", 40)])
    assert roster.get_players() == ["Bo"]
    assert roster.get_payroll() == 40


def test_a_player_may_come_straight_back():
    roster = Roster(100)
    roster.add_player("Ada", "PG", 30)
    roster.add_player("Bo", "C", 40)
    roster.trade(["Ada"], [("Ada", "SG", 10)])
    assert roster.get_players() == ["Bo", "Ada"]
    assert roster.get_player("Ada") == {"name": "Ada", "position": "SG", "salary": 10}
    assert roster.get_payroll() == 50


def test_a_trade_over_the_cap_changes_nothing():
    roster = Roster(100)
    roster.add_player("Ada", "PG", 30)
    with pytest.raises(CapExceeded):
        roster.trade(["Ada"], [("Bo", "C", 101)])
    assert roster.get_players() == ["Ada"]
