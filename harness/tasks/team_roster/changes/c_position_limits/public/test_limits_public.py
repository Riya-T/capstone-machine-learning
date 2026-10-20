"""Public checks for the c_position_limits change (position limits). Shown
to the editor, never to the writer.

Usage (with roster.py importable, e.g. in the sandbox):
    python -m pytest changes/c_position_limits/public/test_limits_public.py
"""

import pytest
from roster import Roster, RosterError


def test_a_full_position_rejects_another_player():
    roster = Roster(1000, position_limits={"C": 1})
    roster.add_player("Bo", "C", 10)
    with pytest.raises(RosterError):
        roster.add_player("Dee", "C", 10)
    assert roster.get_players() == ["Bo"]


def test_positions_without_a_limit_are_open():
    roster = Roster(1000, position_limits={"C": 1})
    for name in ["Ada", "Cy", "Eve"]:
        roster.add_player(name, "PG", 10)
    assert len(roster.get_players("PG")) == 3
