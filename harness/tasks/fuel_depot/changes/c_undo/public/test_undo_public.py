"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with depot.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from depot import Depot, DepotError


def test_undo_reverses_the_last_fill():
    dep = Depot()
    dep.add_tank("north")
    dep.fill("north", 100)
    dep.fill("north", 20)
    dep.undo()
    assert dep.get_level("north") == 100
    assert dep.get_log("north") == [("fill", 100)]


def test_undo_reverses_a_pump_on_both_tanks():
    dep = Depot()
    dep.add_tank("north")
    dep.add_tank("south")
    dep.fill("north", 100)
    dep.pump("north", "south", 30)
    dep.undo()
    assert (dep.get_level("north"), dep.get_level("south")) == (100, 0)
    assert dep.get_log("north") == [("fill", 100)]
    assert dep.get_log("south") == []


def test_undo_with_nothing_to_undo_raises():
    dep = Depot()
    with pytest.raises(DepotError):
        dep.undo()
