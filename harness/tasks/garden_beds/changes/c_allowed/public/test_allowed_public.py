"""Public checks for the c_allowed change (allowed species per bed). Shown to
the editor, never to the writer.

Usage (with garden.py importable, e.g. in the sandbox):
    python -m pytest changes/c_allowed/public/test_allowed_public.py
"""

import pytest
from garden import Garden, NotAllowed


@pytest.fixture
def garden():
    g = Garden()
    g.add_bed("shade", allowed=["fern", "mint"])
    g.add_bed("north")
    return g


def test_allowed_species_can_be_planted(garden):
    garden.plant("shade", "fern", 3)
    assert garden.get_count("shade", "fern") == 3
    assert garden.get_allowed("shade") == ["fern", "mint"]
    assert garden.get_allowed("north") is None


def test_other_species_are_refused(garden):
    with pytest.raises(NotAllowed):
        garden.plant("shade", "rose", 1)
    assert garden.get_species("shade") == []


def test_transplant_all_into_a_bed_that_refuses_a_species_moves_nothing(garden):
    garden.plant("north", "fern", 2)
    garden.plant("north", "rose", 1)
    with pytest.raises(NotAllowed):
        garden.transplant_all("north", "shade")
    assert garden.get_count("north", "fern") == 2
    assert garden.get_species("shade") == []
