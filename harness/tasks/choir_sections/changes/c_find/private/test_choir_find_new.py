"""Hidden tests for the c_find change (where a singer stands). Never shown to
the writer or the editor.

Usage (with choir.py importable, e.g. in the sandbox):
    python -m pytest changes/c_find/private/test_choir_find_new.py
"""

import pytest
from choir import Choir


@pytest.fixture
def choir():
    c = Choir()
    for name in ["soprano", "alto", "tenor"]:
        c.add_section(name)
    for name in ["Ada", "Bea", "Cal"]:
        c.add_singer("soprano", name)
    c.add_singer("alto", "Dot")
    c.add_singer("alto", "Eve")
    return c


def state(c):
    return [(s, c.get_singers(s)) for s in c.get_sections()]


def where(c, singer):
    return c.get_section_of(singer), c.get_position(singer)


# --- plain lookups --------------------------------------------------------------


def test_every_singer_is_found_where_they_stand(choir):
    assert where(choir, "Ada") == ("soprano", 1)
    assert where(choir, "Bea") == ("soprano", 2)
    assert where(choir, "Cal") == ("soprano", 3)
    assert where(choir, "Dot") == ("alto", 1)
    assert where(choir, "Eve") == ("alto", 2)


def test_positions_match_get_singers(choir):
    choir.add_singer("tenor", "Fay")
    for section in choir.get_sections():
        for place, singer in enumerate(choir.get_singers(section), start=1):
            assert choir.get_section_of(singer) == section
            assert choir.get_position(singer) == place


def test_a_new_singer_stands_last(choir):
    choir.add_singer("soprano", "Fay")
    assert where(choir, "Fay") == ("soprano", 4)


def test_lookups_change_nothing(choir):
    before = state(choir)
    where(choir, "Bea")
    where(choir, "Eve")
    assert state(choir) == before


# --- after changes --------------------------------------------------------------


def test_places_behind_a_removed_singer_go_down_by_one(choir):
    choir.remove_singer("Ada")
    assert where(choir, "Bea") == ("soprano", 1)
    assert where(choir, "Cal") == ("soprano", 2)
    assert where(choir, "Dot") == ("alto", 1)


def test_a_moved_singer_is_found_at_the_end_of_the_new_section(choir):
    choir.move_singer("Bea", "alto")
    assert where(choir, "Bea") == ("alto", 3)
    assert where(choir, "Cal") == ("soprano", 2)
    assert where(choir, "Ada") == ("soprano", 1)


def test_a_singer_moved_twice(choir):
    choir.move_singer("Ada", "tenor")
    choir.move_singer("Ada", "alto")
    assert where(choir, "Ada") == ("alto", 3)


def test_merged_singers_are_found_in_the_receiving_section(choir):
    choir.merge_sections("soprano", "alto")
    assert where(choir, "Dot") == ("alto", 1)
    assert where(choir, "Ada") == ("alto", 3)
    assert where(choir, "Cal") == ("alto", 5)


def test_merging_into_an_empty_section(choir):
    choir.merge_sections("alto", "tenor")
    assert where(choir, "Dot") == ("tenor", 1)
    assert where(choir, "Eve") == ("tenor", 2)


def test_singers_moved_by_move_all_are_found_in_the_receiving_section(choir):
    choir.add_singer("tenor", "Fay")
    choir.move_all("alto", "tenor")
    assert where(choir, "Fay") == ("tenor", 1)
    assert where(choir, "Dot") == ("tenor", 2)
    assert where(choir, "Eve") == ("tenor", 3)


def test_a_new_section_and_its_singer_are_found(choir):
    choir.add_section("bass")
    choir.add_singer("bass", "Fay")
    assert where(choir, "Fay") == ("bass", 1)


# --- singers not in the choir ---------------------------------------------------


@pytest.mark.parametrize("method", ["get_section_of", "get_position"])
def test_a_singer_never_added_raises_key_error(choir, method):
    with pytest.raises(KeyError):
        getattr(choir, method)("Zed")


@pytest.mark.parametrize("method", ["get_section_of", "get_position"])
def test_a_removed_singer_raises_key_error(choir, method):
    choir.remove_singer("Bea")
    with pytest.raises(KeyError):
        getattr(choir, method)("Bea")


def test_lookups_of_missing_singers_change_nothing(choir):
    choir.remove_singer("Ada")
    before = state(choir)
    for method in ("get_section_of", "get_position"):
        with pytest.raises(KeyError):
            getattr(choir, method)("Ada")
    assert state(choir) == before
    assert where(choir, "Cal") == ("soprano", 2)
