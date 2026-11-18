"""Public checks for the transfer change. Shown to the editor, never to the
writer.

Usage (with aquarium.py importable, e.g. in the sandbox):
    python -m pytest changes/c_transfer/public/test_transfer_public.py
"""

import pytest
from aquarium import Aquarium, NotEnoughFish


@pytest.fixture
def aquarium():
    a = Aquarium()
    a.add_tank("reef")
    a.add_tank("lagoon")
    a.add_fish("reef", "tang", 5)
    a.add_fish("lagoon", "guppy", 3)
    return a


def test_transfer_makes_every_move_and_returns_how_many(aquarium):
    assert aquarium.transfer([("tang", "reef", "lagoon", 2), ("guppy", "lagoon", "reef", 3)]) == 5
    assert aquarium.get_count("reef", "tang") == 3
    assert aquarium.get_count("lagoon", "tang") == 2
    assert aquarium.get_count("reef", "guppy") == 3
    assert aquarium.get_species("lagoon") == ["tang"]


def test_a_transfer_with_a_failing_move_makes_no_move(aquarium):
    with pytest.raises(NotEnoughFish):
        aquarium.transfer([("tang", "reef", "lagoon", 2), ("guppy", "lagoon", "reef", 4)])
    assert aquarium.get_count("reef", "tang") == 5
    assert aquarium.get_count("lagoon", "tang") == 0
    assert aquarium.get_count("lagoon", "guppy") == 3
