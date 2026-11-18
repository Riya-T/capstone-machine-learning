"""Public checks for the undo change. Shown to the editor, never to the
writer.

Usage (with aquarium.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_tank_undo_public.py
"""

import pytest
from aquarium import Aquarium, AquariumError


@pytest.fixture
def aquarium():
    a = Aquarium()
    a.add_tank("reef")
    a.add_tank("lagoon")
    return a


def test_undo_takes_back_the_last_fish_put_in(aquarium):
    aquarium.add_fish("reef", "tang", 5)
    aquarium.add_fish("reef", "tang", 2)
    aquarium.undo()
    assert aquarium.get_count("reef", "tang") == 5
    aquarium.undo()
    assert aquarium.get_species("reef") == []


def test_undo_takes_back_a_simple_move_all(aquarium):
    aquarium.add_fish("reef", "guppy", 4)
    assert aquarium.move_all("reef", "lagoon") == 4
    aquarium.undo()
    assert aquarium.get_count("reef", "guppy") == 4
    assert aquarium.get_count("lagoon", "guppy") == 0


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(AquariumError):
        Aquarium().undo()
