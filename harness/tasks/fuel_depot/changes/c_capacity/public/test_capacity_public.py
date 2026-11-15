"""Public checks for the c_capacity change (tank capacities). Shown to the
editor, never to the writer.

Usage (with depot.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/public/test_capacity_public.py
"""

import pytest
from depot import Depot, Overflow


def test_filling_up_to_the_capacity_and_past_it():
    dep = Depot()
    dep.add_tank("north")
    assert dep.get_capacity("north") is None
    dep.set_capacity("north", 100)
    assert dep.get_capacity("north") == 100
    dep.fill("north", 100)
    with pytest.raises(Overflow):
        dep.fill("north", 1)
    assert dep.get_level("north") == 100
    assert dep.get_log("north") == [("fill", 100)]


def test_pumping_into_a_full_tank_raises():
    dep = Depot()
    dep.add_tank("north")
    dep.add_tank("south")
    dep.fill("north", 50)
    dep.set_capacity("south", 30)
    with pytest.raises(Overflow):
        dep.pump("north", "south", 31)
    assert (dep.get_level("north"), dep.get_level("south")) == (50, 0)
    dep.pump("north", "south", 30)
    assert (dep.get_level("north"), dep.get_level("south")) == (20, 30)
