"""Hidden tests for the c_allowed change (allowed species per bed). Never
shown to the writer or the editor. They call only the spec's methods and
this change's own, never undo.

Usage (with garden.py importable, e.g. in the sandbox):
    python -m pytest changes/c_allowed/private/test_allowed_new.py
"""

import pytest
from garden import Garden, GardenError, NotAllowed, NotEnoughPlants


@pytest.fixture
def garden():
    g = Garden()
    g.add_bed("north")
    g.add_bed("shade", allowed=["mint", "fern", "mint"])
    g.add_bed("east", allowed=["rose"])
    g.plant("north", "rose", 3)
    g.plant("north", "tulip", 2)
    g.plant("shade", "fern", 4)
    return g


def state(g):
    return [(b, [(s, g.get_count(b, s)) for s in g.get_species(b)]) for b in g.get_beds()]


# --- setting and reading the allowed species ------------------------------------------


def test_get_allowed_returns_none_or_the_species_sorted_without_duplicates(garden):
    assert garden.get_allowed("north") is None
    assert garden.get_allowed("shade") == ["fern", "mint"]
    assert garden.get_allowed("east") == ["rose"]


def test_the_allowed_species_can_be_given_by_position():
    g = Garden()
    g.add_bed("pots", ["sage", "basil"])
    assert g.get_allowed("pots") == ["basil", "sage"]


def test_an_empty_list_allows_nothing():
    g = Garden()
    g.add_bed("gravel", allowed=[])
    assert g.get_allowed("gravel") == []
    with pytest.raises(NotAllowed):
        g.plant("gravel", "rose", 1)
    assert g.get_species("gravel") == []


def test_get_allowed_of_a_bed_not_in_use_raises_key_error(garden):
    with pytest.raises(KeyError):
        garden.get_allowed("west")
    garden.plant("east", "rose", 1)
    garden.clear_bed("east", "north")
    with pytest.raises(KeyError):
        garden.get_allowed("east")


def test_not_allowed_is_a_garden_error_of_its_own():
    assert issubclass(NotAllowed, GardenError)
    assert not issubclass(NotAllowed, NotEnoughPlants)


# --- planting -------------------------------------------------------------------------


def test_allowed_species_can_be_planted(garden):
    garden.plant("shade", "mint", 2)
    garden.plant("shade", "fern", 1)
    garden.plant("east", "rose", 6)
    assert garden.get_species("shade") == ["fern", "mint"]
    assert garden.get_count("shade", "fern") == 5
    assert garden.get_count("east", "rose") == 6


def test_species_that_are_not_allowed_are_refused(garden):
    before = state(garden)
    with pytest.raises(NotAllowed):
        garden.plant("shade", "rose", 1)
    with pytest.raises(NotAllowed):
        garden.plant("east", "tulip", 2)
    assert state(garden) == before


def test_a_bed_without_a_list_takes_any_species(garden):
    garden.plant("north", "fern", 1)
    garden.plant("north", "cactus", 1)
    assert garden.get_species("north") == ["cactus", "fern", "rose", "tulip"]


# --- transplanting and clearing --------------------------------------------------------


def test_transplant_all_of_allowed_species_works(garden):
    garden.pull("north", "tulip", 2)
    assert garden.transplant_all("north", "east") == 3
    assert garden.get_count("east", "rose") == 3
    assert garden.get_species("north") == []


def test_transplant_all_with_one_species_not_allowed_moves_nothing(garden):
    before = state(garden)
    with pytest.raises(NotAllowed):
        garden.transplant_all("north", "east")
    assert state(garden) == before


def test_transplant_all_out_of_a_bed_is_never_limited(garden):
    assert garden.transplant_all("shade", "north") == 4
    assert garden.get_count("north", "fern") == 4
    assert garden.get_species("shade") == []


def test_clear_bed_into_a_bed_that_allows_everything_moved(garden):
    garden.plant("east", "rose", 1)
    assert garden.clear_bed("east", "north") == 1
    garden.plant("north", "mint", 1)
    garden.pull("north", "rose", 4)
    garden.pull("north", "tulip", 2)
    assert garden.clear_bed("north", "shade") == 1
    assert garden.get_beds() == ["shade"]
    assert garden.get_count("shade", "mint") == 1


def test_clear_bed_with_one_species_not_allowed_moves_nothing_and_keeps_the_bed(garden):
    before = state(garden)
    with pytest.raises(NotAllowed):
        garden.clear_bed("north", "east")
    with pytest.raises(NotAllowed):
        garden.clear_bed("shade", "east")
    assert state(garden) == before
    assert garden.get_beds() == ["north", "shade", "east"]
    assert garden.get_allowed("shade") == ["fern", "mint"]


def test_pulling_is_never_limited(garden):
    garden.transplant_all("shade", "north")
    garden.pull("north", "fern", 4)
    garden.pull("north", "rose", 1)
    assert garden.get_species("north") == ["rose", "tulip"]


def test_the_other_beds_keep_their_allowed_species_after_a_clear(garden):
    garden.plant("east", "rose", 2)
    garden.clear_bed("east", "north")
    assert garden.get_allowed("shade") == ["fern", "mint"]
    garden.add_bed("pots", allowed=["sage"])
    assert garden.get_beds() == ["north", "shade", "pots"]
    garden.plant("pots", "sage", 2)
    with pytest.raises(NotAllowed):
        garden.plant("pots", "rose", 1)
    assert garden.get_count("pots", "sage") == 2
