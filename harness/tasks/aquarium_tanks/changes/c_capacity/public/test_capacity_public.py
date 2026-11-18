"""Public checks for the tank capacity change. Shown to the editor, never
to the writer.

Usage (with aquarium.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/public/test_capacity_public.py
"""

import pytest
from aquarium import Aquarium, TankFull


@pytest.fixture
def aquarium():
    a = Aquarium()
    a.add_tank("reef", capacity=5)
    a.add_tank("lagoon")
    return a


def test_fish_can_be_put_in_up_to_the_capacity(aquarium):
    assert aquarium.get_capacity("reef") == 5
    assert aquarium.get_capacity("lagoon") is None
    aquarium.add_fish("reef", "tang", 3)
    aquarium.add_fish("reef", "clownfish", 2)
    with pytest.raises(TankFull):
        aquarium.add_fish("reef", "tang", 1)
    assert aquarium.get_count("reef", "tang") == 3


def test_a_move_all_that_would_overfill_a_tank_moves_nothing(aquarium):
    aquarium.add_fish("reef", "tang", 4)
    aquarium.add_fish("lagoon", "guppy", 2)
    with pytest.raises(TankFull):
        aquarium.move_all("lagoon", "reef")
    assert aquarium.get_count("lagoon", "guppy") == 2
    assert aquarium.get_count("reef", "guppy") == 0
