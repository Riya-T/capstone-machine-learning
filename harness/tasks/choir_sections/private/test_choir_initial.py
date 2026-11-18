"""Hidden tests for the initial choir_sections spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with choir.py importable, e.g. in the sandbox):
    python -m pytest private/test_choir_initial.py
"""

import pytest
from choir import Choir, ChoirError


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
    """Every section in order with its singers in order, to check that a
    failed call changed nothing."""
    return [(s, c.get_singers(s)) for s in c.get_sections()]


# --- sections -----------------------------------------------------------------


def test_a_new_section_is_empty():
    c = Choir()
    c.add_section("bass")
    assert c.get_singers("bass") == []
    assert c.get_sections() == ["bass"]


def test_sections_are_listed_in_the_order_added():
    c = Choir()
    for name in ["tenor", "bass", "alto"]:
        c.add_section(name)
    assert c.get_sections() == ["tenor", "bass", "alto"]


def test_adding_a_section_name_in_use_is_rejected(choir):
    before = state(choir)
    with pytest.raises(ChoirError):
        choir.add_section("alto")
    assert state(choir) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.add_singer("bass", "Fay"),
        lambda c: c.move_singer("Ada", "bass"),
        lambda c: c.move_all("bass", "alto"),
        lambda c: c.move_all("alto", "bass"),
        lambda c: c.merge_sections("bass", "alto"),
        lambda c: c.merge_sections("alto", "bass"),
        lambda c: c.get_singers("bass"),
    ],
)
def test_sections_that_were_never_added_raise_key_error(choir, call):
    before = state(choir)
    with pytest.raises(KeyError):
        call(choir)
    assert state(choir) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.add_singer("tenor", "Fay"),
        lambda c: c.move_singer("Ada", "tenor"),
        lambda c: c.move_all("tenor", "alto"),
        lambda c: c.move_all("alto", "tenor"),
        lambda c: c.merge_sections("tenor", "alto"),
        lambda c: c.merge_sections("alto", "tenor"),
        lambda c: c.get_singers("tenor"),
    ],
)
def test_a_merged_section_is_not_in_use(choir, call):
    choir.merge_sections("tenor", "alto")  # tenor is empty
    before = state(choir)
    with pytest.raises(KeyError):
        call(choir)
    assert state(choir) == before


# --- adding and removing singers ------------------------------------------------


def test_singers_join_at_the_end_of_their_section(choir):
    choir.add_singer("soprano", "Fay")
    choir.add_singer("tenor", "Gus")
    assert choir.get_singers("soprano") == ["Ada", "Bea", "Cal", "Fay"]
    assert choir.get_singers("tenor") == ["Gus"]


def test_a_singer_name_in_use_is_rejected(choir):
    before = state(choir)
    with pytest.raises(ChoirError):
        choir.add_singer("soprano", "Bea")
    with pytest.raises(ChoirError):
        choir.add_singer("tenor", "Eve")
    assert state(choir) == before


def test_removing_a_singer_keeps_the_others_in_order(choir):
    choir.remove_singer("Bea")
    assert choir.get_singers("soprano") == ["Ada", "Cal"]
    choir.remove_singer("Ada")
    assert choir.get_singers("soprano") == ["Cal"]
    assert choir.get_singers("alto") == ["Dot", "Eve"]


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.remove_singer("Zed"),
        lambda c: c.move_singer("Zed", "alto"),
    ],
    ids=["remove", "move"],
)
def test_singers_never_added_raise_key_error(choir, call):
    before = state(choir)
    with pytest.raises(KeyError):
        call(choir)
    assert state(choir) == before


def test_a_removed_singer_is_not_in_the_choir(choir):
    choir.remove_singer("Eve")
    before = state(choir)
    with pytest.raises(KeyError):
        choir.remove_singer("Eve")
    with pytest.raises(KeyError):
        choir.move_singer("Eve", "tenor")
    assert state(choir) == before


# --- moving singers -------------------------------------------------------------


def test_a_moved_singer_stands_at_the_end_of_the_new_section(choir):
    choir.move_singer("Ada", "alto")
    assert choir.get_singers("soprano") == ["Bea", "Cal"]
    assert choir.get_singers("alto") == ["Dot", "Eve", "Ada"]


def test_moving_into_an_empty_section(choir):
    choir.move_singer("Cal", "tenor")
    choir.move_singer("Dot", "tenor")
    assert choir.get_singers("tenor") == ["Cal", "Dot"]
    assert choir.get_singers("alto") == ["Eve"]


def test_a_moved_singer_can_be_moved_and_removed_again(choir):
    choir.move_singer("Bea", "tenor")
    choir.move_singer("Bea", "alto")
    assert choir.get_singers("tenor") == []
    assert choir.get_singers("alto") == ["Dot", "Eve", "Bea"]
    choir.remove_singer("Bea")
    assert choir.get_singers("alto") == ["Dot", "Eve"]


# --- move_all -------------------------------------------------------------------


def test_move_all_moves_every_singer_in_order(choir):
    assert choir.move_all("soprano", "alto") == 3
    assert choir.get_singers("alto") == ["Dot", "Eve", "Ada", "Bea", "Cal"]
    assert choir.get_singers("soprano") == []
    assert choir.get_sections() == ["soprano", "alto", "tenor"]


def test_move_all_into_an_empty_section(choir):
    assert choir.move_all("alto", "tenor") == 2
    assert choir.get_singers("tenor") == ["Dot", "Eve"]
    assert choir.get_singers("alto") == []


def test_move_all_from_an_empty_section_moves_nobody(choir):
    before = state(choir)
    assert choir.move_all("tenor", "soprano") == 0
    assert state(choir) == before


def test_singers_moved_by_move_all_can_still_be_moved_and_removed(choir):
    choir.move_all("alto", "tenor")
    choir.move_singer("Dot", "soprano")
    choir.remove_singer("Eve")
    assert choir.get_singers("tenor") == []
    assert choir.get_singers("soprano") == ["Ada", "Bea", "Cal", "Dot"]


def test_a_section_emptied_by_move_all_can_be_used_again(choir):
    choir.move_all("soprano", "tenor")
    choir.add_singer("soprano", "Fay")
    choir.move_singer("Ada", "soprano")
    assert choir.get_singers("soprano") == ["Fay", "Ada"]
    assert choir.get_singers("tenor") == ["Bea", "Cal"]


# --- merging --------------------------------------------------------------------


def test_merge_moves_every_singer_in_order(choir):
    assert choir.merge_sections("soprano", "alto") == 3
    assert choir.get_sections() == ["alto", "tenor"]
    assert choir.get_singers("alto") == ["Dot", "Eve", "Ada", "Bea", "Cal"]


def test_merge_into_a_section_listed_earlier(choir):
    assert choir.merge_sections("alto", "soprano") == 2
    assert choir.get_sections() == ["soprano", "tenor"]
    assert choir.get_singers("soprano") == ["Ada", "Bea", "Cal", "Dot", "Eve"]


def test_merging_an_empty_section_moves_nobody_and_removes_it(choir):
    assert choir.merge_sections("tenor", "soprano") == 0
    assert choir.get_sections() == ["soprano", "alto"]
    assert choir.get_singers("soprano") == ["Ada", "Bea", "Cal"]


def test_merged_singers_can_still_be_moved_and_removed(choir):
    choir.merge_sections("alto", "tenor")
    choir.move_singer("Dot", "soprano")
    choir.remove_singer("Eve")
    assert choir.get_singers("tenor") == []
    assert choir.get_singers("soprano") == ["Ada", "Bea", "Cal", "Dot"]


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.move_all("alto", "alto"),
        lambda c: c.merge_sections("alto", "alto"),
    ],
    ids=["move_all", "merge_sections"],
)
def test_the_same_section_on_both_sides_is_rejected(choir, call):
    before = state(choir)
    with pytest.raises(ValueError):
        call(choir)
    assert state(choir) == before


# --- general --------------------------------------------------------------------


def test_choirs_do_not_share_sections_or_singers():
    first, second = Choir(), Choir()
    first.add_section("alto")
    first.add_singer("alto", "Ada")
    assert second.get_sections() == []
    second.add_section("alto")
    second.add_singer("alto", "Ada")
    assert second.get_singers("alto") == ["Ada"]
