"""Public checks for the c_allowed change (species allowed in a paddock).
Shown to the editor, never to the writer.

Usage (with farm.py importable, e.g. in the sandbox):
    python -m pytest changes/c_allowed/public/test_allowed_public.py
"""

import pytest
from farm import Farm, NotAllowed


@pytest.fixture
def farm():
    f = Farm()
    f.add_paddock("north")
    f.add_paddock("south")
    return f


def test_only_allowed_species_can_arrive(farm):
    assert farm.get_allowed("north") is None
    farm.set_allowed("north", ["sheep", "goat"])
    assert farm.get_allowed("north") == ["goat", "sheep"]
    farm.arrive("north", "sheep", 3)
    with pytest.raises(NotAllowed):
        farm.arrive("north", "cow", 1)
    assert farm.get_count("north", "cow") == 0
    assert farm.get_count("north", "sheep") == 3


def test_a_move_into_a_paddock_that_refuses_the_species_raises(farm):
    farm.arrive("north", "cow", 4)
    farm.set_allowed("south", ["sheep"])
    with pytest.raises(NotAllowed):
        farm.move("cow", "north", "south", 2)
    assert farm.get_count("north", "cow") == 4
    assert farm.get_count("south", "cow") == 0
