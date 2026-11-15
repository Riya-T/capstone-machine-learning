"""Public checks for the c_seal change (sealed tanks). Shown to the editor,
never to the writer.

Usage (with depot.py importable, e.g. in the sandbox):
    python -m pytest changes/c_seal/public/test_seal_public.py
"""

import pytest
from depot import Depot, Sealed


def test_a_sealed_tank_cannot_be_filled():
    dep = Depot()
    dep.add_tank("north")
    dep.seal("north")
    with pytest.raises(Sealed):
        dep.fill("north", 10)
    assert dep.get_level("north") == 0
    dep.unseal("north")
    dep.fill("north", 10)
    assert dep.get_level("north") == 10


def test_pumping_out_of_a_sealed_tank_is_refused():
    dep = Depot()
    dep.add_tank("north")
    dep.add_tank("south")
    dep.fill("north", 100)
    dep.seal("north")
    with pytest.raises(Sealed):
        dep.pump("north", "south", 40)
    assert (dep.get_level("north"), dep.get_level("south")) == (100, 0)
    assert dep.get_log("south") == []
