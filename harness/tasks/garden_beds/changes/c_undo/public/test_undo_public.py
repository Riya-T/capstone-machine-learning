"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with garden.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from garden import Garden, GardenError


@pytest.fixture
def garden():
    g = Garden()
    g.add_bed("north")
    g.add_bed("south")
    return g


def test_undo_takes_back_the_last_planting(garden):
    garden.plant("north", "rose", 5)
    garden.plant("north", "rose", 2)
    garden.undo()
    assert garden.get_count("north", "rose") == 5
    garden.undo()
    assert garden.get_species("north") == []


def test_undo_takes_back_a_transplant(garden):
    garden.plant("north", "rose", 4)
    assert garden.transplant_all("north", "south") == 4
    garden.undo()
    assert garden.get_count("north", "rose") == 4
    assert garden.get_count("south", "rose") == 0


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(GardenError):
        Garden().undo()
