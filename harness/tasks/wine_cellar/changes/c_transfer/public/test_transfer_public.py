"""Public checks for the c_transfer change (several moves in one call).
Shown to the editor, never to the writer.

Usage (with cellar.py importable, e.g. in the sandbox):
    python -m pytest changes/c_transfer/public/test_transfer_public.py
"""

import pytest
from cellar import Cellar, NotEnoughBottles


@pytest.fixture
def cellar():
    c = Cellar()
    c.add_rack("north")
    c.add_rack("south")
    c.store("north", 2015, 6)
    c.store("north", 2018, 2)
    return c


def test_transfer_makes_every_move(cellar):
    assert cellar.transfer([("north", "south", 2015, 4), ("north", "south", 2018, 1)]) == 5
    assert cellar.get_count("north", 2015) == 2
    assert cellar.get_count("south", 2015) == 4
    assert cellar.get_count("south", 2018) == 1


def test_a_failing_move_cancels_the_whole_transfer(cellar):
    with pytest.raises(NotEnoughBottles):
        cellar.transfer([("north", "south", 2015, 4), ("north", "south", 2018, 3)])
    assert cellar.get_count("north", 2015) == 6
    assert cellar.get_count("south", 2015) == 0
