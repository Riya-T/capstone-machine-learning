"""Public checks for the c_capacity change (rack capacity). Shown to the
editor, never to the writer.

Usage (with cellar.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/public/test_capacity_public.py
"""

import pytest
from cellar import Cellar, RackFull


@pytest.fixture
def cellar():
    c = Cellar()
    c.add_rack("north")
    c.add_rack("south")
    return c


def test_a_rack_holds_at_most_its_capacity(cellar):
    assert cellar.get_capacity("north") is None
    cellar.set_capacity("north", 10)
    assert cellar.get_capacity("north") == 10
    cellar.store("north", 2015, 6)
    cellar.store("north", 2018, 4)
    with pytest.raises(RackFull):
        cellar.store("north", 2015, 1)
    assert cellar.get_count("north", 2015) == 6


def test_relocate_all_into_a_full_rack_moves_nothing(cellar):
    cellar.store("north", 2015, 5)
    cellar.set_capacity("south", 4)
    with pytest.raises(RackFull):
        cellar.relocate_all("north", "south")
    assert cellar.get_count("north", 2015) == 5
    assert cellar.get_count("south", 2015) == 0
