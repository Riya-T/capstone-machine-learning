"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with choir.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_choir_undo_new.py
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
    return [(s, c.get_singers(s)) for s in c.get_sections()]


# --- single singers -------------------------------------------------------------


def test_undoing_add_singer_frees_the_name(choir):
    before = state(choir)
    choir.add_singer("tenor", "Fay")
    choir.undo()
    assert state(choir) == before
    choir.add_singer("alto", "Fay")
    assert choir.get_singers("alto") == ["Dot", "Eve", "Fay"]


def test_an_undone_removal_puts_the_singer_back_in_place(choir):
    before = state(choir)
    choir.remove_singer("Bea")
    choir.undo()
    assert choir.get_singers("soprano") == ["Ada", "Bea", "Cal"]
    assert state(choir) == before


def test_a_singer_brought_back_is_in_the_choir_again(choir):
    choir.remove_singer("Ada")
    choir.undo()
    with pytest.raises(ChoirError):
        choir.add_singer("tenor", "Ada")
    choir.move_singer("Ada", "tenor")
    assert choir.get_singers("tenor") == ["Ada"]
    assert choir.get_singers("soprano") == ["Bea", "Cal"]


def test_an_undone_move_puts_the_singer_back_in_place(choir):
    before = state(choir)
    choir.move_singer("Ada", "alto")
    assert choir.get_singers("alto") == ["Dot", "Eve", "Ada"]
    choir.undo()
    assert choir.get_singers("soprano") == ["Ada", "Bea", "Cal"]
    assert choir.get_singers("alto") == ["Dot", "Eve"]
    assert state(choir) == before


def test_undoing_two_moves_of_the_same_singer(choir):
    before = state(choir)
    choir.move_singer("Bea", "tenor")
    choir.move_singer("Bea", "alto")
    choir.undo()
    assert choir.get_singers("tenor") == ["Bea"]
    assert choir.get_singers("alto") == ["Dot", "Eve"]
    choir.undo()
    assert state(choir) == before


# --- move_all -------------------------------------------------------------------


def test_an_undone_move_all_restores_both_sections(choir):
    before = state(choir)
    assert choir.move_all("soprano", "alto") == 3
    choir.undo()
    assert choir.get_singers("soprano") == ["Ada", "Bea", "Cal"]
    assert choir.get_singers("alto") == ["Dot", "Eve"]
    assert state(choir) == before


def test_one_undo_takes_back_the_whole_move_all(choir):
    choir.add_singer("tenor", "Fay")
    choir.move_all("soprano", "tenor")
    choir.undo()
    assert choir.get_singers("tenor") == ["Fay"]
    assert choir.get_singers("soprano") == ["Ada", "Bea", "Cal"]
    choir.undo()
    assert choir.get_singers("tenor") == []


def test_undo_of_move_all_after_singers_joined_the_source(choir):
    choir.move_all("soprano", "tenor")
    choir.add_singer("soprano", "Fay")
    choir.move_all("tenor", "soprano")
    assert choir.get_singers("soprano") == ["Fay", "Ada", "Bea", "Cal"]
    choir.undo()
    assert choir.get_singers("soprano") == ["Fay"]
    assert choir.get_singers("tenor") == ["Ada", "Bea", "Cal"]
    choir.undo()
    choir.undo()
    assert choir.get_singers("soprano") == ["Ada", "Bea", "Cal"]
    assert choir.get_singers("tenor") == []


# --- merge_sections -------------------------------------------------------------


def test_an_undone_merge_brings_the_source_back(choir):
    before = state(choir)
    assert choir.merge_sections("soprano", "alto") == 3
    choir.undo()
    assert choir.get_sections() == ["soprano", "alto", "tenor"]
    assert choir.get_singers("alto") == ["Dot", "Eve"]
    assert state(choir) == before


def test_an_undone_merge_puts_the_source_back_in_its_place(choir):
    choir.add_section("bass")
    choir.add_singer("bass", "Fay")
    before = state(choir)
    choir.merge_sections("alto", "bass")
    assert choir.get_sections() == ["soprano", "tenor", "bass"]
    choir.undo()
    assert choir.get_sections() == ["soprano", "alto", "tenor", "bass"]
    assert choir.get_singers("bass") == ["Fay"]
    assert state(choir) == before


def test_one_undo_takes_back_the_whole_merge(choir):
    choir.add_singer("tenor", "Fay")
    choir.merge_sections("soprano", "tenor")
    choir.undo()
    assert choir.get_singers("tenor") == ["Fay"]
    assert choir.get_singers("soprano") == ["Ada", "Bea", "Cal"]
    choir.undo()
    assert choir.get_singers("tenor") == []


def test_a_merged_section_brought_back_is_in_use_again(choir):
    choir.merge_sections("alto", "tenor")
    choir.undo()
    with pytest.raises(ChoirError):
        choir.add_section("alto")
    choir.add_singer("alto", "Fay")
    choir.move_singer("Dot", "soprano")
    assert choir.get_singers("alto") == ["Eve", "Fay"]
    assert choir.get_singers("tenor") == []


def test_undoing_merges_in_a_row_restores_the_section_order(choir):
    choir.merge_sections("soprano", "tenor")
    choir.merge_sections("alto", "tenor")
    assert choir.get_sections() == ["tenor"]
    choir.undo()
    assert choir.get_sections() == ["alto", "tenor"]
    choir.undo()
    assert choir.get_sections() == ["soprano", "alto", "tenor"]
    assert choir.get_singers("soprano") == ["Ada", "Bea", "Cal"]


# --- empty sections -------------------------------------------------------------


def test_merging_an_empty_section_is_still_a_call(choir):
    assert choir.merge_sections("tenor", "alto") == 0
    choir.undo()
    assert choir.get_sections() == ["soprano", "alto", "tenor"]
    choir.undo()  # Eve's arrival
    assert choir.get_singers("alto") == ["Dot"]


def test_a_move_all_of_nobody_is_still_a_call(choir):
    assert choir.move_all("tenor", "alto") == 0
    choir.undo()
    assert choir.get_singers("alto") == ["Dot", "Eve"]
    choir.undo()  # Eve's arrival
    assert choir.get_singers("alto") == ["Dot"]


# --- what is and is not recorded ------------------------------------------------


def test_each_undo_goes_one_call_further_back():
    c = Choir()
    calls = [
        lambda: c.add_section("soprano"),
        lambda: c.add_section("alto"),
        lambda: c.add_singer("soprano", "Ada"),
        lambda: c.add_singer("soprano", "Bea"),
        lambda: c.add_section("tenor"),
        lambda: c.add_singer("alto", "Cal"),
        lambda: c.add_singer("soprano", "Dot"),
        lambda: c.move_singer("Bea", "tenor"),
        lambda: c.remove_singer("Ada"),
        lambda: c.move_singer("Cal", "soprano"),
        lambda: c.move_all("soprano", "tenor"),
        lambda: c.add_section("bass"),
        lambda: c.add_singer("bass", "Eve"),
        lambda: c.merge_sections("alto", "bass"),
        lambda: c.merge_sections("tenor", "bass"),
    ]
    states = [state(c)]
    for call in calls:
        call()
        states.append(state(c))
    assert c.get_sections() == ["soprano", "bass"]
    assert c.get_singers("bass") == ["Eve", "Bea", "Dot", "Cal"]
    for expected in reversed(states[:-1]):
        c.undo()
        assert state(c) == expected
    with pytest.raises(ChoirError):
        c.undo()
    assert c.get_sections() == []


def test_failed_calls_are_not_recorded(choir):
    choir.add_singer("tenor", "Fay")
    for call in (
        lambda: choir.add_section("alto"),
        lambda: choir.add_singer("alto", "Ada"),
        lambda: choir.add_singer("bass", "Gus"),
        lambda: choir.remove_singer("Zed"),
        lambda: choir.move_singer("Zed", "alto"),
        lambda: choir.move_singer("Ada", "bass"),
        lambda: choir.move_all("alto", "alto"),
        lambda: choir.move_all("bass", "alto"),
        lambda: choir.merge_sections("alto", "alto"),
        lambda: choir.merge_sections("bass", "alto"),
    ):
        with pytest.raises((ValueError, KeyError, ChoirError)):
            call()
    choir.undo()  # Fay
    assert choir.get_singers("tenor") == []
    assert choir.get_singers("soprano") == ["Ada", "Bea", "Cal"]


def test_get_calls_are_not_recorded(choir):
    choir.add_singer("tenor", "Fay")
    choir.get_singers("tenor")
    choir.get_sections()
    choir.undo()
    assert choir.get_singers("tenor") == []
    assert choir.get_singers("alto") == ["Dot", "Eve"]


def test_there_is_no_redo():
    c = Choir()
    c.add_section("alto")
    c.add_singer("alto", "Ada")
    c.undo()
    c.undo()
    assert c.get_sections() == []
    with pytest.raises(ChoirError):
        c.undo()


def test_new_calls_after_an_undo_are_undone_first(choir):
    choir.remove_singer("Cal")
    choir.undo()
    choir.move_singer("Cal", "tenor")
    choir.undo()
    assert choir.get_singers("soprano") == ["Ada", "Bea", "Cal"]
    choir.undo()  # Eve's arrival in the fixture
    assert choir.get_singers("alto") == ["Dot"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    c = Choir()
    with pytest.raises(ChoirError):
        c.undo()
    c.add_section("alto")
    c.undo()
    with pytest.raises(ChoirError):
        c.undo()
    assert c.get_sections() == []
    c.add_section("alto")
    c.add_singer("alto", "Ada")
    assert c.get_singers("alto") == ["Ada"]


def test_the_whole_fixture_can_be_undone(choir):
    for _ in range(8):
        choir.undo()
    assert choir.get_sections() == []
    with pytest.raises(ChoirError):
        choir.undo()
