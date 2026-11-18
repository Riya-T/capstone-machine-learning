"""Hidden tests for the c_limit change (a limit per section). Never shown to
the writer or the editor.

Usage (with choir.py importable, e.g. in the sandbox):
    python -m pytest changes/c_limit/private/test_choir_limit_new.py
"""

import pytest
from choir import Choir, ChoirError, SectionFull


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


# --- the setting ----------------------------------------------------------------


def test_every_section_starts_without_a_limit(choir):
    assert [choir.get_limit(s) for s in choir.get_sections()] == [None, None, None]
    choir.add_section("bass")
    assert choir.get_limit("bass") is None
    for name in ["Fay", "Gus", "Hal", "Ivy"]:
        choir.add_singer("bass", name)
    assert len(choir.get_singers("bass")) == 4


def test_each_setting_replaces_the_one_before(choir):
    choir.set_limit("tenor", 1)
    choir.set_limit("tenor", 2)
    assert choir.get_limit("tenor") == 2
    choir.add_singer("tenor", "Fay")
    choir.add_singer("tenor", "Gus")
    with pytest.raises(SectionFull):
        choir.add_singer("tenor", "Hal")
    choir.set_limit("tenor", None)
    assert choir.get_limit("tenor") is None
    choir.add_singer("tenor", "Hal")
    assert choir.get_singers("tenor") == ["Fay", "Gus", "Hal"]


@pytest.mark.parametrize("limit", [0, -2])
def test_limits_below_1_are_rejected_and_keep_the_old_one(choir, limit):
    choir.set_limit("alto", 3)
    with pytest.raises(ValueError):
        choir.set_limit("alto", limit)
    assert choir.get_limit("alto") == 3


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.set_limit("bass", 2),
        lambda c: c.set_limit("bass", None),
        lambda c: c.get_limit("bass"),
        lambda c: c.set_limit("tenor", 2),  # merged below
        lambda c: c.get_limit("tenor"),
    ],
)
def test_sections_not_in_use_raise_key_error(choir, call):
    choir.merge_sections("tenor", "alto")
    with pytest.raises(KeyError):
        call(choir)


def test_a_setting_changes_no_singers(choir):
    before = state(choir)
    choir.set_limit("soprano", 1)
    choir.set_limit("tenor", 5)
    assert state(choir) == before


def test_a_limit_only_applies_to_its_own_section(choir):
    choir.set_limit("tenor", 1)
    choir.add_singer("alto", "Fay")
    choir.move_singer("Ada", "alto")
    assert choir.get_singers("alto") == ["Dot", "Eve", "Fay", "Ada"]


# --- add_singer and move_singer -------------------------------------------------


def test_singers_can_join_up_to_the_limit(choir):
    choir.set_limit("alto", 4)
    choir.add_singer("alto", "Fay")
    choir.move_singer("Ada", "alto")
    assert choir.get_singers("alto") == ["Dot", "Eve", "Fay", "Ada"]


def test_add_singer_to_a_full_section_changes_nothing(choir):
    choir.set_limit("alto", 2)
    before = state(choir)
    with pytest.raises(SectionFull):
        choir.add_singer("alto", "Fay")
    assert state(choir) == before
    choir.add_singer("tenor", "Fay")  # the name was not taken
    assert choir.get_singers("tenor") == ["Fay"]


def test_move_into_a_full_section_changes_nothing(choir):
    choir.set_limit("alto", 2)
    before = state(choir)
    with pytest.raises(SectionFull):
        choir.move_singer("Bea", "alto")
    assert state(choir) == before


# --- move_all and merge_sections ------------------------------------------------


@pytest.mark.parametrize("how", ["move_all", "merge_sections"])
def test_moving_a_section_into_one_with_room_for_everyone(choir, how):
    choir.set_limit("alto", 5)
    assert getattr(choir, how)("soprano", "alto") == 3
    assert choir.get_singers("alto") == ["Dot", "Eve", "Ada", "Bea", "Cal"]


def test_move_all_that_would_overfill_moves_nobody(choir):
    choir.set_limit("alto", 4)
    before = state(choir)
    with pytest.raises(SectionFull):
        choir.move_all("soprano", "alto")
    assert state(choir) == before


def test_merge_that_would_overfill_moves_nobody_and_keeps_the_source(choir):
    choir.set_limit("alto", 4)
    before = state(choir)
    with pytest.raises(SectionFull):
        choir.merge_sections("soprano", "alto")
    assert state(choir) == before
    assert choir.get_sections() == ["soprano", "alto", "tenor"]


def test_a_refused_merge_can_be_retried_once_there_is_room(choir):
    choir.set_limit("tenor", 2)
    with pytest.raises(SectionFull):
        choir.merge_sections("soprano", "tenor")
    choir.remove_singer("Bea")
    assert choir.merge_sections("soprano", "tenor") == 2
    assert choir.get_singers("tenor") == ["Ada", "Cal"]
    assert choir.get_sections() == ["alto", "tenor"]


# --- singers already in a section -----------------------------------------------


def test_a_limit_below_the_current_size_keeps_everyone(choir):
    choir.set_limit("soprano", 1)
    assert choir.get_limit("soprano") == 1
    assert choir.get_singers("soprano") == ["Ada", "Bea", "Cal"]
    with pytest.raises(SectionFull):
        choir.add_singer("soprano", "Fay")
    choir.remove_singer("Ada")
    choir.move_singer("Bea", "tenor")
    assert choir.get_singers("soprano") == ["Cal"]
    with pytest.raises(SectionFull):
        choir.move_singer("Dot", "soprano")
    choir.move_singer("Cal", "alto")
    choir.add_singer("soprano", "Fay")
    assert choir.get_singers("soprano") == ["Fay"]


def test_leaving_a_section_is_never_refused(choir):
    choir.set_limit("soprano", 1)
    choir.set_limit("alto", 1)
    assert choir.move_all("soprano", "tenor") == 3
    assert choir.merge_sections("alto", "tenor") == 2
    assert choir.get_sections() == ["soprano", "tenor"]
    assert choir.get_singers("tenor") == ["Ada", "Bea", "Cal", "Dot", "Eve"]


# --- other errors ---------------------------------------------------------------


def test_other_errors_still_work_with_limits(choir):
    choir.set_limit("tenor", 1)
    before = state(choir)
    with pytest.raises(ChoirError):
        choir.add_singer("alto", "Ada")
    with pytest.raises(KeyError):
        choir.move_singer("Zed", "alto")
    with pytest.raises(ValueError):
        choir.merge_sections("alto", "alto")
    assert state(choir) == before


def test_section_full_is_a_choir_error():
    assert issubclass(SectionFull, ChoirError)
